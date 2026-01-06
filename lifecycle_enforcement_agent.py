"""Lifecycle enforcement agent.

Blocks stage transitions unless required fields are present.
Execution happens in n8n.
"""

from __future__ import annotations

from typing import Any, Dict, List

from agentic_mesh.agents.base_agent import BaseAgent
from gtm_os.config_store import JSONConfigStore


class LifecycleEnforcementAgent(BaseAgent):
    async def evaluate(self, workspace_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        store = JSONConfigStore()
        cfg = store.load(workspace_id)
        rules: Dict[str, List[str]] = cfg.thresholds.get(
            "definition_of_done",
            {
                "poc": ["problem", "success_criteria"],
                "closed_won": ["signed_date", "amount"],
            },
        )

        stage = str(payload.get("stage") or payload.get("lifecycle_stage") or "").lower()
        required = rules.get(stage, [])
        missing = [f for f in required if not payload.get(f)]

        actions: List[Dict[str, Any]] = []
        if missing:
            actions.append(
                {
                    "type": "n8n_webhook",
                    "webhook": "webhooks/lifecycle_enforce",
                    "payload": {
                        "workspace_id": workspace_id,
                        "stage": stage,
                        "missing_fields": missing,
                        "record": payload,
                    },
                }
            )

        return {"stage": stage, "missing_fields": missing, "actions": actions}


__all__ = ["LifecycleEnforcementAgent"]