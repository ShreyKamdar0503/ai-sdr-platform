"""
Fixed Copywriting Agent

Key Fixes:
1. Properly handles input from orchestrator
2. Generates 2 email variants reliably
3. Better error handling
4. Uses research data effectively
"""

import os
import asyncio
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI


class CopywritingAgent:
    """
    AI-powered copywriting agent for personalized sales emails
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            temperature=0.7  # Add some creativity
        )
    
    async def process(self, context: Dict) -> List[Dict]:
        """
        Generate personalized email variants based on research
        
        Args:
            context: Dict containing:
                - lead: Lead data (firstName, lastName, company, title, email)
                - research: Research results
                - company_summary: Company description
                - tech_stack: Detected technologies
                - hiring_departments: Active hiring areas
                - recent_news: Recent company news
                - hooks: Engagement hooks from research
        
        Returns:
            List of email variants with subject and body
        """
        
        # Extract data from context
        lead = context.get("lead", {})
        research = context.get("research", {})
        company_info = research.get("company_info", {})
        
        first_name = lead.get("firstName", "there")
        last_name = lead.get("lastName", "")
        company = lead.get("company", "your company")
        title = lead.get("title", "")
        email = lead.get("email", "")
        
        # Get research insights
        company_summary = context.get("company_summary") or company_info.get("summary", "")
        tech_stack = context.get("tech_stack") or company_info.get("tech_stack", [])
        hiring = context.get("hiring_departments") or company_info.get("hiring_departments", [])
        news = context.get("recent_news") or company_info.get("recent_news", [])
        hooks = context.get("hooks") or research.get("hooks", [])
        
        # Build the prompt
        prompt = f"""You are an expert SDR writing personalized cold emails. Generate 2 email variants for this lead.

## LEAD INFORMATION
- Name: {first_name} {last_name}
- Title: {title}
- Company: {company}
- Email: {email}

## RESEARCH INSIGHTS
- Company Summary: {company_summary[:500] if company_summary else 'Technology company'}
- Tech Stack: {', '.join(tech_stack[:5]) if tech_stack else 'Not detected'}
- Currently Hiring: {', '.join(hiring[:5]) if hiring else 'Unknown'}
- Recent News: {news[0] if news and news[0] != 'Recent company activity' else 'No recent news'}

## ENGAGEMENT HOOKS (use these for personalization)
{chr(10).join([f'- {hook}' for hook in hooks[:3]]) if hooks else '- General industry trends'}

---

Generate exactly 2 email variants. Each email should:
1. Be personalized using the research data above
2. Reference something specific about the company (tech stack, hiring, news)
3. Be concise (under 150 words)
4. Have a clear, compelling subject line
5. End with a soft CTA (no aggressive sales pitch)

Format your response EXACTLY like this:

VARIANT A
SUBJECT: [Your subject line here]
BODY:
[Your email body here]

VARIANT B
SUBJECT: [Your subject line here]  
BODY:
[Your email body here]

Generate the emails now:"""

        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content
            
            # Parse the response
            emails = self._parse_email_response(content, lead, company)
            
            if emails:
                return emails
            else:
                # Fallback if parsing fails
                return self._generate_fallback_emails(lead, company_summary, tech_stack, hooks)
                
        except Exception as e:
            print(f"  ❌ Copywriting error: {str(e)[:100]}")
            return self._generate_fallback_emails(lead, company_summary, tech_stack, hooks)
    
    def _parse_email_response(self, content: str, lead: Dict, company: str) -> List[Dict]:
        """Parse the LLM response into email variants"""
        emails = []
        
        try:
            # Split by VARIANT
            parts = content.split("VARIANT")
            
            for i, part in enumerate(parts[1:], 1):  # Skip first empty part
                email = {"variant": chr(64 + i)}  # A, B, C...
                
                # Extract subject
                if "SUBJECT:" in part:
                    subject_start = part.index("SUBJECT:") + 8
                    subject_end = part.find("\n", subject_start)
                    email["subject"] = part[subject_start:subject_end].strip()
                else:
                    email["subject"] = f"Quick question about {company}"
                
                # Extract body
                if "BODY:" in part:
                    body_start = part.index("BODY:") + 5
                    # Body goes until next VARIANT or end
                    body = part[body_start:].strip()
                    email["body"] = body
                else:
                    email["body"] = ""
                
                if email.get("body"):
                    emails.append(email)
            
            return emails[:2]  # Return max 2 variants
            
        except Exception as e:
            print(f"  ⚠️ Email parsing error: {e}")
            return []
    
    def _generate_fallback_emails(self, lead: Dict, summary: str, tech_stack: List, hooks: List) -> List[Dict]:
        """Generate fallback emails if LLM fails"""
        first_name = lead.get("firstName", "there")
        company = lead.get("company", "your company")
        title = lead.get("title", "")
        
        # Build personalization
        personalization = ""
        if tech_stack:
            personalization = f"I noticed {company} is using {tech_stack[0]}"
        elif hooks:
            personalization = hooks[0]
        else:
            personalization = f"I've been following {company}'s growth"
        
        return [
            {
                "variant": "A",
                "subject": f"Quick question about {company}",
                "body": f"""Hi {first_name},

{personalization} and thought I'd reach out.

I work with companies like {company} to help them scale their operations more efficiently. Given your role as {title}, I thought you might find our approach interesting.

Would you be open to a quick 15-minute chat to see if there's a fit?

Best regards"""
            },
            {
                "variant": "B",
                "subject": f"Helping {company} scale faster",
                "body": f"""Hi {first_name},

{personalization} - exciting times!

I specialize in helping {title}s at companies like {company} navigate growth challenges. I have some ideas that might be valuable for your team.

Do you have 15 minutes this week for a brief call?

Cheers"""
            }
        ]


# Test function
async def test_copywriting():
    """Test the copywriting agent"""
    agent = CopywritingAgent()
    
    print("\n" + "=" * 70)
    print("  🧪 COPYWRITING AGENT TEST")
    print("=" * 70)
    
    context = {
        "lead": {
            "firstName": "Sam",
            "lastName": "Altman",
            "company": "OpenAI",
            "title": "CEO",
            "email": "sam@openai.com"
        },
        "research": {
            "company_info": {
                "summary": "OpenAI is an AI research company focused on developing safe and beneficial artificial general intelligence.",
                "tech_stack": ["Python", "PyTorch", "Kubernetes"],
                "hiring_departments": ["Engineering", "Research", "Safety"],
                "recent_news": ["OpenAI launches GPT-5", "Partnership with Microsoft expands"]
            },
            "hooks": [
                "Given OpenAI's focus on AI safety, how are you balancing innovation speed with responsible development?",
                "With your recent hiring surge in Engineering, what challenges are you facing in scaling your team?"
            ]
        },
        "company_summary": "OpenAI is a leading AI research company.",
        "tech_stack": ["Python", "PyTorch"],
        "hooks": ["AI safety is a key focus area"]
    }
    
    emails = await agent.process(context)
    
    print(f"\n  Generated {len(emails)} emails:\n")
    
    for email in emails:
        print(f"  📧 Variant {email.get('variant', '?')}:")
        print(f"     Subject: {email.get('subject', 'N/A')}")
        print(f"     Body:\n{email.get('body', 'N/A')}")
        print()
    
    print("  ✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_copywriting())
