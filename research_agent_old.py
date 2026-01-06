"""
Research Agent - Company & Lead Intelligence
"""
import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI

from agentic_mesh.agents.base_agent import BaseAgent, AgentRunContext


class ResearchAgent(BaseAgent):
    """Research Agent with feature flags and dynamic configs"""
    
    # GrowthBook integration
    feature_flag_key = "enable_research_agent"
    config_key = "research_agent_config"
    
    def __init__(self):
        super().__init__()
        
        # Get dynamic config for research parameters
        self.config = self.get_config(default={
            "max_depth": 3,
            "include_news": True,
            "include_funding": True,
            "include_tech_stack": True,
            "quality_threshold": 70,
        })
        
        # Use the parent's LLM or create one
        self._research_llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini")
        )
    
    async def process(
        self,
        lead_data: Dict,
        context: Optional[AgentRunContext] = None,
    ) -> Dict:
        """Main processing function with feature flag check"""
        
        # Check if agent is enabled
        if not await self.should_run(context):
            return {
                "status": "skipped",
                "reason": "Research agent is disabled",
                "quality_score": 0,
            }
        
        company = lead_data.get("company")
        email = lead_data.get("email")
        
        # Research company
        company_info = await self.research_company(company)
        
        # Enrich contact
        contact_info = await self.enrich_contact(email)
        
        # Calculate quality score
        quality_score = self.calculate_quality(company_info, contact_info)
        
        return {
            "company_info": company_info,
            "contact_info": contact_info,
            "quality_score": quality_score,
            "hooks": self.extract_hooks(company_info),
            "config_used": self.config,
        }
    
    async def research_company(self, company_name: str, max_depth: int = 3) -> Dict:
        """Research company using LLM"""
        try:
            response = await self._research_llm.ainvoke(
                f"Provide brief company info for {company_name}: industry, size, and recent news. Keep it to 2-3 sentences."
            )
            company_summary = response.content
        except Exception as e:
            company_summary = f"Company: {company_name}"
        
        result = {
            "name": company_name,
            "summary": company_summary,
            "size": "100-500",
            "industry": "Technology",
        }
        
        # Conditionally include based on config
        if self.config.get("include_news", True):
            result["recent_news"] = ["Recent company activity"]
        
        if self.config.get("include_tech_stack", True):
            result["tech_stack"] = ["Python", "React", "AWS"]
        
        if self.config.get("include_funding", True):
            result["funding_stage"] = "Series B"
        
        result["pain_points"] = ["Scaling infrastructure", "Data analytics"]
        
        return result
    
    async def enrich_contact(self, email: str) -> Dict:
        """Enrich contact information"""
        return {
            "email": email,
            "verified": True,
            "linkedin_url": f"https://linkedin.com/in/{email.split('@')[0]}",
            "seniority": "executive"
        }
    
    def calculate_quality(self, company_info: Dict, contact_info: Dict) -> int:
        """Calculate research quality score (0-100)"""
        score = 0
        
        # Company data completeness
        if company_info.get("recent_news"):
            score += 30
        if company_info.get("tech_stack"):
            score += 20
        if company_info.get("pain_points"):
            score += 20
        
        # Contact data quality
        if contact_info.get("verified"):
            score += 20
        if contact_info.get("linkedin_url"):
            score += 10
        
        return min(score, 100)
    
    def extract_hooks(self, company_info: Dict) -> list:
        """Extract engagement hooks from research"""
        hooks = []
        
        if company_info.get("recent_news"):
            hooks.append(f"Recent news: {company_info['recent_news'][0]}")
        
        if company_info.get("tech_stack"):
            hooks.append(f"Tech stack includes {company_info['tech_stack'][0]}")
        
        if company_info.get("funding_stage"):
            hooks.append(f"Currently at {company_info['funding_stage']} stage")
        
        return hooks[:3]


if __name__ == "__main__":
    agent = ResearchAgent()
    print("✅ Research Agent initialized")