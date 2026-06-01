OpenNMS AI Monitoring MCP
=========================

Backend foundation for the OpenNMS AI Monitoring Minimum Credible Product.

Authoritative implementation prompts live under `prompt/`.

Phase 1 scope currently includes:

- FastAPI application setup
- PostgreSQL-ready SQLAlchemy configuration
- Alembic migration baseline
- Required persistence models:
  - nodes
  - alerts
  - alert_history
  - feedback
  - chat_messages
  - llm_responses
  - audit_logs
- LDAP authentication service scaffold with an explicit Phase 1 stub mode
- RBAC role constants and dependency helpers
- LLM sanitization utility
- Node label parser for `{operator}-{circle}-{ip}-{server_type}`


Phase 2 scope currently includes:

- OpenNMS XML REST connector with Basic Auth, retry, timeout, and XML accept handling
- XML parser that preserves raw XML and converts payloads into structured dictionaries
- Normalizers for nodes, alarms, events, and outages
- Idempotent UPSERT repositories for events and outages in addition to Phase 1 nodes/alerts
- Ingestion service for fetch -> parse -> normalize -> UPSERT -> audit logging
- Alert lifecycle history creation when ingested alarm status changes

OpenNMS credentials are read from environment-backed settings only:

- `OPENNMS_BASE_URL`
- `OPENNMS_USERNAME`
- `OPENNMS_PASSWORD`
- `OPENNMS_TIMEOUT_SECONDS`
- `OPENNMS_MAX_RETRIES`
- `OPENNMS_BACKOFF_FACTOR`


Phase 3 scope currently includes:

- Critical-only alert processor for AI recommendation generation
- Context builder for alert, node, recent events, and alert history
- Mandatory sanitization before any LLM provider call
- Provider abstraction for mock, Ollama, OpenAI, and Anthropic
- Advisory-only recommendation engine with structured outputs
- `ai_recommendations` persistence with one recommendation per alert
- Audit logging for AI recommendation generation

LLM provider settings are environment-backed:

- `LLM_PROVIDER` (`mock`, `ollama`, `openai`, or `anthropic`)
- `LLM_MODEL_NAME`
- `OLLAMA_BASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `ANTHROPIC_API_KEY`
- `ANTHROPIC_BASE_URL`
- `LLM_TIMEOUT_SECONDS`
- `LLM_MAX_INPUT_CHARS`


Phase 4 scope currently includes:

- Idempotent operator feedback submission linked to alerts and AI recommendations
- Resolution outcome tracking (`Resolved` / `Not Resolved`) and usefulness tracking (`Helpful` / `Not Helpful`)
- Structured incident learning store for future RAG, fine-tuning candidate review, and recommendation quality analysis
- Lightweight advisory chat service with incident context retrieval
- Chat context retrieval for node history, similar alerts, prior AI recommendations, and feedback history
- Mandatory sanitization for chat inputs, retrieved context, and assistant responses
- Service-level RBAC checks for feedback and chat operator actions

Phase 4 does not perform model training. It only stores structured learning signals for future improvement workflows.

Run tests:

```bash
python3 -m pytest
```
