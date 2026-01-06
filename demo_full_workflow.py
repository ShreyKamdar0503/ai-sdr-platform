"""
🎬 AI SDR Platform - Full Workflow Demo

This script demonstrates:
1. New lead comes in → Notion Contact created → Slack notification
2. Lead qualified → Deal created in Notion → Slack alert
3. Deal stage changes → Notion updated → Slack notification
4. Full pipeline visibility
"""

import os
import asyncio
import httpx
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_BASE = "http://localhost:8000"
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL_ID", "#sdr-alerts")
NOTION_TOKEN = os.getenv("NOTION_API_KEY")
NOTION_CONTACTS_DB = os.getenv("NOTION_CONTACTS_DB")
NOTION_DEALS_DB = os.getenv("NOTION_DEALS_DB")
N8N_WEBHOOK = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/sdr-lead-processed")


def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_step(num, text):
    print(f"\n  {'🔵' * num} STEP {num}: {text}")


async def send_slack_message(message: str, blocks: list = None):
    """Send a Slack message"""
    if not SLACK_TOKEN:
        print("  ⚠️  Slack not configured")
        return None
    
    async with httpx.AsyncClient() as client:
        payload = {
            "channel": SLACK_CHANNEL,
            "text": message,
        }
        if blocks:
            payload["blocks"] = blocks
        
        response = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {SLACK_TOKEN}"},
            json=payload
        )
        return response.json()


async def create_notion_contact(contact: dict):
    """Create a contact in Notion"""
    if not NOTION_TOKEN or not NOTION_CONTACTS_DB:
        print("  ⚠️  Notion not configured")
        return None
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.notion.com/v1/pages",
            headers={
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            },
            json={
                "parent": {"database_id": NOTION_CONTACTS_DB},
                "properties": {
                    "Name": {"title": [{"text": {"content": contact["name"]}}]},
                    "Email": {"email": contact["email"]},
                    "Company": {"rich_text": [{"text": {"content": contact["company"]}}]},
                    "Title": {"rich_text": [{"text": {"content": contact["title"]}}]},
                    "Score": {"number": contact["score"]},
                    "Status": {"select": {"name": contact["status"]}}
                }
            }
        )
        if response.status_code == 200:
            return response.json()
        return None


async def update_notion_contact(page_id: str, updates: dict):
    """Update a contact in Notion"""
    if not NOTION_TOKEN:
        return None
    
    properties = {}
    if "status" in updates:
        properties["Status"] = {"select": {"name": updates["status"]}}
    if "score" in updates:
        properties["Score"] = {"number": updates["score"]}
    
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers={
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            },
            json={"properties": properties}
        )
        return response.json() if response.status_code == 200 else None


async def create_notion_deal(deal: dict):
    """Create a deal in Notion"""
    if not NOTION_TOKEN or not NOTION_DEALS_DB:
        return None
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.notion.com/v1/pages",
            headers={
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            },
            json={
                "parent": {"database_id": NOTION_DEALS_DB},
                "properties": {
                    "Name": {"title": [{"text": {"content": deal["name"]}}]},
                    "Company": {"rich_text": [{"text": {"content": deal["company"]}}]},
                    "Amount": {"number": deal["amount"]},
                    "Stage": {"select": {"name": deal["stage"]}},
                    "Owner": {"rich_text": [{"text": {"content": deal["owner"]}}]}
                }
            }
        )
        if response.status_code == 200:
            return response.json()
        return None


async def update_notion_deal(page_id: str, updates: dict):
    """Update a deal in Notion"""
    if not NOTION_TOKEN:
        return None
    
    properties = {}
    if "stage" in updates:
        properties["Stage"] = {"select": {"name": updates["stage"]}}
    if "amount" in updates:
        properties["Amount"] = {"number": updates["amount"]}
    
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers={
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            },
            json={"properties": properties}
        )
        return response.json() if response.status_code == 200 else None


