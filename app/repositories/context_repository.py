from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.alert import Alert, AlertHistory
from app.models.event import Event
from app.repositories.base import BaseRepository


class AlertContextRepository(BaseRepository[Alert]):
    model = Alert

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_alert_with_node(self, alert_id: int) -> Alert | None:
        statement = (
            select(Alert)
            .options(selectinload(Alert.node))
            .where(Alert.id == alert_id)
        )
        return self.db.scalar(statement)

    def list_recent_events_for_node(self, node_id: int | None, limit: int = 10) -> list[Event]:
        if node_id is None:
            return []
        statement = (
            select(Event)
            .where(Event.node_id == node_id)
            .order_by(desc(Event.event_time).nullslast(), desc(Event.id))
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def list_recent_alert_history(self, alert_id: int, limit: int = 10) -> list[AlertHistory]:
        statement = (
            select(AlertHistory)
            .where(AlertHistory.alert_id == alert_id)
            .order_by(desc(AlertHistory.created_at), desc(AlertHistory.id))
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())
