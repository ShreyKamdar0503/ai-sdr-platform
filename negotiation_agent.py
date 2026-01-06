"""
Negotiation Agent - Multi-Agent Consensus (Simplified)

This version works without uagents for easier demo setup.
"""
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

from agentic_mesh.agents.base_agent import BaseAgent


@dataclass
class NegotiationRequest:
    lead_id: str
    agent_bids: Dict[str, float]
    quality_scores: Dict[str, int]
    budget_limit: float


@dataclass 
class NegotiationResponse:
    consensus_reached: bool
    selected_agents: List[str]
    total_cost: float
    rationale: str


class NegotiationAgent(BaseAgent):
    """Simplified Negotiation Agent for resource allocation"""
    
    feature_flag_key = "enable_negotiation_agent"
    
    def __init__(self):
        super().__init__()
        self.budget_per_lead = float(os.getenv("AGENT_MAX_COST_PER_LEAD", "0.25"))
    
    async def run_negotiation(self, state: Dict) -> Dict:
        """Run negotiation to allocate resources among agents"""
        
        lead_id = state.get("lead_id", "unknown")
        lead_score = state.get("lead_score", 50)
        
        # Simulated agent bids (cost per operation)
        agent_bids = {
            "research": 0.05,
            "copywriting": 0.08,
            "timing": 0.02,
            "qualification": 0.02,
        }
        
        # Quality scores based on lead score
        quality_scores = {
            "research": min(lead_score + 10, 100),
            "copywriting": min(lead_score + 5, 100),
            "timing": lead_score,
            "qualification": lead_score,
        }
        
        # Run auction
        result = await self.run_auction(
            NegotiationRequest(
                lead_id=lead_id,
                agent_bids=agent_bids,
                quality_scores=quality_scores,
                budget_limit=self.budget_per_lead
            )
        )
        
        return {
            "consensus_reached": result.consensus_reached,
            "selected_agents": result.selected_agents,
            "total_cost": result.total_cost,
            "rationale": result.rationale,
            "agent_votes": {agent: True for agent in result.selected_agents}
        }
    
    async def run_auction(self, request: NegotiationRequest) -> NegotiationResponse:
        """
        Run a simplified Vickrey auction for agent selection.
        
        Selects agents based on quality/cost ratio within budget.
        """
        # Calculate value ratio for each agent
        value_ratios = {}
        for agent, bid in request.agent_bids.items():
            quality = request.quality_scores.get(agent, 50)
            if bid > 0:
                value_ratios[agent] = quality / bid
            else:
                value_ratios[agent] = quality
        
        # Sort by value ratio (highest first)
        sorted_agents = sorted(value_ratios.items(), key=lambda x: x[1], reverse=True)
        
        # Select agents within budget
        selected = []
        total_cost = 0.0
        
        for agent, ratio in sorted_agents:
            agent_cost = request.agent_bids[agent]
            if total_cost + agent_cost <= request.budget_limit:
                selected.append(agent)
                total_cost += agent_cost
        
        # Determine if consensus reached (at least 2 agents selected)
        consensus = len(selected) >= 2
        
        return NegotiationResponse(
            consensus_reached=consensus,
            selected_agents=selected,
            total_cost=round(total_cost, 4),
            rationale=f"Selected {len(selected)} agents within ${request.budget_limit} budget"
        )


if __name__ == "__main__":
    import asyncio
    
    agent = NegotiationAgent()
    result = asyncio.run(agent.run_negotiation({
        "lead_id": "test-001",
        "lead_score": 75
    }))
    print("✅ Negotiation Agent Test:")
    print(f"   Consensus: {result['consensus_reached']}")
    print(f"   Selected: {result['selected_agents']}")
    print(f"   Cost: ${result['total_cost']}")