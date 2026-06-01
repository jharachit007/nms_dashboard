Implement security layer for MCP.

Requirements:

1. LDAP authentication
2. Role-based access control:
   - noc-viewer
   - noc-operator
   - noc-admin

3. Data sanitization before LLM calls:
   - Remove IPs
   - Remove emails
   - Remove secrets/tokens
   - Truncate large logs

4. Audit logging:
   - Login events
   - Alert view
   - AI usage
   - Feedback submission

5. Secure configuration:
   - No secrets in code
   - Use environment variables