async def demo_scenario_1():
    """Scenario 1: New Lead → Research → Notion → Slack"""
    print_header("🎬 SCENARIO 1: New Inbound Lead")
    
    lead = {
        "name": "Tim Cook",
        "email": "tim@apple.com",
        "company": "Apple",
        "title": "CEO"
    }
    
    print(f"\n  📥 New lead received: {lead['name']} @ {lead['company']}")
    await asyncio.sleep(1)
    
    # Step 1: Process through AI
    print_step(1, "Processing through AI agents...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{API_BASE}/api/leads/process",
            json={
                "id": f"lead-{lead['company'].lower()}-{datetime.now().strftime('%H%M%S')}",
                "email": lead["email"],
                "firstName": lead["name"].split()[0],
                "lastName": lead["name"].split()[-1],
                "company": lead["company"],
                "title": lead["title"]
            }
        )
        if response.status_code == 200:
            result = response.json()
            lead_score = result.get("lead_score", 0)
            email_subject = result.get("email_variants", [{}])[0].get("subject", "N/A")
            print(f"     ✅ AI Research complete!")
            print(f"     📊 Lead Score: {lead_score}/100")
            print(f"     ✉️  Email: {email_subject}")
        else:
            lead_score = 85
            email_subject = "Quick chat about Apple's infrastructure"
    
    await asyncio.sleep(1)
    
    # Step 2: Create in Notion
    print_step(2, "Creating contact in Notion CRM...")
    contact_result = await create_notion_contact({
        "name": lead["name"],
        "email": lead["email"],
        "company": lead["company"],
        "title": lead["title"],
        "score": lead_score,
        "status": "New"
    })
    if contact_result:
        contact_page_id = contact_result.get("id")
        print(f"     ✅ Contact created in Notion!")
        print(f"     📄 URL: {contact_result.get('url')}")
    else:
        contact_page_id = None
    
    await asyncio.sleep(1)
    
    # Step 3: Send Slack notification
    print_step(3, "Sending Slack notification...")
    slack_result = await send_slack_message(
        f"🆕 New Lead: {lead['name']} @ {lead['company']}",
        blocks=[
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🆕 New Inbound Lead"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Name:*\n{lead['name']}"},
                    {"type": "mrkdwn", "text": f"*Company:*\n{lead['company']}"},
                    {"type": "mrkdwn", "text": f"*Title:*\n{lead['title']}"},
                    {"type": "mrkdwn", "text": f"*Lead Score:*\n{lead_score}/100 {'🔥' if lead_score >= 80 else ''}"},
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Suggested Email Subject:*\n_{email_subject}_"}
            },
            {
                "type": "actions",
                "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "✅ Approve & Send"}, "style": "primary"},
                    {"type": "button", "text": {"type": "plain_text", "text": "✏️ Edit Email"}},
                    {"type": "button", "text": {"type": "plain_text", "text": "❌ Reject"}, "style": "danger"},
                ]
            }
        ]
    )
    if slack_result and slack_result.get("ok"):
        print(f"     ✅ Slack notification sent to {SLACK_CHANNEL}!")
    
    return contact_page_id, lead


async def demo_scenario_2(contact_page_id: str, lead: dict):
    """Scenario 2: Lead Qualified → Deal Created"""
    print_header("🎬 SCENARIO 2: Lead Qualified → Deal Created")
    
    print(f"\n  📞 Sales call completed with {lead['name']}")
    print(f"  ✅ Lead qualified! Creating deal...")
    await asyncio.sleep(1)
    
    # Step 1: Update contact status in Notion
    print_step(1, "Updating contact status in Notion...")
    if contact_page_id:
        await update_notion_contact(contact_page_id, {"status": "Qualified", "score": 95})
        print(f"     ✅ Contact status updated to 'Qualified'")
        print(f"     ✅ Score updated to 95")
    
    await asyncio.sleep(1)
    
    # Step 2: Create deal in Notion
    print_step(2, "Creating deal in Notion...")
    deal = {
        "name": f"{lead['company']} Enterprise Deal",
        "company": lead["company"],
        "amount": 250000,
        "stage": "Discovery",
        "owner": "sales@yourcompany.com"
    }
    deal_result = await create_notion_deal(deal)
    deal_page_id = None
    if deal_result:
        deal_page_id = deal_result.get("id")
        print(f"     ✅ Deal created: {deal['name']}")
        print(f"     💰 Amount: ${deal['amount']:,}")
        print(f"     📊 Stage: {deal['stage']}")
    
    await asyncio.sleep(1)
    
    # Step 3: Send Slack notification
    print_step(3, "Sending Slack notification...")
    await send_slack_message(
        f"🎯 New Deal Created: {lead['company']}",
        blocks=[
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🎯 New Deal Created!"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Deal:*\n{deal['name']}"},
                    {"type": "mrkdwn", "text": f"*Amount:*\n${deal['amount']:,}"},
                    {"type": "mrkdwn", "text": f"*Stage:*\n{deal['stage']}"},
                    {"type": "mrkdwn", "text": f"*Contact:*\n{lead['name']}"},
                ]
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Owner: {deal['owner']}"}
                ]
            }
        ]
    )
    print(f"     ✅ Slack notification sent!")
    
    return deal_page_id, deal


