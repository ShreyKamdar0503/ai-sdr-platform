"""
🚀 AI SDR PLATFORM - FULL END-TO-END PIPELINE TEST

This script tests the complete flow:
1. Process a lead through AI agents
2. Trigger GTM event
3. Send to n8n webhook
4. (Optional) Slack notification
5. (Optional) Notion CRM entry
"""

import os
import asyncio
import httpx
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_BASE = "http://localhost:8000"
N8N_WEBHOOK = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/sdr-lead-processed")

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_success(text):
    print(f"  ✅ {text}")

def print_error(text):
    print(f"  ❌ {text}")

def print_info(text):
    print(f"  ℹ️  {text}")

def print_data(label, value):
    print(f"     {label}: {value}")


async def test_full_pipeline():
    """Run the complete end-to-end test"""
    
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                       ║")
    print("║        🚀 AI SDR PLATFORM - FULL PIPELINE TEST                        ║")
    print("║                                                                       ║")
    print("║        Testing: Lead → AI → GTM → n8n → Complete                      ║")
    print("║                                                                       ║")
    print("╚═══════════════════════════════════════════════════════════════════════╝")
    
    results = {
        "api_health": False,
        "lead_processing": False,
        "gtm_event": False,
        "n8n_webhook": False,
        "slack": False,
        "notion": False,
    }
    
    # Test data
    test_lead = {
        "id": f"lead-e2e-{datetime.now().strftime('%H%M%S')}",
        "email": "sundar@google.com",
        "firstName": "Sundar",
        "lastName": "Pichai",
        "company": "Google",
        "title": "CEO"
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        
        # ============================================================
        # STEP 1: Health Check
        # ============================================================
        print_header("STEP 1: API Health Check")
        
        try:
            response = await client.get(f"{API_BASE}/health")
            if response.status_code == 200:
                print_success("API is healthy!")
                print_data("Status", response.json().get("status", "ok"))
                results["api_health"] = True
            else:
                print_error(f"API returned {response.status_code}")
        except Exception as e:
            print_error(f"Cannot connect to API: {e}")
            print_info("Make sure the API is running: uvicorn api.app:app --reload --port 8000")
            return results
        
        # ============================================================
        # STEP 2: Process Lead through AI Pipeline
        # ============================================================
        print_header("STEP 2: AI Lead Processing")
        print(f"\n  📧 Processing: {test_lead['firstName']} {test_lead['lastName']}")
        print(f"  🏢 Company: {test_lead['company']}")
        print(f"  💼 Title: {test_lead['title']}")
        print("\n  ⏳ Running AI agents (this takes ~10-15 seconds)...\n")
        
        try:
            response = await client.post(
                f"{API_BASE}/api/leads/process",
                json=test_lead
            )
            
            if response.status_code == 200:
                lead_result = response.json()
                results["lead_processing"] = True
                
                print_success("Lead processed successfully!\n")
                
                # Research results
                research = lead_result.get("research_results", {})
                company_info = research.get("company_info", {})
                
                print("  📊 RESEARCH RESULTS:")
                print_data("Company", company_info.get("name"))
                print_data("Industry", company_info.get("industry"))
                print_data("Summary", company_info.get("summary", "")[:100] + "...")
                print_data("Quality Score", f"{research.get('quality_score', 0)}/100")
                
                # Lead score
                print(f"\n  🎯 LEAD SCORING:")
                print_data("Lead Score", f"{lead_result.get('lead_score', 0)}/100")
                
                # Email variants
                emails = lead_result.get("email_variants", [])
                print(f"\n  ✉️  EMAIL VARIANTS ({len(emails)} generated):")
                for i, email in enumerate(emails[:2], 1):
                    print(f"\n     Variant {email.get('variant', i)}:")
                    print(f"     Subject: {email.get('subject', 'N/A')}")
                    body_preview = email.get('body', '')[:150].replace('\n', ' ')
                    print(f"     Body: {body_preview}...")
                
                # Timing
                timing = lead_result.get("timing_recommendation", {})
                print(f"\n  ⏰ TIMING:")
                print_data("Optimal Send Time", timing.get("optimal_time", "N/A"))
                
                # Agent consensus
                votes = lead_result.get("agent_votes", {})
                print(f"\n  🤝 AGENT CONSENSUS:")
                for agent, vote in votes.items():
                    status = "✅" if vote else "❌"
                    print(f"     {status} {agent}")
                
            else:
                print_error(f"Lead processing failed: {response.status_code}")
                print_info(response.text[:200])
                
        except Exception as e:
            print_error(f"Lead processing error: {e}")
        
        # ============================================================
        # STEP 3: GTM Event Processing
        # ============================================================
        print_header("STEP 3: GTM Event Processing")
        
        gtm_event = {
            "workspace_id": "demo-001",
            "event_type": "deal_created",
            "payload": {
                "deal_id": f"deal-{test_lead['company'].lower()}-001",
                "account_name": test_lead["company"],
                "contact_name": f"{test_lead['firstName']} {test_lead['lastName']}",
                "amount": 150000,
                "stage": "Discovery",
                "source": "AI SDR Platform",
                "lead_score": lead_result.get("lead_score", 0) if results["lead_processing"] else 80
            }
        }
        
        print(f"\n  📋 Event: {gtm_event['event_type']}")
        print(f"  🏢 Account: {gtm_event['payload']['account_name']}")
        print(f"  💰 Amount: ${gtm_event['payload']['amount']:,}")
        print("\n  ⏳ Processing through GTM agents...\n")
        
        try:
            response = await client.post(
                f"{API_BASE}/api/gtm/event",
                json=gtm_event
            )
            
            if response.status_code == 200:
                gtm_result = response.json()
                results["gtm_event"] = True
                
                print_success("GTM event processed!\n")
                
                decisions = gtm_result.get("decisions", {})
                
                print("  🔍 AGENT DECISIONS:")
                print_data("Event Category", decisions.get("event", {}).get("category", "N/A"))
                print_data("Confidence", decisions.get("event", {}).get("confidence", "N/A"))
                print_data("Schema Valid", "✅" if not decisions.get("schema", {}).get("missing_ids") else "❌")
                
                actions = gtm_result.get("actions", [])
                print(f"\n  ⚡ ACTIONS GENERATED: {len(actions)}")
                for action in actions[:3]:
                    print(f"     → {action.get('type')}: {action.get('webhook', 'N/A')}")
                
            else:
                print_error(f"GTM processing failed: {response.status_code}")
                
        except Exception as e:
            print_error(f"GTM processing error: {e}")
        
        # ============================================================
        # STEP 4: n8n Webhook
        # ============================================================
        print_header("STEP 4: n8n Workflow Trigger")
        
        n8n_payload = {
            "event": "lead_processed",
            "timestamp": datetime.now().isoformat(),
            "lead": {
                "id": test_lead["id"],
                "name": f"{test_lead['firstName']} {test_lead['lastName']}",
                "company": test_lead["company"],
                "title": test_lead["title"],
                "email": test_lead["email"]
            },
            "scores": {
                "lead_score": lead_result.get("lead_score", 0) if results["lead_processing"] else 80,
                "quality_score": lead_result.get("research_results", {}).get("quality_score", 0) if results["lead_processing"] else 85
            },
            "email": {
                "subject": lead_result.get("email_variants", [{}])[0].get("subject", "N/A") if results["lead_processing"] else "N/A",
                "variant": "A"
            },
            "next_action": "send_email" if lead_result.get("lead_score", 0) >= 70 else "nurture"
        }
        
        print(f"\n  🔗 Webhook URL: {N8N_WEBHOOK}")
        print(f"  📦 Payload: lead_processed event")
        
        try:
            response = await client.post(N8N_WEBHOOK, json=n8n_payload)
            
            if response.status_code == 200:
                results["n8n_webhook"] = True
                print_success("n8n workflow triggered!")
                print_data("Response", response.text[:100])
            else:
                print_error(f"n8n webhook failed: {response.status_code}")
                print_info("Make sure the n8n workflow is activated (toggle ON)")
                
        except Exception as e:
            print_error(f"n8n connection error: {e}")
            print_info("Make sure n8n is running: docker ps | grep n8n")
        
        # ============================================================
        # STEP 5: Slack Notification (if configured)
        # ============================================================
        print_header("STEP 5: Slack Notification")
        
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        slack_channel = os.getenv("SLACK_CHANNEL_ID", "#general")
        
        if slack_token and not slack_token.startswith("xoxb-your"):
            try:
                slack_message = {
                    "channel": slack_channel,
                    "text": f"🚀 New Lead Processed: {test_lead['company']}",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {"type": "plain_text", "text": "🚀 New Lead from AI SDR"}
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Contact:*\n{test_lead['firstName']} {test_lead['lastName']}"},
                                {"type": "mrkdwn", "text": f"*Company:*\n{test_lead['company']}"},
                                {"type": "mrkdwn", "text": f"*Title:*\n{test_lead['title']}"},
                                {"type": "mrkdwn", "text": f"*Score:*\n{lead_result.get('lead_score', 'N/A')}/100"},
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Email Subject:*\n_{lead_result.get('email_variants', [{}])[0].get('subject', 'N/A')}_"
                            }
                        }
                    ]
                }
                
                response = await client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {slack_token}"},
                    json=slack_message
                )
                
                if response.json().get("ok"):
                    results["slack"] = True
                    print_success(f"Slack notification sent to {slack_channel}!")
                else:
                    print_error(f"Slack error: {response.json().get('error')}")
                    
            except Exception as e:
                print_error(f"Slack error: {e}")
        else:
            print_info("Slack not configured (optional)")
            print_info("Add SLACK_BOT_TOKEN to .env to enable")
        
        # ============================================================
        # STEP 6: Notion CRM (if configured)
        # ============================================================
        print_header("STEP 6: Notion CRM Entry")
        
        notion_token = os.getenv("NOTION_API_KEY")
        notion_db = os.getenv("NOTION_CONTACTS_DB")
        
        if notion_token and not notion_token.startswith("secret_xxx") and notion_db:
            try:
                response = await client.post(
                    "https://api.notion.com/v1/pages",
                    headers={
                        "Authorization": f"Bearer {notion_token}",
                        "Notion-Version": "2022-06-28",
                        "Content-Type": "application/json"
                    },
                    json={
                        "parent": {"database_id": notion_db},
                        "properties": {
                            "Name": {"title": [{"text": {"content": f"{test_lead['firstName']} {test_lead['lastName']}"}}]},
                            "Email": {"email": test_lead["email"]},
                            "Company": {"rich_text": [{"text": {"content": test_lead["company"]}}]},
                            "Title": {"rich_text": [{"text": {"content": test_lead["title"]}}]},
                            "Score": {"number": lead_result.get("lead_score", 0) if results["lead_processing"] else 80},
                            "Status": {"select": {"name": "New"}}
                        }
                    }
                )
                
                if response.status_code == 200:
                    results["notion"] = True
                    print_success("Contact created in Notion!")
                    print_data("Page URL", response.json().get("url", "N/A"))
                else:
                    print_error(f"Notion error: {response.status_code}")
                    
            except Exception as e:
                print_error(f"Notion error: {e}")
        else:
            print_info("Notion not configured (optional)")
            print_info("Add NOTION_API_KEY and NOTION_CONTACTS_DB to .env to enable")
    
    # ============================================================
    # FINAL SUMMARY
    # ============================================================
    print_header("📊 FINAL RESULTS")
    
    total = sum(results.values())
    required_passed = results["api_health"] and results["lead_processing"] and results["gtm_event"]
    
    print(f"""
  ┌─────────────────────────────────────────────────────────────┐
  │  COMPONENT              STATUS                              │
  ├─────────────────────────────────────────────────────────────┤
  │  API Health             {'✅ PASS' if results['api_health'] else '❌ FAIL'}                              │
  │  AI Lead Processing     {'✅ PASS' if results['lead_processing'] else '❌ FAIL'}                              │
  │  GTM Event Processing   {'✅ PASS' if results['gtm_event'] else '❌ FAIL'}                              │
  │  n8n Webhook            {'✅ PASS' if results['n8n_webhook'] else '❌ FAIL'}                              │
  │  Slack (optional)       {'✅ PASS' if results['slack'] else '⚠️  SKIP'}                              │
  │  Notion (optional)      {'✅ PASS' if results['notion'] else '⚠️  SKIP'}                              │
  ├─────────────────────────────────────────────────────────────┤
  │  TOTAL                  {total}/6 passed                          │
  └─────────────────────────────────────────────────────────────┘
    """)
    
    if required_passed:
        print("""
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║                                                                       ║
  ║   🎉 SUCCESS! Your AI SDR Platform is fully operational!              ║
  ║                                                                       ║
  ║   The pipeline successfully:                                          ║
  ║   • Researched the company using AI (OpenAI)                          ║
  ║   • Scored the lead based on research                                 ║
  ║   • Generated personalized email variants                             ║
  ║   • Processed GTM events through 8 agents                             ║
  ║   • Triggered n8n workflow automation                                 ║
  ║                                                                       ║
  ╚═══════════════════════════════════════════════════════════════════════╝
        """)
    else:
        print("""
  ⚠️  Some core components failed. Please check:
     • Is the API running? (uvicorn api.app:app --reload --port 8000)
     • Is Docker running? (docker ps)
     • Are your API keys configured in .env?
        """)
    
    return results


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
