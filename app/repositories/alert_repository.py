from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.constants import AlertSeverity
from app.models.ai_recommendation import AIRecommendation
from app.models.alert import Alert, AlertHistory
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    model = Alert

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_opennms_alarm_id(self, opennms_alarm_id: str) -> Alert | None:
        return self.db.scalar(select(Alert).where(Alert.opennms_alarm_id == opennms_alarm_id))

    def upsert_by_opennms_alarm_id(self, values: dict) -> Alert:
        update_values = {
            key: value
            for key, value in values.items()
            if key not in {"id", "opennms_alarm_id", "created_at"}
        }
        statement = (
            insert(Alert)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[Alert.opennms_alarm_id],
                set_=update_values,
            )
            .returning(Alert)
        )
        return self.db.execute(statement).scalar_one()

    def list_unprocessed_critical(self, limit: int = 50) -> list[Alert]:
        statement = (
            select(Alert)
            .outerjoin(AIRecommendation, AIRecommendation.alert_id == Alert.id)
            .where(Alert.severity == AlertSeverity.CRITICAL.value)
            .where(AIRecommendation.id.is_(None))
            .order_by(Alert.last_event_time.desc().nullslast(), Alert.id.desc())
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def add_history(self, history: AlertHistory) -> AlertHistory:
        self.db.add(history)
        return history
