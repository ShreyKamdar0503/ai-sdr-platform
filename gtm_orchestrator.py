"""GTM / RevOps Orchestrator (LangGraph).

This orchestrator is separate from the outbound SDR flow. It is designed to run
"plays" in response to events (webhooks, schedules, CRM updates, Notion updates).

Design principle:
  - Agents decide (classify, recommend, configure, approve)
  - n8n executes (writes to tools, retries, idempotency)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover
    # Keep the repo runnable even if langgraph isn't installed.
    END = "__end__"  # type: ignore
    StateGraph = None  # type: ignore


class GTMState(TypedDict):
    workspace_id: str
    event_type: str
    event_payload: Dict[str, Any]
    decisions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    approved: bool
    errors: List[str]
    timestamp: datetime


class GTMOrchestrator:
    """Routes events to play-specific agents and emits actions for n8n."""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        if StateGraph is None:
            return None

        wf = StateGraph(GTMState)
        wf.add_node("classify", self.classify_event)
        wf.add_node("schema", self.schema_discovery)
        wf.add_node("routing", self.routing_sla)
        wf.add_node("lifecycle", self.lifecycle_enforcement)
        wf.add_node("hygiene", self.data_hygiene)
        wf.add_node("onboarding", self.onboarding_go_live)
        wf.add_node("reporting", self.reporting_attribution)
        wf.add_node("ops", self.ops_self_heal)

        wf.set_entry_point("classify")

        wf.add_edge("classify", "schema")
        wf.add_edge("schema", "routing")
        wf.add_edge("routing", "lifecycle")
        wf.add_edge("lifecycle", "hygiene")

        # Only run onboarding/reporting when event warrants it
        wf.add_conditional_edges(
            "hygiene",
            self._needs_onboarding,
            {"onboarding": "onboarding", "reporting": "reporting"},
        )

        wf.add_edge("onboarding", "reporting")
        wf.add_edge("reporting", "ops")
        wf.add_edge("ops", END)
        return wf.compile()

    async def classify_event(self, state: GTMState) -> GTMState:
        from agentic_mesh.agents.gtm_event_classifier import GTMEventClassifierAgent

        agent = GTMEventClassifierAgent()
        decision = await agent.classify(state["event_type"], state["event_payload"])
        state["decisions"]["event"] = decision
        return state

    async def schema_discovery(self, state: GTMState) -> GTMState:
        from agentic_mesh.agents.schema_discovery_agent import SchemaDiscoveryAgent

        agent = SchemaDiscoveryAgent()
        decision = await agent.ensure_workspace_schema(state["workspace_id"])
        state["decisions"]["schema"] = decision
        state["actions"].extend(decision.get("actions", []))
        return state

    async def routing_sla(self, state: GTMState) -> GTMState:
        from agentic_mesh.agents.routing_sla_agent import RoutingSLAAgent

        agent = RoutingSLAAgent()
        decision = await agent.evaluate(state["workspace_id"], state["decisions"], state["event_payload"])
        state["decisions"]["routing"] = decision
        state["actions"].extend(decision.get("actions", []))
        return state

    async def lifecycle_enforcement(self, state: GTMState) -> GTMState:
        from agentic_mesh.agents.lifecycle_enforcement_agent import LifecycleEnforcementAgent

        agent = LifecycleEnforcementAgent()
        decision = await agent.evaluate(state["workspace_id"], state["event_payload"])
        state["decisions"]["lifecycle"] = decision
        state["actions"].extend(decision.get("actions", []))
        return state

    async def data_hygiene(self, state: GTMState) -> GTMState:
        from agentic_mesh.agents.data_hygiene_agent import DataHygieneAgent

        agent = DataHygieneAgent()
        decision = await agent.evaluate(state["workspace_id"], state["event_payload"])
        state["decisions"]["hygiene"] = decision
        state["actions"].extend(decision.get("actions", []))
        return state

    async def onboarding_go_live(self, state: GTMState) -> GTMState:
        from agentic_mesh.agents.onboarding_go_live_agent import OnboardingGoLiveAgent

        agent = OnboardingGoLiveAgent()
        decision = await agent.evaluate(state["workspace_id"], state["event_payload"])
        state["decisions"]["onboarding"] = decision
        state["actions"].extend(decision.get("actions", []))
        return state

    async def reporting_attribution(self, state: GTMState) -> GTMState:
        from agentic_mesh.agents.reporting_attribution_agent import ReportingAttributionAgent

        agent = ReportingAttributionAgent()
        decision = await agent.evaluate(state["workspace_id"], state["event_type"], state["event_payload"])
        state["decisions"]["reporting"] = decision
        state["actions"].extend(decision.get("actions", []))
        return state

    async def ops_self_heal(self, state: GTMState) -> GTMState:
        from agentic_mesh.agents.ops_self_heal_agent import OpsSelfHealAgent

        agent = OpsSelfHealAgent()
        decision = await agent.evaluate(state["workspace_id"], state["decisions"], state["actions"], state["errors"])
        state["decisions"]["ops"] = decision
        state["actions"].extend(decision.get("actions", []))
        return state

    def _needs_onboarding(self, state: GTMState) -> str:
        evt = state["decisions"].get("event", {})
        if evt.get("category") in {"deal_stage_changed", "qa_updated", "go_live"}:
            return "onboarding"
        return "reporting"

    async def handle_event(self, workspace_id: str, event_type: str, event_payload: Dict[str, Any]) -> Dict[str, Any]:
        initial: GTMState = {
            "workspace_id": workspace_id,
            "event_type": event_type,
            "event_payload": event_payload,
            "decisions": {},
            "actions": [],
            "approved": False,
            "errors": [],
            "timestamp": datetime.utcnow(),
        }
        if self.graph is None:
            # Fallback sequential execution (no LangGraph)
            state = await self.classify_event(initial)
            state = await self.schema_discovery(state)
            state = await self.routing_sla(state)
            state = await self.lifecycle_enforcement(state)
            state = await self.data_hygiene(state)
            if self._needs_onboarding(state) == "onboarding":
                state = await self.onboarding_go_live(state)
            state = await self.reporting_attribution(state)
            state = await self.ops_self_heal(state)
            return state

        return await self.graph.ainvoke(initial)


__all__ = ["GTMOrchestrator", "GTMState"]
