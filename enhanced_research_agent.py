"""
Enhanced Research Agent - VERSION 3

New Features:
1. Company summary (what they do, domain, headquarters/country)
2. News articles with clickable URLs
3. LinkedIn company URL
4. All previous fixes (deduplication, complete hooks)
"""

import os
import sys
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()

from langchain_openai import ChatOpenAI
from agentic_mesh.agents.playwright_research_agent import PlaywrightResearchAgent


class EnhancedResearchAgent:
    """Research agent combining live web scraping with AI analysis"""
    
    def __init__(self):
        self.playwright = PlaywrightResearchAgent()
        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini")
        )
        self.started = False
    
    async def start(self):
        if not self.started:
            await self.playwright.start()
            self.started = True
    
    async def stop(self):
        if self.started:
            await self.playwright.stop()
            self.started = False
    
    def _guess_website_url(self, company_name: str, email: str = None) -> str:
        """Guess company website from name or email domain"""
        if email and "@" in email:
            domain = email.split("@")[1]
            if domain not in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com"]:
                return f"https://www.{domain}"
        
        clean_name = company_name.lower()
        clean_name = clean_name.replace(" inc", "").replace(" llc", "").replace(" corp", "")
        clean_name = clean_name.replace(" ", "").replace(",", "").replace(".", "")
        
        return f"https://www.{clean_name}.com"
    
    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on title similarity"""
        if not articles:
            return []
        
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            title = article.get('title', '').strip().lower()
            title_key = title[:50]
            
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(article)
        
        return unique_articles
    
    async def scrape_news(self, company_name: str) -> Dict:
        """Scrape recent news about the company - WITH URLs"""
        if not self.started:
            await self.start()
        
        page = await self.playwright.context.new_page()
        result = {"company": company_name, "status": "success", "articles": []}
        
        try:
            search_query = f'"{company_name}" company business news 2024 2025'
            search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&tbm=nws"
            
            print(f'     📰 Searching news for "{company_name}" company...')
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Extract news WITH URLs
            articles = await page.evaluate('''() => {
                const results = [];
                const items = document.querySelectorAll('[data-news-doc-id], .SoaBEf, article, .WlydOe, .IBr9hb');
                
                items.forEach((item, index) => {
                    if (index >= 10) return;
                    
                    const titleEl = item.querySelector('h3, .mCBkyc, [role="heading"], .nDgy9d, .JheGif');
                    const linkEl = item.querySelector('a[href]');
                    const snippetEl = item.querySelector('.GI74Re, .Y3v8qd, .st, .VwiC3b');
                    const sourceEl = item.querySelector('.NUnG9d, .CEMjEf, .WF4CUc, .vr1PYe');
                    const timeEl = item.querySelector('.OSrXXb, time, .LfVVr');
                    
                    if (titleEl && titleEl.innerText && titleEl.innerText.length > 10) {
                        let url = null;
                        if (linkEl && linkEl.href) {
                            url = linkEl.href;
                            // Clean Google redirect URLs
                            if (url.includes('/url?q=')) {
                                const match = url.match(/[?&]q=([^&]+)/);
                                if (match) url = decodeURIComponent(match[1]);
                            }
                        }
                        
                        results.push({
                            title: titleEl.innerText.trim(),
                            url: url,
                            snippet: snippetEl ? snippetEl.innerText.trim() : null,
                            source: sourceEl ? sourceEl.innerText.trim() : null,
                            time: timeEl ? timeEl.innerText.trim() : null
                        });
                    }
                });
                return results;
            }''')
            
            unique_articles = self._deduplicate_articles(articles)
            
            company_lower = company_name.lower()
            relevant_articles = []
            
            for article in unique_articles:
                title_lower = article.get('title', '').lower()
                snippet_lower = (article.get('snippet') or '').lower()
                
                if company_lower in title_lower or company_lower in snippet_lower:
                    relevant_articles.append(article)
            
            if len(relevant_articles) >= 2:
                result["articles"] = relevant_articles[:5]
            else:
                result["articles"] = unique_articles[:5]
            
            print(f"     📰 Found {len(result['articles'])} unique news articles")
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        finally:
            await page.close()
        
        return result
    
    async def find_linkedin(self, company_name: str) -> Optional[str]:
        """Find the company's LinkedIn page"""
        if not self.started:
            await self.start()
        
        page = await self.playwright.context.new_page()
        linkedin_url = None
        
        try:
            search_url = f"https://www.google.com/search?q={company_name.replace(' ', '+')}+site:linkedin.com/company"
            
            print(f"     🔗 Searching for LinkedIn page...")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(1500)
            
            linkedin_url = await page.evaluate('''() => {
                const links = document.querySelectorAll('a[href*="linkedin.com/company"]');
                for (let link of links) {
                    const href = link.href;
                    if (href.includes('linkedin.com/company/')) {
                        // Clean up the URL
                        const match = href.match(/linkedin\\.com\\/company\\/[a-zA-Z0-9-]+/);
                        if (match) {
                            return 'https://www.' + match[0];
                        }
                    }
                }
                return null;
            }''')
            
            if linkedin_url:
                print(f"     🔗 Found LinkedIn: {linkedin_url}")
            else:
                print(f"     🔗 LinkedIn not found")
                
        except Exception as e:
            print(f"     ⚠️ LinkedIn search error: {str(e)[:50]}")
        finally:
            await page.close()
        
        return linkedin_url
    
    async def deep_research(self, lead_data: Dict) -> Dict:
        """Perform comprehensive research on a lead"""
        await self.start()
        
        company = lead_data.get("company", "Unknown")
        email = lead_data.get("email", "")
        first_name = lead_data.get("firstName", "")
        last_name = lead_data.get("lastName", "")
        title = lead_data.get("title", "")
        
        print(f"\n  🔬 Deep Research: {company}")
        print("  " + "=" * 50)
        
        result = {
            "company": company,
            "contact": f"{first_name} {last_name} ({title})",
            "timestamp": datetime.now().isoformat(),
            "live_data": {},
            "news": [],
            "ai_analysis": {},
            "quality_score": 0,
            "engagement_hooks": [],
            "playwright_used": True,
            "company_summary": "",
            "company_domain": "",
            "company_headquarters": "",
            "linkedin_url": None
        }
        
        # Step 1: Scrape company website
        website_url = self._guess_website_url(company, email)
        print(f"\n  1️⃣ Scraping website: {website_url}")
        print(f"     🎭 Using Playwright browser automation...")
        website_data = await self.playwright.research_company_website(website_url)
        result["live_data"]["website"] = website_data
        result["live_data"]["website_url"] = website_url
        
        # Step 2: Find careers/job info
        print(f"\n  2️⃣ Analyzing job postings...")
        jobs_data = await self.playwright.analyze_job_postings(website_url)
        result["live_data"]["jobs"] = jobs_data
        
        # Step 3: Search for news (with URLs)
        print(f"\n  3️⃣ Searching for recent news...")
        news_data = await self.scrape_news(company)
        result["news"] = news_data.get("articles", [])
        
        # Step 4: Find LinkedIn
        print(f"\n  4️⃣ Finding LinkedIn profile...")
        linkedin_url = await self.find_linkedin(company)
        result["linkedin_url"] = linkedin_url
        
        # Step 5: AI Analysis
        print(f"\n  5️⃣ AI analyzing all data...")
        
        news_text = ""
        for i, article in enumerate(result["news"][:5], 1):
            news_text += f"{i}. {article.get('title', 'N/A')}"
            if article.get('source'):
                news_text += f" ({article['source']})"
            if article.get('time'):
                news_text += f" - {article['time']}"
            news_text += "\n"
        
        analysis_prompt = f"""
You are a sales intelligence analyst. Analyze this LIVE data scraped from {company}'s online presence.

## CONTACT INFO
- Name: {first_name} {last_name}
- Title: {title}
- Email: {email}
- Company: {company}

## WEBSITE DATA
- URL: {website_url}
- Title: {website_data.get('data', {}).get('title', 'N/A')}
- Description: {website_data.get('data', {}).get('description', 'N/A')}
- Tech Stack Detected: {website_data.get('data', {}).get('tech_stack', [])}
- Social Links: {len(website_data.get('data', {}).get('social_links', []))} found

## HIRING DATA
- Careers Page: {jobs_data.get('insights', {}).get('careers_page', 'Not found')}
- Hiring Departments: {jobs_data.get('insights', {}).get('hiring_departments', [])}
- Open Positions: {jobs_data.get('insights', {}).get('open_positions', 'Unknown')}

## RECENT NEWS
{news_text if news_text else 'No recent news found'}

---

Provide analysis with these EXACT sections:

**COMPANY OVERVIEW**
In exactly 2 sentences: What does {company} do? What industry/domain are they in?

**HEADQUARTERS**
What country/city is {company} headquartered in? (If unknown, make best guess based on website)

**DOMAIN**
What is their primary business domain? (e.g., Healthcare, Technology, Finance, Retail, etc.)

**GROWTH SIGNALS**
List 2-3 specific indicators that the company is growing.

**ENGAGEMENT HOOKS**
Write exactly 3 COMPLETE conversation starters for {first_name}. Each hook should be:
- A full sentence (20-40 words)
- Reference specific data (tech stack, hiring, news)
- Be conversational and personalized

Format hooks as:
1. [Complete hook here]
2. [Complete hook here]
3. [Complete hook here]

**RESEARCH QUALITY**
Rate 1-10 based on data quality.
"""
        
        try:
            ai_response = await self.llm.ainvoke(analysis_prompt)
            result["ai_analysis"]["full_analysis"] = ai_response.content
            content = ai_response.content
            
            # Extract company overview/summary
            if "COMPANY OVERVIEW" in content:
                summary_section = content.split("COMPANY OVERVIEW")[1]
                for end_marker in ["**HEADQUARTERS", "HEADQUARTERS", "**DOMAIN", "DOMAIN"]:
                    if end_marker in summary_section:
                        summary_section = summary_section.split(end_marker)[0]
                        break
                result["company_summary"] = summary_section.strip().strip("*").strip().replace("\n", " ")[:300]
            
            # Extract headquarters
            if "HEADQUARTERS" in content:
                hq_section = content.split("HEADQUARTERS")[1]
                for end_marker in ["**DOMAIN", "DOMAIN", "**GROWTH"]:
                    if end_marker in hq_section:
                        hq_section = hq_section.split(end_marker)[0]
                        break
                result["company_headquarters"] = hq_section.strip().strip("*").strip().replace("\n", " ")[:100]
            
            # Extract domain
            if "DOMAIN" in content.upper():
                domain_section = content.upper().split("DOMAIN")[1]
                domain_section = content[content.upper().find("DOMAIN") + 6:]
                for end_marker in ["**GROWTH", "GROWTH SIGNALS", "**ENGAGEMENT"]:
                    if end_marker in domain_section.upper():
                        idx = domain_section.upper().find(end_marker)
                        domain_section = domain_section[:idx]
                        break
                result["company_domain"] = domain_section.strip().strip("*").strip().replace("\n", " ")[:100]
            
            # Extract engagement hooks
            hooks = []
            if "ENGAGEMENT HOOKS" in content:
                hooks_section = content.split("ENGAGEMENT HOOKS")[1]
                for end_marker in ["RESEARCH QUALITY", "**RESEARCH", "---"]:
                    if end_marker in hooks_section:
                        hooks_section = hooks_section.split(end_marker)[0]
                        break
                
                lines = hooks_section.split("\n")
                for line in lines:
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                        hook = line.lstrip("0123456789.-•) ").strip()
                        hook = hook.strip('"').strip("*").strip()
                        if len(hook) > 20:
                            hooks.append(hook)
            
            result["engagement_hooks"] = hooks[:3]
            
            print(f"     ✅ AI analysis complete! Generated {len(hooks)} engagement hooks")
            
        except Exception as e:
            result["ai_analysis"]["error"] = str(e)
            print(f"     ❌ AI analysis error: {str(e)[:100]}")
        
        # Calculate quality score
        score = 0
        if website_data.get("status") == "success":
            score += 20
            if website_data.get("data", {}).get("tech_stack"):
                score += 15
            if website_data.get("data", {}).get("social_links"):
                score += 5
        
        if jobs_data.get("insights", {}).get("careers_page"):
            score += 10
        if jobs_data.get("insights", {}).get("hiring_departments"):
            score += 10
        
        if result["news"]:
            score += 15
        
        if linkedin_url:
            score += 10
        
        if result["ai_analysis"].get("full_analysis"):
            score += 5
        
        if result["company_summary"]:
            score += 5
        
        if result["engagement_hooks"]:
            score += 5
        
        result["quality_score"] = min(score, 100)
        
        print(f"\n  📊 Research Quality Score: {result['quality_score']}/100")
        
        return result


async def test():
    """Test the enhanced research agent"""
    agent = EnhancedResearchAgent()
    
    try:
        lead = {
            "email": "ceo@stripe.com",
            "firstName": "Patrick",
            "lastName": "Collison",
            "company": "Stripe",
            "title": "CEO"
        }
        
        result = await agent.deep_research(lead)
        
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"Company: {result['company']}")
        print(f"Summary: {result['company_summary']}")
        print(f"Domain: {result['company_domain']}")
        print(f"HQ: {result['company_headquarters']}")
        print(f"LinkedIn: {result['linkedin_url']}")
        print(f"Quality: {result['quality_score']}/100")
        
        print("\nNews:")
        for article in result['news'][:3]:
            print(f"  - {article['title'][:60]}...")
            print(f"    URL: {article.get('url', 'N/A')}")
        
        print("\nHooks:")
        for hook in result['engagement_hooks']:
            print(f"  - {hook}")
            
    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(test())
