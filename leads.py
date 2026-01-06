"""
Simplified API Routes - Direct Research Agent Call
This bypasses the complex LangGraph orchestrator and calls agents directly
with full error logging to help debug issues.

Replace your api/routes/leads.py with this file.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
import traceback
import asyncio
import os

router = APIRouter()


class LeadInput(BaseModel):
    """Lead input model"""
    id: Optional[str] = None
    firstName: str
    lastName: str
    email: str
    company: str
    title: Optional[str] = ""
    website: Optional[str] = ""


class LeadResponse(BaseModel):
    """Response model with all research data"""
    success: bool
    lead_id: str
    research_results: Optional[Dict] = None
    email_variants: Optional[List[Dict]] = None
    lead_score: int = 0
    quality_score: int = 0
    error: Optional[str] = None


@router.post("/process")
async def process_lead(lead: LeadInput) -> Dict:
    """
    Process a lead through the research pipeline.
    This is a simplified version that directly calls agents.
    """
    
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
    print(f"📥 PROCESSING LEAD: {lead.company}")
    print(f"{'='*60}")
    print(f"  Name: {lead.firstName} {lead.lastName}")
    print(f"  Email: {lead.email}")
    print(f"  Title: {lead.title}")
    print(f"  Website: {lead.website}")
    
    result = {
        "success": False,
        "lead_id": lead_data["id"],
        "research_results": None,
        "email_variants": [],
        "lead_score": 0,
        "quality_score": 0,
        "error": None
    }
    
    # Step 1: Research
    print(f"\n🔬 STEP 1: Running Research Agent...")
    try:
        from agentic_mesh.agents.research_agent import ResearchAgent
        
        research_agent = ResearchAgent()
        print(f"  ✓ Research agent imported")
        print(f"  ✓ Agent type: {type(research_agent)}")
        
        # Check if it has the real_agent attribute (wrapper class)
        if hasattr(research_agent, 'real_agent'):
            print(f"  ✓ Using RealResearchAgent wrapper")
        
        research_results = await research_agent.process(lead_data)
        
        print(f"  ✓ Research complete")
        print(f"  ✓ Quality score: {research_results.get('quality_score', 0)}")
        print(f"  ✓ Tech stack: {research_results.get('tech_stack', [])}")
        print(f"  ✓ Keys returned: {list(research_results.keys())}")
        
        result["research_results"] = research_results
        result["quality_score"] = research_results.get("quality_score", 0)
        
        # If we have full_research, flatten it for the frontend
        if "full_research" in research_results:
            full = research_results["full_research"]
            result["research_results"] = {
                **research_results,
                "tech_stack": full.get("tech_stack", []),
                "hiring_data": full.get("hiring_data", {}),
                "recent_news": full.get("recent_news", []),
                "reddit_mentions": full.get("reddit_mentions", {}),
                "hooks": full.get("hooks", []),
                "company_info": full.get("company_info", {}),
                "contact_info": full.get("contact_info", {}),
            }
        
    except Exception as e:
        error_msg = f"Research failed: {str(e)}\n{traceback.format_exc()}"
        print(f"  ✗ ERROR: {error_msg}")
        result["error"] = error_msg
        return result
    
    # Step 2: Lead Scoring
    print(f"\n📊 STEP 2: Scoring Lead...")
    try:
        # Simple scoring based on research quality
        quality = result["quality_score"]
        
        # Title-based score
        title_lower = (lead.title or "").lower()
        title_score = 0
        if any(t in title_lower for t in ["ceo", "cto", "cfo", "coo", "founder", "president"]):
            title_score = 30
        elif any(t in title_lower for t in ["vp", "vice president", "svp"]):
            title_score = 25
        elif any(t in title_lower for t in ["director", "head"]):
            title_score = 20
        elif any(t in title_lower for t in ["manager", "lead", "senior"]):
            title_score = 15
        else:
            title_score = 10
        
        # Hiring signal score
        hiring_data = result["research_results"].get("hiring_data", {})
        if isinstance(hiring_data, dict):
            jobs = hiring_data.get("total_jobs", 0)
        else:
            jobs = 0
        
        hiring_score = min(jobs // 5, 20)  # Up to 20 points
        
        # Tech stack score
        tech_stack = result["research_results"].get("tech_stack", [])
        tech_score = min(len(tech_stack) * 2, 15)
        
        # Calculate total
        lead_score = min(quality * 0.35 + title_score + hiring_score + tech_score, 100)
        result["lead_score"] = int(lead_score)
        
        print(f"  ✓ Quality contribution: {quality * 0.35:.1f}")
        print(f"  ✓ Title score: {title_score}")
        print(f"  ✓ Hiring score: {hiring_score}")
        print(f"  ✓ Tech score: {tech_score}")
        print(f"  ✓ Total lead score: {result['lead_score']}")
        
    except Exception as e:
        print(f"  ⚠ Scoring error (non-fatal): {e}")
        result["lead_score"] = 50  # Default score
    
    # Step 3: Generate Emails
    print(f"\n✍️ STEP 3: Generating Emails...")
    try:
        # Try to use the copywriting agent
        try:
            from agentic_mesh.agents.copywriting_agent import CopywritingAgent
            copywriter = CopywritingAgent()
            emails = await copywriter.generate_emails(lead_data, result["research_results"])
            result["email_variants"] = emails
            print(f"  ✓ Generated {len(emails)} email variants")
        except Exception as copy_error:
            print(f"  ⚠ Copywriting agent error: {copy_error}")
            # Generate basic emails from research
            hooks = result["research_results"].get("hooks", [])
            result["email_variants"] = generate_fallback_emails(lead_data, hooks, result["research_results"])
            print(f"  ✓ Generated {len(result['email_variants'])} fallback emails")
            
    except Exception as e:
        print(f"  ⚠ Email generation error (non-fatal): {e}")
        result["email_variants"] = []
    
    result["success"] = True
    
    print(f"\n{'='*60}")
    print(f"✅ LEAD PROCESSING COMPLETE")
    print(f"  Quality: {result['quality_score']}/100")
    print(f"  Lead Score: {result['lead_score']}/100")
    print(f"  Emails: {len(result['email_variants'])}")
    print(f"{'='*60}\n")
    
    return result


def generate_fallback_emails(lead_data: Dict, hooks: List[str], research: Dict) -> List[Dict]:
    """Generate basic emails when copywriting agent fails"""
    
    first_name = lead_data.get("firstName", "there")
    company = lead_data.get("company", "your company")
    
    hook1 = hooks[0] if hooks else f"I've been following {company}'s growth"
    hook2 = hooks[1] if len(hooks) > 1 else f"I noticed {company} is expanding"
    
    hiring = research.get("hiring_data", {})
    total_jobs = hiring.get("total_jobs", 0) if isinstance(hiring, dict) else 0
    
    email1 = {
        "subject": f"Quick question about {company}'s growth",
        "body": f"""Hi {first_name},

