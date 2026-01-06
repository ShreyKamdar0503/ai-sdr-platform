"""Reporting and attribution agent."""

from __future__ import annotations

from typing import Any, Dict, List

from agentic_mesh.agents.base_agent import BaseAgent


class ReportingAttributionAgent(BaseAgent):
    async def evaluate(self, workspace_id: str, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        actions: List[Dict[str, Any]] = []

        et = (event_type or "").lower()
        if "weekly" in et or "digest" in et:
            actions.append(
                {
                    "type": "n8n_webhook",
                    "webhook": "webhooks/weekly_digest",
                    "payload": {"workspace_id": workspace_id},
                }
            )
        if payload.get("deal_id") or payload.get("stage"):
            actions.append(
                {
                    "type": "n8n_webhook",
                    "webhook": "webhooks/update_velocity_and_attribution",
                    "payload": {"workspace_id": workspace_id, "record": payload},
                }
            )

        return {"actions": actions}


__all__ = ["ReportingAttributionAgent"]