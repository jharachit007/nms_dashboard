import logging

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.repositories.incident_embedding_repository import IncidentEmbeddingRepository
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class SemanticSearchService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.embedding_service = EmbeddingService(db, settings)
        self.embedding_repository = IncidentEmbeddingRepository(db)

    def search_by_text(self, query: str, limit: int = 5) -> list[dict]:
        embedding = self.embedding_service.generate_embedding(query)
        return self._safe_search(embedding, limit)

    def search_by_alert(self, alert_id: int, limit: int = 5) -> list[dict]:
        alert = self.embedding_service.alert_repository.get(alert_id)
        if alert is None:
            raise ValueError(f"alert not found: {alert_id}")
        content = self.embedding_service.build_content_for_alert(alert)
        embedding = self.embedding_service.generate_embedding(content)
        return self._safe_search(embedding, limit)

    def _safe_search(self, embedding: list[float], limit: int) -> list[dict]:
        try:
            return self.embedding_repository.search_similar(embedding, limit=limit)
        except Exception:
            logger.exception("semantic_search_failed")
            return []
