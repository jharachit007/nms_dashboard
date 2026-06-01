You are working on an OpenNMS AI Monitoring MCP (Minimum Credible Product).

This system integrates with an existing OpenNMS deployment using REST APIs (XML-based responses).

Core goals:
- Ingest OpenNMS alarms, nodes, events, outages
- Store all data in PostgreSQL
- Provide AI-based troubleshooting recommendations
- Collect operator feedback
- Provide chat-based incident assistance
- Support LDAP authentication

Primary focus:
- Critical alerts only
- NOC operator usability
- Fast incident resolution (MTTR reduction)

Environment:
- Backend: Python FastAPI
- Frontend: Vanilla HTML/CSS/JS
- DB: PostgreSQL
- LLM: Local (Ollama) + OpenAI/Anthropic fallback
- Deployment: Bare metal internal server
- Security: LDAP authentication required

Important constraint:
This is MCP stage — simplicity > scalability, but architecture must be production-aligned.