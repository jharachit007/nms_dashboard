from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import require_role
from app.core.config import Settings, get_settings
from app.core.constants import UserRole
from app.services.background_jobs import JobType, get_background_job_manager
from app.services.cache import app_cache
from app.services.metrics import metrics_registry

router = APIRouter()


@router.get("/metrics")
def metrics(user=Depends(require_role(UserRole.NOC_ADMIN))) -> dict:
    return {
        "metrics": metrics_registry.snapshot(),
        "cache": app_cache.stats(),
    }


@router.get("/ops/jobs")
def job_status(
    settings: Settings = Depends(get_settings),
    user=Depends(require_role(UserRole.NOC_ADMIN)),
) -> dict:
    return get_background_job_manager(settings).snapshot()


@router.post("/ops/ingestion/enqueue")
async def enqueue_ingestion(
    force: bool = False,
    settings: Settings = Depends(get_settings),
    user=Depends(require_role(UserRole.NOC_ADMIN)),
) -> dict:
    try:
        job = await get_background_job_manager(settings).enqueue(JobType.INGESTION_SYNC, force=force)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    return {"job_id": job.job_id, "job_type": job.job_type.value, "status": job.status}


@router.post("/ops/ai/enqueue")
async def enqueue_ai_processing(
    force: bool = False,
    settings: Settings = Depends(get_settings),
    user=Depends(require_role(UserRole.NOC_ADMIN)),
) -> dict:
    try:
        job = await get_background_job_manager(settings).enqueue(JobType.AI_PROCESSING, force=force)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    return {"job_id": job.job_id, "job_type": job.job_type.value, "status": job.status}
