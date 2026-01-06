"""
Real Integrations - Slack, Notion, n8n
These actually send webhooks and update databases.

Environment Variables Required:
- SLACK_WEBHOOK_URL: Slack incoming webhook URL
- NOTION_API_KEY: Notion integration token
- NOTION_DATABASE_ID: ID of the Notion database for leads
- N8N_WEBHOOK_URL: n8n webhook URL for workflows
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class SlackIntegration:
    """Send notifications to Slack"""
    
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    @property
    def is_configured(self) -> bool:
        return bool(self.webhook_url)
    
    async def send_message(self, message: str, blocks: Optional[List[Dict]] = None) -> Dict:
        """Send a message to Slack"""
        if not self.webhook_url:
            return {"success": False, "error": "SLACK_WEBHOOK_URL not set"}
        
        payload = {"text": message}
        if blocks:
            payload["blocks"] = blocks
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return {"success": True, "status": response.status}
                    else:
                        text = await response.text()
                        return {"success": False, "error": f"Slack returned {response.status}: {text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_lead_notification(self, lead_data: Dict, research: Dict, score: int) -> Dict:
        """Send a formatted lead notification"""
        company = lead_data.get("company", "Unknown")
        name = f"{lead_data.get('firstName', '')} {lead_data.get('lastName', '')}"
        title = lead_data.get("title", "")
        email = lead_data.get("email", "")
        
        quality = research.get("quality_score", 0)
        tech_stack = research.get("tech_stack", [])[:5]
        hiring = research.get("hiring_data", {})
        total_jobs = hiring.get("total_jobs", 0) if isinstance(hiring, dict) else 0
        hooks = research.get("hooks", [])[:2]
        
        # Determine status emoji
        status_emoji = "🔥" if score >= 80 else "✅" if score >= 60 else "📋"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{status_emoji} New Lead: {company}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Contact:*\n{name}"},
                    {"type": "mrkdwn", "text": f"*Title:*\n{title}"},
                    {"type": "mrkdwn", "text": f"*Email:*\n{email}"},
                    {"type": "mrkdwn", "text": f"*Lead Score:*\n{score}/100"},
                ]
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Research Quality:*\n{quality}/100"},
                    {"type": "mrkdwn", "text": f"*Open Jobs:*\n{total_jobs}"},
                ]
            },
        ]
        
        if tech_stack:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Tech Stack:* {', '.join(tech_stack)}"}
            })
        
        if hooks:
            hooks_text = "\n".join([f"• {h[:100]}" for h in hooks])
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Engagement Hooks:*\n{hooks_text}"}
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"🤖 Processed by SDRForge at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
            ]
        })
        
        return await self.send_message(f"New lead from {company}", blocks)
    
    async def send_stage_change(self, lead_data: Dict, from_stage: str, to_stage: str, handoff_notes: str = "") -> Dict:
        """Send a pipeline stage change notification"""
        company = lead_data.get("company", "Unknown")
        name = f"{lead_data.get('firstName', '')} {lead_data.get('lastName', '')}"
        
        stage_emojis = {
            "new": "📥",
            "qualified": "✅",
            "discovery": "🔍",
            "proposal": "📄",
            "negotiation": "🤝",
            "won": "🎉",
            "lost": "❌"
        }
        
        from_emoji = stage_emojis.get(from_stage.lower(), "📋")
        to_emoji = stage_emojis.get(to_stage.lower(), "📋")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔄 Pipeline Update: {company}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{name}* moved from {from_emoji} *{from_stage.title()}* → {to_emoji} *{to_stage.title()}*"
                }
            },
        ]
        
        if handoff_notes:
            # Truncate if too long
            notes_preview = handoff_notes[:500] + "..." if len(handoff_notes) > 500 else handoff_notes
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Handoff Notes:*\n```{notes_preview}```"}
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"🤖 GTMForge Pipeline at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
            ]
        })
        
        return await self.send_message(f"Pipeline update for {company}", blocks)


class NotionIntegration:
    """Create and update records in Notion"""
    
    def __init__(self):
        self.api_key = os.getenv("NOTION_API_KEY")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self.base_url = "https://api.notion.com/v1"
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.database_id)
    
    async def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make a request to Notion API"""
        if not self.api_key:
            return {"success": False, "error": "NOTION_API_KEY not set"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "POST":
                    async with session.post(url, json=data, headers=headers, timeout=15) as response:
                        result = await response.json()
                        if response.status in [200, 201]:
                            return {"success": True, "data": result}
                        else:
                            return {"success": False, "error": result.get("message", str(result))}
                elif method == "PATCH":
                    async with session.patch(url, json=data, headers=headers, timeout=15) as response:
                        result = await response.json()
                        if response.status == 200:
                            return {"success": True, "data": result}
                        else:
                            return {"success": False, "error": result.get("message", str(result))}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_lead(self, lead_data: Dict, research: Dict, score: int) -> Dict:
        """Create a new lead in Notion database"""
        if not self.database_id:
            return {"success": False, "error": "NOTION_DATABASE_ID not set"}
        
        company = lead_data.get("company", "Unknown")
        name = f"{lead_data.get('firstName', '')} {lead_data.get('lastName', '')}"
        email = lead_data.get("email", "")
        title = lead_data.get("title", "")
        website = lead_data.get("website", "")
        
        quality = research.get("quality_score", 0)
        tech_stack = research.get("tech_stack", [])
        hiring = research.get("hiring_data", {})
        total_jobs = hiring.get("total_jobs", 0) if isinstance(hiring, dict) else 0
        
        # Build Notion page properties
        properties = {
            "Name": {
                "title": [{"text": {"content": name}}]
            },
            "Company": {
                "rich_text": [{"text": {"content": company}}]
            },
            "Email": {
                "email": email
            },
            "Title": {
                "rich_text": [{"text": {"content": title}}]
            },
            "Lead Score": {
                "number": score
            },
            "Research Quality": {
                "number": quality
            },
            "Stage": {
                "select": {"name": "New"}
            },
            "Open Jobs": {
                "number": total_jobs
            },
        }
        
        # Add website if provided
        if website:
            properties["Website"] = {"url": website}
        
        # Add tech stack as multi-select if not too many
        if tech_stack and len(tech_stack) <= 10:
            properties["Tech Stack"] = {
                "multi_select": [{"name": t[:100]} for t in tech_stack[:10]]
            }
        
        data = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }
        
        result = await self._request("POST", "pages", data)
        
        if result.get("success"):
            return {
                "success": True,
                "page_id": result["data"].get("id"),
                "url": result["data"].get("url")
            }
        return result
    
    async def update_lead_stage(self, page_id: str, new_stage: str, notes: str = "") -> Dict:
        """Update a lead's pipeline stage"""
        properties = {
            "Stage": {
                "select": {"name": new_stage}
            }
        }
        
        if notes:
            properties["Handoff Notes"] = {
                "rich_text": [{"text": {"content": notes[:2000]}}]  # Notion limit
            }
        
        return await self._request("PATCH", f"pages/{page_id}", {"properties": properties})


