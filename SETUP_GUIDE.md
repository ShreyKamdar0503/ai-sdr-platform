# 🚀 AI SDR Platform - Complete Setup & Demo Guide

This guide covers everything you need to run a working demo of the AI SDR Platform, including the hybrid PaaS/SaaS architecture and x402 payment integration.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Required Accounts & API Keys](#required-accounts--api-keys)
3. [Quick Start (Demo Mode)](#quick-start-demo-mode)
4. [Full Production Setup](#full-production-setup)
5. [Running the Demo](#running-the-demo)
6. [Testing the API](#testing-the-api)
7. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Storage | 20 GB SSD | 50+ GB SSD |
| GPU | None (uses OpenAI) | NVIDIA RTX 4070+ (for self-hosted LLM) |

### Required Software

```bash
# Check versions
docker --version          # Docker 24.0+
docker-compose --version  # Docker Compose 2.20+
python --version          # Python 3.10+
node --version            # Node.js 18+ (optional, for docx-js)
```

### Installation (Ubuntu/Debian)

```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Python 3.10+
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# Optional: NVIDIA Docker (for GPU/vLLM)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update && sudo apt install nvidia-docker2
```

---

## 🔑 Required Accounts & API Keys

### Tier 1: Essential (Required for Demo)

| Service | Purpose | Get Key At | Free Tier |
|---------|---------|------------|-----------|
| **OpenAI** | Embeddings & fallback LLM | [platform.openai.com](https://platform.openai.com) | $5 credit |
| **Pinecone** | Vector database | [app.pinecone.io](https://app.pinecone.io) | 1 free index |

### Tier 2: Recommended (Production Features)

| Service | Purpose | Get Key At | Free Tier |
|---------|---------|------------|-----------|
| **Hunter.io** | Email verification | [hunter.io/api](https://hunter.io/api) | 50 requests/mo |
| **Fetch.ai** | uAgents communication | [fetch.ai/docs](https://fetch.ai/docs) | Free testnet |
| **Slack** | Notifications & approvals | [api.slack.com/apps](https://api.slack.com/apps) | Free |

### Tier 3: Optional (Advanced Features)

| Service | Purpose | Get Key At |
|---------|---------|------------|
| **x402/Coinbase** | Stablecoin payments | [coinbase.com/developer-platform](https://www.coinbase.com/developer-platform) |
| **Twenty CRM** | Open-source CRM | Self-hosted or [twenty.com](https://twenty.com) |
| **Listmonk** | Email delivery | Self-hosted |
| **SendGrid** | Email delivery (alternative) | [sendgrid.com](https://sendgrid.com) |

---

## ⚡ Quick Start (Demo Mode)

### Step 1: Clone and Configure

```bash
# Clone the repository
cd ai-sdr-platform-v2

# Copy environment template
cp .env.example .env
```

### Step 2: Set Minimum Required Keys

Edit `.env` with your actual keys:

```bash
# REQUIRED - Get from platform.openai.com
OPENAI_API_KEY=sk-your-openai-key

# REQUIRED - Get from app.pinecone.io
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-east-1

# Database passwords (set your own)
POSTGRES_PASSWORD=your_secure_password_123
REDIS_PASSWORD=your_redis_password_456
```

### Step 3: Start Core Services

```bash
# Create network
docker network create ai-sdr-network

# Start PostgreSQL and Redis only (minimal demo)
docker-compose up -d postgres redis

# Wait for databases to be ready (10-15 seconds)
docker-compose ps

# Verify health
docker-compose logs postgres | tail -5
```

### Step 4: Run the Demo Script

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the demo
python demo.py
```

### Expected Output

```
╔═══════════════════════════════════════════════════════════╗
║        AI SDR PLATFORM - AGENTIC MESH DEMO                ║
╚═══════════════════════════════════════════════════════════╝

============================================================
  DEMO 1: SaaS Mode - Out-of-Box Deployment
============================================================

  ✓ Workspace Created:
    - ID: demo-saas-001
    - Mode: saas
    - Agents: 6

  Pre-configured Agents:
    - Research Agent: Company & contact intelligence gathering
    - Qualifier Agent: Lead scoring and prioritization
    ...
```

---

## 🏭 Full Production Setup

### Step 1: Complete Environment Configuration

```bash
# Edit .env with all production keys
nano .env
```

**Required for Production:**

```bash
# LLM (choose one)
OPENAI_API_KEY=sk-...
# OR for self-hosted:
VLLM_API_URL=http://localhost:8001/v1
VLLM_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct

# Vector Store
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=ai-sdr-leads

# Agent Communication
FETCHAI_WALLET_KEY=your_wallet_seed_phrase

# Email Verification
HUNTER_API_KEY=...

# Notifications
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...

# Email Delivery
LISTMONK_URL=http://localhost:9000
LISTMONK_USERNAME=admin
LISTMONK_PASSWORD=...
```

### Step 2: Start All Services

```bash
# Start core services
docker-compose up -d

# For PaaS mode (n8n workflow engine)
docker-compose -f docker-compose.n8n.yml up -d

# For GPU/vLLM (requires NVIDIA GPU)
docker-compose --profile gpu up -d

# For full agent network
docker-compose --profile agents up -d
```

### Step 3: Initialize Database

```bash
# Run migrations
docker-compose exec api python -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.getenv('DATABASE_URL'))
# Tables are created by init-db.sql
print('Database initialized!')
"
```

### Step 4: Verify All Services

```bash
# Check service health
curl http://localhost:8000/health
# Expected: {"status": "healthy", ...}

curl http://localhost:8000/agents/status
# Expected: {"research": "active", "copywriting": "active", ...}

# Check n8n (if PaaS mode)
curl http://localhost:5678/healthz
```

---

## 🎮 Running the Demo

### Demo 1: SaaS Mode (Out-of-Box)

```bash
python demo.py
```

This demonstrates:
- Pre-configured agents
- Lead processing pipeline
- Negotiation consensus
- Automatic approvals

### Demo 2: API Testing

```bash
# Health check
curl http://localhost:8000/

# Get agent status
curl http://localhost:8000/agents/status

# Process a lead
curl -X POST http://localhost:8000/api/leads/process \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jane@techcorp.com",
    "firstName": "Jane",
    "lastName": "Doe",
    "company": "TechCorp Inc",
    "title": "VP Engineering"
  }'
```

### Demo 3: GTM Event Processing

```bash
# Send a GTM event
curl -X POST http://localhost:8000/api/gtm/event \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "demo-workspace",
    "event_type": "deal_stage_changed",
    "payload": {
      "deal_id": "deal-123",
      "old_stage": "Discovery",
      "new_stage": "Proposal"
    },
    "execute_actions": false
  }'
```

### Demo 4: Create a PaaS Workspace

```bash
# Create workspace with custom n8n workflows
curl -X POST http://localhost:8000/api/workspaces \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "partner-001",
    "name": "Consulting Partner",
    "mode": "paas",
    "n8n_base_url": "http://localhost:5678",
    "custom_workflows": {
      "research": "webhook/custom-research",
      "scoring": "webhook/custom-scoring"
    }
  }'
```

---

## 🧪 Testing the API

### Using the Interactive Docs

Open in browser: [http://localhost:8000/docs](http://localhost:8000/docs)

This provides:
- Swagger UI with all endpoints
- Try-it-out functionality
- Request/response examples

### Using cURL

```bash
# Create a workspace
curl -X POST http://localhost:8000/api/workspaces \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "test-001", "name": "Test Workspace", "mode": "saas"}'

# Get workspace
curl http://localhost:8000/api/workspaces/test-001

# Process lead in workspace
curl -X POST http://localhost:8000/api/workspaces/test-001/process \
  -H "Content-Type: application/json" \
  -d '{"id": "lead-001", "email": "test@example.com", "company": "Test Corp"}'
```

### Using Python

```python
import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Health check
        r = await client.get("/health")
        print(r.json())
        
        # Process lead
        r = await client.post("/api/leads/process", json={
            "email": "cto@startup.io",
            "company": "Hot Startup",
            "title": "CTO"
        })
        print(r.json())

asyncio.run(test_api())
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Docker Compose Fails

```bash
# Check Docker is running
docker info

# Check for port conflicts
netstat -tulpn | grep -E '(5432|6379|8000)'

# View logs
docker-compose logs -f
```

#### 2. Database Connection Error

```bash
# Check PostgreSQL is healthy
docker-compose exec postgres pg_isready

# Manually connect
docker-compose exec postgres psql -U ai_sdr_user -d ai_sdr
```

#### 3. API Returns 500 Error

```bash
# View API logs
docker-compose logs api

# Check environment variables
docker-compose exec api env | grep -E '(DATABASE|OPENAI|PINECONE)'
```

#### 4. OpenAI API Errors

```bash
# Test OpenAI key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### 5. Pinecone Connection Issues

```bash
# Test Pinecone
python -c "
import pinecone
pinecone.init(api_key='$PINECONE_API_KEY', environment='us-east-1')
print(pinecone.list_indexes())
"
```

### Reset Everything

```bash
# Stop all containers
docker-compose down -v

# Remove all data
docker volume rm $(docker volume ls -q | grep ai-sdr)

# Start fresh
docker-compose up -d
```

---

## 📊 Service Ports Reference

| Service | Port | URL |
|---------|------|-----|
| API | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| n8n (PaaS) | 5678 | http://localhost:5678 |
| GrowthBook | 3100 | http://localhost:3100 |
| GrowthBook MCP | 8105 | http://localhost:8105 |
| vLLM (GPU) | 8001 | http://localhost:8001 |
| MCP Filesystem | 8100 | http://localhost:8100 |
| MCP Postgres | 8101 | http://localhost:8101 |
| uAgents | 8002 | http://localhost:8002 |

---

## 🎯 Next Steps

1. **For SaaS Demo**: Run `python demo.py` to see all features
2. **For PaaS Setup**: Deploy n8n and build custom workflows
3. **For Production**: Add all API keys and enable monitoring
4. **For x402 Payments**: Configure wallet and enable `X402_ENABLED=true`
5. **For Feature Flags**: Access GrowthBook at http://localhost:3100

---

## 📚 Additional Documentation

- `docs/ARCHITECTURE.md` - Technical architecture deep-dive
- `docs/AGENT_PROTOCOLS.md` - Agent communication specs
- `docs/API_REFERENCE.md` - Complete API documentation
- `docs/N8N_WORKFLOWS.md` - PaaS workflow examples

---

## 🆘 Support

- GitHub Issues: [your-org/ai-sdr-platform/issues](https://github.com/your-org/ai-sdr-platform/issues)
- Documentation: `./docs/`
- Demo Script: `python demo.py --help`
