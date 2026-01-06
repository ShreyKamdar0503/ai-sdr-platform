"""Workspace configuration (per customer / tenant).

This config is the *single source of truth* for runtime wiring.
No workflow or agent should hardcode tool-specific IDs.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

class WorkspaceMode(str, Enum):
    notion_first = "notion_first"
    hybrid = "hybrid"
    full_crm = "full_crm"
    saas = "saas"
    paas = "paas"


class WorkspaceConfig(BaseModel):
    """Tenant configuration.

    In production, this would typically live in Postgres/Supabase and be loaded
    by ID. For v1, it can also be stored in Notion or a config file.
    """

    workspace_id: str
    name: str
    mode: WorkspaceMode

    # Tool connection hints (do not store secrets here)
    crm_type: Optional[str] = Field(
        default=None, description="hubspot | salesforce | twenty | custom | none"
    )
    notion_enabled: bool = True
    slack_enabled: bool = True
    n8n_enabled: bool = True

    # Tool-specific IDs, database IDs, pipeline IDs, channel IDs, etc.
    ids: Dict[str, str] = Field(default_factory=dict)

    # Field/property mapping between tools and canonical GTM OS
    field_map: Dict[str, str] = Field(default_factory=dict)

    # Play toggles & thresholds
    plays_enabled: Dict[str, bool] = Field(default_factory=dict)
    thresholds: Dict[str, Any] = Field(default_factory=dict)

    # Default routing owners / teams
    routing: Dict[str, Any] = Field(default_factory=dict)
