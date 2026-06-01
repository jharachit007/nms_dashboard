import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.constants import AlertSeverity
from app.models.alert import Alert
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.repositories.alert_repository import AlertRepository
from app.services.ai_provider import AIProvider, build_ai_provider
from app.services.alert_context_builder import AlertContextBuilder
from app.services.audit_service import AuditService
from app.services.recommendation_engine import RecommendationEngine, build_recommendation_prompt

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AlertProcessingResult:
    scanned_count: int
    processed_count: int
    skipped_count: int
    error_count: int
    processed_alert_ids: list[int]
    errors: list[str]


class AlertProcessorService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        provider: AIProvider | None = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.alert_repository = AlertRepository(db)
        self.recommendation_repository = AIRecommendationRepository(db)
        self.context_builder = AlertContextBuilder(db, settings.llm_max_input_chars)
        self.provider = provider or build_ai_provider(settings)
        self.recommendation_engine = RecommendationEngine(self.provider)
        self.audit_service = AuditService(db)

    def process_pending_critical_alerts(self, limit: int = 50) -> AlertProcessingResult:
        alerts = self.alert_repository.list_unprocessed_critical(limit=limit)
        processed_alert_ids: list[int] = []
        errors: list[str] = []
        skipped_count = 0

        for alert in alerts:
            try:
                if not self._is_critical(alert):
                    skipped_count += 1
                    continue
                if self.recommendation_repository.exists_for_alert(alert.id):
                    skipped_count += 1
                    continue
                self._process_alert(alert)
                processed_alert_ids.append(alert.id)
            except Exception as exc:
                self.db.rollback()
                logger.exception("AI recommendation generation failed for alert_id=%s", alert.id)
                errors.append(f"alert_id={alert.id}: {exc}")
                self._record_audit(alert.id, success=False, error=str(exc))
                self.db.commit()

        return AlertProcessingResult(
            scanned_count=len(alerts),
            processed_count=len(processed_alert_ids),
            skipped_count=skipped_count,
            error_count=len(errors),
            processed_alert_ids=processed_alert_ids,
            errors=errors,
        )

    def process_alert(self, alert_id: int):
        alert = self.alert_repository.get(alert_id)
        if alert is None:
            raise ValueError(f"alert not found: {alert_id}")
        if not self._is_critical(alert):
            raise ValueError("AI processing is allowed only for CRITICAL alerts")
        if self.recommendation_repository.exists_for_alert(alert.id):
            return self.recommendation_repository.get_by_alert_id(alert.id)
        return self._process_alert(alert)

    def _process_alert(self, alert: Alert):
        context = self.context_builder.build(alert.id)
        prompt = build_recommendation_prompt(context.sanitized_text)
        response = self.recommendation_engine.generate(context)
        recommendation = self.recommendation_repository.create_once_for_alert(
            {
                "alert_id": alert.id,
                "input_context_hash": context.context_hash,
                "provider": response.provider,
                "model_name": response.model_name,
                "prompt_sanitized": prompt,
                "sanitized_context": context.sanitized_context,
                "recommendation": response.recommendation,
                "response_text": response.response_text,
                "confidence_score": response.confidence_score,
                "advisory_only": True,
            }
        )
        if recommendation is None:
            return self.recommendation_repository.get_by_alert_id(alert.id)

        self._record_audit(
            alert.id,
            success=True,
            provider=response.provider,
            context_hash=context.context_hash,
        )
        self.db.commit()
        return recommendation

    def _is_critical(self, alert: Alert) -> bool:
        return alert.severity == AlertSeverity.CRITICAL.value

    def _record_audit(
        self,
        alert_id: int,
        success: bool,
        provider: str | None = None,
        context_hash: str | None = None,
        error: str | None = None,
    ) -> None:
        details = {
            "success": success,
            "provider": provider,
            "context_hash": context_hash,
            "error": error,
        }
        self.audit_service.record(
            action="ai_recommendation_generation",
            user_id="system",
            resource_type="alert",
            resource_id=str(alert_id),
            details=details,
        )
