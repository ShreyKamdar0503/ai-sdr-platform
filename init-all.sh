#!/bin/bash
echo "🚀 Initializing AI SDR Platform - Agentic Mesh"
echo "================================================"

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker required"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose required"; exit 1; }

# Load environment
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    exit 1
fi

source .env

# Create directories
mkdir -p data logs backups

# Start infrastructure
echo "Starting services..."
docker-compose up -d

echo ""
echo "✅ Platform initialized!"
echo ""
echo "Services:"
echo "  - API: http://localhost:8000"
echo "  - MCP Filesystem: http://localhost:8100"
echo "  - MCP Postgres: http://localhost:8101"
echo "  - MCP Slack: http://localhost:8102"
echo ""
echo "Next: Test with: curl http://localhost:8000/agents/status"
