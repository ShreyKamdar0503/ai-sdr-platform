"""Classify incoming GTM events.

Normalizes raw triggers (CRM webhooks, Notion webhooks, schedules) into a small
set of categories used by the GTM orchestrator.
"""

from __future__ import annotations

from typing import Any, Dict

from agentic_mesh.agents.base_agent import BaseAgent


class GTMEventClassifierAgent(BaseAgent):
    async def classify(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        et = (event_type or "").lower().strip()

        # Common CRM + Notion + n8n patterns
        if "deal" in et and ("stage" in et or payload.get("stage")):
            return {"category": "deal_stage_changed", "confidence": 0.9}
        if "contact" in et or "lead" in et:
            return {"category": "lead_created_or_updated", "confidence": 0.8}
        if "qa" in et:
            return {"category": "qa_updated", "confidence": 0.9}
        if "go_live" in et or "golive" in et or "go-live" in et:
            return {"category": "go_live", "confidence": 0.95}
        if "weekly" in et or "digest" in et:
            return {"category": "scheduled_digest", "confidence": 0.95}
        if "cleanup" in et or "hygiene" in et:
            return {"category": "scheduled_hygiene", "confidence": 0.9}

        return {"category": "unknown", "confidence": 0.4, "raw": {"event_type": event_type}}


__all__ = ["GTMEventClassifierAgent"]