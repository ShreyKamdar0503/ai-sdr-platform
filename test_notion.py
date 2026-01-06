"""Test Notion Integration"""
import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

NOTION_API_URL = "https://api.notion.com/v1"

async def create_notion_contact(contact_data: dict):
    """Create a contact in Notion"""
    token = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_CONTACTS_DB")
    
    if not token or token.startswith("secret_xxx"):
        print("❌ NOTION_API_KEY not configured")
        print("   Get one at: https://www.notion.so/my-integrations")
        return None
    
    if not database_id:
        print("❌ NOTION_CONTACTS_DB not configured")
        return None
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API_URL}/pages",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            },
            json={
                "parent": {"database_id": database_id},
                "properties": {
                    "Name": {
                        "title": [
                            {"text": {"content": f"{contact_data.get('firstName')} {contact_data.get('lastName')}"}}
                        ]
                    },
                    "Email": {
                        "email": contact_data.get("email")
                    },
                    "Company": {
                        "rich_text": [
                            {"text": {"content": contact_data.get("company", "")}}
                        ]
                    },
                    "Title": {
                        "rich_text": [
                            {"text": {"content": contact_data.get("title", "")}}
                        ]
                    },
                    "Score": {
                        "number": contact_data.get("score", 0)
                    },
                    "Status": {
                        "select": {"name": "New"}
                    }
                }
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Contact created in Notion!")
            print(f"   Page ID: {data.get('id')}")
            print(f"   URL: {data.get('url')}")
            return data
        else:
            print(f"❌ Notion error: {response.status_code}")
            print(f"   {response.text}")
            return None


async def create_notion_deal(deal_data: dict):
    """Create a deal in Notion"""
    token = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DEALS_DB")
    
    if not token or not database_id:
        print("❌ Notion not configured for deals")
        return None
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API_URL}/pages",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            },
            json={
                "parent": {"database_id": database_id},
                "properties": {
                    "Name": {
                        "title": [
                            {"text": {"content": deal_data.get("name", "New Deal")}}
                        ]
                    },
                    "Company": {
                        "rich_text": [
                            {"text": {"content": deal_data.get("company", "")}}
                        ]
                    },
                    "Amount": {
                        "number": deal_data.get("amount", 0)
                    },
                    "Stage": {
                        "select": {"name": deal_data.get("stage", "Discovery")}
                    },
                    "Owner": {
                        "rich_text": [
                            {"text": {"content": deal_data.get("owner", "")}}
                        ]
                    }
                }
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Deal created in Notion!")
            print(f"   Page ID: {data.get('id')}")
            return data
        else:
            print(f"❌ Notion error: {response.status_code}")
            return None


async def main():
    print("=" * 60)
    print("  NOTION CRM INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Create contact
    print("\n1️⃣ Creating contact in Notion...")
    await create_notion_contact({
        "firstName": "Elliott",
        "lastName": "Hill",
        "email": "ceo@nike.com",
        "company": "Nike",
        "title": "CEO",
        "score": 80
    })
    
    # Test 2: Create deal
    print("\n2️⃣ Creating deal in Notion...")
    await create_notion_deal({
        "name": "Nike Enterprise Deal",
        "company": "Nike",
        "amount": 75000,
        "stage": "Proposal",
        "owner": "sales@yourcompany.com"
    })
    
    print("\n✅ Check your Notion workspace!")


if __name__ == "__main__":
    asyncio.run(main())
