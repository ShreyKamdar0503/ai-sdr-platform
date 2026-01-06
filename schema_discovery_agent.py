"""Schema discovery and provisioning agent.

Ensures a workspace has the minimum schema required to run plays.

In v1, this agent emits provisioning actions that are executed by deterministic
workflows (n8n) rather than mutating tools directly.
"""

from __future__ import annotations

from typing import Any, Dict, List

from agentic_mesh.agents.base_agent import BaseAgent
from gtm_os.config_store import JSONConfigStore


MIN_REQUIRED_IDS = {
    "notion_contacts_db",
    "notion_accounts_db",
    "notion_deals_db",
    "notion_tasks_db",
    "slack_ops_channel",
}


class SchemaDiscoveryAgent(BaseAgent):
    async def ensure_workspace_schema(self, workspace_id: str) -> Dict[str, Any]:
        store = JSONConfigStore()
        cfg = store.load(workspace_id)

        missing = sorted(list(MIN_REQUIRED_IDS - set(cfg.ids.keys())))
        actions: List[Dict[str, Any]] = []
        if missing:
            actions.append(
                {
                    "type": "n8n_webhook",
                    "webhook": "webhooks/provision_schema",
                    "payload": {
                        "workspace_id": workspace_id,
                        "mode": cfg.mode,
                        "missing_ids": missing,
                    },
                }
            )

        return {
            "missing_ids": missing,
            "actions": actions,
            "notes": "Provisioning runs via deterministic n8n workflow.",
        }


__all__ = ["SchemaDiscoveryAgent"]