class N8NIntegration:
    """Trigger n8n workflows via webhooks"""
    
    def __init__(self):
        self.webhook_url = os.getenv("N8N_WEBHOOK_URL")
    
    @property
    def is_configured(self) -> bool:
        return bool(self.webhook_url)
    
    async def trigger_webhook(self, event_type: str, payload: Dict) -> Dict:
        """Trigger an n8n webhook with event data"""
        if not self.webhook_url:
            return {"success": False, "error": "N8N_WEBHOOK_URL not set"}
        
        data = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "source": "forge_ai",
            "payload": payload
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                ) as response:
                    if response.status in [200, 201, 204]:
                        try:
                            result = await response.json()
                        except:
                            result = {"status": "ok"}
                        return {"success": True, "response": result}
                    else:
                        text = await response.text()
                        return {"success": False, "error": f"n8n returned {response.status}: {text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def trigger_lead_processed(self, lead_data: Dict, research: Dict, score: int) -> Dict:
        """Trigger workflow for new lead processed"""
        payload = {
            "lead": lead_data,
            "research_summary": {
                "quality_score": research.get("quality_score", 0),
                "tech_stack": research.get("tech_stack", []),
                "hiring_total": research.get("hiring_data", {}).get("total_jobs", 0) if isinstance(research.get("hiring_data"), dict) else 0,
                "hooks": research.get("hooks", [])
            },
            "lead_score": score,
            "qualified": score >= 60
        }
        return await self.trigger_webhook("lead_processed", payload)
    
    async def trigger_stage_change(self, lead_data: Dict, from_stage: str, to_stage: str) -> Dict:
        """Trigger workflow for pipeline stage change"""
        payload = {
            "lead": lead_data,
            "from_stage": from_stage,
            "to_stage": to_stage
        }
        return await self.trigger_webhook("stage_change", payload)


class IntegrationOrchestrator:
    """Orchestrate all integrations"""
    
    def __init__(self):
        self.slack = SlackIntegration()
        self.notion = NotionIntegration()
        self.n8n = N8NIntegration()
    
    def get_status(self) -> Dict:
        """Get configuration status of all integrations"""
        return {
            "slack": {
                "configured": self.slack.is_configured,
                "webhook_set": bool(os.getenv("SLACK_WEBHOOK_URL"))
            },
            "notion": {
                "configured": self.notion.is_configured,
                "api_key_set": bool(os.getenv("NOTION_API_KEY")),
                "database_id_set": bool(os.getenv("NOTION_DATABASE_ID"))
            },
            "n8n": {
                "configured": self.n8n.is_configured,
                "webhook_set": bool(os.getenv("N8N_WEBHOOK_URL"))
            }
        }
    
    async def process_new_lead(self, lead_data: Dict, research: Dict, score: int) -> Dict:
        """Process a new lead through all integrations"""
        results = {
            "slack": {"triggered": False},
            "notion": {"triggered": False},
            "n8n": {"triggered": False}
        }
        
        # Run all integrations in parallel
        tasks = []
        
        if self.slack.is_configured:
            tasks.append(("slack", self.slack.send_lead_notification(lead_data, research, score)))
        
        if self.notion.is_configured:
            tasks.append(("notion", self.notion.create_lead(lead_data, research, score)))
        
        if self.n8n.is_configured:
            tasks.append(("n8n", self.n8n.trigger_lead_processed(lead_data, research, score)))
        
        if tasks:
            task_results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
            
            for i, (name, _) in enumerate(tasks):
                result = task_results[i]
                if isinstance(result, Exception):
                    results[name] = {"triggered": False, "error": str(result)}
                else:
                    results[name] = {"triggered": True, **result}
        
        return results
    
    async def process_stage_change(self, lead_data: Dict, from_stage: str, to_stage: str, handoff_notes: str = "") -> Dict:
        """Process a pipeline stage change through all integrations"""
        results = {
            "slack": {"triggered": False},
            "notion": {"triggered": False},
            "n8n": {"triggered": False}
        }
        
        tasks = []
        
        if self.slack.is_configured:
            tasks.append(("slack", self.slack.send_stage_change(lead_data, from_stage, to_stage, handoff_notes)))
        
        if self.n8n.is_configured:
            tasks.append(("n8n", self.n8n.trigger_stage_change(lead_data, from_stage, to_stage)))
        
        if tasks:
            task_results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
            
            for i, (name, _) in enumerate(tasks):
                result = task_results[i]
                if isinstance(result, Exception):
                    results[name] = {"triggered": False, "error": str(result)}
                else:
                    results[name] = {"triggered": True, **result}
        
        return results


# Singleton instance
integrations = IntegrationOrchestrator()
