When debugging:

1. Always check logs first
2. Validate OpenNMS API response structure (XML)
3. Verify database UPSERT logic
4. Check sanitization pipeline
5. Validate LLM request payload
6. Ensure LDAP authentication flow

If issue involves AI:
- Inspect prompt before LLM call
- Verify sanitized output
- Check token limits

Always isolate issue by layer:
OpenNMS → Backend → DB → AI → UI