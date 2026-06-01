import json
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256

from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertHistory
from app.models.event import Event
from app.models.node import Node
from app.repositories.context_repository import AlertContextRepository
from app.services.sanitization import sanitize_for_llm


@dataclass(frozen=True)
class AlertContext:
    alert_id: int
    context: dict
    serialized: str
    sanitized_text: str
    sanitized_context: dict
    context_hash: str
    truncated: bool


class AlertContextBuilder:
    def __init__(self, db: Session, max_chars: int) -> None:
        self.repository = AlertContextRepository(db)
        self.max_chars = max_chars

    def build(self, alert_id: int) -> AlertContext:
        alert = self.repository.get_alert_with_node(alert_id)
        if alert is None:
            raise ValueError(f"alert not found: {alert_id}")

        recent_events = self.repository.list_recent_events_for_node(alert.node_id)
        history = self.repository.list_recent_alert_history(alert.id)
        context = {
            "alert": _alert_to_context(alert),
            "node": _node_to_context(alert.node),
            "recent_events": [_event_to_context(event) for event in recent_events],
            "recent_alert_history": [_history_to_context(item) for item in history],
            "ai_policy": {
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
        context_hash = sha256(sanitized.text.encode("utf-8")).hexdigest()
        return AlertContext(
            alert_id=alert.id,
            context=context,
            serialized=serialized,
            sanitized_text=sanitized.text,
            sanitized_context={
                "sanitized_json": sanitized.text,
                "truncated": sanitized.truncated,
            },
            context_hash=context_hash,
            truncated=sanitized.truncated,
        )


def _alert_to_context(alert: Alert) -> dict:
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
        "acknowledged": bool(alert.acknowledged_by or alert.acknowledged_at),
    }


def _node_to_context(node: Node | None) -> dict | None:
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


def _event_to_context(event: Event) -> dict:
    return {
        "id": event.id,
        "opennms_event_id": event.opennms_event_id,
        "uei": event.uei,
        "severity": event.severity,
        "log_message": event.log_message,
        "description": event.description,
        "event_time": event.event_time,
    }


def _history_to_context(history: AlertHistory) -> dict:
    return {
        "from_status": history.from_status,
        "to_status": history.to_status,
        "changed_by": history.changed_by,
        "note": history.note,
        "created_at": history.created_at,
    }


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)
