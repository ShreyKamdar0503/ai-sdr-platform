"""Onboarding + QA + Go-Live readiness agent.

Bridges post-sale implementation workflows. Emits actions for:
- creating onboarding tasks
- updating QA status
- go-live handoff
"""

from __future__ import annotations

from typing import Any, Dict, List

from agentic_mesh.agents.base_agent import BaseAgent


class OnboardingGoLiveAgent(BaseAgent):
    async def evaluate(self, workspace_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        actions: List[Dict[str, Any]] = []

        # Simple trigger: when stage becomes 'poc' or 'go_live'
        stage = str(payload.get("stage") or "").lower()
        if stage in {"poc", "implementation", "onboarding"}:
            actions.append(
                {
                    "type": "n8n_webhook",
                    "webhook": "webhooks/create_onboarding_tasks",
                    "payload": {"workspace_id": workspace_id, "record": payload},
                }
            )

        if payload.get("qa_score") is not None:
            actions.append(
                {
                    "type": "n8n_webhook",
                    "webhook": "webhooks/update_qa_metrics",
                    "payload": {"workspace_id": workspace_id, "record": payload},
                }
            )

        if stage in {"go_live", "golive", "live"}:
            actions.append(
                {
                    "type": "n8n_webhook",
                    "webhook": "webhooks/go_live_handoff",
                    "payload": {"workspace_id": workspace_id, "record": payload},
                }
            )

        return {"actions": actions}


__all__ = ["OnboardingGoLiveAgent"]