"""Script to update orchestrator to use enhanced research"""

import re

# Read the orchestrator file
with open('agentic_mesh/orchestrator.py', 'r') as f:
    content = f.read()

# Check if already using integrated agent
if 'integrated_research_agent' in content:
    print("✅ Orchestrator already using integrated research agent!")
else:
    # Update the import
    old_import = "from agentic_mesh.agents.research_agent import ResearchAgent"
    new_import = """# Try to use enhanced research agent, fallback to basic
try:
    from agentic_mesh.agents.integrated_research_agent import IntegratedResearchAgent as ResearchAgent
    print("  🔬 Using Enhanced Research Agent (Playwright + OpenAI)")
except ImportError:
    from agentic_mesh.agents.research_agent import ResearchAgent
    print("  📝 Using Basic Research Agent (OpenAI only)")"""
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        
        with open('agentic_mesh/orchestrator.py', 'w') as f:
            f.write(content)
        
        print("✅ Updated orchestrator to use enhanced research agent!")
    else:
        print("⚠️ Could not find import to replace. Manual update may be needed.")
        print("   Add this import at the top of orchestrator.py:")
        print(new_import)

