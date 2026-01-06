#!/usr/bin/env python3
"""
AI SDR Platform - Demo Script

This script demonstrates the core capabilities of the platform:
1. Lead processing through the agentic mesh
2. Hybrid PaaS/SaaS deployment modes
3. x402 payment integration
4. GTM orchestration

Run: python demo.py
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_result(label: str, data: Any):
    """Print a formatted result"""
    print(f"  ✓ {label}:")
    if isinstance(data, dict):
        for k, v in data.items():
            print(f"    - {k}: {v}")
    else:
        print(f"    {data}")
    print()


async def demo_saas_mode():
    """Demonstrate SaaS mode - out-of-box deployment"""
    print_section("DEMO 1: SaaS Mode - Out-of-Box Deployment")
    
    from gtm_os.hybrid_deployment import (
        HybridDeploymentManager,
        create_saas_workspace,
    )
    
    # Create deployment manager
    manager = HybridDeploymentManager()
    
    # Create a SaaS workspace (pre-configured agents)
    workspace = create_saas_workspace(
        workspace_id="demo-saas-001",
        name="Demo SaaS Client",
        integrations={
            "crm": {"type": "twenty", "api_key": "demo_key"},
            "email": {"type": "listmonk", "url": "http://localhost:9000"},
        }
    )
    manager.register_workspace(workspace)
    
    print_result("Workspace Created", {
        "ID": workspace.workspace_id,
        "Mode": workspace.mode.value,
        "Agents": len(workspace.agents),
    })
    
    # Show pre-configured agents
    print("  Pre-configured Agents:")
    for agent in workspace.agents:
        print(f"    - {agent.name}: {agent.description}")
    
    print()
    return manager


async def demo_paas_mode():
    """Demonstrate PaaS mode - n8n execution layer"""
    print_section("DEMO 2: PaaS Mode - n8n Execution Layer")
    
    from gtm_os.hybrid_deployment import (
        HybridDeploymentManager,
        create_paas_workspace,
    )
    
    manager = HybridDeploymentManager()
    
    # Create a PaaS workspace for consulting partner
    workspace = create_paas_workspace(
        workspace_id="consulting-partner-001",
        name="Consulting Partner - Custom Build",
        n8n_base_url="http://localhost:5678",
        n8n_api_key="demo_n8n_key",
        custom_workflows={
            "research": "webhook/custom-research-flow",
            "scoring": "webhook/custom-scoring-model",
            "copywriting": "webhook/custom-email-generator",
            "enrichment": "webhook/custom-data-enrichment",
        },
        integrations={
            "crm": {"type": "salesforce", "instance": "client.salesforce.com"},
            "data_warehouse": {"type": "snowflake", "account": "client_account"},
        }
    )
    manager.register_workspace(workspace)
    
    print_result("PaaS Workspace Created", {
        "ID": workspace.workspace_id,
        "Mode": workspace.mode.value,
        "n8n URL": workspace.n8n_base_url,
        "Custom Workflows": len(workspace.custom_workflows),
    })
    
    print("  Custom n8n Workflows:")
    for action, webhook in workspace.custom_workflows.items():
        print(f"    - {action} → {webhook}")
    
    print()
    return manager


async def demo_lead_processing():
    """Demonstrate lead processing through the agentic mesh"""
    print_section("DEMO 3: Lead Processing - Agentic Mesh")
    
    # Sample lead data
    lead = {
        "id": "lead-demo-001",
        "email": "jane.doe@techcorp.com",
        "firstName": "Jane",
        "lastName": "Doe",
        "company": "TechCorp Inc",
        "title": "VP of Engineering",
        "source": "LinkedIn Campaign",
    }
    
    print_result("Processing Lead", lead)
    
    # Simulate agent processing (without actual LLM calls for demo)
    print("  Agent Processing Pipeline:")
    
    # Research Agent
    print("    [1] Research Agent...")
    research_result = {
        "company_info": {
            "name": "TechCorp Inc",
            "size": "500-1000 employees",
            "industry": "Enterprise SaaS",
            "funding": "Series C - $50M",
            "tech_stack": ["Python", "Kubernetes", "AWS"],
        },
        "contact_info": {
            "verified": True,
            "linkedin": "linkedin.com/in/janedoe",
            "seniority": "VP Level",
        },
        "quality_score": 85,
    }
    print(f"        → Research Quality: {research_result['quality_score']}/100")
    
    # Qualifier Agent
    print("    [2] Qualifier Agent...")
    lead_score = 78
    print(f"        → Lead Score: {lead_score}/100")
    
    # Copywriting Agent
    print("    [3] Copywriting Agent...")
    email_variants = [
        {
            "subject": "Congratulations on your Series C, Jane!",
            "preview": "I noticed TechCorp just closed $50M...",
            "variant": "A - Funding Hook",
        },
        {
            "subject": "Quick question about your Python infrastructure",
            "preview": "I see your team is using Python and K8s...",
            "variant": "B - Tech Stack Hook",
        },
    ]
    print(f"        → Generated {len(email_variants)} email variants")
    
    # Timing Agent
    print("    [4] Timing Optimizer...")
    optimal_time = "Tuesday 10:15 AM PST"
    print(f"        → Optimal Send Time: {optimal_time}")
    
    # Negotiation Agent
    print("    [5] Negotiation Agent (uAgents Protocol)...")
    negotiation_result = {
        "consensus_reached": True,
        "total_cost": "$0.17",
        "agents_approved": ["research", "copywriting", "timing"],
    }
    print(f"        → Consensus: {negotiation_result['consensus_reached']}")
    print(f"        → Total Cost: {negotiation_result['total_cost']}")
    
    print("\n  ✓ Lead processing complete!")
    print(f"    - Lead Score: {lead_score}")
    print(f"    - Email Variants: {len(email_variants)}")
    print(f"    - Scheduled: {optimal_time}")
    print()


async def demo_x402_payments():
    """Demonstrate x402 payment integration"""
    print_section("DEMO 4: x402 Payment Protocol Integration")
    
    from integrations.x402_payments import (
        X402Client,
        X402Middleware,
        AgentPaymentManager,
        PaymentNetwork,
    )
    
    # Show client configuration
    print("  x402 Client Configuration:")
    print(f"    - Network: Base L2 (eip155:8453)")
    print(f"    - Asset: USDC")
    print(f"    - Facilitator: https://x402.org/facilitator")
    print()
    
    # Demonstrate payment middleware setup
    middleware = X402Middleware(
        pay_to="0xDemoAddress123",
        default_network=PaymentNetwork.BASE,
    )
    
    # Set pricing for API endpoints
    middleware.set_pricing(
        endpoint="POST /api/leads/enrich",
        amount_usd=0.01,
        description="Lead enrichment with company data",
    )
    middleware.set_pricing(
        endpoint="POST /api/emails/generate",
        amount_usd=0.05,
        description="AI-powered email generation",
    )
    middleware.set_pricing(
        endpoint="GET /api/research/company",
        amount_usd=0.02,
        description="Company research and analysis",
    )
    
    print("  API Pricing (USDC):")
    for endpoint, pricing in middleware.pricing.items():
        amount = float(pricing["amount"]) / 1_000_000
        print(f"    - {endpoint}: ${amount:.4f}")
    print()
    
    # Demonstrate agent payment manager
    payment_manager = AgentPaymentManager(
        budget_per_lead=0.25,
        wallet_address="0xAgentWallet123",
    )
    
    print("  Agent Budget Management:")
    print(f"    - Budget per Lead: ${payment_manager.budget_per_lead:.2f}")
    print(f"    - Remaining for lead-001: ${payment_manager.get_remaining_budget('lead-001'):.2f}")
    print()
    
    print("  x402 Benefits:")
    print("    - Pay-per-use micropayments (as low as $0.001)")
    print("    - No subscriptions or API keys required")
    print("    - AI agents can pay autonomously")
    print("    - Instant settlement on Base L2")
    print("    - Multi-chain support via CAIP standards")
    print()


async def demo_gtm_orchestration():
    """Demonstrate GTM/RevOps orchestration"""
    print_section("DEMO 5: GTM Orchestration - Event Processing")
    
    # Simulate GTM event
    event = {
        "workspace_id": "demo-001",
        "event_type": "deal_stage_changed",
        "payload": {
            "deal_id": "deal-123",
            "old_stage": "Discovery",
            "new_stage": "Proposal",
            "amount": 50000,
            "contact": "jane.doe@techcorp.com",
        }
    }
    
    print_result("GTM Event Received", {
        "Type": event["event_type"],
        "Deal Stage": f"{event['payload']['old_stage']} → {event['payload']['new_stage']}",
        "Deal Amount": f"${event['payload']['amount']:,}",
    })
    
    print("  Orchestration Pipeline:")
    print("    [1] Event Classifier → deal_stage_changed (confidence: 0.95)")
    print("    [2] Schema Discovery → workspace schema validated")
    print("    [3] Routing SLA → assigned to senior AE")
    print("    [4] Lifecycle Enforcement → proposal stage requirements checked")
    print("    [5] Data Hygiene → contact data verified")
    print("    [6] Reporting Attribution → pipeline updated")
    print()
    
    print("  Actions Generated:")
    actions = [
        "n8n_webhook: /notify-sales-team",
        "n8n_webhook: /update-crm-pipeline",
        "n8n_webhook: /trigger-proposal-workflow",
    ]
    for action in actions:
        print(f"    → {action}")
    print()


async def demo_growthbook():
    """Demonstrate GrowthBook feature flags, A/B testing, and dynamic configs"""
    print_section("DEMO 6: GrowthBook - Feature Flags & A/B Testing")
    
    from mcp_servers.growthbook_mcp import GrowthBookClient
    
    # Initialize client in local mode (no external dependencies)
    client = GrowthBookClient(local_mode=True)
    
    print("  1️⃣ FEATURE FLAGS (Agent Gates):")
    print("     Control which agents are enabled in production\n")
    
    # Show default feature flags
    flags = await client.get_feature_flags()
    print("     Current Feature Flags:")
    for flag in flags[:5]:  # Show first 5
        status = "✓ ON" if flag["enabled"] else "✗ OFF"
        print(f"       {status}  {flag['key']}")
    print()
    
    # Demonstrate feature flag evaluation
    print("     Evaluating 'enable_negotiation_agent':")
    is_enabled = client.is_on("enable_negotiation_agent")
    print(f"       → Agent enabled: {is_enabled}")
    print()
    
    # Create a new feature flag
    new_flag = await client.create_feature_flag(
        key="enable_beta_scoring_model",
        description="Use new ML scoring model",
        enabled=False,
    )
    print(f"     Created new flag: {new_flag['key']} (enabled: {new_flag['enabled']})")
    print()
    
    print("  2️⃣ A/B EXPERIMENTS (Campaign Testing):")
    print("     Test email variants, timing strategies\n")
    
    # Create an experiment
    experiment = await client.create_experiment(
        key="email_subject_line_test",
        name="Email Subject Line A/B Test",
        hypothesis="Personalized subjects increase open rates by 20%",
        variations=[
            {"key": "control", "name": "Generic Subject", "weight": 50},
            {"key": "treatment", "name": "Personalized Subject", "weight": 50},
        ],
        metrics=["open_rate", "reply_rate", "meeting_booked"],
    )
    print(f"     Created Experiment: {experiment['name']}")
    print(f"       Hypothesis: {experiment['hypothesis']}")
    print(f"       Variations: {[v['name'] for v in experiment['variations']]}")
    print()
    
    # Start the experiment
    await client.start_experiment("email_subject_line_test")
    print("     ▶ Experiment started!")
    print()
    
    # Assign variants to users
    print("     Variant Assignment:")
    test_users = ["lead-001", "lead-002", "lead-003", "lead-004"]
    for user_id in test_users:
        variant = client.get_experiment_variant("email_subject_line_test", user_id)
        print(f"       {user_id} → {variant}")
    print()
    
    print("  3️⃣ DYNAMIC CONFIGS (Agent Parameters):")
    print("     Adjust scoring thresholds, budgets without code changes\n")
    
    # Get dynamic config
    configs = await client.get_dynamic_configs()
    for config in configs[:3]:
        print(f"     📋 {config['key']}:")
        for k, v in list(config['value'].items())[:3]:
            print(f"        - {k}: {v}")
        print()
    
    # Update a config
    await client.update_dynamic_config(
        "lead_qualification_config",
        {
            "min_qualification_score": 65,  # Raised from 60
            "auto_approve_threshold": 85,   # Lowered from 90
            "research_quality_threshold": 75,
            "max_cost_per_lead": 0.30,      # Increased budget
        }
    )
    print("     ✓ Updated lead_qualification_config dynamically!")
    print()
    
    print("  4️⃣ STALE FLAG DETECTION:")
    print("     Identify unused feature flags for cleanup\n")
    
    stale_flags = await client.get_stale_flags(days=30)
    if stale_flags:
        print(f"     Found {len(stale_flags)} stale flags (not evaluated in 30 days)")
    else:
        print("     No stale flags detected")
    print()
    
    print("  GrowthBook Benefits:")
    print("    ✓ 100% Open Source (MIT License)")
    print("    ✓ Self-hosted - full data ownership")
    print("    ✓ $54K savings vs Statsig over 3 years")
    print("    ✓ Built-in statistical engine for experiments")
    print("    ✓ Easy MCP integration")
    print()


def show_setup_requirements():
    """Show required setup for running the platform"""
    print_section("SETUP REQUIREMENTS")
    
    print("  1. REQUIRED ACCOUNTS & API KEYS:")
    print("     ├── OpenAI API Key (for embeddings)")
    print("     │   └── Get at: https://platform.openai.com")
    print("     ├── Pinecone API Key (vector store)")
    print("     │   └── Get at: https://app.pinecone.io")
    print("     ├── Hunter.io API Key (email verification)")
    print("     │   └── Get at: https://hunter.io/api")
    print("     └── Fetch.ai Wallet (agent communication)")
    print("         └── Get at: https://fetch.ai/docs")
    print()
    
    print("  2. OPTIONAL (Based on Integration Needs):")
    print("     ├── Slack Bot Token (approvals/notifications)")
    print("     ├── SendGrid/Listmonk (email delivery)")
    print("     ├── Twenty CRM API Key (CRM integration)")
    print("     ├── GitHub Token (version control)")
    print("     └── x402 Wallet (stablecoin payments)")
    print()
    
    print("  3. INFRASTRUCTURE:")
    print("     ├── PostgreSQL 16 (database)")
    print("     ├── Redis 7 (queue/cache)")
    print("     ├── Docker & Docker Compose")
    print("     └── GPU (optional, for self-hosted LLM)")
    print()
    
    print("  4. QUICK START:")
    print("     $ cp .env.example .env")
    print("     $ # Edit .env with your API keys")
    print("     $ docker-compose up -d")
    print("     $ python demo.py")
    print()


async def main():
    """Run all demos"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║        AI SDR PLATFORM - AGENTIC MESH DEMO                ║
    ║                                                           ║
    ║   • Hybrid PaaS/SaaS Architecture                         ║
    ║   • x402 Stablecoin Payments (Coinbase)                   ║
    ║   • n8n Execution Layer for Custom Workflows              ║
    ║   • GrowthBook Feature Flags & A/B Testing                ║
    ║   • Multi-Agent Negotiation & Orchestration               ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Run demos
    await demo_saas_mode()
    await demo_paas_mode()
    await demo_lead_processing()
    await demo_x402_payments()
    await demo_gtm_orchestration()
    await demo_growthbook()
    
    # Show setup requirements
    show_setup_requirements()
    
    print_section("DEMO COMPLETE")
    print("  Next Steps:")
    print("    1. Copy .env.example to .env and add your API keys")
    print("    2. Run: docker-compose up -d")
    print("    3. Access API at: http://localhost:8000")
    print("    4. View API docs: http://localhost:8000/docs")
    print()
    print("  For PaaS Mode (Consulting Partners):")
    print("    1. Deploy n8n: docker-compose -f docker-compose.n8n.yml up -d")
    print("    2. Build custom workflows in n8n")
    print("    3. Configure workspace with n8n webhook URLs")
    print()
    print("  Documentation: ./docs/")
    print("  Support: https://github.com/your-org/ai-sdr-platform")
    print()


if __name__ == "__main__":
    asyncio.run(main())
