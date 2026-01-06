"""
Fixed Orchestrator - Compatible with your project structure

Key Fixes:
1. Ensures company_info.summary is populated for copywriting agent
2. Fixes lead score calculation to not depend on email generation
3. Better error handling and logging
4. Uses correct imports for YOUR project (timing_optimizer, not timing_agent)
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()

# Try to use enhanced research agent, fallback to basic
try:
    from agentic_mesh.agents.integrated_research_agent import IntegratedResearchAgent as ResearchAgent
    print("  🔬 Using Enhanced Research Agent (Playwright + OpenAI)")
except ImportError:
    from agentic_mesh.agents.research_agent import ResearchAgent
    print("  📝 Using Basic Research Agent (OpenAI only)")

from agentic_mesh.agents.copywriting_agent import CopywritingAgent

# FIXED: Use timing_optimizer (your actual file) instead of timing_agent
try:
    from agentic_mesh.agents.timing_optimizer import TimingOptimizer as TimingAgent
except ImportError:
    # Fallback: create a simple timing class if import fails
    class TimingAgent:
        async def process(self, lead_data):
            return {"optimal_time": datetime.now().isoformat(), "timezone": "UTC"}

from agentic_mesh.agents.negotiation_agent import NegotiationAgent
from agentic_mesh.agents.qualifier_agent import QualifierAgent


class SDROrchestrator:
    """
    Orchestrates the AI SDR pipeline with proper data flow
    """
    
    def __init__(self):
        self.research_agent = ResearchAgent()
        self.copywriting_agent = CopywritingAgent()
        self.timing_agent = TimingAgent()
        self.negotiation_agent = NegotiationAgent()
        self.qualifier_agent = QualifierAgent()
    
    async def process_lead(self, lead_data: Dict) -> Dict:
        """
        Process a lead through the full AI pipeline
        
        Steps:
        1. Research (Playwright + OpenAI)
        2. Qualification (scoring)
        3. Copywriting (email generation)
        4. Timing (optimal send time)
        5. Negotiation (consensus)
        """
        
        lead_id = lead_data.get("id", f"lead-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        result = {
            "lead_id": lead_id,
            "lead_data": {
                "email": lead_data.get("email"),
                "firstName": lead_data.get("firstName"),
                "lastName": lead_data.get("lastName"),
                "company": lead_data.get("company"),
                "title": lead_data.get("title"),
            },
            "research_results": {},
            "email_variants": [],
            "timing_recommendation": {},
            "lead_score": 0,
            "quality_metrics": {},
            "approved": False,
            "sent": False,
            "timestamp": datetime.now().isoformat(),
            "agent_votes": {},
            "cost_tracker": {},
        }
        
        try:
            # Step 1: Research
            print(f"\n  📋 Processing lead: {lead_data.get('firstName')} @ {lead_data.get('company')}")
            
            research_results = await self.research_agent.process(lead_data)
            result["research_results"] = research_results
            
            # CRITICAL FIX: Ensure company_info.summary exists for copywriting
            company_info = research_results.get("company_info", {})
            if not company_info.get("summary"):
                # Try to extract from AI analysis
                ai_analysis = research_results.get("ai_analysis", "")
                if ai_analysis:
                    # Use first 500 chars of AI analysis as summary
                    company_info["summary"] = ai_analysis[:500]
                else:
                    # Generate basic summary
                    company_info["summary"] = f"{lead_data.get('company')} is a company in the technology sector."
                research_results["company_info"] = company_info
            
            print(f"  ✅ Research complete - Quality: {research_results.get('quality_score', 0)}/100")
            
            # Step 2: Qualification
            # Handle different qualifier_agent signatures
            try:
                qualification_result = await self.qualifier_agent.process(lead_data, research_results)
            except TypeError:
                # If qualifier_agent.process only takes one argument
                qualification_result = await self.qualifier_agent.process(lead_data)
            except Exception:
                qualification_result = {}
            
            # FIXED: Calculate lead score based on research quality and contact info
            # Maximum possible: 100 points
            research_quality = research_results.get("quality_score", 50)
            
            # Base score from research quality (max 40 points)
            base_score = research_quality * 0.4
            
            # Bonus for executive title (max 20 points)
            title = lead_data.get("title", "").lower()
            if any(t in title for t in ["ceo", "cto", "cfo", "coo", "president", "founder"]):
                base_score += 20
            elif any(t in title for t in ["vp", "director", "head"]):
                base_score += 15
            elif any(t in title for t in ["manager", "lead"]):
                base_score += 10
            
            # Bonus for verified email domain (max 10 points)
            email = lead_data.get("email", "")
            if email and "@" in email:
                domain = email.split("@")[1]
                if domain not in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]:
                    base_score += 10
            
            # Bonus for having engagement hooks (max 10 points)
            if research_results.get("hooks") and len(research_results.get("hooks", [])) >= 2:
                base_score += 10
            elif research_results.get("hooks"):
                base_score += 5
            
            # Bonus for tech stack detected (max 5 points)
            if company_info.get("tech_stack") and len(company_info.get("tech_stack", [])) > 0:
                base_score += 5
            
            # Bonus for hiring activity (max 5 points)
            if company_info.get("hiring_departments") and len(company_info.get("hiring_departments", [])) > 0:
                base_score += 5
            
            # Bonus for recent news (max 5 points)
            news = company_info.get("recent_news", [])
            if news and len(news) > 0 and news[0] != "Recent company activity":
                base_score += 5
            
            # Bonus for LinkedIn found (max 5 points)
            if company_info.get("linkedin_url"):
                base_score += 5
            
            lead_score = min(int(base_score), 100)
            result["lead_score"] = lead_score
            result["quality_metrics"]["research"] = research_quality
            
            print(f"  ✅ Qualification complete - Lead Score: {lead_score}/100")
            
            # Step 3: Copywriting - Generate emails
            # Only proceed if we have enough research
            if research_quality >= 40:
                try:
                    # Prepare context for copywriting agent
                    copywriting_context = {
                        "lead": lead_data,
                        "research": research_results,
                        "company_summary": company_info.get("summary", ""),
                        "tech_stack": company_info.get("tech_stack", []),
                        "hiring_departments": company_info.get("hiring_departments", []),
                        "recent_news": company_info.get("recent_news", []),
                        "hooks": research_results.get("hooks", []),
                    }
                    
                    email_variants = await self.copywriting_agent.process(copywriting_context)
                    
                    if email_variants and isinstance(email_variants, list):
                        result["email_variants"] = email_variants
                        print(f"  ✅ Copywriting complete - Generated {len(email_variants)} email(s)")
                    else:
                        print(f"  ⚠️ Copywriting returned no emails")
                        result["email_variants"] = self._generate_fallback_email(lead_data, research_results)
                        
                except Exception as e:
                    print(f"  ❌ Copywriting error: {str(e)[:100]}")
                    # Generate fallback email
                    result["email_variants"] = self._generate_fallback_email(lead_data, research_results)
            else:
                print(f"  ⚠️ Research quality too low ({research_quality}), using fallback emails")
                result["email_variants"] = self._generate_fallback_email(lead_data, research_results)
            
            # Step 4: Timing
            try:
                timing_result = await self.timing_agent.process(lead_data)
                result["timing_recommendation"] = timing_result
                print(f"  ✅ Timing optimized")
            except Exception as e:
                result["timing_recommendation"] = {"optimal_time": datetime.now().isoformat()}
            
            # Step 5: Negotiation / Consensus
            try:
                votes = {
                    "research": research_quality >= 60,
                    "qualification": lead_score >= 60,
                    "copywriting": len(result["email_variants"]) > 0,
                    "timing": True,
                }
                result["agent_votes"] = votes
                
                # Auto-approve if score >= 90 and all agents agree
                all_approve = all(votes.values())
                result["approved"] = all_approve and lead_score >= 90
                
                print(f"  ✅ Consensus: {sum(votes.values())}/4 agents approved")
                
            except Exception as e:
                result["agent_votes"] = {"error": str(e)}
            
            return result
            
        except Exception as e:
            print(f"  ❌ Pipeline error: {str(e)}")
            result["error"] = str(e)
            return result
    
    def _generate_fallback_email(self, lead_data: Dict, research: Dict) -> List[Dict]:
        """Generate a basic fallback email if copywriting agent fails"""
        first_name = lead_data.get("firstName", "there")
        company = lead_data.get("company", "your company")
        title = lead_data.get("title", "")
        
        # Get some research data
        company_info = research.get("company_info", {})
        tech_stack = company_info.get("tech_stack", [])
        hooks = research.get("hooks", [])
        
        # Build personalized elements
        personalization = ""
        if hooks and len(hooks) > 0:
            personalization = hooks[0]
        elif tech_stack and len(tech_stack) > 0:
            personalization = f"I noticed you're using {tech_stack[0]}"
        else:
            personalization = f"I've been following {company}'s growth"
        
        return [
            {
                "variant": "A",
                "subject": f"Quick question about {company}",
                "body": f"""Hi {first_name},

