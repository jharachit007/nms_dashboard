from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.config import Settings, get_settings
from app.services.auth_service import AuthenticatedUser
from app.services.semantic_search_service import SemanticSearchService
from app.services.sanitization import sanitize_for_llm

router = APIRouter()


@router.get("/search/similar-incidents")
def similar_incidents(
    alert_id: int | None = None,
    query: str | None = Query(default=None, max_length=4_000),
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    service = SemanticSearchService(db, settings)
    if alert_id is not None:
        results = service.search_by_alert(alert_id, limit=limit)
    elif query:
        sanitized_query = sanitize_for_llm(query, settings.llm_max_input_chars).text
        results = service.search_by_text(sanitized_query, limit=limit)
    else:
        results = []

    return {
        "items": [_serialize_result(item) for item in results],
        "limit": limit,
        "roles": [role.value for role in user.roles],
    }


def _serialize_result(item: dict) -> dict:
    return {
        "id": item.get("id"),
        "alert_id": item.get("alert_id"),
        "node_id": item.get("node_id"),
        "content_text": item.get("content_text"),
        "metadata": item.get("metadata"),
        "distance": float(item["distance"]) if item.get("distance") is not None else None,
        "ai_recommendation": item.get("ai_recommendation"),
        "feedback_type": item.get("feedback_type"),
        "resolution_status": item.get("resolution_status"),
        "created_at": item.get("created_at").isoformat() if item.get("created_at") else None,
    }
