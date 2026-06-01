Build AI recommendation engine for critical alerts.

Input:
- OpenNMS alert
- Node context
- Recent events
- Historical similar alerts (if available)

Output:
- Summary
- Probable causes
- Step-by-step troubleshooting
- Confidence score

Rules:
- Must sanitize input before sending to LLM
- Must support multiple LLM providers:
  - Ollama (primary)
  - OpenAI
  - Anthropic
- AI must NEVER execute actions
- AI is advisory only

Advanced (future-ready):
- Multi-step reasoning pipeline:
  1. Summarize
  2. Diagnose
  3. Recommend