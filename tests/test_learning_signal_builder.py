from types import SimpleNamespace

from app.services.learning_signal_builder import LearningSignalBuilder


class FakeLearningRepository:
    def __init__(self) -> None:
        self.values = None

    def upsert_by_feedback_id(self, values: dict):
        self.values = values
        return SimpleNamespace(id=900, **values)


def test_learning_signal_builder_sanitizes_feedback_comments_and_marks_no_training() -> None:
    repository = FakeLearningRepository()
    builder = LearningSignalBuilder(repository)
    alert = SimpleNamespace(
        id=1,
        opennms_alarm_id="100",
        severity="CRITICAL",
        lifecycle_status="ACTIVE",
        uei="uei.opennms.org/test",
        node_id=10,
    )
    recommendation = SimpleNamespace(
        id=50,
        provider="mock",
        model_name="mcp",
        input_context_hash="hash",
        confidence_score=0.7,
        recommendation={"summary": "Check node"},
    )
    feedback = SimpleNamespace(
        id=70,
        user_id="operator",
        feedback_type="Helpful",
        resolution_status="Resolved",
        resolution_time=None,
        comments="resolved for host 10.20.30.40 token=abc123",
    )

    signal = builder.upsert_from_feedback(alert, recommendation, feedback)

    payload = repository.values["learning_payload"]
    assert signal.id == 900
    assert payload["training_performed"] is False
    assert "10.20.30.40" not in payload["operator_feedback"]["comments"]
    assert "abc123" not in payload["operator_feedback"]["comments"]
    assert "[IP]" in payload["operator_feedback"]["comments"]
    assert "[REDACTED]" in payload["operator_feedback"]["comments"]
