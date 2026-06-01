Design the full MCP architecture for an AI-assisted OpenNMS monitoring system.

Include:

1. System architecture diagram (text-based)
2. Data flow (OpenNMS → ingestion → DB → AI → UI)
3. Database design (PostgreSQL)
4. API structure (FastAPI)
5. LLM integration layer (multi-provider)
6. LDAP authentication flow
7. Feedback loop architecture
8. Chat system architecture
9. Logging & audit system
10. Data sanitization pipeline

Constraints:
- OpenNMS uses XML APIs
- System must store raw + parsed data
- Critical alerts only for AI processing
- Must support 2000+ servers in future

Output must be structured for implementation.