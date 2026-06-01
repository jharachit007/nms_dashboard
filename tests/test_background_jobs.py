import pytest

from app.core.config import Settings
from app.services.background_jobs import BackgroundJobManager, JobType


@pytest.mark.anyio
async def test_background_job_manager_enqueue_rate_limits_by_type() -> None:
    manager = BackgroundJobManager(
        Settings(
            ingestion_queue_max_size=5,
            ingestion_job_rate_limit_seconds=60,
            ingestion_worker_enabled=False,
        )
    )

    first = await manager.enqueue(JobType.INGESTION_SYNC)

    assert first.job_type == JobType.INGESTION_SYNC
    with pytest.raises(ValueError):
        await manager.enqueue(JobType.INGESTION_SYNC)

    second = await manager.enqueue(JobType.AI_PROCESSING)
    assert second.job_type == JobType.AI_PROCESSING
    assert manager.snapshot()["queue_depth"] == 2
