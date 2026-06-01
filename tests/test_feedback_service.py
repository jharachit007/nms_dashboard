from types import SimpleNamespace

from app.core.constants import FeedbackType, ResolutionStatus, UserRole
from app.services.feedback_service import FeedbackService, FeedbackSubmission
from app.services.rbac import AuthorizationError


class FakeDB:
    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


class FakeAlertRepository:
    def get(self, alert_id: int):
        return SimpleNamespace(id=alert_id, opennms_alarm_id="100")


class FakeRecommendationRepository:
    def get_by_alert_id(self, alert_id: int):
        return SimpleNamespace(id=50, alert_id=alert_id, recommendation={"summary": "Check node"})


class FakeFeedbackRepository:
    def __init__(self) -> None:
        self.values = []

    def upsert_for_recommendation(self, values: dict):
        self.values.append(values)
        return SimpleNamespace(id=70, **values)


class FakeLearningBuilder:
    def __init__(self) -> None:
        self.calls = []

    def upsert_from_feedback(self, alert, recommendation, feedback):
        self.calls.append((alert, recommendation, feedback))
        return SimpleNamespace(id=90)


class FakeAuditService:
    def __init__(self) -> None:
        self.entries = []

    def record(self, **kwargs) -> None:
        self.entries.append(kwargs)


def _service() -> FeedbackService:
    service = FeedbackService.__new__(FeedbackService)
    service.db = FakeDB()
    service.alert_repository = FakeAlertRepository()
    service.recommendation_repository = FakeRecommendationRepository()
    service.feedback_repository = FakeFeedbackRepository()
    service.learning_builder = FakeLearningBuilder()
    service.audit_service = FakeAuditService()
    return service


def test_feedback_service_upserts_feedback_and_learning_signal() -> None:
    service = _service()
    submission = FeedbackSubmission(
        alert_id=1,
        ai_recommendation_id=50,
        user_id="noc-user",
        user_roles=(UserRole.NOC_OPERATOR,),
        feedback_type=FeedbackType.HELPFUL,
        resolution_status=ResolutionStatus.RESOLVED,
        comments="helpful",
    )

    feedback = service.submit_feedback(submission)
    service.submit_feedback(submission)

    assert feedback.helpful is True
    assert feedback.resolved is True
    assert len(service.feedback_repository.values) == 2
    assert len(service.learning_builder.calls) == 2
    assert service.audit_service.entries[0]["action"] == "feedback_submission"
    assert service.db.commits == 2


def test_feedback_service_rejects_viewer_role() -> None:
    service = _service()
    submission = FeedbackSubmission(
        alert_id=1,
        ai_recommendation_id=50,
        user_id="viewer",
        user_roles=(UserRole.NOC_VIEWER,),
        feedback_type=FeedbackType.NOT_HELPFUL,
        resolution_status=ResolutionStatus.NOT_RESOLVED,
    )

    try:
        service.submit_feedback(submission)
    except AuthorizationError:
        pass
    else:
        raise AssertionError("viewer feedback submission should be rejected")
