"""
🧪 GROWTHBOOK DEMO - Feature Flags & A/B Testing

This demo shows how GrowthBook controls your AI SDR Platform:
1. Feature Flags - Enable/disable features without code changes
2. A/B Testing - Test different email variants, timing strategies
3. Gradual Rollouts - Roll out features to % of users
"""

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# GrowthBook SDK
try:
    from growthbook import GrowthBook
    GROWTHBOOK_AVAILABLE = True
except ImportError:
    GROWTHBOOK_AVAILABLE = False
    print("⚠️ GrowthBook not installed. Run: pip install growthbook")


def create_growthbook_instance(user_id: str, company: str = None):
    """Create a GrowthBook instance for a specific user/lead"""
    
    gb = GrowthBook(
        api_host="http://localhost:3100",
        client_key=os.getenv("GROWTHBOOK_CLIENT_KEY", "sdk-dev-key"),
        attributes={
            "id": user_id,
            "company": company or "Unknown",
            "timestamp": datetime.now().isoformat(),
        }
    )
    
    return gb


def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_feature(name, value, description=""):
    status = "✅ ON" if value else "❌ OFF"
    print(f"  {status}  {name}")
    if description:
        print(f"        └─ {description}")


async def demo_feature_flags():
    """Demo 1: Feature Flags - Enable/Disable Features"""
    
    print_header("🚦 DEMO 1: FEATURE FLAGS")
    print("""
  Feature flags let you enable/disable features WITHOUT deploying code.
  
  Use cases:
  • Turn off a broken feature instantly
  • Enable features for specific customers only
  • Gradual rollout of new features
    """)
    
    # Simulate different scenarios
    scenarios = [
        {
            "name": "Standard Lead Processing",
            "user_id": "lead-001",
            "company": "Acme Corp",
            "features": {
                "enable_research_agent": True,
                "enable_playwright_scraping": True,
                "enable_email_generation": True,
                "enable_slack_notifications": True,
                "enable_notion_sync": True,
            }
        },
        {
            "name": "New Customer (Limited Features)",
            "user_id": "lead-002", 
            "company": "StartupXYZ",
            "features": {
                "enable_research_agent": True,
                "enable_playwright_scraping": False,  # Not enabled yet
                "enable_email_generation": True,
                "enable_slack_notifications": False,  # Free tier
                "enable_notion_sync": False,  # Free tier
            }
        },
        {
            "name": "Enterprise Customer (All Features)",
            "user_id": "lead-003",
            "company": "BigCorp Inc",
            "features": {
                "enable_research_agent": True,
                "enable_playwright_scraping": True,
                "enable_email_generation": True,
                "enable_slack_notifications": True,
                "enable_notion_sync": True,
                "enable_advanced_analytics": True,  # Enterprise only
                "enable_custom_models": True,  # Enterprise only
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n  📋 Scenario: {scenario['name']}")
        print(f"     Company: {scenario['company']}")
        print(f"     Features:")
        
        for feature, enabled in scenario['features'].items():
            status = "✅" if enabled else "❌"
            print(f"       {status} {feature}")
    
    print("""
  
  💡 HOW IT WORKS IN YOUR CODE:
```python
  from growthbook import GrowthBook
  
  gb = GrowthBook(attributes={"company": "Acme Corp"})
  
  if gb.is_on("enable_playwright_scraping"):
      # Use Playwright for live scraping
      result = await playwright_agent.scrape(url)
  else:
      # Use basic OpenAI research
      result = await basic_research(company)
```
    """)


async def demo_ab_testing():
    """Demo 2: A/B Testing - Test Different Variants"""
    
    print_header("🧪 DEMO 2: A/B TESTING")
    print("""
  A/B testing lets you test different versions of features to see which
  performs better.
  
  Use cases:
  • Test different email subject lines
  • Test different email tones (formal vs casual)
  • Test different send times
  • Test different lead scoring algorithms
    """)
    
    # Simulate A/B test for email variants
    print("\n  📧 A/B TEST: Email Subject Lines")
    print("  " + "-" * 50)
    
    test_leads = [
        {"id": "lead-001", "name": "John", "company": "Google"},
        {"id": "lead-002", "name": "Sarah", "company": "Microsoft"},
        {"id": "lead-003", "name": "Mike", "company": "Apple"},
        {"id": "lead-004", "name": "Lisa", "company": "Amazon"},
        {"id": "lead-005", "name": "Tom", "company": "Meta"},
        {"id": "lead-006", "name": "Emma", "company": "Netflix"},
        {"id": "lead-007", "name": "Alex", "company": "Uber"},
        {"id": "lead-008", "name": "Kate", "company": "Airbnb"},
    ]
    
    variants = {
        "A": {
            "subject": "Quick question about {company}",
            "tone": "casual",
            "count": 0
        },
        "B": {
            "subject": "Helping {company} scale faster",
            "tone": "professional", 
            "count": 0
        }
    }
    
    print("\n  Assigning leads to variants:\n")
    
    for lead in test_leads:
        # Simulate GrowthBook variant assignment (deterministic based on ID)
        # In real GrowthBook, this is done automatically
        variant = "A" if hash(lead["id"]) % 2 == 0 else "B"
        variants[variant]["count"] += 1
        
        subject = variants[variant]["subject"].format(company=lead["company"])
        print(f"    {lead['name']:6} @ {lead['company']:10} → Variant {variant}: \"{subject}\"")
    
    print(f"\n  📊 Distribution:")
    print(f"     Variant A (Casual): {variants['A']['count']} leads ({variants['A']['count']/len(test_leads)*100:.0f}%)")
    print(f"     Variant B (Professional): {variants['B']['count']} leads ({variants['B']['count']/len(test_leads)*100:.0f}%)")
    
    # Simulate results
    print("\n  📈 SIMULATED RESULTS (after 1 week):")
    print("  " + "-" * 50)
    print("""
    Variant A (Casual):
      • Sent: 4 emails
      • Opened: 3 (75% open rate)
      • Replied: 1 (25% reply rate)
    
    Variant B (Professional):
      • Sent: 4 emails
      • Opened: 2 (50% open rate)
      • Replied: 2 (50% reply rate)
    
    🏆 WINNER: Variant A has better open rate, but Variant B has better reply rate!
       Recommendation: Use casual subject + professional body
    """)
    
    print("""
  💡 HOW IT WORKS IN YOUR CODE:
```python
  # GrowthBook automatically assigns variants
  variant = gb.get_feature_value("email_subject_test", "A")
  
  if variant == "A":
      subject = f"Quick question about {company}"
  else:
      subject = f"Helping {company} scale faster"
  
  # Track the result for analysis
  gb.track("email_sent", {"variant": variant, "lead_id": lead_id})
```
    """)


async def demo_gradual_rollout():
    """Demo 3: Gradual Rollouts"""
    
    print_header("📈 DEMO 3: GRADUAL ROLLOUTS")
    print("""
  Gradual rollouts let you release features to a percentage of users,
  reducing risk when launching new features.
  
  Use case: Rolling out Playwright scraping to all customers
    """)
    
    rollout_stages = [
        {"day": 1, "percentage": 5, "users": ["beta-testers"]},
        {"day": 3, "percentage": 10, "users": ["early-adopters"]},
        {"day": 7, "percentage": 25, "users": ["power-users"]},
        {"day": 14, "percentage": 50, "users": ["half-of-users"]},
        {"day": 21, "percentage": 75, "users": ["most-users"]},
        {"day": 30, "percentage": 100, "users": ["everyone"]},
    ]
    
    print("\n  🚀 ROLLOUT PLAN: Playwright Live Scraping")
    print("  " + "-" * 50)
    
    for stage in rollout_stages:
        bar = "█" * (stage["percentage"] // 5) + "░" * (20 - stage["percentage"] // 5)
        print(f"    Day {stage['day']:2}: [{bar}] {stage['percentage']:3}% - {stage['users'][0]}")
    
    print("""
  
  💡 BENEFITS:
  • Catch bugs early with small user group
  • Monitor performance before full rollout
  • Easy rollback if issues found
  • Build confidence in new features
  
  💡 HOW IT WORKS IN GROWTHBOOK:
```json
  {
    "feature": "enable_playwright_scraping",
    "rules": [
      {
        "type": "rollout",
        "percentage": 25,
        "value": true
      }
    ]
  }
```
    """)


async def demo_real_integration():
    """Demo 4: Real Integration with Your Platform"""
    
    print_header("🔌 DEMO 4: REAL INTEGRATION")
    print("""
  Here's how GrowthBook is ACTUALLY used in your AI SDR Platform:
    """)
    
    features_in_use = [
        {
            "feature": "enable_research_agent",
            "location": "agentic_mesh/agents/research_agent.py",
            "description": "Controls whether research agent runs",
            "default": True
        },
        {
            "feature": "enable_playwright_scraping",
            "location": "agentic_mesh/agents/integrated_research_agent.py", 
            "description": "Use Playwright for live scraping vs basic research",
            "default": True
        },
        {
            "feature": "email_variant_test",
            "location": "agentic_mesh/agents/copywriting_agent.py",
            "description": "A/B test email subject lines and tones",
            "default": "A"
        },
        {
            "feature": "timing_optimization",
            "location": "agentic_mesh/agents/timing_agent.py",
            "description": "Use AI timing vs fixed schedule",
            "default": True
        },
        {
            "feature": "multi_agent_consensus",
            "location": "agentic_mesh/agents/negotiation_agent.py",
            "description": "Require multiple agents to agree before sending",
            "default": True
        },
        {
            "feature": "auto_send_threshold",
            "location": "agentic_mesh/orchestrator.py",
            "description": "Lead score threshold for auto-sending emails",
            "default": 90
        }
    ]
    
    print("\n  📋 FEATURES CONTROLLED BY GROWTHBOOK:\n")
    
    for f in features_in_use:
        print(f"  🚦 {f['feature']}")
        print(f"     📁 {f['location']}")
        print(f"     📝 {f['description']}")
        print(f"     🔧 Default: {f['default']}")
        print()


async def demo_live_test():
    """Demo 5: Live Test with GrowthBook"""
    
    print_header("🔴 DEMO 5: LIVE GROWTHBOOK TEST")
    
    if not GROWTHBOOK_AVAILABLE:
        print("\n  ⚠️ GrowthBook SDK not installed")
        print("  Run: pip install growthbook")
        return
    
    print("\n  Testing connection to GrowthBook server...")
    
    try:
        gb = GrowthBook(
            api_host="http://localhost:3100",
            client_key=os.getenv("GROWTHBOOK_CLIENT_KEY", "sdk-dev-key"),
            attributes={
                "id": "test-user-001",
                "company": "TestCorp",
                "plan": "enterprise"
            }
        )
        
        # Test some features
        test_features = [
            "enable_research_agent",
            "enable_playwright_scraping", 
            "email_variant_test",
            "auto_send_threshold"
        ]
        
        print("\n  📊 LIVE FEATURE VALUES:\n")
        
        for feature in test_features:
            value = gb.get_feature_value(feature, "default")
            is_on = gb.is_on(feature)
            print(f"    {feature}")
            print(f"      └─ Value: {value}")
            print(f"      └─ Is On: {is_on}")
            print()
        
        print("  ✅ GrowthBook connection successful!")
        
    except Exception as e:
        print(f"\n  ⚠️ Could not connect to GrowthBook: {e}")
        print("  Make sure GrowthBook is running: docker ps | grep growthbook")


async def main():
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                       ║")
    print("║   🧪 GROWTHBOOK DEMO - Feature Flags & A/B Testing                    ║")
    print("║                                                                       ║")
    print("║   GrowthBook controls which features are enabled and lets you         ║")
    print("║   run A/B tests to optimize your AI SDR Platform.                     ║")
    print("║                                                                       ║")
    print("╚═══════════════════════════════════════════════════════════════════════╝")
    
    await demo_feature_flags()
    input("\n  Press ENTER to continue to A/B Testing demo...")
    
    await demo_ab_testing()
    input("\n  Press ENTER to continue to Gradual Rollouts demo...")
    
    await demo_gradual_rollout()
    input("\n  Press ENTER to continue to Real Integration demo...")
    
    await demo_real_integration()
    input("\n  Press ENTER to run Live GrowthBook test...")
    
    await demo_live_test()
    
    print_header("🎉 DEMO COMPLETE")
    print("""
  KEY TAKEAWAYS:
  
  1. 🚦 FEATURE FLAGS
     • Turn features on/off without code changes
     • Different features for different customers (free vs paid)
     • Instant rollback if something breaks
  
  2. 🧪 A/B TESTING  
     • Test different email subject lines
     • Test different email tones
     • Measure what works best
  
  3. 📈 GRADUAL ROLLOUTS
     • Release features to 5% → 25% → 50% → 100%
     • Catch bugs early
     • Build confidence
  
  4. 💰 COST SAVINGS
     • GrowthBook is FREE (open source)
     • vs LaunchDarkly: $12,000/year
     • vs Statsig: $20,000/year
  
  🔗 GrowthBook Dashboard: http://localhost:3100
    """)


if __name__ == "__main__":
    asyncio.run(main())
