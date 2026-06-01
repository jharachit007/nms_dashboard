from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, record_id: int) -> ModelT | None:
        return self.db.get(self.model, record_id)

    def add(self, instance: ModelT) -> ModelT:
        self.db.add(instance)
        return instance
