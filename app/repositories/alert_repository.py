from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

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

    def add_history(self, history: AlertHistory) -> AlertHistory:
        self.db.add(history)
        return history
