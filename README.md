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


Phase 5 scope currently includes:

- Minimal vanilla HTML/CSS/JavaScript NOC operator UI served from `/ui`
- LDAP-backed login flow using a browser session token
- Critical alert list with operator/circle/server type filters and 20-second auto-refresh
- Alert detail view with timeline, AI recommendation, feedback, and chat panels
- Role-aware UI rendering for viewer vs operator/admin actions
- Minimal UI API routes for alerts, AI recommendations, feedback, and chat


Phase 6 scope currently includes:

- Background job queue for non-blocking OpenNMS ingestion and AI processing
- Retry with exponential backoff and simple job rate limiting
- Lightweight in-memory TTL cache for active alerts and AI recommendations
- Admin operations endpoints for metrics and queue status/enqueue actions
- JSON structured logging with request IDs and API latency metrics
- Performance indexes for alert timestamp/severity queries and operator/circle/server filters
- Centralized production settings for cache TTLs, ingestion intervals, queue limits, and AI batch size

Operational endpoints:

- `GET /api/v1/metrics`
- `GET /api/v1/ops/jobs`
- `POST /api/v1/ops/ingestion/enqueue`
- `POST /api/v1/ops/ai/enqueue`


pgvector + Redis integration scope currently includes:

- `pgvector` extension migration and `incident_embeddings` semantic memory table
- Sanitized deterministic embedding generation for alerts and incident context
- Redis-backed hot cache layered under the in-memory TTL cache
- Redis list integration for `embedding_queue` and `ai_processing_queue` with safe fallback
- Async embedding worker path integrated into the existing background job manager
- Similar incident search API at `/api/v1/search/similar-incidents`
- AI recommendation cache/enrichment hook that falls back to normal context if Redis or pgvector is unavailable

Run tests:

```bash
python3 -m pytest
```
