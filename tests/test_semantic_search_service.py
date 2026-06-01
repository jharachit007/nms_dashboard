from app.core.config import Settings
from app.services.semantic_search_service import SemanticSearchService


class FakeEmbeddingService:
    def generate_embedding(self, text: str) -> list[float]:
        return [1.0, 0.0]


class FailingRepository:
    def search_similar(self, embedding: list[float], limit: int = 5):
        raise RuntimeError("pgvector unavailable")


def test_semantic_search_falls_back_to_empty_results_on_pgvector_failure() -> None:
    service = SemanticSearchService.__new__(SemanticSearchService)
    service.settings = Settings()
    service.embedding_service = FakeEmbeddingService()
    service.embedding_repository = FailingRepository()

    assert service.search_by_text("query", limit=5) == []
