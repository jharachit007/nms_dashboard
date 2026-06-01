from types import SimpleNamespace

from app.core.config import Settings
from app.repositories.incident_embedding_repository import vector_literal
from app.services.embedding_service import EmbeddingService


def test_vector_literal_formats_pgvector_input() -> None:
    assert vector_literal([0.1, 0.25]) == "[0.10000000,0.25000000]"


def test_embedding_service_sanitizes_content_and_generates_configured_dimension() -> None:
    service = EmbeddingService.__new__(EmbeddingService)
    service.settings = Settings(embedding_dimension=8)

    embedding = service.generate_embedding("host 10.20.30.40 owner noc@example.com token=abc")

    assert len(embedding) == 8
    assert any(value for value in embedding)


def test_embedding_content_does_not_include_sensitive_node_ip() -> None:
    service = EmbeddingService.__new__(EmbeddingService)
    service.settings = Settings(embedding_dimension=8, llm_max_input_chars=10_000)
    alert = SimpleNamespace(
        id=1,
        severity="CRITICAL",
        lifecycle_status="ACTIVE",
        uei="uei.test",
        log_message="host 10.20.30.40 token=abc",
        description=None,
        node=SimpleNamespace(
            raw_label="airtel-delhi-10.20.30.40-web",
            operator="airtel",
            circle="delhi",
            server_type="web",
        ),
    )

    content = service.build_content_for_alert(alert)

    assert "10.20.30.40" not in content
    assert "abc" not in content
    assert "[IP]" in content
    assert "[REDACTED]" in content
