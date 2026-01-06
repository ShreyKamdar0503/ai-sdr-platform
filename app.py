"""
GTMFlow - Complete FastAPI Application
Serves demo at root, loads .env file, real integrations.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
import traceback
import asyncio
import aiohttp
import os
import sys
from datetime import datetime

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load from .env file in current directory
    print("✓ Loaded .env file")
except ImportError:
    print("⚠ python-dotenv not installed, using environment variables only")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="GTMFlow", description="Automated SDR + GTM Pipeline", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# INTEGRATIONS (Load from .env)
# ============================================================================

class SlackIntegration:
    def __init__(self):
        # Try multiple env var names for compatibility
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL") or os.getenv("SLACK_BOT_TOKEN")
        # If it's a bot token, we'd need different logic, but webhook is simpler
        if self.webhook_url and self.webhook_url.startswith("xoxb-"):
            # It's a bot token, not a webhook - need webhook URL
            self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    @property
    def is_configured(self):
        return bool(self.webhook_url and self.webhook_url.startswith("https://"))
    
    async def send_message(self, message: str, blocks=None):
        if not self.is_configured:
            return {"success": False, "error": "SLACK_WEBHOOK_URL not configured"}
        
        payload = {"text": message}
        if blocks:
            payload["blocks"] = blocks
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload, timeout=10) as response:
                    return {"success": response.status == 200, "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_lead_notification(self, lead_data, research, score):
        company = lead_data.get("company", "Unknown")
        name = f"{lead_data.get('firstName', '')} {lead_data.get('lastName', '')}"
        title = lead_data.get("title", "")
        quality = research.get("quality_score", 0)
        tech = research.get("tech_stack", [])[:5]
        hooks = research.get("hooks", [])[:2]
        
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": f"🔥 FlowSDR: New Lead - {company}", "emoji": True}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Contact:* {name}"},
                {"type": "mrkdwn", "text": f"*Title:* {title}"},
                {"type": "mrkdwn", "text": f"*Lead Score:* {score}/100"},
                {"type": "mrkdwn", "text": f"*Research Quality:* {quality}/100"},
            ]},
        ]
        if tech:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Tech Stack:* {', '.join(tech)}"}})
        if hooks:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Hooks:*\n• {hooks[0][:100]}"}})
        blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": f"🤖 GTMFlow • {datetime.now().strftime('%H:%M:%S')}"}]})
        
        return await self.send_message(f"New lead: {company}", blocks)
    
    async def send_stage_change(self, lead_data, from_stage, to_stage, handoff_notes="", agents_used=None):
        company = lead_data.get("company", "Unknown")
        stage_emoji = {"new": "📥", "qualified": "✅", "discovery": "🔍", "proposal": "📄", "negotiation": "🤝", "won": "🎉"}
        
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": f"🔄 FlowGTM: Pipeline Update", "emoji": True}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*{company}*: {stage_emoji.get(from_stage, '📋')} {from_stage.title()} → {stage_emoji.get(to_stage, '📋')} {to_stage.title()}"}},
        ]
        if agents_used:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Agents:* {', '.join(agents_used)}"}})
        if handoff_notes:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"```{handoff_notes[:400]}```"}})
        blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": f"🤖 GTMFlow • {datetime.now().strftime('%H:%M:%S')}"}]})
        
        return await self.send_message(f"Stage: {company}", blocks)


class NotionIntegration:
    def __init__(self):
        self.api_key = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
        self.database_id = os.getenv("NOTION_DATABASE_ID") or os.getenv("NOTION_CRM_DATABASE_ID")
    
    @property
    def is_configured(self):
        return bool(self.api_key and self.database_id)
    
    async def create_lead(self, lead_data, research, score):
        if not self.is_configured:
            return {"success": False, "error": "Notion not configured"}
        
        properties = {
            "Name": {"title": [{"text": {"content": f"{lead_data.get('firstName', '')} {lead_data.get('lastName', '')}"}}]},
            "Company": {"rich_text": [{"text": {"content": lead_data.get("company", "")}}]},
            "Email": {"email": lead_data.get("email", "")},
            "Lead Score": {"number": score},
            "Stage": {"select": {"name": "New"}},
            "Research Quality": {"number": research.get("quality_score", 0)},
        }
        
        if lead_data.get("title"):
            properties["Title"] = {"rich_text": [{"text": {"content": lead_data.get("title", "")}}]}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.notion.com/v1/pages",
                    json={"parent": {"database_id": self.database_id}, "properties": properties},
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "Notion-Version": "2022-06-28"
                    },
                    timeout=15
                ) as response:
                    result = await response.json()
                    if response.status in [200, 201]:
                        return {"success": True, "page_id": result.get("id"), "url": result.get("url")}
                    return {"success": False, "error": result.get("message", str(result))}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def update_stage(self, page_id, new_stage):
        if not self.is_configured:
            return {"success": False, "error": "Notion not configured"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"https://api.notion.com/v1/pages/{page_id}",
                    json={"properties": {"Stage": {"select": {"name": new_stage}}}},
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "Notion-Version": "2022-06-28"
                    },
                    timeout=10
                ) as response:
                    return {"success": response.status == 200}
        except Exception as e:
            return {"success": False, "error": str(e)}


class N8NIntegration:
    def __init__(self):
        self.webhook_url = os.getenv("N8N_WEBHOOK_URL") or os.getenv("N8N_BASE_URL")
    
    @property
    def is_configured(self):
        return bool(self.webhook_url)
    
    async def trigger_webhook(self, event_type, payload):
        if not self.is_configured:
            return {"success": False, "error": "N8N_WEBHOOK_URL not configured"}
        
        data = {"event": event_type, "timestamp": datetime.now().isoformat(), "source": "gtmflow", "payload": payload}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=data, timeout=10) as response:
                    return {"success": response.status in [200, 201, 204]}
        except Exception as e:
            return {"success": False, "error": str(e)}


class IntegrationOrchestrator:
    def __init__(self):
        self.slack = SlackIntegration()
        self.notion = NotionIntegration()
        self.n8n = N8NIntegration()
    
    def get_status(self):
        return {
            "slack": {"configured": self.slack.is_configured, "url_set": bool(os.getenv("SLACK_WEBHOOK_URL"))},
            "notion": {"configured": self.notion.is_configured, "api_key_set": bool(os.getenv("NOTION_API_KEY")), "db_set": bool(os.getenv("NOTION_DATABASE_ID"))},
            "n8n": {"configured": self.n8n.is_configured, "url_set": bool(os.getenv("N8N_WEBHOOK_URL"))}
        }
    
    async def process_new_lead(self, lead_data, research, score):
        results = {"slack": {"triggered": False}, "notion": {"triggered": False}, "n8n": {"triggered": False}}
        
        tasks = []
        if self.slack.is_configured:
            tasks.append(("slack", self.slack.send_lead_notification(lead_data, research, score)))
        if self.notion.is_configured:
            tasks.append(("notion", self.notion.create_lead(lead_data, research, score)))
        if self.n8n.is_configured:
            tasks.append(("n8n", self.n8n.trigger_webhook("lead_processed", {"lead": lead_data, "score": score})))
        
        if tasks:
            task_results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
            for i, (name, _) in enumerate(tasks):
                r = task_results[i]
                if isinstance(r, Exception):
                    results[name] = {"triggered": True, "success": False, "error": str(r)}
                else:
                    results[name] = {"triggered": True, **r}
        
        return results
    
    async def process_stage_change(self, lead_data, from_stage, to_stage, handoff_notes="", agents_used=None):
        results = {"slack": {"triggered": False}, "n8n": {"triggered": False}}
        
        tasks = []
        if self.slack.is_configured:
            tasks.append(("slack", self.slack.send_stage_change(lead_data, from_stage, to_stage, handoff_notes, agents_used)))
        if self.n8n.is_configured:
            tasks.append(("n8n", self.n8n.trigger_webhook("stage_change", {"lead": lead_data, "from": from_stage, "to": to_stage})))
        
        if tasks:
            task_results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
            for i, (name, _) in enumerate(tasks):
                r = task_results[i]
                if isinstance(r, Exception):
                    results[name] = {"triggered": True, "success": False, "error": str(r)}
                else:
                    results[name] = {"triggered": True, **r}
        
        return results


integrations = IntegrationOrchestrator()


# ============================================================================
# MODELS
# ============================================================================

class LeadInput(BaseModel):
    id: Optional[str] = None
    firstName: str
    lastName: str
    email: str
    company: str
    title: Optional[str] = ""
    website: Optional[str] = ""


class StageChangeInput(BaseModel):
    lead_id: str
    firstName: str
    lastName: str
    email: str
    company: str
    from_stage: str
    to_stage: str
    handoff_notes: Optional[str] = ""
    agents_used: Optional[List[str]] = None


# ============================================================================
# DEMO HTML
# ============================================================================

DEMO_HTML = None
demo_paths = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai-sdr-demo", "index.html"),
    os.path.join(os.path.dirname(__file__), "index.html"),
    "ai-sdr-demo/index.html",
    "index.html"
]

for path in demo_paths:
    if os.path.exists(path):
        with open(path, 'r') as f:
            DEMO_HTML = f.read()
        print(f"✓ Loaded demo from: {path}")
        break


@app.get("/", response_class=HTMLResponse)
async def serve_demo():
    if DEMO_HTML:
        return HTMLResponse(content=DEMO_HTML)
    return HTMLResponse(content="""
        <html><head><title>GTMFlow</title></head>
        <body style="background:#0a0a0f;color:white;font-family:sans-serif;padding:2rem;">
            <h1>🚀 GTMFlow Running</h1>
            <p>Place index.html in ai-sdr-demo/ folder</p>
            <ul>
                <li><a href="/api/leads/health" style="color:#6366f1;">/api/leads/health</a></li>
                <li><a href="/api/leads/test-research?company=Stripe" style="color:#6366f1;">/api/leads/test-research</a></li>
                <li><a href="/api/integrations/status" style="color:#6366f1;">/api/integrations/status</a></li>
            </ul>
        </body></html>
    """)


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.get("/api/leads/health")
async def health_check():
    checks = {"api": True, "research_agent": False, "playwright": False, "openai": False}
    
    try:
        from agentic_mesh.agents.research_agent import ResearchAgent
        checks["research_agent"] = True
        checks["agent_type"] = "RealResearchAgent"
    except Exception as e:
        checks["research_error"] = str(e)
    
    try:
        from playwright.async_api import async_playwright
        checks["playwright"] = True
    except:
        pass
    
    checks["openai"] = bool(os.getenv("OPENAI_API_KEY"))
    checks["integrations"] = integrations.get_status()
    
    return {"status": "healthy" if checks["research_agent"] else "degraded", "checks": checks}


@app.get("/api/integrations/status")
async def integration_status():
    return {
        "integrations": integrations.get_status(),
        "env_vars": {
            "OPENAI_API_KEY": "✓" if os.getenv("OPENAI_API_KEY") else "✗",
            "SLACK_WEBHOOK_URL": "✓" if os.getenv("SLACK_WEBHOOK_URL") else "✗",
            "NOTION_API_KEY": "✓" if os.getenv("NOTION_API_KEY") else "✗",
            "NOTION_DATABASE_ID": "✓" if os.getenv("NOTION_DATABASE_ID") else "✗",
            "N8N_WEBHOOK_URL": "✓" if os.getenv("N8N_WEBHOOK_URL") else "✗",
        }
    }


# ============================================================================
# MAIN LEAD PROCESSING
# ============================================================================

@app.post("/api/leads/process")
async def process_lead(lead: LeadInput) -> Dict:
    lead_data = {
        "id": lead.id or f"lead-{id(lead)}",
        "firstName": lead.firstName,
        "lastName": lead.lastName,
        "email": lead.email,
        "company": lead.company,
        "title": lead.title or "",
        "website": lead.website or ""
    }
    
    print(f"\n{'='*60}")
    print(f"📥 PROCESSING: {lead.company}")
    print(f"{'='*60}")
    
    result = {
        "success": False,
        "lead_id": lead_data["id"],
        "research_results": None,
        "email_variants": [],
        "lead_score": 0,
        "quality_score": 0,
        "integrations": {},
        "error": None
    }
    
    # STEP 1: Research
    print(f"🔬 Research...")
    try:
        from agentic_mesh.agents.research_agent import ResearchAgent
        agent = ResearchAgent()
        research_results = await agent.process(lead_data)
        
        if "full_research" in research_results:
            full = research_results["full_research"]
            research_results = {
                "company_info": full.get("company_info", {}),
                "contact_info": full.get("contact_info", {}),
                "tech_stack": full.get("tech_stack", []),
                "hiring_data": full.get("hiring_data", {}),
                "recent_news": full.get("recent_news", []),
                "reddit_mentions": full.get("reddit_mentions", {}),
                "hooks": full.get("hooks", []),
                "quality_score": full.get("quality_score", 0),
            }
        
        result["research_results"] = research_results
        result["quality_score"] = research_results.get("quality_score", 0)
        print(f"  ✓ Quality: {result['quality_score']}/100")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        result["error"] = str(e)
        return result
    
    # STEP 2: Scoring
    print(f"📊 Scoring...")
    quality = result["quality_score"]
    title_lower = (lead.title or "").lower()
    
    title_score = 30 if any(t in title_lower for t in ["ceo", "cto", "cfo", "founder"]) else \
                  25 if any(t in title_lower for t in ["vp", "vice president"]) else \
                  20 if any(t in title_lower for t in ["director", "head"]) else \
                  15 if any(t in title_lower for t in ["manager", "senior"]) else 10
    
    hiring = result["research_results"].get("hiring_data", {})
    jobs = hiring.get("total_jobs", 0) if isinstance(hiring, dict) else 0
    hiring_score = min(jobs // 5, 20)
    
    tech = result["research_results"].get("tech_stack", [])
    tech_score = min(len(tech) * 2, 15)
    
    result["lead_score"] = min(int(quality * 0.35 + title_score + hiring_score + tech_score), 100)
    print(f"  ✓ Lead Score: {result['lead_score']}/100")
    
    # STEP 3: Emails
    print(f"✍️ Emails...")
    hooks = result["research_results"].get("hooks", [])
    hook1 = hooks[0] if hooks else f"I've been following {lead.company}'s growth"
    hook2 = hooks[1] if len(hooks) > 1 else f"I noticed {lead.company} is expanding"
    
    result["email_variants"] = [
        {"subject": f"Quick question about {lead.company}", "body": f"Hi {lead.firstName},\n\n{hook1}\n\n{'With ' + str(jobs) + '+ roles, scaling is key.' if jobs > 20 else 'I wanted to reach out.'}\n\nWe help automate sales research — 2-hour tasks in 45 seconds.\n\n15-min demo?\n\nBest,\n[Your Name]"},
        {"subject": f"{lead.company} + AI research", "body": f"Hi {lead.firstName},\n\n{hook2}\n\n{'Using ' + ', '.join(tech[:2]) + ' — we integrate.' if len(tech) >= 2 else 'Something useful for your team.'}\n\nOur AI researches leads in real-time.\n\nQuick chat?\n\nBest,\n[Your Name]"}
    ]
    print(f"  ✓ Generated 2 emails")
    
    # STEP 4: Integrations
    print(f"🔗 Integrations...")
    try:
        integration_results = await integrations.process_new_lead(lead_data, result["research_results"], result["lead_score"])
        result["integrations"] = integration_results
        
        for name, status in integration_results.items():
            if status.get("success"):
                print(f"  ✓ {name}: Sent")
            elif status.get("triggered"):
                print(f"  ⚠ {name}: Error - {status.get('error', 'unknown')}")
            else:
                print(f"  - {name}: Not configured")
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    result["success"] = True
    print(f"✅ Complete!\n")
    
    return result


# ============================================================================
# STAGE CHANGE
# ============================================================================

@app.post("/api/pipeline/stage-change")
async def pipeline_stage_change(data: StageChangeInput) -> Dict:
    lead_data = {"id": data.lead_id, "firstName": data.firstName, "lastName": data.lastName, "email": data.email, "company": data.company}
    
    print(f"\n🔄 STAGE: {data.company} | {data.from_stage} → {data.to_stage}")
    
    result = {"success": True, "from_stage": data.from_stage, "to_stage": data.to_stage, "integrations": {}}
    
    try:
        integration_results = await integrations.process_stage_change(
            lead_data, data.from_stage, data.to_stage, data.handoff_notes or "", data.agents_used
        )
        result["integrations"] = integration_results
        
        for name, status in integration_results.items():
            if status.get("success"):
                print(f"  ✓ {name}: Sent")
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    return result


# ============================================================================
# TEST
# ============================================================================

@app.get("/api/leads/test-research")
async def test_research(company: str = "Stripe", website: str = "https://stripe.com"):
    print(f"\n🧪 TEST: {company}")
    
    try:
        from agentic_mesh.agents.research_agent import ResearchAgent
        agent = ResearchAgent()
        
        results = await agent.process({
            "firstName": "Test", "lastName": "User",
            "email": f"test@{company.lower()}.com",
            "company": company, "title": "VP Sales", "website": website
        })
        
        if "full_research" in results:
            full = results["full_research"]
            return {"success": True, "company": company, "quality_score": full.get("quality_score", 0), "tech_stack": full.get("tech_stack", []), "hiring_data": full.get("hiring_data", {}), "news_count": len(full.get("recent_news", [])), "hooks": full.get("hooks", [])}
        
        return {"success": True, **results}
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@app.post("/api/integrations/test-slack")
async def test_slack():
    if not integrations.slack.is_configured:
        return {"success": False, "error": "Slack not configured", "hint": "Set SLACK_WEBHOOK_URL in .env"}
    return await integrations.slack.send_message("🧪 Test from GTMFlow")


# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*60)
    print("🚀 GTMFlow STARTED")
    print("   FlowSDR + FlowGTM Pipeline")
    print("="*60)
    print(f"  OpenAI:   {'✓' if os.getenv('OPENAI_API_KEY') else '✗'}")
    print(f"  Slack:    {'✓' if integrations.slack.is_configured else '✗'} {os.getenv('SLACK_WEBHOOK_URL', '')[:30] + '...' if os.getenv('SLACK_WEBHOOK_URL') else ''}")
    print(f"  Notion:   {'✓' if integrations.notion.is_configured else '✗'}")
    print(f"  n8n:      {'✓' if integrations.n8n.is_configured else '✗'}")
    
    try:
        from agentic_mesh.agents.research_agent import ResearchAgent
        print(f"  Agent:    ✓ Ready")
    except Exception as e:
        print(f"  Agent:    ✗ {e}")
    
    print("="*60)
    print("  http://localhost:8000")
    print("="*60 + "\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