{hook1}

{f"With {total_jobs}+ open roles, scaling efficiently is probably top of mind." if total_jobs > 20 else f"I wanted to reach out about something that might help your team."}

We help companies automate the research phase of sales development — turning 2-hour research tasks into 45 seconds of AI-powered intelligence.

Would you be open to a 15-minute demo?

Best,
[Your Name]"""
    }
    
    email2 = {
        "subject": f"{company} + AI-powered research",
        "body": f"""Hi {first_name},

{hook2}

Our AI researches leads in real-time, generating personalized outreach based on actual company data, news, and competitive intelligence.

The result: SDRs spend 80% less time researching and 3x more time selling.

Worth a quick chat?

Best,
[Your Name]"""
    }
    
    return [email1, email2]


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    checks = {
        "api": True,
        "playwright": False,
        "openai": False,
    }
    
    # Check Playwright
    try:
        from playwright.async_api import async_playwright
        checks["playwright"] = True
    except:
        pass
    
    # Check OpenAI
    if os.getenv("OPENAI_API_KEY"):
        checks["openai"] = True
    
    return {
        "status": "healthy" if all(checks.values()) else "degraded",
        "checks": checks
    }


@router.post("/test-research")
async def test_research(company: str = "Stripe", website: str = "https://stripe.com"):
    """
    Test endpoint to directly test the research agent.
    Usage: POST /api/leads/test-research?company=Stripe&website=https://stripe.com
    """
    print(f"\n🧪 TEST: Researching {company}...")
    
    try:
        from agentic_mesh.agents.research_agent import ResearchAgent
        
        agent = ResearchAgent()
        
        test_lead = {
            "firstName": "Test",
            "lastName": "User",
            "email": f"test@{company.lower().replace(' ', '')}.com",
            "company": company,
            "title": "VP of Sales",
            "website": website
        }
        
        results = await agent.process(test_lead)
        
        return {
            "success": True,
            "company": company,
            "quality_score": results.get("quality_score", 0),
            "tech_stack": results.get("tech_stack", results.get("full_research", {}).get("tech_stack", [])),
            "hiring_jobs": results.get("hiring_data", results.get("full_research", {}).get("hiring_data", {})).get("total_jobs", 0),
            "news_count": len(results.get("recent_news", results.get("full_research", {}).get("recent_news", []))),
            "hooks": results.get("hooks", results.get("full_research", {}).get("hooks", [])),
            "full_results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
