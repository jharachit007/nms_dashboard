from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.incident_embedding import IncidentEmbedding
from app.repositories.base import BaseRepository


class IncidentEmbeddingRepository(BaseRepository[IncidentEmbedding]):
    model = IncidentEmbedding

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def upsert_for_alert(self, values: dict) -> IncidentEmbedding:
        insert_values = dict(values)
        insert_values["embedding"] = vector_literal(values["embedding"])
        statement = (
            insert(IncidentEmbedding)
            .values(**insert_values)
            .on_conflict_do_update(
                index_elements=[IncidentEmbedding.alert_id],
                set_={
                    "node_id": values.get("node_id"),
                    "embedding": insert_values["embedding"],
                    "content_text": values["content_text"],
                    "embedding_metadata": values.get("embedding_metadata"),
                },
            )
            .returning(IncidentEmbedding)
        )
        return self.db.execute(statement).scalar_one()

    def list_alert_ids_missing_embeddings(self, limit: int = 10) -> list[int]:
        statement = (
            select(Alert.id)
            .outerjoin(IncidentEmbedding, IncidentEmbedding.alert_id == Alert.id)
            .where(IncidentEmbedding.id.is_(None))
            .order_by(Alert.last_event_time.desc().nullslast(), Alert.id.desc())
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def search_similar(self, embedding: list[float], limit: int = 5) -> list[dict]:
        statement = text(
            """
            SELECT
                ie.id,
                ie.alert_id,
                ie.node_id,
                ie.content_text,
                ie.metadata,
                ie.created_at,
                (ie.embedding <=> :embedding) AS distance,
                ar.recommendation AS ai_recommendation,
                f.feedback_type,
                f.resolution_status
            FROM incident_embeddings ie
            LEFT JOIN ai_recommendations ar ON ar.alert_id = ie.alert_id
            LEFT JOIN feedback f ON f.alert_id = ie.alert_id
            ORDER BY ie.embedding <=> :embedding
            LIMIT :limit
            """
        )
        rows = self.db.execute(
            statement,
            {"embedding": vector_literal(embedding), "limit": limit},
        ).mappings()
        return [dict(row) for row in rows]


def vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"
