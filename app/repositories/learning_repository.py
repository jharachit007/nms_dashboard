from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.incident_learning import IncidentLearningStore
from app.repositories.base import BaseRepository


class IncidentLearningRepository(BaseRepository[IncidentLearningStore]):
    model = IncidentLearningStore

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_feedback_id(self, feedback_id: int) -> IncidentLearningStore | None:
        return self.db.scalar(
            select(IncidentLearningStore).where(IncidentLearningStore.feedback_id == feedback_id)
        )

    def upsert_by_feedback_id(self, values: dict) -> IncidentLearningStore:
        update_values = {
            key: value
            for key, value in values.items()
            if key not in {"id", "feedback_id", "created_at"}
        }
        statement = (
            insert(IncidentLearningStore)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[IncidentLearningStore.feedback_id],
                set_=update_values,
            )
            .returning(IncidentLearningStore)
        )
        return self.db.execute(statement).scalar_one()
