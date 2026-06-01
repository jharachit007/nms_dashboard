from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_current_user, get_db, require_role
from app.core.config import Settings, get_settings
from app.core.constants import AlertSeverity, FeedbackType, ResolutionStatus, UserRole
from app.models.ai_recommendation import AIRecommendation
from app.models.alert import Alert, AlertHistory
from app.models.chat import ChatMessage
from app.models.feedback import Feedback
from app.services.auth_service import AuthenticatedUser
from app.services.chat_service import ChatRequest, ChatService
from app.services.feedback_service import FeedbackService, FeedbackSubmission
from app.services.sanitization import sanitize_for_llm

router = APIRouter()


class FeedbackRequest(BaseModel):
    alert_id: int
    ai_recommendation_id: int
    feedback_type: FeedbackType
    resolution_status: ResolutionStatus
    resolution_time: datetime | None = None
    comments: str | None = None


class ChatRequestPayload(BaseModel):
    alert_id: int
    question: str = Field(min_length=1, max_length=4_000)
    session_id: int | None = None


@router.get("/alerts")
def list_alerts(
    severity: str = Query(default=AlertSeverity.CRITICAL.value),
    operator: str | None = None,
    circle: str | None = None,
    server_type: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    normalized_severity = severity.upper()
    statement = (
        select(Alert)
        .options(selectinload(Alert.node))
        .join(Alert.node, isouter=True)
        .where(Alert.severity == normalized_severity)
        .order_by(Alert.last_event_time.desc().nullslast(), Alert.id.desc())
        .offset(offset)
        .limit(limit)
    )
    if operator:
        statement = statement.where(Alert.node.has(operator=operator))
    if circle:
        statement = statement.where(Alert.node.has(circle=circle))
    if server_type:
        statement = statement.where(Alert.node.has(server_type=server_type))

    alerts = db.scalars(statement).all()
    return {
        "items": [_alert_summary(alert) for alert in alerts],
        "limit": limit,
        "offset": offset,
        "roles": [role.value for role in user.roles],
    }


@router.get("/alerts/{alert_id}")
def get_alert_detail(
    alert_id: int,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    alert = db.scalar(
        select(Alert)
        .options(selectinload(Alert.node), selectinload(Alert.ai_recommendation))
        .where(Alert.id == alert_id)
    )
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="alert not found")

    history = db.scalars(
        select(AlertHistory)
        .where(AlertHistory.alert_id == alert_id)
        .order_by(AlertHistory.created_at.desc(), AlertHistory.id.desc())
        .limit(20)
    ).all()
    return {
        "alert": _alert_detail(alert),
        "timeline": [_history_item(item) for item in history],
        "roles": [role.value for role in user.roles],
    }


@router.get("/ai/recommendation/{alert_id}")
def get_ai_recommendation(
    alert_id: int,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    recommendation = db.scalar(select(AIRecommendation).where(AIRecommendation.alert_id == alert_id))
    if recommendation is None:
        return {"recommendation": None, "roles": [role.value for role in user.roles]}
    return {
        "recommendation": _recommendation(recommendation),
        "roles": [role.value for role in user.roles],
    }


@router.get("/feedback/{alert_id}")
def list_feedback(
    alert_id: int,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    feedback = db.scalars(
        select(Feedback)
        .where(Feedback.alert_id == alert_id)
        .order_by(Feedback.created_at.desc(), Feedback.id.desc())
        .limit(20)
    ).all()
    return {
        "items": [_feedback(item) for item in feedback],
        "roles": [role.value for role in user.roles],
    }


@router.post("/feedback")
def submit_feedback(
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role(UserRole.NOC_OPERATOR)),
) -> dict:
    feedback = FeedbackService(db).submit_feedback(
        FeedbackSubmission(
            alert_id=payload.alert_id,
            ai_recommendation_id=payload.ai_recommendation_id,
            user_id=user.username,
            user_roles=tuple(user.roles),
            feedback_type=payload.feedback_type,
            resolution_status=payload.resolution_status,
            resolution_time=payload.resolution_time,
            comments=payload.comments,
        )
    )
    return {"feedback": _feedback(feedback)}


@router.get("/chat/{alert_id}")
def list_chat_messages(
    alert_id: int,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.alert_id == alert_id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        .limit(100)
    ).all()
    return {
        "items": [_chat_message(message) for message in messages],
        "roles": [role.value for role in user.roles],
    }


@router.post("/chat")
def ask_chat(
    payload: ChatRequestPayload,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: AuthenticatedUser = Depends(require_role(UserRole.NOC_OPERATOR)),
) -> dict:
    sanitized_question = sanitize_for_llm(payload.question, settings.llm_max_input_chars)
    response = ChatService(db, settings).ask(
        ChatRequest(
            alert_id=payload.alert_id,
            user_id=user.username,
            question=sanitized_question.text,
            user_roles=tuple(user.roles),
            session_id=payload.session_id,
        )
    )
    return {
        "session_id": response.session_id,
        "response_text": response.response_text,
        "provider": response.provider,
        "advisory_only": response.advisory_only,
    }


def _alert_summary(alert: Alert) -> dict:
    node = alert.node
    return {
        "id": alert.id,
        "node_name": node.raw_label if node else "Unknown node",
        "severity": alert.severity,
        "timestamp": _iso(alert.last_event_time or alert.first_event_time or alert.created_at),
        "status": alert.lifecycle_status,
        "operator": node.operator if node else None,
        "circle": node.circle if node else None,
        "server_type": node.server_type if node else None,
    }


def _alert_detail(alert: Alert) -> dict:
    node = alert.node
    return {
        "id": alert.id,
        "opennms_alarm_id": alert.opennms_alarm_id,
        "severity": alert.severity,
        "status": alert.lifecycle_status,
        "uei": alert.uei,
        "summary": alert.log_message or alert.description or "No alert summary available.",
        "description": alert.description,
        "first_event_time": _iso(alert.first_event_time),
        "last_event_time": _iso(alert.last_event_time),
        "node": {
            "name": node.raw_label,
            "operator": node.operator,
            "circle": node.circle,
            "server_type": node.server_type,
            "ip_address": node.ip_address,
        }
        if node
        else None,
    }


def _recommendation(recommendation: AIRecommendation) -> dict:
    return {
        "id": recommendation.id,
        "alert_id": recommendation.alert_id,
        "provider": recommendation.provider,
        "model_name": recommendation.model_name,
        "recommendation": recommendation.recommendation,
        "confidence_score": recommendation.confidence_score,
        "created_at": _iso(recommendation.created_at),
        "advisory_only": recommendation.advisory_only,
    }


def _feedback(feedback: Feedback) -> dict:
    return {
        "id": feedback.id,
        "alert_id": feedback.alert_id,
        "ai_recommendation_id": feedback.ai_recommendation_id,
        "user_id": feedback.user_id,
        "feedback_type": feedback.feedback_type,
        "resolution_status": feedback.resolution_status,
        "resolution_time": _iso(feedback.resolution_time),
        "comments": feedback.comments,
        "created_at": _iso(feedback.created_at),
    }


def _history_item(history: AlertHistory) -> dict:
    return {
        "from_status": history.from_status,
        "to_status": history.to_status,
        "changed_by": history.changed_by,
        "note": history.note,
        "created_at": _iso(history.created_at),
    }


def _chat_message(message: ChatMessage) -> dict:
    return {
        "id": message.id,
        "session_id": message.session_id,
        "role": message.role,
        "message": message.sanitized_message or message.message,
        "provider": message.provider,
        "created_at": _iso(message.created_at),
        "advisory_only": message.advisory_only,
    }


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
