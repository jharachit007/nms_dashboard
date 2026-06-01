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

Run tests:

```bash
python3 -m pytest
```
