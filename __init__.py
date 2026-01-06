"""GTM OS (Canonical Data Model).

This package defines tool-agnostic objects and semantics used across all customer
modes:

- Notion-first (CRM-lite)
- Hybrid (Notion + point tools)
- Full CRM (HubSpot / Salesforce / other)

Agents and deterministic workflows should communicate using these objects.
"""

from .models import (
    Account,
    Activity,
    AttributionEvent,
    Contact,
    Deal,
    Signal,
    Task,
)
from .workspace import WorkspaceConfig, WorkspaceMode

__all__ = [
    "Account",
    "Activity",
    "AttributionEvent",
    "Contact",
    "Deal",
    "Signal",
    "Task",
    "WorkspaceConfig",
    "WorkspaceMode",
]
