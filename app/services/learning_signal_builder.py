from app.models.ai_recommendation import AIRecommendation
from app.models.alert import Alert
from app.models.feedback import Feedback
from app.repositories.learning_repository import IncidentLearningRepository
from app.services.sanitization import sanitize_for_llm


class LearningSignalBuilder:
    def __init__(self, repository: IncidentLearningRepository) -> None:
        self.repository = repository

    def upsert_from_feedback(
        self,
        alert: Alert,
        ai_recommendation: AIRecommendation,
        feedback: Feedback,
    ):
        sanitized_comments = sanitize_for_llm(feedback.comments or "", 4_000).text if feedback.comments else None
        payload = {
            "alert": {
                "id": alert.id,
                "opennms_alarm_id": alert.opennms_alarm_id,
                "severity": alert.severity,
                "lifecycle_status": alert.lifecycle_status,
                "uei": alert.uei,
                "node_id": alert.node_id,
            },
            "ai_recommendation": {
                "id": ai_recommendation.id,
                "provider": ai_recommendation.provider,
                "model_name": ai_recommendation.model_name,
                "input_context_hash": ai_recommendation.input_context_hash,
                "confidence_score": ai_recommendation.confidence_score,
                "recommendation": ai_recommendation.recommendation,
            },
            "operator_feedback": {
                "id": feedback.id,
                "user_id": feedback.user_id,
                "feedback_type": feedback.feedback_type,
                "resolution_status": feedback.resolution_status,
                "resolution_time": feedback.resolution_time.isoformat() if feedback.resolution_time else None,
                "comments": sanitized_comments,
            },
            "learning_use": [
                "future_rag_corpus",
                "future_fine_tuning_candidate",
                "recommendation_quality_analysis",
            ],
            "training_performed": False,
        }
        return self.repository.upsert_by_feedback_id(
            {
                "alert_id": alert.id,
                "ai_recommendation_id": ai_recommendation.id,
                "feedback_id": feedback.id,
                "feedback_type": feedback.feedback_type,
                "resolution_status": feedback.resolution_status,
                "learning_payload": payload,
            }
        )
