from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.repositories.base import BaseRepository


class FeedbackRepository(BaseRepository[Feedback]):
    model = Feedback

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_for_recommendation(self, alert_id: int, ai_recommendation_id: int, user_id: str) -> Feedback | None:
        statement = select(Feedback).where(
            Feedback.alert_id == alert_id,
            Feedback.ai_recommendation_id == ai_recommendation_id,
            Feedback.user_id == user_id,
        )
        return self.db.scalar(statement)

    def list_by_alert(self, alert_id: int) -> list[Feedback]:
        statement = (
            select(Feedback)
            .where(Feedback.alert_id == alert_id)
            .order_by(Feedback.created_at.desc(), Feedback.id.desc())
        )
        return list(self.db.scalars(statement).all())

    def upsert_for_recommendation(self, values: dict) -> Feedback:
        update_values = {
            key: value
            for key, value in values.items()
            if key not in {"id", "alert_id", "ai_recommendation_id", "user_id", "created_at"}
        }
        statement = (
            insert(Feedback)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[
                    Feedback.alert_id,
                    Feedback.ai_recommendation_id,
                    Feedback.user_id,
                ],
                set_=update_values,
            )
            .returning(Feedback)
        )
        return self.db.execute(statement).scalar_one()
