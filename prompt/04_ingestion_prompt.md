Build OpenNMS ingestion system.

Requirements:

1. Connect to OpenNMS REST APIs
2. Authenticate using Basic Auth
3. Parse XML responses
4. Normalize data into PostgreSQL schema
5. Handle:
   - Nodes
   - Alerts
   - Events
   - Outages

Rules:
- Never lose raw XML
- Use UPSERT for alerts and nodes
- Add retry logic for API failures
- Add logging for every ingestion cycle
- Avoid duplicate alert creation

Node parsing requirement:
Extract from node label:
{operator}-{circle}-{ip}-{server_type}