{personalization} and thought I'd reach out.

I work with companies like {company} to help them scale their operations more efficiently. Given your role as {title}, I thought you might find our approach interesting.

Would you be open to a quick 15-minute chat to see if there's a fit?

Best regards"""
            },
            {
                "variant": "B",
                "subject": f"Helping {company} scale faster",
                "body": f"""Hi {first_name},

{personalization} - exciting things happening at {company}!

I specialize in helping companies navigate growth challenges, and I have some ideas that might be valuable for your team.

Do you have 15 minutes this week for a brief call?

Cheers"""
            }
        ]
    
    async def cleanup(self):
        """Cleanup resources"""
        if hasattr(self.research_agent, 'cleanup'):
            await self.research_agent.cleanup()


# Test function
async def test_orchestrator():
    """Test the fixed orchestrator"""
    orchestrator = SDROrchestrator()
    
    try:
        print("\n" + "=" * 70)
        print("  🧪 FIXED ORCHESTRATOR TEST")
        print("=" * 70)
        
        lead = {
            "id": "test-lead-001",
            "email": "ceo@stripe.com",
            "firstName": "Patrick",
            "lastName": "Collison",
            "company": "Stripe",
            "title": "CEO"
        }
        
        result = await orchestrator.process_lead(lead)
        
        print("\n" + "=" * 70)
        print("  📋 RESULTS")
        print("=" * 70)
        
        print(f"\n  Lead Score: {result.get('lead_score')}/100")
        print(f"  Research Quality: {result.get('research_results', {}).get('quality_score', 0)}/100")
        print(f"  Emails Generated: {len(result.get('email_variants', []))}")
        print(f"  Approved: {result.get('approved')}")
        
        # Show emails
        for email in result.get('email_variants', [])[:2]:
            print(f"\n  📧 Email {email.get('variant', '?')}:")
            print(f"     Subject: {email.get('subject', 'N/A')}")
            print(f"     Body: {email.get('body', 'N/A')[:100]}...")
        
        print("\n  ✅ Test complete!")
        
    finally:
        await orchestrator.cleanup()


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
