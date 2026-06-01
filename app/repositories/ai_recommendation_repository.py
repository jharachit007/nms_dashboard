from sqlalchemy import exists, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.ai_recommendation import AIRecommendation
from app.repositories.base import BaseRepository


class AIRecommendationRepository(BaseRepository[AIRecommendation]):
    model = AIRecommendation

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def exists_for_alert(self, alert_id: int) -> bool:
        statement = select(exists().where(AIRecommendation.alert_id == alert_id))
        return bool(self.db.scalar(statement))

    def get_by_alert_id(self, alert_id: int) -> AIRecommendation | None:
        return self.db.scalar(select(AIRecommendation).where(AIRecommendation.alert_id == alert_id))

    def create_once_for_alert(self, values: dict) -> AIRecommendation | None:
        statement = (
            insert(AIRecommendation)
            .values(**values)
            .on_conflict_do_nothing(index_elements=[AIRecommendation.alert_id])
            .returning(AIRecommendation)
        )
        return self.db.execute(statement).scalar_one_or_none()
