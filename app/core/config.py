from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import UserRole


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "OpenNMS AI Monitoring MCP"
    environment: str = "development"
    api_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+psycopg://opennms_mcp@localhost:5432/opennms_mcp",
        description="SQLAlchemy database URL. PostgreSQL is required outside tests.",
    )

    ldap_stub_enabled: bool = Field(
        default=True,
        description="Phase 1 LDAP stub switch. Disable when LDAP settings are ready.",
    )
    ldap_server_url: str | None = None
    ldap_bind_dn_template: str | None = Field(
        default=None,
        description="Template such as uid={username},ou=people,dc=example,dc=com.",
    )
    ldap_user_search_base: str | None = None
    ldap_group_search_base: str | None = None
    ldap_default_role: UserRole = UserRole.NOC_VIEWER

    opennms_base_url: str | None = Field(
        default=None,
        description="Base OpenNMS URL, for example https://opennms.internal/opennms.",
    )
    opennms_username: str | None = None
    opennms_password: str | None = None
    opennms_timeout_seconds: float = 15.0
    opennms_max_retries: int = 3
    opennms_backoff_factor: float = 0.5

    llm_provider: str = "mock"
    llm_model_name: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str | None = None
    anthropic_base_url: str = "https://api.anthropic.com/v1"
    llm_timeout_seconds: float = 30.0

    llm_max_input_chars: int = 12_000

    session_token_secret: str | None = Field(
        default=None,
        description="Optional HMAC secret for browser session tokens. A process-local secret is used if unset.",
    )
    session_token_ttl_seconds: int = 28_800

    cache_alert_ttl_seconds: int = 20
    cache_ai_ttl_seconds: int = 14_400
    cache_node_ttl_seconds: int = 300

    ingestion_interval_seconds: int = 60
    ingestion_queue_max_size: int = 100
    ingestion_worker_enabled: bool = True
    ingestion_job_rate_limit_seconds: int = 10

    ai_processing_interval_seconds: int = 30
    ai_processing_batch_size: int = 25

    request_log_enabled: bool = True

    redis_enabled: bool = True
    redis_url: str = "redis://localhost:6379/0"
    redis_socket_timeout_seconds: float = 0.1
    redis_alert_ttl_seconds: int = 60
    redis_ai_ttl_seconds: int = 14_400
    redis_node_ttl_seconds: int = 1_800
    redis_queue_embedding: str = "embedding_queue"
    redis_queue_ai_processing: str = "ai_processing_queue"

    embedding_dimension: int = 1536
    embedding_worker_enabled: bool = True
    embedding_batch_size: int = 10
    embedding_queue_poll_seconds: float = 2.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
