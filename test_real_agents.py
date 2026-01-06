"""
Test REAL agent processing with actual API calls
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Check if API keys are set
def check_api_keys():
    print("=" * 60)
    print("  CHECKING API KEYS")
    print("=" * 60)
    
    keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY"),
        "HUNTER_API_KEY": os.getenv("HUNTER_API_KEY"),
    }
    
    for name, value in keys.items():
        if value and not value.startswith("your_"):
            # Mask the key for security
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"  ✅ {name}: {masked}")
        else:
            print(f"  ❌ {name}: NOT SET or placeholder")
    
    print()
    return keys["OPENAI_API_KEY"] and not keys["OPENAI_API_KEY"].startswith("your_")


async def test_openai_real():
    """Test REAL OpenAI API call"""
    print("=" * 60)
    print("  TEST 1: Real OpenAI API Call")
    print("=" * 60)
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        print("  Calling OpenAI GPT-4o-mini...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a sales development representative."},
                {"role": "user", "content": "Write a 2-sentence cold email intro for Jane Doe, VP of Engineering at TechCorp, a Series B startup that just raised $20M."}
            ],
            max_tokens=150
        )
        
        result = response.choices[0].message.content
        print(f"\n  ✅ REAL Response from OpenAI:\n")
        print(f"  \"{result}\"")
        print()
        return True
        
    except Exception as e:
        print(f"  ❌ OpenAI Error: {e}")
        return False


async def test_embeddings_real():
    """Test REAL OpenAI Embeddings"""
    print("=" * 60)
    print("  TEST 2: Real OpenAI Embeddings")
    print("=" * 60)
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        print("  Creating embedding for: 'TechCorp is a B2B SaaS company'...")
        
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="TechCorp is a B2B SaaS company specializing in sales automation"
        )
        
        embedding = response.data[0].embedding
        print(f"\n  ✅ REAL Embedding created!")
        print(f"     Dimensions: {len(embedding)}")
        print(f"     First 5 values: {embedding[:5]}")
        print()
        return True
        
    except Exception as e:
        print(f"  ❌ Embeddings Error: {e}")
        return False


async def test_pinecone_real():
    """Test REAL Pinecone connection"""
    print("=" * 60)
    print("  TEST 3: Real Pinecone Connection")
    print("=" * 60)
    
    try:
        from pinecone import Pinecone
        
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key or api_key.startswith("your_"):
            print("  ⚠️  Pinecone API key not set, skipping...")
            return False
            
        pc = Pinecone(api_key=api_key)
        
        print("  Connecting to Pinecone...")
        indexes = pc.list_indexes()
        
        print(f"\n  ✅ REAL Pinecone connected!")
        print(f"     Available indexes: {[idx.name for idx in indexes]}")
        print()
        return True
        
    except Exception as e:
        print(f"  ❌ Pinecone Error: {e}")
        return False


async def test_hunter_real():
    """Test REAL Hunter.io API"""
    print("=" * 60)
    print("  TEST 4: Real Hunter.io Email Verification")
    print("=" * 60)
    
    try:
        import httpx
        
        api_key = os.getenv("HUNTER_API_KEY")
        if not api_key or api_key.startswith("your_"):
            print("  ⚠️  Hunter.io API key not set, skipping...")
            return False
        
        print("  Verifying email: test@google.com...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.hunter.io/v2/email-verifier",
                params={
                    "email": "test@google.com",
                    "api_key": api_key
                }
            )
            
            data = response.json()
            
            if "data" in data:
                result = data["data"]
                print(f"\n  ✅ REAL Hunter.io response!")
                print(f"     Email: {result.get('email')}")
                print(f"     Status: {result.get('status')}")
                print(f"     Score: {result.get('score')}")
            else:
                print(f"  ⚠️  Hunter.io response: {data}")
        
        print()
        return True
        
    except Exception as e:
        print(f"  ❌ Hunter.io Error: {e}")
        return False


async def test_growthbook_real():
    """Test REAL GrowthBook (local mode)"""
    print("=" * 60)
    print("  TEST 5: Real GrowthBook Feature Flags")
    print("=" * 60)
    
    try:
        from mcp_servers.growthbook_mcp import GrowthBookClient
        
        client = GrowthBookClient(local_mode=True)
        
        # This is REAL - actually evaluates the flag
        is_enabled = client.is_on("enable_research_agent")
        
        print(f"\n  ✅ REAL GrowthBook evaluation!")
        print(f"     enable_research_agent: {is_enabled}")
        
        # Create a real experiment and get variant
        await client.create_experiment(
            key="test_experiment",
            name="Test Experiment",
            variations=[
                {"key": "control", "weight": 50},
                {"key": "treatment", "weight": 50}
            ]
        )
        await client.start_experiment("test_experiment")
        
        # This is REAL - uses hash-based assignment
        variant = client.get_experiment_variant("test_experiment", "user-123")
        print(f"     Experiment variant for user-123: {variant}")
        print()
        return True
        
    except Exception as e:
        print(f"  ❌ GrowthBook Error: {e}")
        return False


async def test_database_real():
    """Test REAL PostgreSQL connection"""
    print("=" * 60)
    print("  TEST 6: Real PostgreSQL Database")
    print("=" * 60)
    
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "ai_sdr"),
            user=os.getenv("POSTGRES_USER", "ai_sdr_user"),
            password=os.getenv("POSTGRES_PASSWORD", "demo_password_123")
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        print(f"\n  ✅ REAL PostgreSQL connected!")
        print(f"     Version: {version[:50]}...")
        
        cursor.close()
        conn.close()
        print()
        return True
        
    except Exception as e:
        print(f"  ❌ PostgreSQL Error: {e}")
        print(f"     (Make sure Docker containers are running)")
        return False


async def main():
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║      AI SDR PLATFORM - REAL API INTEGRATION TEST         ║")
    print("║                                                           ║")
    print("║   This tests ACTUAL API calls, not simulated ones!       ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    
    # Check API keys first
    has_openai = check_api_keys()
    
    results = {}
    
    # Run real tests
    if has_openai:
        results["OpenAI Chat"] = await test_openai_real()
        results["OpenAI Embeddings"] = await test_embeddings_real()
    else:
        print("  ⚠️  Skipping OpenAI tests - API key not configured\n")
        results["OpenAI Chat"] = False
        results["OpenAI Embeddings"] = False
    
    results["Pinecone"] = await test_pinecone_real()
    results["Hunter.io"] = await test_hunter_real()
    results["GrowthBook"] = await test_growthbook_real()
    results["PostgreSQL"] = await test_database_real()
    
    # Summary
    print("=" * 60)
    print("  SUMMARY: Real Integration Tests")
    print("=" * 60)
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print()
    print(f"  Results: {passed_count}/{total_count} tests passed")
    print()
    
    if passed_count == total_count:
        print("  🎉 All integrations working! Your platform is fully connected.")
    elif passed_count > 0:
        print("  ⚠️  Some integrations need configuration. Check your .env file.")
    else:
        print("  ❌ No integrations working. Please configure your API keys.")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())
