from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.ai_recommendation import AIRecommendation
from app.models.alert import Alert
from app.models.event import Event
from app.models.feedback import Feedback


class ChatContextRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_alert_with_context(self, alert_id: int) -> Alert | None:
        statement = (
            select(Alert)
            .options(selectinload(Alert.node), selectinload(Alert.ai_recommendation))
            .where(Alert.id == alert_id)
        )
        return self.db.scalar(statement)

    def list_node_events(self, node_id: int | None, limit: int = 10) -> list[Event]:
        if node_id is None:
            return []
        statement = (
            select(Event)
            .where(Event.node_id == node_id)
            .order_by(desc(Event.event_time).nullslast(), desc(Event.id))
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def list_similar_alerts(self, alert: Alert, limit: int = 5) -> list[Alert]:
        conditions = []
        if alert.uei:
            conditions.append(Alert.uei == alert.uei)
        if alert.node_id:
            conditions.append(Alert.node_id == alert.node_id)
        if not conditions:
            return []
        statement = (
            select(Alert)
            .where(Alert.id != alert.id)
            .where(or_(*conditions))
            .order_by(desc(Alert.last_event_time).nullslast(), desc(Alert.id))
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def list_feedback(self, alert_id: int, limit: int = 10) -> list[Feedback]:
        statement = (
            select(Feedback)
            .where(Feedback.alert_id == alert_id)
            .order_by(desc(Feedback.created_at), desc(Feedback.id))
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def list_previous_recommendations(self, alert: Alert, limit: int = 5) -> list[AIRecommendation]:
        if not alert.uei:
            return []
        statement = (
            select(AIRecommendation)
            .join(Alert, Alert.id == AIRecommendation.alert_id)
            .where(Alert.uei == alert.uei)
            .where(Alert.id != alert.id)
            .order_by(desc(AIRecommendation.created_at), desc(AIRecommendation.id))
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())
