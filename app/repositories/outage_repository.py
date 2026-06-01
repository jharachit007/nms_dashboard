from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.outage import Outage
from app.repositories.base import BaseRepository


class OutageRepository(BaseRepository[Outage]):
    model = Outage

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def upsert_by_opennms_outage_id(self, values: dict) -> Outage:
        update_values = {
            key: value
            for key, value in values.items()
            if key not in {"id", "opennms_outage_id", "created_at"}
        }
        statement = (
            insert(Outage)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[Outage.opennms_outage_id],
                set_=update_values,
            )
            .returning(Outage)
        )
        return self.db.execute(statement).scalar_one()