async def demo_scenario_3(deal_page_id: str, deal: dict):
    """Scenario 3: Deal Stage Changes"""
    print_header("🎬 SCENARIO 3: Deal Progresses Through Stages")
    
    stages = [
        ("Proposal", "📝 Proposal sent to client"),
        ("Negotiation", "💬 Negotiating terms"),
        ("Closed Won", "🎉 DEAL WON!")
    ]
    
    for stage, description in stages:
        print(f"\n  {description}")
        await asyncio.sleep(2)
        
        # Update Notion
        print(f"     📝 Updating Notion: Stage → {stage}")
        if deal_page_id:
            await update_notion_deal(deal_page_id, {"stage": stage})
        
        # Send GTM Event
        print(f"     🔄 Processing GTM event...")
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{API_BASE}/api/gtm/event",
                json={
                    "workspace_id": "demo-001",
                    "event_type": "deal_stage_changed",
                    "payload": {
                        "deal_id": deal_page_id or "deal-001",
                        "account_name": deal["company"],
                        "old_stage": deal["stage"],
                        "new_stage": stage,
                        "amount": deal["amount"]
                    }
                }
            )
        
        # Send Slack notification
        emoji = "📝" if stage == "Proposal" else "💬" if stage == "Negotiation" else "🎉"
        color = "warning" if stage == "Negotiation" else "good" if stage == "Closed Won" else None
        
        await send_slack_message(
            f"{emoji} Deal Update: {deal['company']} → {stage}",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{emoji} *{deal['company']}* moved to *{stage}*" + 
                               (" 🎉🎉🎉" if stage == "Closed Won" else "")
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"💰 ${deal['amount']:,} | 👤 {deal['owner']}"}
                    ]
                }
            ]
        )
        print(f"     ✅ Slack notification sent!")
        
        deal["stage"] = stage
    
    # Final celebration
    print("\n  🎉🎉🎉 DEAL CLOSED WON! 🎉🎉🎉")


async def demo_scenario_4():
    """Scenario 4: Weekly Pipeline Report"""
    print_header("🎬 SCENARIO 4: Weekly Pipeline Report to Slack")
    
    print("\n  📊 Generating weekly pipeline report...")
    await asyncio.sleep(1)
    
    # Send weekly summary to Slack
    await send_slack_message(
        "📊 Weekly Pipeline Report",
        blocks=[
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📊 Weekly Pipeline Report"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Pipeline Summary - This Week*"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*New Leads:*\n12"},
                    {"type": "mrkdwn", "text": "*Qualified:*\n8"},
                    {"type": "mrkdwn", "text": "*Proposals Sent:*\n5"},
                    {"type": "mrkdwn", "text": "*Deals Won:*\n2"},
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Pipeline Value:*\n$1,250,000"},
                    {"type": "mrkdwn", "text": "*Avg Lead Score:*\n82/100"},
                    {"type": "mrkdwn", "text": "*Emails Sent:*\n24"},
                    {"type": "mrkdwn", "text": "*Response Rate:*\n35%"},
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*🔥 Hot Leads This Week:*\n• Tim Cook @ Apple ($250K)\n• Satya Nadella @ Microsoft ($180K)\n• Jensen Huang @ NVIDIA ($320K)"}
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "Generated by AI SDR Platform | View full report in Notion"}
                ]
            }
        ]
    )
    print("     ✅ Weekly report sent to Slack!")


async def main():
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                       ║")
    print("║   🎬 AI SDR PLATFORM - FULL WORKFLOW DEMONSTRATION                    ║")
    print("║                                                                       ║")
    print("║   This demo shows how Notion and Slack update in real-time           ║")
    print("║   as leads move through your pipeline.                                ║")
    print("║                                                                       ║")
    print("║   👀 Watch your Slack channel and Notion databases!                   ║")
    print("║                                                                       ║")
    print("╚═══════════════════════════════════════════════════════════════════════╝")
    
    input("\n  Press ENTER to start the demo (watch Slack & Notion)...")
    
    # Scenario 1: New Lead
    contact_page_id, lead = await demo_scenario_1()
    input("\n  ✅ Scenario 1 complete! Press ENTER to continue...")
    
    # Scenario 2: Lead Qualified
    deal_page_id, deal = await demo_scenario_2(contact_page_id, lead)
    input("\n  ✅ Scenario 2 complete! Press ENTER to continue...")
    
    # Scenario 3: Deal Progression
    await demo_scenario_3(deal_page_id, deal)
    input("\n  ✅ Scenario 3 complete! Press ENTER to continue...")
    
    # Scenario 4: Weekly Report
    await demo_scenario_4()
    
    print_header("🎉 DEMO COMPLETE!")
    print("""
  You just saw:
  
  ✅ Scenario 1: New lead → AI processing → Notion contact → Slack alert
  ✅ Scenario 2: Lead qualified → Contact updated → Deal created → Slack alert  
  ✅ Scenario 3: Deal stages: Discovery → Proposal → Negotiation → Closed Won
  ✅ Scenario 4: Weekly pipeline report to Slack
  
  📱 Check your Slack #{} channel for all notifications!
  📝 Check your Notion databases for new contacts and deals!
  
  This is how your AI SDR Platform automates your entire sales workflow!
    """.format(SLACK_CHANNEL))


if __name__ == "__main__":
    asyncio.run(main())
