# n8n Workflow Templates for PaaS Mode

This directory contains example n8n workflow templates that consulting partners can use as starting points for building custom client integrations.

## Available Templates

### 1. Custom Research Workflow (`custom-research-template.json`)

A template for custom lead research that:
- Receives lead data via webhook
- Enriches with Hunter.io
- Enriches with Apollo.io
- Returns formatted research data

**Trigger:** `POST /webhook/custom-research`

**Input:**
```json
{
  "workspace_id": "partner-001",
  "action": "research",
  "payload": {
    "email": "jane@company.com",
    "company_domain": "company.com"
  }
}
```

**Output:**
```json
{
  "company_info": {
    "name": "Company Inc",
    "size": "100-500",
    "industry": "SaaS"
  },
  "quality_score": 85
}
```

## How to Use

### Import a Template

1. Open n8n at http://localhost:5678
2. Go to Workflows > Import from File
3. Select the template JSON file
4. Configure credentials (API keys)
5. Activate the workflow

### Register with AI SDR Platform

After creating your n8n workflow, register it with a workspace:

```bash
curl -X POST http://localhost:8000/api/workspaces \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "my-client",
    "name": "My Client Workspace",
    "mode": "paas",
    "n8n_base_url": "http://localhost:5678",
    "custom_workflows": {
      "research": "webhook/custom-research"
    }
  }'
```

## Building Custom Workflows

### Required Webhook Pattern

All custom workflows should:

1. **Start with Webhook Trigger**
   - Use POST method
   - Accept JSON body

2. **Process the Payload**
   - Access `$json.workspace_id`
   - Access `$json.action`
   - Access `$json.payload.*`

3. **Return Structured Response**
   - Use "Respond to Webhook" node
   - Return JSON matching expected schema

### Workflow Types

| Action | Expected Output |
|--------|-----------------|
| `research` | `{ company_info: {}, contact_info: {}, quality_score: int }` |
| `scoring` | `{ score: int, factors: {} }` |
| `copywriting` | `{ variants: [], selected: int }` |
| `enrichment` | `{ enriched_data: {} }` |

## Example: Salesforce Integration

```json
{
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "salesforce-sync",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Salesforce",
      "type": "n8n-nodes-base.salesforce",
      "parameters": {
        "operation": "upsert",
        "resource": "lead"
      }
    }
  ]
}
```

## Environment Variables

n8n can access these environment variables:

- `HUNTER_API_KEY`
- `APOLLO_API_KEY`
- `CLEARBIT_API_KEY`
- `OPENAI_API_KEY`

Set them in `docker-compose.n8n.yml`:

```yaml
services:
  n8n:
    environment:
      - HUNTER_API_KEY=${HUNTER_API_KEY}
```

## Best Practices

1. **Error Handling**: Add error handlers to catch API failures
2. **Rate Limiting**: Use n8n's built-in rate limiting
3. **Logging**: Log important steps for debugging
4. **Testing**: Test workflows in isolation before connecting
5. **Versioning**: Export workflows as JSON and version control them

## Support

- n8n Documentation: https://docs.n8n.io
- AI SDR Platform Docs: ../docs/N8N_WORKFLOWS.md
