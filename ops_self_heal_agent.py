"""Ops self-healing agent."""

from __future__ import annotations

from typing import Any, Dict, List

from agentic_mesh.agents.base_agent import BaseAgent


class OpsSelfHealAgent(BaseAgent):
    async def evaluate(self, workspace_id: str, decisions: Dict[str, Any], actions: List[Dict[str, Any]], errors: List[str]) -> Dict[str, Any]:
        extra: List[Dict[str, Any]] = []
        if errors:
            extra.append(
                {
                    "type": "n8n_webhook",
                    "webhook": "webhooks/ops_alert",
                    "payload": {
                        "workspace_id": workspace_id,
                        "errors": errors,
                        "decisions": decisions,
                    },
                }
            )
        return {"actions": extra}


__all__ = ["OpsSelfHealAgent"]