# Architecture Deep-Dive

## Agentic Mesh Design

This platform implements a true agentic mesh where:

1. **LangGraph** manages stateful workflows
2. **uAgents** enables decentralized negotiation
3. **MCP** provides unified context
4. **Pinecone** powers semantic search

## Agent Communication Flow

```
Lead Input → LangGraph Orchestrator
    ↓
Research Agent ⇄ Qualifier Agent (parallel)
    ↓
Copywriting Agent (if qualified)
    ↓
Timing Optimizer Agent
    ↓
Negotiation Agent (uAgents consensus)
    ↓
Approval Agent (human-in-loop)
    ↓
Email Sent via Listmonk
```

## Key Differences vs Sequential

- **Parallel Processing**: 3x faster
- **Agent Negotiation**: Dynamic resource allocation
- **Self-Healing**: Automatic retry on failure
- **Consensus-Based**: Democratic decision making
