from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.node import Node
from app.repositories.base import BaseRepository


class NodeRepository(BaseRepository[Node]):
    model = Node

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_opennms_id(self, opennms_id: str) -> Node | None:
        return self.db.scalar(select(Node).where(Node.opennms_id == opennms_id))

    def upsert_by_opennms_id(self, values: dict) -> Node:
        update_values = {
            key: value
            for key, value in values.items()
            if key not in {"id", "opennms_id", "created_at"}
        }
        statement = (
            insert(Node)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[Node.opennms_id],
                set_=update_values,
            )
            .returning(Node)
        )
        return self.db.execute(statement).scalar_one()
