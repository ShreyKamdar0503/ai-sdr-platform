"""Listmonk Email Client"""
import os
import aiohttp

class ListmonkClient:
    def __init__(self):
        self.api_url = os.getenv("LISTMONK_API_URL")
        self.auth = (
            os.getenv("LISTMONK_USERNAME"),
            os.getenv("LISTMONK_PASSWORD")
        )
    
    async def schedule_email(self, email_data, send_at):
        """Schedule email for sending"""
        # Would call Listmonk API
        return {"scheduled": True, "send_at": send_at}
