from app.core.constants import AlertSeverity
from app.models.alert import Alert
from app.services.ai_provider import MockAIProvider
from app.services.alert_context_builder import AlertContext
from app.services.alert_processor import AlertProcessorService


class FakeDB:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeAlertRepository:
    def __init__(self) -> None:
        self.critical = Alert(id=1, opennms_alarm_id="1", severity=AlertSeverity.CRITICAL.value, raw_xml="<alarm />")
        self.major = Alert(id=2, opennms_alarm_id="2", severity=AlertSeverity.MAJOR.value, raw_xml="<alarm />")

    def list_unprocessed_critical(self, limit: int = 50) -> list[Alert]:
        return [self.critical, self.major]

    def get(self, alert_id: int) -> Alert | None:
        return self.critical if alert_id == 1 else self.major


class FakeRecommendationRepository:
    def __init__(self) -> None:
        self.created = []
        self.existing_alert_ids = set()

    def exists_for_alert(self, alert_id: int) -> bool:
        return alert_id in self.existing_alert_ids

    def get_by_alert_id(self, alert_id: int):
        return None

    def create_once_for_alert(self, values: dict):
        self.created.append(values)
        self.existing_alert_ids.add(values["alert_id"])
        return values


class FakeContextBuilder:
    def build(self, alert_id: int) -> AlertContext:
        return AlertContext(
            alert_id=alert_id,
            context={},
            serialized="{}",
            sanitized_text='{"alert": {"severity": "CRITICAL", "ip": "[IP]"}}',
            sanitized_context={"sanitized_json": "{}", "truncated": False},
            context_hash="abc123",
            truncated=False,
        )


class FakeAuditService:
    def __init__(self) -> None:
        self.entries = []

    def record(self, **kwargs) -> None:
        self.entries.append(kwargs)


def test_alert_processor_processes_only_critical_and_stores_once() -> None:
    service = AlertProcessorService.__new__(AlertProcessorService)
    service.db = FakeDB()
    service.alert_repository = FakeAlertRepository()
    service.recommendation_repository = FakeRecommendationRepository()
    service.context_builder = FakeContextBuilder()
    service.provider = MockAIProvider()
    from app.services.recommendation_engine import RecommendationEngine

    service.recommendation_engine = RecommendationEngine(service.provider)
    service.audit_service = FakeAuditService()

    result = service.process_pending_critical_alerts()
    second = service.process_pending_critical_alerts()

    assert result.processed_count == 1
    assert result.skipped_count == 1
    assert result.processed_alert_ids == [1]
    assert second.processed_count == 0
    assert second.skipped_count == 2
    assert len(service.recommendation_repository.created) == 1
    stored = service.recommendation_repository.created[0]
    assert stored["alert_id"] == 1
    assert stored["provider"] == "mock"
    assert stored["advisory_only"] is True
    assert service.audit_service.entries[0]["action"] == "ai_recommendation_generation"
