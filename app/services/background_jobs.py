import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import StrEnum
from uuid import uuid4

from app.connectors.opennms.client import OpenNMSClient
from app.core.config import Settings
from app.db.session import SessionLocal
from app.services.alert_processor import AlertProcessorService
from app.services.cache import app_cache
from app.services.ingestion_service import OpenNMSIngestionService
from app.services.metrics import metrics_registry

logger = logging.getLogger(__name__)


class JobType(StrEnum):
    INGESTION_SYNC = "ingestion_sync"
    AI_PROCESSING = "ai_processing"


@dataclass
class JobStatus:
    job_id: str
    job_type: JobType
    status: str = "queued"
    attempts: int = 0
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class BackgroundJobManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.queue: asyncio.Queue[JobStatus] = asyncio.Queue(maxsize=settings.ingestion_queue_max_size)
        self.statuses: dict[str, JobStatus] = {}
        self._worker_task: asyncio.Task | None = None
        self._scheduler_task: asyncio.Task | None = None
        self._last_enqueued_at: dict[JobType, float] = {}
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        if self._worker_task is not None:
            return
        self._stopping.clear()
        self._worker_task = asyncio.create_task(self._worker_loop(), name="mcp-background-worker")
        if self.settings.ingestion_worker_enabled:
            self._scheduler_task = asyncio.create_task(self._scheduler_loop(), name="mcp-ingestion-scheduler")

    async def stop(self) -> None:
        self._stopping.set()
        for task in (self._scheduler_task, self._worker_task):
            if task:
                task.cancel()
        await asyncio.gather(
            *(task for task in (self._scheduler_task, self._worker_task) if task),
            return_exceptions=True,
        )
        self._worker_task = None
        self._scheduler_task = None

    async def enqueue(self, job_type: JobType, force: bool = False) -> JobStatus:
        now = time.monotonic()
        last = self._last_enqueued_at.get(job_type, 0)
        if not force and now - last < self.settings.ingestion_job_rate_limit_seconds:
            raise ValueError(f"job rate limited: {job_type.value}")

        job = JobStatus(job_id=str(uuid4()), job_type=job_type)
        await self.queue.put(job)
        self.statuses[job.job_id] = job
        self._last_enqueued_at[job_type] = now
        metrics_registry.set_gauge("background_queue_depth", self.queue.qsize())
        return job

    def snapshot(self) -> dict:
        statuses = sorted(self.statuses.values(), key=lambda item: item.created_at, reverse=True)[:25]
        return {
            "queue_depth": self.queue.qsize(),
            "worker_running": self._worker_task is not None and not self._worker_task.done(),
            "recent_jobs": [
                {
                    "job_id": status.job_id,
                    "job_type": status.job_type.value,
                    "status": status.status,
                    "attempts": status.attempts,
                    "error": status.error,
                    "created_at": status.created_at,
                    "updated_at": status.updated_at,
                }
                for status in statuses
            ],
        }

    async def _scheduler_loop(self) -> None:
        while not self._stopping.is_set():
            try:
                await self.enqueue(JobType.INGESTION_SYNC)
            except ValueError:
                pass
            except Exception:
                logger.exception("failed to enqueue scheduled ingestion")
            await asyncio.sleep(self.settings.ingestion_interval_seconds)

    async def _worker_loop(self) -> None:
        while not self._stopping.is_set():
            job = await self.queue.get()
            metrics_registry.set_gauge("background_queue_depth", self.queue.qsize())
            try:
                await self._run_with_retry(job)
            finally:
                self.queue.task_done()
                metrics_registry.set_gauge("background_queue_depth", self.queue.qsize())

    async def _run_with_retry(self, job: JobStatus) -> None:
        max_attempts = max(1, self.settings.opennms_max_retries)
        for attempt in range(1, max_attempts + 1):
            job.attempts = attempt
            job.status = "running"
            job.updated_at = time.time()
            start = time.perf_counter()
            try:
                await asyncio.to_thread(self._run_job, job)
                metrics_registry.observe_latency(f"{job.job_type.value}_latency", time.perf_counter() - start)
                job.status = "completed"
                job.error = None
                job.updated_at = time.time()
                metrics_registry.increment(f"{job.job_type.value}_success_count")
                return
            except Exception as exc:
                job.error = str(exc)
                job.status = "retrying" if attempt < max_attempts else "failed"
                job.updated_at = time.time()
                metrics_registry.increment(f"{job.job_type.value}_failure_count")
                logger.exception(
                    "background_job_failed",
                    extra={"job_id": job.job_id, "job_type": job.job_type.value},
                )
                if attempt < max_attempts:
                    await asyncio.sleep(min(30, 2 ** (attempt - 1)))

    def _run_job(self, job: JobStatus) -> None:
        with SessionLocal() as db:
            if job.job_type == JobType.INGESTION_SYNC:
                client = OpenNMSClient(self.settings)
                result = OpenNMSIngestionService(db, client).sync_all()
                stored = sum(item.stored_count for item in result.resources.values())
                failures = sum(1 for item in result.resources.values() if not item.success)
                metrics_registry.increment("alerts_ingested_count", result.resources["alarms"].stored_count)
                metrics_registry.increment("ingestion_records_stored_count", stored)
                metrics_registry.set_gauge("ingestion_failure_rate", failures / max(1, len(result.resources)))
                app_cache.invalidate_prefix("alerts:")
                app_cache.invalidate_prefix("recommendation:")
                return

            if job.job_type == JobType.AI_PROCESSING:
                result = AlertProcessorService(db, self.settings).process_pending_critical_alerts(
                    limit=self.settings.ai_processing_batch_size
                )
                metrics_registry.increment("ai_recommendations_generated_count", result.processed_count)
                metrics_registry.increment("ai_recommendation_error_count", result.error_count)
                app_cache.invalidate_prefix("recommendation:")
                return

            raise ValueError(f"unsupported job type: {job.job_type}")


_manager: BackgroundJobManager | None = None


def get_background_job_manager(settings: Settings) -> BackgroundJobManager:
    global _manager
    if _manager is None:
        _manager = BackgroundJobManager(settings)
    return _manager


def reset_background_job_manager() -> None:
    global _manager
    _manager = None
