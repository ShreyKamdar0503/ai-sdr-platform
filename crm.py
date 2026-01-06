"""CRM abstraction.

The platform is CRM-optional. When a customer has a full CRM (HubSpot/Salesforce/etc.),
agents and deterministic workflows should call a CRM adapter.

When a customer has no CRM, these calls can be routed to a Notion-backed adapter.
"""

from __future__ import annotations

from typing import Protocol

from gtm_os import Account, Contact, Deal, Task, Activity


class CRMAdapter(Protocol):
    async def upsert_contact(self, contact: Contact) -> Contact: ...
    async def upsert_account(self, account: Account) -> Account: ...
    async def upsert_deal(self, deal: Deal) -> Deal: ...
    async def create_task(self, task: Task) -> Task: ...
    async def log_activity(self, activity: Activity) -> Activity: ...
