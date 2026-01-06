"""Data hygiene agent.

Detects common data issues and emits cleanup actions.
"""

from __future__ import annotations

from typing import Any, Dict, List

from agentic_mesh.agents.base_agent import BaseAgent


class DataHygieneAgent(BaseAgent):
    async def evaluate(self, workspace_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        actions: List[Dict[str, Any]] = []

        # Example rules; production uses scheduled sweeps.
        email = (payload.get("email") or "").strip().lower()
        domain = (payload.get("domain") or "").strip().lower()
        if email and not domain and "@" in email:
            domain = email.split("@", 1)[1]
            actions.append(
                {
                    "type": "n8n_webhook",
                    "webhook": "webhooks/hygiene_backfill",
                    "payload": {"workspace_id": workspace_id, "domain": domain, "record": payload},
                }
            )

        if payload.get("suspected_duplicate"):
            actions.append(
                {
                    "type": "n8n_webhook",
                    "webhook": "webhooks/dedupe_flag",
                    "payload": {"workspace_id": workspace_id, "record": payload},
                }
            )

        return {"actions": actions}


__all__ = ["DataHygieneAgent"]