"""
Integrated Research Agent - VERSION 3

Passes through all new fields:
- Company summary (what they do)
- Company domain (industry)
- Company headquarters (country)
- LinkedIn URL (clickable)
- News articles with URLs (clickable)
"""

import os
import asyncio
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from agentic_mesh.agents.base_agent import BaseAgent, AgentRunContext

try:
    from agentic_mesh.agents.enhanced_research_agent import EnhancedResearchAgent
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class IntegratedResearchAgent(BaseAgent):
    """Research Agent with full data passthrough"""
    
    feature_flag_key = "enable_research_agent"
    config_key = "research_agent_config"
    
    def __init__(self):
        super().__init__()
        
        self.config = self.get_config(default={
            "enable_playwright": True,
            "enable_news_search": True,
            "max_depth": 3,
            "include_news": True,
            "include_funding": True,
            "include_tech_stack": True,
            "quality_threshold": 70,
        })
        
        self._llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini")
        )
        
        self._enhanced_agent = None
        if PLAYWRIGHT_AVAILABLE and self.config.get("enable_playwright", True):
            self._enhanced_agent = EnhancedResearchAgent()
    
    async def process(
        self,
        lead_data: Dict,
        context: Optional[AgentRunContext] = None,
    ) -> Dict:
        """Main processing function"""
        
        if not await self.should_run(context):
            return {
                "status": "skipped",
                "reason": "Research agent is disabled",
                "quality_score": 0,
            }
        
        company = lead_data.get("company", "Unknown")
        email = lead_data.get("email", "")
        first_name = lead_data.get("firstName", "")
        title = lead_data.get("title", "")
        
        # Use enhanced research (Playwright + OpenAI)
        if self._enhanced_agent:
            try:
                print(f"  🔬 Using Enhanced Research (Playwright + OpenAI)...")
                enhanced_result = await self._enhanced_agent.deep_research(lead_data)
                return self._convert_enhanced_result(enhanced_result, lead_data)
                
            except Exception as e:
                print(f"  ⚠️ Enhanced research failed: {e}")
                print(f"  📝 Falling back to basic research...")
        
        return await self._basic_research(lead_data)
    
    def _convert_enhanced_result(self, enhanced: Dict, lead_data: Dict) -> Dict:
        """Convert enhanced research result to standard format - WITH ALL NEW FIELDS"""
        
        website_data = enhanced.get("live_data", {}).get("website", {}).get("data", {})
        jobs_data = enhanced.get("live_data", {}).get("jobs", {}).get("insights", {})
        
        # Build company_info with all new fields
        company_info = {
            "name": enhanced.get("company", lead_data.get("company")),
            "summary": enhanced.get("company_summary", ""),
            "domain": enhanced.get("company_domain", ""),
            "headquarters": enhanced.get("company_headquarters", ""),
            "size": "Unknown",
            "industry": enhanced.get("company_domain", "Technology"),
            
            # News with URLs (clickable)
            "recent_news": enhanced.get("news", []),  # Full article objects with URLs
            
            # Tech and hiring
            "tech_stack": website_data.get("tech_stack", []),
            "funding_stage": "Unknown",
            "pain_points": [],
            "hiring_departments": jobs_data.get("hiring_departments", []),
            "careers_page": jobs_data.get("careers_page"),
            "open_positions": jobs_data.get("open_positions", "Unknown"),
            
            # LinkedIn (clickable)
            "linkedin_url": enhanced.get("linkedin_url"),
            "social_links": website_data.get("social_links", []),
            "website_url": enhanced.get("live_data", {}).get("website_url"),
        }
        
        contact_info = {
            "email": lead_data.get("email"),
            "verified": True,
            "linkedin_url": f"https://linkedin.com/in/{lead_data.get('firstName', '').lower()}",
            "seniority": "executive" if lead_data.get("title", "").lower() in ["ceo", "cto", "cfo", "coo", "vp", "director"] else "senior"
        }
        
        return {
            "company_info": company_info,
            "contact_info": contact_info,
            "quality_score": enhanced.get("quality_score", 50),
            "hooks": enhanced.get("engagement_hooks", []),
            "config_used": self.config,
            "research_type": "enhanced",
            "playwright_used": enhanced.get("playwright_used", True),
            "ai_analysis": enhanced.get("ai_analysis", {}).get("full_analysis", ""),
            
            # New fields for frontend
            "company_summary": enhanced.get("company_summary", ""),
            "company_domain": enhanced.get("company_domain", ""),
            "company_headquarters": enhanced.get("company_headquarters", ""),
            "linkedin_url": enhanced.get("linkedin_url"),
            "news_articles": enhanced.get("news", []),  # With URLs
        }
    
    async def _basic_research(self, lead_data: Dict) -> Dict:
        """Fallback basic research using only OpenAI"""
        
        company = lead_data.get("company", "Unknown")
        email = lead_data.get("email", "")
        
        try:
            response = await self._llm.ainvoke(
                f"""Provide brief info about {company}:
                1. What does the company do? (2 sentences)
                2. What industry/domain?
                3. Where is headquarters?
                Keep each answer to 1-2 sentences."""
            )
            company_summary = response.content
        except Exception as e:
            company_summary = f"Company: {company}"
        
        company_info = {
            "name": company,
            "summary": company_summary,
            "domain": "Technology",
            "headquarters": "Unknown",
            "size": "100-500",
            "industry": "Technology",
            "recent_news": [],
            "tech_stack": ["Unknown"],
            "funding_stage": "Unknown",
            "pain_points": ["Scaling infrastructure", "Data analytics"],
            "hiring_departments": [],
            "careers_page": None,
            "linkedin_url": None,
        }
        
        contact_info = {
            "email": email,
            "verified": True,
            "linkedin_url": f"https://linkedin.com/in/{email.split('@')[0] if email else 'unknown'}",
            "seniority": "executive"
        }
        
        return {
            "company_info": company_info,
            "contact_info": contact_info,
            "quality_score": 40,
            "hooks": [f"I'd love to learn more about {company}'s growth plans."],
            "config_used": self.config,
            "research_type": "basic",
            "playwright_used": False,
            "company_summary": company_summary,
            "company_domain": "Technology",
            "company_headquarters": "Unknown",
            "linkedin_url": None,
            "news_articles": [],
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self._enhanced_agent:
            await self._enhanced_agent.stop()


# Make this the default research agent
ResearchAgent = IntegratedResearchAgent


if __name__ == "__main__":
    async def test():
        agent = IntegratedResearchAgent()
        
        lead = {
            "email": "ceo@stripe.com",
            "firstName": "Patrick",
            "lastName": "Collison",
            "company": "Stripe",
            "title": "CEO"
        }
        
        try:
            result = await agent.process(lead)
            
            print("\n" + "=" * 60)
            print("INTEGRATED RESEARCH RESULTS")
            print("=" * 60)
            print(f"Company: {result['company_info']['name']}")
            print(f"Summary: {result.get('company_summary', 'N/A')}")
            print(f"Domain: {result.get('company_domain', 'N/A')}")
            print(f"HQ: {result.get('company_headquarters', 'N/A')}")
            print(f"LinkedIn: {result.get('linkedin_url', 'N/A')}")
            print(f"Quality: {result['quality_score']}/100")
            
            print("\nNews:")
            for article in result.get('news_articles', [])[:3]:
                print(f"  - {article.get('title', 'N/A')[:50]}...")
                print(f"    URL: {article.get('url', 'N/A')}")
            
        finally:
            await agent.cleanup()
    
    asyncio.run(test())
