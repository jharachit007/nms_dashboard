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


@lru_cache
def get_settings() -> Settings:
    return Settings()
