"""n8n execution gateway.

We keep *execution* deterministic in n8n. Agents decide what to do, but n8n does
the actual record updates, retries, and side effects.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx


class N8NGateway:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = (base_url or os.getenv("N8N_BASE_URL") or "").rstrip("/")
        self.api_key = api_key or os.getenv("N8N_API_KEY")

    async def trigger_webhook(
        self,
        webhook_path: str,
        payload: Dict[str, Any],
        timeout_s: int = 30,
    ) -> Dict[str, Any]:
        """Trigger a webhook workflow.

        webhook_path can be either a full URL or a path under N8N_BASE_URL.
        """
        if webhook_path.startswith("http"):
            url = webhook_path
        else:
            if not self.base_url:
                raise ValueError("N8N_BASE_URL is not set")
            url = f"{self.base_url}/{webhook_path.lstrip('/')}"

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key

        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json() if resp.content else {"ok": True}
