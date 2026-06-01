from app.core.constants import AlertLifecycleStatus, AlertSeverity
from app.models.alert import Alert
from app.models.event import Event
from app.models.node import Node
from app.services.alert_context_builder import AlertContextBuilder


class FakeContextRepository:
    def get_alert_with_node(self, alert_id: int) -> Alert:
        node = Node(
            id=10,
            opennms_id="42",
            raw_label="airtel-delhi-10.20.30.40-web",
            operator="airtel",
            circle="delhi",
            ip_address="10.20.30.40",
            server_type="web",
            raw_xml="<node />",
        )
        return Alert(
            id=alert_id,
            opennms_alarm_id="100",
            node_id=10,
            node=node,
            severity=AlertSeverity.CRITICAL.value,
            lifecycle_status=AlertLifecycleStatus.ACTIVE.value,
            uei="uei.opennms.org/test",
            log_message="host 10.20.30.40 owner noc@example.com token=abc123",
            raw_xml="<alarm />",
        )

    def list_recent_events_for_node(self, node_id: int | None, limit: int = 10) -> list[Event]:
        return [
            Event(
                id=200,
                opennms_event_id="200",
                node_id=node_id,
                severity=AlertSeverity.CRITICAL.value,
                log_message="password:secret 10.20.30.41",
                raw_xml="<event />",
            )
        ]

    def list_recent_alert_history(self, alert_id: int, limit: int = 10) -> list:
        return []


def test_alert_context_builder_sanitizes_context_before_ai_use() -> None:
    builder = AlertContextBuilder.__new__(AlertContextBuilder)
    builder.repository = FakeContextRepository()
    builder.max_chars = 10_000

    context = builder.build(alert_id=100)

    assert "10.20.30.40" not in context.sanitized_text
    assert "10.20.30.41" not in context.sanitized_text
    assert "noc@example.com" not in context.sanitized_text
    assert "abc123" not in context.sanitized_text
    assert "secret" not in context.sanitized_text
    assert "[IP]" in context.sanitized_text
    assert "[EMAIL]" in context.sanitized_text
    assert "[REDACTED]" in context.sanitized_text
    assert context.context_hash
    assert context.sanitized_context["truncated"] is False
