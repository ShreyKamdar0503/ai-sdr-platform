"""
AI-Powered Handoff Notes Generation System
Automatically generates comprehensive handoff notes when deals transition between stages

Features:
- SDR → AE handoff notes (Qualified → Discovery)
- AE → AE handoff (Territory change)
- AE → CS handoff (Closed Won → Onboarding)
- Stage-specific requirements and templates
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# For AI generation
try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage
except ImportError:
    ChatOpenAI = None


class HandoffType(Enum):
    """Types of sales handoffs"""
    SDR_TO_AE = "sdr_to_ae"
    AE_TO_AE = "ae_to_ae"
    AE_TO_CS = "ae_to_cs"
    CS_TO_RENEWAL = "cs_to_renewal"
    STAGE_TRANSITION = "stage_transition"


class StageTransition(Enum):
    """Standard stage transitions"""
    NEW_TO_QUALIFIED = "New Lead → Qualified"
    QUALIFIED_TO_DISCOVERY = "Qualified → Discovery"
    DISCOVERY_TO_PROPOSAL = "Discovery → Proposal"
    PROPOSAL_TO_NEGOTIATION = "Proposal → Negotiation"
    NEGOTIATION_TO_WON = "Negotiation → Closed Won"
    ANY_TO_LOST = "Any → Closed Lost"


@dataclass
class HandoffContext:
    """Context for generating handoff notes"""
    deal_id: str
    company: str
    contact_name: str
    contact_title: str
    contact_email: str
    current_stage: str
    new_stage: str
    lead_score: int
    research_summary: str
    engagement_history: List[Dict]
    pain_points: List[str]
    competition: List[str]
    deal_value: float
    win_probability: float
    notes: str
    from_rep: str = None
    to_rep: str = None


class HandoffNotesGenerator:
    """
    Generates AI-powered handoff notes for deal transitions
    """
    
    def __init__(self):
        self.llm = None
        if ChatOpenAI:
            self.llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.3,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        
        self.stage_requirements = {
            "Qualified": {
                "required_info": ["Lead score", "Research summary", "Initial engagement"],
                "next_actions": ["Schedule discovery call", "Send calendar invite"],
                "sla_hours": 24
            },
            "Discovery": {
                "required_info": ["Pain points identified", "Budget discussion", "Timeline", "Decision makers"],
                "next_actions": ["Document discovery findings", "Prepare proposal outline"],
                "sla_hours": 48
            },
            "Proposal": {
                "required_info": ["Proposal sent", "Pricing discussed", "Stakeholders aligned"],
                "next_actions": ["Follow up on proposal", "Address objections"],
                "sla_hours": 72
            },
            "Negotiation": {
                "required_info": ["Terms discussed", "Legal review status", "Final decision maker"],
                "next_actions": ["Send contract", "Schedule signing"],
                "sla_hours": 48
            },
            "Closed Won": {
                "required_info": ["Contract signed", "Implementation timeline", "Success criteria"],
                "next_actions": ["Trigger onboarding", "Assign CSM", "Schedule kickoff"],
                "sla_hours": 24
            }
        }
    
    async def generate_handoff_notes(
        self,
        context: HandoffContext,
        handoff_type: HandoffType = HandoffType.STAGE_TRANSITION
    ) -> Dict:
        """Generate comprehensive handoff notes"""
        generators = {
            HandoffType.SDR_TO_AE: self._generate_sdr_to_ae_notes,
            HandoffType.AE_TO_AE: self._generate_ae_to_ae_notes,
            HandoffType.AE_TO_CS: self._generate_ae_to_cs_notes,
            HandoffType.STAGE_TRANSITION: self._generate_stage_transition_notes
        }
        
        generator = generators.get(handoff_type, self._generate_stage_transition_notes)
        notes = await generator(context)
        
        notes["metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "handoff_type": handoff_type.value,
            "from_stage": context.current_stage,
            "to_stage": context.new_stage,
            "deal_id": context.deal_id
        }
        
        return notes
    
    async def _generate_sdr_to_ae_notes(self, context: HandoffContext) -> Dict:
        """Generate SDR → AE handoff notes"""
        requirements = self.stage_requirements.get(context.new_stage, {})
        
        notes = {
            "header": {
                "title": f"🎯 SDR → AE Handoff: {context.company}",
                "contact": f"{context.contact_name} ({context.contact_title})",
                "email": context.contact_email,
                "lead_score": context.lead_score,
                "deal_value": context.deal_value,
                "assigned_ae": context.to_rep or "TBD"
            },
            "sections": {}
        }
        
        notes["sections"]["executive_summary"] = self._generate_executive_summary(context)
        notes["sections"]["research_summary"] = self._format_research_section(context)
        notes["sections"]["qualification_criteria"] = self._generate_qualification_criteria(context)
        notes["sections"]["engagement_history"] = self._format_engagement_history(context)
        
        notes["sections"]["pain_points"] = {
            "identified_pain_points": context.pain_points or ["To be discovered in first call"],
            "potential_opportunities": self._identify_opportunities(context)
        }
        
        notes["sections"]["competition"] = {
            "known_competitors": context.competition or ["Unknown"],
            "competitive_positioning": self._generate_competitive_positioning(context)
        }
        
        notes["sections"]["recommended_approach"] = await self._generate_recommended_approach(context)
        
        notes["sections"]["next_steps"] = {
            "immediate_actions": requirements.get("next_actions", []),
            "sla_deadline_hours": requirements.get("sla_hours", 24),
            "success_criteria": [
                "Discovery call scheduled within 48 hours",
                "Pain points documented",
                "Decision-making process understood"
            ]
        }
        
        notes["formatted_text"] = self._format_as_text(notes)
        
        if self.llm:
            notes["ai_summary"] = await self._generate_ai_summary(context, "sdr_to_ae")
        
        return notes
    
    async def _generate_ae_to_ae_notes(self, context: HandoffContext) -> Dict:
        """Generate AE → AE handoff notes (territory change)"""
        notes = {
            "header": {
                "title": f"🔄 AE Handoff: {context.company}",
                "contact": f"{context.contact_name} ({context.contact_title})",
                "email": context.contact_email,
                "deal_value": context.deal_value,
                "win_probability": f"{int(context.win_probability * 100)}%",
                "from_ae": context.from_rep or "Unknown",
                "to_ae": context.to_rep or "TBD"
            },
            "sections": {}
        }
        
        notes["sections"]["deal_status"] = {
            "current_stage": context.current_stage,
            "deal_value": context.deal_value,
            "expected_close_date": "TBD",
            "win_probability": context.win_probability,
            "days_in_pipeline": "TBD"
        }
        
        notes["sections"]["relationship_context"] = {
            "primary_contact": context.contact_name,
            "relationship_strength": "Medium" if context.lead_score >= 70 else "Building",
            "key_conversations": context.engagement_history or [],
            "personal_notes": context.notes or "No personal notes recorded"
        }
        
        notes["sections"]["deal_history"] = {
            "how_deal_originated": "AI SDR Outbound",
            "key_milestones": [
                {"date": "TBD", "event": "Initial qualification"},
                {"date": "TBD", "event": f"Moved to {context.current_stage}"}
            ],
            "blockers_encountered": [],
            "objections_raised": []
        }
        
        notes["sections"]["next_steps"] = {
            "immediate_actions": [
                "Send introduction email from new AE",
                "Review all previous communications",
                "Schedule handoff call with prospect"
            ],
            "pending_items": [
                "Proposal follow-up",
                "Technical questions"
            ]
        }
        
        notes["formatted_text"] = self._format_as_text(notes)
        
        return notes
    
    async def _generate_ae_to_cs_notes(self, context: HandoffContext) -> Dict:
        """Generate AE → CS handoff notes (Closed Won)"""
        notes = {
            "header": {
                "title": f"🎉 Deal Won: {context.company} - CS Handoff",
                "contact": f"{context.contact_name} ({context.contact_title})",
                "email": context.contact_email,
                "deal_value": context.deal_value,
                "closing_ae": context.from_rep or "Unknown",
                "assigned_csm": context.to_rep or "TBD"
            },
            "sections": {}
        }
        
        notes["sections"]["deal_overview"] = {
            "company": context.company,
            "contract_value": context.deal_value,
            "contract_term": "12 months",
            "close_date": datetime.now().strftime("%Y-%m-%d"),
            "products_purchased": ["AI SDR Platform"]
        }
        
        notes["sections"]["stakeholders"] = {
            "primary_contact": {
                "name": context.contact_name,
                "title": context.contact_title,
                "email": context.contact_email,
                "role": "Champion / Primary User"
            },
            "executive_sponsor": "TBD - identify during kickoff",
            "technical_contact": "TBD - identify during kickoff"
        }
        
        notes["sections"]["purchase_drivers"] = {
            "primary_pain_points": context.pain_points or ["See notes"],
            "expected_outcomes": [
                "Reduce SDR research time by 80%",
                "Increase reply rates by 3x",
                "Automate CRM data entry"
            ],
            "success_metrics": [
                "Time to first value: 14 days",
                "User adoption: 80% within 30 days",
                "ROI positive: Within 90 days"
            ]
        }
        
        notes["sections"]["implementation"] = {
            "integrations_needed": ["CRM sync", "Email integration"],
            "data_migration": "None required",
            "training_required": ["Admin training", "User training"],
            "timeline": {
                "kickoff": "Within 3 business days",
                "go_live": "Within 14 days",
                "first_review": "30 days post go-live"
            }
        }
        
        notes["sections"]["risks"] = {
            "known_risks": [
                "Champion may have limited time for implementation",
                "May need executive alignment on workflow changes"
            ],
            "mitigation_strategies": [
                "Schedule recurring check-ins",
                "Provide self-service resources"
            ]
        }
        
        notes["sections"]["onboarding_tasks"] = [
            {"task": "Send welcome email", "owner": "CSM", "due": "+1 day", "status": "pending"},
            {"task": "Schedule kickoff call", "owner": "CSM", "due": "+2 days", "status": "pending"},
            {"task": "Provision account", "owner": "Ops", "due": "+1 day", "status": "pending"},
            {"task": "Send training materials", "owner": "CSM", "due": "+3 days", "status": "pending"},
            {"task": "Configure integrations", "owner": "Technical", "due": "+5 days", "status": "pending"},
            {"task": "User training session", "owner": "CSM", "due": "+7 days", "status": "pending"},
            {"task": "Go-live support", "owner": "CSM", "due": "+14 days", "status": "pending"},
            {"task": "30-day check-in", "owner": "CSM", "due": "+30 days", "status": "pending"}
        ]
        
        notes["sections"]["expansion_opportunities"] = {
            "potential_upsells": [
                "Additional user licenses",
                "Premium intelligence features",
                "Custom integrations"
            ],
            "cross_sell_potential": [
                "GTM automation module",
                "Content intelligence suite"
            ],
            "expansion_timeline": "Review at 90-day mark"
        }
        
        notes["formatted_text"] = self._format_as_text(notes)
        
        if self.llm:
            notes["ai_summary"] = await self._generate_ai_summary(context, "ae_to_cs")
        
        return notes
    
    async def _generate_stage_transition_notes(self, context: HandoffContext) -> Dict:
        """Generate generic stage transition notes"""
        requirements = self.stage_requirements.get(context.new_stage, {})
        
        notes = {
            "header": {
                "title": f"📊 Stage Update: {context.company}",
                "transition": f"{context.current_stage} → {context.new_stage}",
                "contact": context.contact_name,
                "deal_value": context.deal_value
            },
            "sections": {}
        }
        
        notes["sections"]["transition_summary"] = {
            "from_stage": context.current_stage,
            "to_stage": context.new_stage,
            "transition_date": datetime.now().isoformat(),
            "triggered_by": "AI SDR System"
        }
        
        notes["sections"]["stage_requirements"] = {
            "required_info": requirements.get("required_info", []),
            "status": "Complete" if context.lead_score >= 70 else "Partial"
        }
        
        notes["sections"]["next_actions"] = {
            "immediate": requirements.get("next_actions", ["Review deal status"]),
            "sla_hours": requirements.get("sla_hours", 24)
        }
        
        notes["formatted_text"] = self._format_as_text(notes)
        
        return notes
    
    def _generate_executive_summary(self, context: HandoffContext) -> Dict:
        """Generate executive summary section"""
        score_rating = "Hot" if context.lead_score >= 80 else "Warm" if context.lead_score >= 60 else "Cool"
        
        return {
            "one_liner": f"{context.contact_name} at {context.company} is a {score_rating} lead (Score: {context.lead_score}/100)",
            "company_overview": context.research_summary[:500] if context.research_summary else "Research pending",
            "deal_potential": {
                "estimated_value": context.deal_value,
                "win_probability": f"{int(context.win_probability * 100)}%",
                "rating": score_rating
            }
        }
    
    def _format_research_section(self, context: HandoffContext) -> Dict:
        """Format research data into sections"""
        return {
            "summary": context.research_summary or "No research available",
            "data_quality": "High" if len(context.research_summary or "") > 200 else "Medium",
            "last_updated": datetime.now().isoformat()
        }
    
    def _generate_qualification_criteria(self, context: HandoffContext) -> Dict:
        """Generate qualification criteria analysis"""
        score = context.lead_score
        
        return {
            "lead_score": score,
            "score_breakdown": {
                "research_quality": "High" if score >= 80 else "Medium",
                "title_seniority": "Decision Maker" if any(t in context.contact_title.lower() for t in ["ceo", "cto", "vp", "director"]) else "Influencer",
                "engagement_level": "Engaged" if context.engagement_history else "New"
            },
            "qualification_status": "Fully Qualified" if score >= 75 else "Partially Qualified",
            "recommendation": "Prioritize" if score >= 80 else "Standard follow-up"
        }
    
    def _format_engagement_history(self, context: HandoffContext) -> Dict:
        """Format engagement history"""
        if not context.engagement_history:
            return {
                "total_touchpoints": 0,
                "timeline": [],
                "last_engagement": "None recorded"
            }
        
        return {
            "total_touchpoints": len(context.engagement_history),
            "timeline": context.engagement_history[-5:],  # Last 5
            "last_engagement": context.engagement_history[-1] if context.engagement_history else None
        }
    
    def _identify_opportunities(self, context: HandoffContext) -> List[str]:
        """Identify potential opportunities based on context"""
        opportunities = []
        
        if context.lead_score >= 80:
            opportunities.append("High-value opportunity - prioritize engagement")
        
        if "hiring" in context.research_summary.lower():
            opportunities.append("Company is growing - position as scale solution")
        
        if "funding" in context.research_summary.lower():
            opportunities.append("Recent funding - budget likely available")
        
        if any(t in context.contact_title.lower() for t in ["ceo", "founder"]):
            opportunities.append("Executive sponsor potential - fast decision possible")
        
        if not opportunities:
            opportunities.append("Standard opportunity - follow discovery process")
        
        return opportunities
    
    def _generate_competitive_positioning(self, context: HandoffContext) -> List[str]:
        """Generate competitive positioning points"""
        positioning = []
        
        for competitor in (context.competition or []):
            comp_lower = competitor.lower()
            if "outreach" in comp_lower:
                positioning.append(f"vs {competitor}: We're 70% cheaper with better AI")
            elif "zoominfo" in comp_lower:
                positioning.append(f"vs {competitor}: Real-time data vs stale database")
            elif "apollo" in comp_lower:
                positioning.append(f"vs {competitor}: 10x deeper research capabilities")
            else:
                positioning.append(f"vs {competitor}: Focus on our unique AI capabilities")
        
        if not positioning:
            positioning.append("No known competitors - focus on value proposition")
        
        return positioning
    
    async def _generate_recommended_approach(self, context: HandoffContext) -> Dict:
        """Generate recommended approach for engagement"""
        approach = {
            "overall_strategy": "Consultative",
            "key_messages": [],
            "talking_points": [],
            "questions_to_ask": [],
            "materials_to_send": []
        }
        
        # Customize based on title
        if "ceo" in context.contact_title.lower() or "founder" in context.contact_title.lower():
            approach["overall_strategy"] = "Executive Briefing"
            approach["key_messages"] = [
                "Focus on ROI and business impact",
                "Keep technical details high-level",
                "Emphasize time-to-value"
            ]
            approach["questions_to_ask"] = [
                "What's your top priority this quarter?",
                "How is pipeline generation impacting growth goals?",
                "What does success look like in 90 days?"
            ]
        elif "vp" in context.contact_title.lower() or "director" in context.contact_title.lower():
            approach["overall_strategy"] = "Strategic Discussion"
            approach["key_messages"] = [
                "Balance ROI with operational details",
                "Discuss team productivity gains",
                "Address scalability concerns"
            ]
            approach["questions_to_ask"] = [
                "How many SDRs are on your team currently?",
                "What's your current tech stack for prospecting?",
                "What's your biggest bottleneck in pipeline generation?"
            ]
        else:
            approach["overall_strategy"] = "Technical Deep-Dive"
            approach["key_messages"] = [
                "Focus on features and capabilities",
                "Discuss integration requirements",
                "Address day-to-day workflow"
            ]
        
        approach["materials_to_send"] = [
            "Product overview deck",
            "Relevant case study",
            "ROI calculator"
        ]
        
        return approach
    
    async def _generate_ai_summary(self, context: HandoffContext, handoff_type: str) -> str:
        """Generate AI-powered summary using LLM"""
        if not self.llm:
            return "AI summary not available"
        
        prompts = {
            "sdr_to_ae": f"""
            Generate a concise, actionable handoff summary for an AE receiving this lead:
            
            Company: {context.company}
            Contact: {context.contact_name}, {context.contact_title}
            Lead Score: {context.lead_score}/100
            Research: {context.research_summary[:500]}
            
            Format as 3-4 bullet points with the most important things the AE needs to know.
            Focus on: Why this is a good lead, what to talk about, and recommended next steps.
            """,
            
            "ae_to_cs": f"""
            Generate a concise onboarding summary for a CSM receiving this new customer:
            
            Company: {context.company}
            Contact: {context.contact_name}, {context.contact_title}
            Deal Value: ${context.deal_value}
            Pain Points: {', '.join(context.pain_points) if context.pain_points else 'See notes'}
            
            Format as 3-4 bullet points with key information for successful onboarding.
            Focus on: Why they bought, what success looks like, and potential risks.
            """
        }
        
        prompt = prompts.get(handoff_type, prompts["sdr_to_ae"])
        
        try:
            messages = [
                SystemMessage(content="You are a sales operations expert. Be concise and actionable."),
                HumanMessage(content=prompt)
            ]
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            return f"AI summary generation failed: {str(e)}"
    
    def _format_as_text(self, notes: Dict) -> str:
        """Format notes as readable text"""
        lines = []
        
        # Header
        header = notes.get("header", {})
        lines.append("=" * 60)
        lines.append(header.get("title", "Handoff Notes"))
        lines.append("=" * 60)
        lines.append("")
        
        for key, value in header.items():
            if key != "title":
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
        lines.append("")
        
        # Sections
        for section_name, section_data in notes.get("sections", {}).items():
            lines.append("-" * 40)
            lines.append(section_name.replace("_", " ").upper())
            lines.append("-" * 40)
            
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    if isinstance(value, list):
                        lines.append(f"\n{key.replace('_', ' ').title()}:")
                        for item in value:
                            if isinstance(item, dict):
                                lines.append(f"  • {json.dumps(item)}")
                            else:
                                lines.append(f"  • {item}")
                    elif isinstance(value, dict):
                        lines.append(f"\n{key.replace('_', ' ').title()}:")
                        for k, v in value.items():
                            lines.append(f"  {k}: {v}")
                    else:
                        lines.append(f"{key.replace('_', ' ').title()}: {value}")
            elif isinstance(section_data, list):
                for item in section_data:
                    if isinstance(item, dict):
                        lines.append(f"  • {item.get('task', item)}")
                    else:
                        lines.append(f"  • {item}")
            else:
                lines.append(str(section_data))
            
            lines.append("")
        
        return "\n".join(lines)


class HandoffNotesManager:
    """
    Manages handoff notes generation and storage
    """
    
    def __init__(self):
        self.generator = HandoffNotesGenerator()
        self.notes_history = []
    
    async def create_handoff(
        self,
        deal_data: Dict,
        research_results: Dict,
        from_stage: str,
        to_stage: str,
        from_rep: str = None,
        to_rep: str = None
    ) -> Dict:
        """
        Create handoff notes from deal and research data
        """
        # Build context
        context = HandoffContext(
            deal_id=deal_data.get("id", "unknown"),
            company=deal_data.get("company", "Unknown"),
            contact_name=f"{deal_data.get('firstName', '')} {deal_data.get('lastName', '')}".strip(),
            contact_title=deal_data.get("title", "Unknown"),
            contact_email=deal_data.get("email", ""),
            current_stage=from_stage,
            new_stage=to_stage,
            lead_score=research_results.get("lead_score", 0),
            research_summary=self._extract_research_summary(research_results),
            engagement_history=deal_data.get("engagement_history", []),
            pain_points=self._extract_pain_points(research_results),
            competition=self._extract_competition(research_results),
            deal_value=deal_data.get("deal_value", 25000),
            win_probability=self._calculate_win_probability(research_results.get("lead_score", 0)),
            notes=deal_data.get("notes", ""),
            from_rep=from_rep,
            to_rep=to_rep
        )
        
        # Determine handoff type
        handoff_type = self._determine_handoff_type(from_stage, to_stage)
        
        # Generate notes
        notes = await self.generator.generate_handoff_notes(context, handoff_type)
        
        # Store in history
        self.notes_history.append({
            "deal_id": context.deal_id,
            "notes": notes,
            "created_at": datetime.now().isoformat()
        })
        
        return notes
    
    def _extract_research_summary(self, research_results: Dict) -> str:
        """Extract research summary from results"""
        parts = []
        
        company_info = research_results.get("research_results", {}).get("company_info", {})
        
        if company_info.get("summary"):
            parts.append(company_info["summary"])
        
        if company_info.get("domain"):
            parts.append(f"Industry: {company_info['domain']}")
        
        if company_info.get("tech_stack"):
            parts.append(f"Tech Stack: {', '.join(company_info['tech_stack'][:3])}")
        
        if company_info.get("hiring_departments"):
            parts.append(f"Hiring in: {', '.join(company_info['hiring_departments'][:3])}")
        
        hooks = research_results.get("research_results", {}).get("hooks", [])
        if hooks:
            parts.append(f"Engagement hooks: {'; '.join(hooks[:2])}")
        
        return " | ".join(parts) if parts else "Research data not available"
    
    def _extract_pain_points(self, research_results: Dict) -> List[str]:
        """Extract potential pain points from research"""
        pain_points = []
        
        company_info = research_results.get("research_results", {}).get("company_info", {})
        
        if company_info.get("hiring_departments"):
            pain_points.append(f"Scaling {', '.join(company_info['hiring_departments'][:2])} teams")
        
        hooks = research_results.get("research_results", {}).get("hooks", [])
        for hook in hooks:
            if any(word in hook.lower() for word in ["struggle", "challenge", "need", "looking"]):
                pain_points.append(hook)
        
        if not pain_points:
            pain_points.append("To be discovered in discovery call")
        
        return pain_points[:5]
    
    def _extract_competition(self, research_results: Dict) -> List[str]:
        """Extract competitive information"""
        company_info = research_results.get("research_results", {}).get("company_info", {})
        tech_stack = company_info.get("tech_stack", [])
        
        competitors = []
        
        competitor_tools = {
            "Outreach": ["outreach"],
            "Salesloft": ["salesloft"],
            "Apollo.io": ["apollo"],
            "ZoomInfo": ["zoominfo"],
            "HubSpot": ["hubspot"]
        }
        
        for tool, keywords in competitor_tools.items():
            if any(kw in str(tech_stack).lower() for kw in keywords):
                competitors.append(tool)
        
        return competitors if competitors else ["Unknown"]
    
    def _calculate_win_probability(self, lead_score: int) -> float:
        """Calculate win probability from lead score"""
        if lead_score >= 90:
            return 0.8
        elif lead_score >= 80:
            return 0.6
        elif lead_score >= 70:
            return 0.5
        elif lead_score >= 60:
            return 0.4
        else:
            return 0.3
    
    def _determine_handoff_type(self, from_stage: str, to_stage: str) -> HandoffType:
        """Determine handoff type from stages"""
        to_lower = to_stage.lower()
        
        if to_lower in ["qualified", "discovery"] and from_stage.lower() in ["new", "new lead"]:
            return HandoffType.SDR_TO_AE
        elif to_lower in ["closed won", "won"]:
            return HandoffType.AE_TO_CS
        else:
            return HandoffType.STAGE_TRANSITION


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

async def example_usage():
    """Example of generating handoff notes"""
    
    manager = HandoffNotesManager()
    
    # Sample deal data
    deal_data = {
        "id": "deal-12345",
        "firstName": "John",
        "lastName": "Smith",
        "email": "john@acme.com",
        "company": "Acme Corp",
        "title": "VP of Sales",
        "deal_value": 50000
    }
    
    # Sample research results
    research_results = {
        "lead_score": 87,
        "research_results": {
            "company_info": {
                "summary": "Acme Corp is a Series B SaaS company focused on developer tools with $20M ARR.",
                "domain": "Technology / SaaS",
                "headquarters": "San Francisco, CA",
                "tech_stack": ["React", "Node.js", "Salesforce", "Outreach"],
                "hiring_departments": ["Engineering", "Sales", "Marketing"],
                "recent_news": [{"title": "Acme raises $30M Series B"}]
            },
            "hooks": [
                "I noticed you're scaling your sales team",
                "Your recent funding suggests growth mode",
                "Your tech stack aligns with our integrations"
            ]
        }
    }
    
    # Generate SDR → AE handoff
    notes = await manager.create_handoff(
        deal_data=deal_data,
        research_results=research_results,
        from_stage="New Lead",
        to_stage="Qualified",
        from_rep="SDR Bot",
        to_rep="Jane AE"
    )
    
    print(notes["formatted_text"])
    print("\n" + "=" * 60 + "\n")
    
    if notes.get("ai_summary"):
        print("AI SUMMARY:")
        print(notes["ai_summary"])
    
    return notes


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
