from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.constants import FeedbackType, ResolutionStatus, UserRole
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.learning_repository import IncidentLearningRepository
from app.services.audit_service import AuditService
from app.services.learning_signal_builder import LearningSignalBuilder
from app.services.rbac import ensure_role


@dataclass(frozen=True)
class FeedbackSubmission:
    alert_id: int
    ai_recommendation_id: int
    user_id: str
    user_roles: tuple[UserRole, ...]
    feedback_type: FeedbackType
    resolution_status: ResolutionStatus
    resolution_time: datetime | None = None
    comments: str | None = None


class FeedbackService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.alert_repository = AlertRepository(db)
        self.recommendation_repository = AIRecommendationRepository(db)
        self.feedback_repository = FeedbackRepository(db)
        self.learning_repository = IncidentLearningRepository(db)
        self.learning_builder = LearningSignalBuilder(self.learning_repository)
        self.audit_service = AuditService(db)

    def submit_feedback(self, submission: FeedbackSubmission):
        ensure_role(submission.user_roles, UserRole.NOC_OPERATOR)

        alert = self.alert_repository.get(submission.alert_id)
        if alert is None:
            raise ValueError(f"alert not found: {submission.alert_id}")

        recommendation = self.recommendation_repository.get_by_alert_id(submission.alert_id)
        if recommendation is None or recommendation.id != submission.ai_recommendation_id:
            raise ValueError("AI recommendation does not belong to alert")

        feedback = self.feedback_repository.upsert_for_recommendation(
            {
                "alert_id": submission.alert_id,
                "ai_recommendation_id": submission.ai_recommendation_id,
                "user_id": submission.user_id,
                "helpful": submission.feedback_type == FeedbackType.HELPFUL,
                "resolved": submission.resolution_status == ResolutionStatus.RESOLVED,
                "feedback_type": submission.feedback_type.value,
                "resolution_status": submission.resolution_status.value,
                "resolution_time": submission.resolution_time,
                "comments": submission.comments,
            }
        )
        learning_signal = self.learning_builder.upsert_from_feedback(alert, recommendation, feedback)
        self.audit_service.record(
            action="feedback_submission",
            user_id=submission.user_id,
            resource_type="alert",
            resource_id=str(submission.alert_id),
            details={
                "ai_recommendation_id": submission.ai_recommendation_id,
                "feedback_id": feedback.id,
                "learning_signal_id": learning_signal.id,
                "feedback_type": submission.feedback_type.value,
                "resolution_status": submission.resolution_status.value,
            },
        )
        self.db.commit()
        return feedback
