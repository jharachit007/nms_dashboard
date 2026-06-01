import json
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.ai_recommendation import AIRecommendation
from app.models.alert import Alert
from app.models.event import Event
from app.models.feedback import Feedback
from app.repositories.chat_context_repository import ChatContextRepository
from app.services.sanitization import sanitize_for_llm


@dataclass(frozen=True)
class RetrievedChatContext:
    alert_id: int
    context: dict
    sanitized_text: str
    sanitized_context: dict
    truncated: bool


class ChatContextRetrievalEngine:
    def __init__(self, db: Session, max_chars: int) -> None:
        self.repository = ChatContextRepository(db)
        self.max_chars = max_chars

    def retrieve(self, alert_id: int, user_question: str) -> RetrievedChatContext:
        alert = self.repository.get_alert_with_context(alert_id)
        if alert is None:
            raise ValueError(f"alert not found: {alert_id}")

        context = {
            "user_question": user_question,
            "alert": _alert_context(alert),
            "node": _node_context(alert),
            "current_ai_recommendation": _recommendation_context(alert.ai_recommendation),
            "node_history": [_event_context(event) for event in self.repository.list_node_events(alert.node_id)],
            "similar_incidents": [
                _similar_alert_context(similar_alert)
                for similar_alert in self.repository.list_similar_alerts(alert)
            ],
            "previous_ai_recommendations": [
                _recommendation_context(recommendation)
                for recommendation in self.repository.list_previous_recommendations(alert)
            ],
            "feedback_history": [
                _feedback_context(feedback)
                for feedback in self.repository.list_feedback(alert.id)
            ],
            "chat_policy": {
                "advisory_only": True,
                "forbidden_actions": [
                    "execute commands",
                    "modify infrastructure",
                    "restart services",
                    "perform remediation",
                ],
            },
        }
        serialized = json.dumps(context, sort_keys=True, default=_json_default)
        sanitized = sanitize_for_llm(serialized, self.max_chars)
        return RetrievedChatContext(
            alert_id=alert.id,
            context=context,
            sanitized_text=sanitized.text,
            sanitized_context={
                "sanitized_json": sanitized.text,
                "truncated": sanitized.truncated,
            },
            truncated=sanitized.truncated,
        )


def _alert_context(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "opennms_alarm_id": alert.opennms_alarm_id,
        "severity": alert.severity,
        "lifecycle_status": alert.lifecycle_status,
        "uei": alert.uei,
        "log_message": alert.log_message,
        "description": alert.description,
        "first_event_time": alert.first_event_time,
        "last_event_time": alert.last_event_time,
    }


def _node_context(alert: Alert) -> dict | None:
    node = alert.node
    if node is None:
        return None
    return {
        "id": node.id,
        "opennms_id": node.opennms_id,
        "raw_label": node.raw_label,
        "operator": node.operator,
        "circle": node.circle,
        "ip_address": node.ip_address,
        "server_type": node.server_type,
    }


def _recommendation_context(recommendation: AIRecommendation | None) -> dict | None:
    if recommendation is None:
        return None
    return {
        "id": recommendation.id,
        "provider": recommendation.provider,
        "model_name": recommendation.model_name,
        "input_context_hash": recommendation.input_context_hash,
        "recommendation": recommendation.recommendation,
        "confidence_score": recommendation.confidence_score,
        "created_at": recommendation.created_at,
    }


def _event_context(event: Event) -> dict:
    return {
        "id": event.id,
        "opennms_event_id": event.opennms_event_id,
        "uei": event.uei,
        "severity": event.severity,
        "log_message": event.log_message,
        "description": event.description,
        "event_time": event.event_time,
    }


def _similar_alert_context(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "opennms_alarm_id": alert.opennms_alarm_id,
        "severity": alert.severity,
        "lifecycle_status": alert.lifecycle_status,
        "uei": alert.uei,
        "first_event_time": alert.first_event_time,
        "last_event_time": alert.last_event_time,
    }


def _feedback_context(feedback: Feedback) -> dict:
    return {
        "id": feedback.id,
        "feedback_type": feedback.feedback_type,
        "resolution_status": feedback.resolution_status,
        "resolution_time": feedback.resolution_time,
        "comments": feedback.comments,
        "created_at": feedback.created_at,
    }


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)
