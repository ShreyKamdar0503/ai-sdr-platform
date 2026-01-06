"""Routing and SLA enforcement agent.

Decisioning only. n8n executes updates and timers.
"""

from __future__ import annotations

from typing import Any, Dict, List

from agentic_mesh.agents.base_agent import BaseAgent
from gtm_os.config_store import JSONConfigStore


class RoutingSLAAgent(BaseAgent):
    async def evaluate(
        self,
        workspace_id: str,
        decisions: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        store = JSONConfigStore()
        cfg = store.load(workspace_id)

        category = (decisions.get("event") or {}).get("category")
        actions: List[Dict[str, Any]] = []

        if category in {"lead_created_or_updated", "unknown"}:
            # Simple routing rule v1: use ICP score if present, else default owner
            icp_score = int(payload.get("icp_score") or 0)
            owner = cfg.routing.get("high_fit_owner") if icp_score >= 70 else cfg.routing.get("default_owner")
            actions.append(
                {
                    "type": "n8n_webhook",
                    "webhook": "webhooks/route_and_sla",
                    "payload": {
                        "workspace_id": workspace_id,
                        "owner": owner,
                        "icp_score": icp_score,
                        "record": payload,
                    },
                }
            )

        return {"actions": actions}


__all__ = ["RoutingSLAAgent"]