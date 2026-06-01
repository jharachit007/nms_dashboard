import hashlib
import json
import math

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.alert import Alert
from app.repositories.alert_repository import AlertRepository
from app.repositories.incident_embedding_repository import IncidentEmbeddingRepository
from app.services.sanitization import sanitize_for_llm


class EmbeddingService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.alert_repository = AlertRepository(db)
        self.embedding_repository = IncidentEmbeddingRepository(db)

    def generate_embedding(self, text: str) -> list[float]:
        sanitized = sanitize_for_llm(text, self.settings.llm_max_input_chars).text
        dimensions = self.settings.embedding_dimension
        vector = [0.0] * dimensions
        for index, token in enumerate(sanitized.lower().split()):
            digest = hashlib.sha256(f"{index}:{token}".encode("utf-8")).digest()
            slot = int.from_bytes(digest[:4], "big") % dimensions
            weight = 1.0 + (digest[4] / 255.0)
            vector[slot] += weight
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def build_content_for_alert(self, alert: Alert) -> str:
        node = alert.node
        payload = {
            "alert": {
                "id": alert.id,
                "severity": alert.severity,
                "status": alert.lifecycle_status,
                "uei": alert.uei,
                "log_message": alert.log_message,
                "description": alert.description,
            },
            "node": {
                "label": node.raw_label,
                "operator": node.operator,
                "circle": node.circle,
                "server_type": node.server_type,
            }
            if node
            else None,
        }
        return sanitize_for_llm(
            json.dumps(payload, sort_keys=True, default=str),
            self.settings.llm_max_input_chars,
        ).text

    def upsert_alert_embedding(self, alert_id: int):
        alert = self.alert_repository.get(alert_id)
        if alert is None:
            raise ValueError(f"alert not found: {alert_id}")
        content = self.build_content_for_alert(alert)
        embedding = self.generate_embedding(content)
        return self.embedding_repository.upsert_for_alert(
            {
                "alert_id": alert.id,
                "node_id": alert.node_id,
                "embedding": embedding,
                "content_text": content,
                "embedding_metadata": {
                    "source": "alert",
                    "severity": alert.severity,
                    "uei": alert.uei,
                    "sanitized": True,
                },
            }
        )


class EmbeddingWorkerService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.embedding_service = EmbeddingService(db, settings)
        self.embedding_repository = IncidentEmbeddingRepository(db)
        self.settings = settings

    def process_pending_embeddings(self, limit: int | None = None) -> int:
        batch_size = limit or self.settings.embedding_batch_size
        alert_ids = self.embedding_repository.list_alert_ids_missing_embeddings(limit=batch_size)
        processed = 0
        for alert_id in alert_ids:
            self.embedding_service.upsert_alert_embedding(alert_id)
            processed += 1
        return processed
