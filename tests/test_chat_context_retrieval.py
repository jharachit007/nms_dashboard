from types import SimpleNamespace

from app.services.chat_context_retrieval import ChatContextRetrievalEngine


class FakeChatContextRepository:
    def get_alert_with_context(self, alert_id: int):
        node = SimpleNamespace(
            id=10,
            opennms_id="42",
            raw_label="airtel-delhi-10.20.30.40-web",
            operator="airtel",
            circle="delhi",
            ip_address="10.20.30.40",
            server_type="web",
        )
        recommendation = SimpleNamespace(
            id=50,
            provider="mock",
            model_name="mcp",
            input_context_hash="hash",
            recommendation={"summary": "Check 10.20.30.40"},
            confidence_score=0.6,
            created_at=None,
        )
        return SimpleNamespace(
            id=alert_id,
            opennms_alarm_id="100",
            severity="CRITICAL",
            lifecycle_status="ACTIVE",
            uei="uei.opennms.org/test",
            log_message="contact noc@example.com password:secret",
            description="node down",
            first_event_time=None,
            last_event_time=None,
            node_id=10,
            node=node,
            ai_recommendation=recommendation,
        )

    def list_node_events(self, node_id: int | None, limit: int = 10) -> list:
        return [
            SimpleNamespace(
                id=200,
                opennms_event_id="200",
                uei="uei.opennms.org/event",
                severity="CRITICAL",
                log_message="event from 10.20.30.41",
                description=None,
                event_time=None,
            )
        ]

    def list_similar_alerts(self, alert, limit: int = 5) -> list:
        return [SimpleNamespace(id=2, opennms_alarm_id="101", severity="CRITICAL", lifecycle_status="CLEARED", uei=alert.uei, first_event_time=None, last_event_time=None)]

    def list_previous_recommendations(self, alert, limit: int = 5) -> list:
        return []

    def list_feedback(self, alert_id: int, limit: int = 10) -> list:
        return [SimpleNamespace(id=70, feedback_type="Helpful", resolution_status="Resolved", resolution_time=None, comments="fixed token=abc", created_at=None)]


def test_chat_context_retrieval_sanitizes_question_and_context() -> None:
    engine = ChatContextRetrievalEngine.__new__(ChatContextRetrievalEngine)
    engine.repository = FakeChatContextRepository()
    engine.max_chars = 20_000

    context = engine.retrieve(1, "What happened to 10.20.30.40?")

    assert "10.20.30.40" not in context.sanitized_text
    assert "10.20.30.41" not in context.sanitized_text
    assert "noc@example.com" not in context.sanitized_text
    assert "secret" not in context.sanitized_text
    assert "abc" not in context.sanitized_text
    assert "[IP]" in context.sanitized_text
    assert "[EMAIL]" in context.sanitized_text
    assert "[REDACTED]" in context.sanitized_text
    assert context.sanitized_context["truncated"] is False
