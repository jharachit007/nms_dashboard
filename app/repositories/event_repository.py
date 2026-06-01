from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.event import Event
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    model = Event

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def upsert_by_opennms_event_id(self, values: dict) -> Event:
        update_values = {
            key: value
            for key, value in values.items()
            if key not in {"id", "opennms_event_id", "created_at"}
        }
        statement = (
            insert(Event)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[Event.opennms_event_id],
                set_=update_values,
            )
            .returning(Event)
        )
        return self.db.execute(statement).scalar_one()
