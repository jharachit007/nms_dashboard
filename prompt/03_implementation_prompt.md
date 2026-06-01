Implement the MCP backend step-by-step.

Phase 1:
- FastAPI setup
- PostgreSQL connection
- Base models (Node, Alert, Feedback, Chat, Audit)

Phase 2:
- OpenNMS connector (XML parsing)
- Node ingestion
- Alert ingestion (UPSERT logic)

Phase 3:
- AI service layer (mock first, real LLM later)
- Sanitization layer

Phase 4:
- Feedback system
- Chat system

Rules:
- No placeholder logic unless explicitly marked
- Always store raw OpenNMS payloads
- Use service-repository separation
- Ensure each module is independently testable