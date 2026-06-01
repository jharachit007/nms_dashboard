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

Run tests:

```bash
python3 -m pytest
```
