"""
Test the full integrated pipeline with Playwright research
"""

import asyncio
import httpx
from datetime import datetime

API_BASE = "http://localhost:8000"


async def test_integrated_pipeline():
    print("\n" + "=" * 70)
    print("  🚀 INTEGRATED PIPELINE TEST")
    print("  Testing: Lead → Playwright Research → AI Analysis → Email Generation")
    print("=" * 70)
    
    # Test lead
    lead = {
        "id": f"lead-integrated-{datetime.now().strftime('%H%M%S')}",
        "email": "brian@airbnb.com",
        "firstName": "Brian",
        "lastName": "Chesky",
        "company": "Airbnb",
        "title": "CEO"
    }
    
    print(f"\n  📧 Processing: {lead['firstName']} {lead['lastName']}")
    print(f"  🏢 Company: {lead['company']}")
    print(f"  💼 Title: {lead['title']}")
    print("\n  ⏳ Running full pipeline (this may take 30-60 seconds)...")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{API_BASE}/api/leads/process",
            json=lead
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "=" * 70)
            print("  📊 RESULTS")
            print("=" * 70)
            
            # Research results
            research = result.get("research_results", {})
            company = research.get("company_info", {})
            
            print(f"\n  🔬 RESEARCH:")
            print(f"     Quality Score: {research.get('quality_score', 'N/A')}/100")
            print(f"     Research Type: {research.get('research_type', 'basic')}")
            print(f"     Tech Stack: {company.get('tech_stack', [])}")
            print(f"     Hiring Depts: {company.get('hiring_departments', [])}")
            print(f"     LinkedIn: {company.get('linkedin_url', 'Not found')}")
            
            # News
            news = company.get("recent_news", [])
            if news and news[0] != "Recent company activity":
                print(f"\n  📰 NEWS:")
                for article in news[:3]:
                    print(f"     • {article[:60]}...")
            
            # Engagement hooks
            hooks = research.get("hooks", [])
            print(f"\n  🎯 ENGAGEMENT HOOKS:")
            for hook in hooks[:3]:
                print(f"     • {hook[:70]}...")
            
            # Email variants
            emails = result.get("email_variants", [])
            print(f"\n  ✉️ EMAILS GENERATED: {len(emails)}")
            for email in emails[:2]:
                print(f"\n     Subject: {email.get('subject', 'N/A')}")
                body = email.get('body', '')[:200]
                print(f"     Body: {body}...")
            
            # Scores
            print(f"\n  📊 SCORES:")
            print(f"     Lead Score: {result.get('lead_score', 'N/A')}/100")
            print(f"     Research Quality: {research.get('quality_score', 'N/A')}/100")
            
            # AI Analysis preview
            ai_analysis = research.get("ai_analysis", "")
            if ai_analysis:
                print(f"\n  🤖 AI ANALYSIS PREVIEW:")
                print(f"     {ai_analysis[:300]}...")
            
            print("\n  ✅ Integrated pipeline test complete!")
            
        else:
            print(f"\n  ❌ Error: {response.status_code}")
            print(f"     {response.text[:500]}")


if __name__ == "__main__":
    asyncio.run(test_integrated_pipeline())
