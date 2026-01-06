import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_slack():
    token = os.getenv("SLACK_BOT_TOKEN")
    channel = os.getenv("SLACK_CHANNEL_ID")
    
    print("=" * 50)
    print("  SLACK TEST")
    print("=" * 50)
    print(f"\n  Token: {token[:20]}..." if token else "  Token: NOT SET")
    print(f"  Channel: {channel}")
    
    if not token or token.startswith("xoxb-your"):
        print("\n  ❌ Please set SLACK_BOT_TOKEN in .env")
        return
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "channel": channel,
                "text": "🎉 AI SDR Platform Connected!",
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "🤖 AI SDR Platform"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "✅ *Slack integration is working!*\n\nYou'll receive lead notifications here."}
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": "*Status:*\nConnected"},
                            {"type": "mrkdwn", "text": "*Time:*\nNow"}
                        ]
                    }
                ]
            }
        )
        
        result = response.json()
        if result.get("ok"):
            print(f"\n  ✅ Message sent to Slack!")
            print(f"  Check your #{channel} channel!")
        else:
            print(f"\n  ❌ Error: {result.get('error')}")
            if result.get('error') == 'channel_not_found':
                print("     Make sure the bot is invited to the channel")
            elif result.get('error') == 'invalid_auth':
                print("     Check your SLACK_BOT_TOKEN")

asyncio.run(test_slack())
