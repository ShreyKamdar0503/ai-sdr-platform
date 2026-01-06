"""
REAL Research Agent - Actually scrapes live data using Playwright
This replaces the placeholder research_agent.py with real functionality

Requirements:
- pip install playwright aiohttp openai
- playwright install chromium
- Set OPENAI_API_KEY environment variable
"""

import asyncio
import os
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlparse, urljoin

# Playwright for browser automation
try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright not installed. Run: pip install playwright && playwright install chromium")

# OpenAI for analysis
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not installed. Run: pip install openai")

# aiohttp for API calls
import aiohttp


class RealResearchAgent:
    """
    Production-ready research agent that scrapes REAL data from:
    - Company websites (tech stack, about info)
    - Google News (recent articles)
    - LinkedIn Jobs (hiring data)
    - Reddit (community mentions)
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.openai_client = None
        
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Tech stack signatures to detect
        self.tech_signatures = {
            # CRMs
            "Salesforce": ["force.com", "salesforce.com", "lightning.force", "visualforce"],
            "HubSpot": ["hubspot", "hs-scripts", "hs-analytics", "hbspt", "hubapi"],
            "Pipedrive": ["pipedrive"],
            "Zoho": ["zoho.com", "zohocdn"],
            
            # Sales Tools
            "Outreach": ["outreach.io", "outreach-cdn"],
            "Salesloft": ["salesloft"],
            "Apollo": ["apollo.io"],
            "ZoomInfo": ["zoominfo"],
            "Gong": ["gong.io"],
            "Chorus": ["chorus.ai"],
            "Drift": ["drift.com", "driftt"],
            "Intercom": ["intercom.io", "intercomcdn"],
            
            # Marketing
            "Marketo": ["marketo", "munchkin"],
            "Pardot": ["pardot", "pi.pardot"],
            "Mailchimp": ["mailchimp", "chimpstatic"],
            "ActiveCampaign": ["activecampaign"],
            "Klaviyo": ["klaviyo"],
            
            # Analytics
            "Google Analytics": ["google-analytics", "googletagmanager", "gtag", "ga.js"],
            "Segment": ["segment.com", "segment.io", "analytics.js/v1"],
            "Mixpanel": ["mixpanel"],
            "Amplitude": ["amplitude.com"],
            "Heap": ["heap-api", "heapanalytics"],
            "Hotjar": ["hotjar", "static.hotjar"],
            "FullStory": ["fullstory"],
            
            # Dev/Infrastructure
            "AWS": ["amazonaws.com", "aws-sdk"],
            "Google Cloud": ["googleapis.com", "gstatic"],
            "Cloudflare": ["cloudflare", "cdnjs.cloudflare"],
            "Fastly": ["fastly"],
            "Vercel": ["vercel", "vercel-analytics"],
            "Netlify": ["netlify"],
            
            # Frameworks
            "React": ["react", "reactjs", "_next"],
            "Vue": ["vue.js", "vuejs"],
            "Angular": ["angular", "ng-"],
            "Next.js": ["_next/static", "nextjs"],
            "WordPress": ["wp-content", "wp-includes", "wordpress"],
            "Shopify": ["shopify", "cdn.shopify"],
            "Webflow": ["webflow"],
            
            # Support
            "Zendesk": ["zendesk", "zdassets"],
            "Freshdesk": ["freshdesk", "freshworks"],
            "Crisp": ["crisp.chat"],
            
            # HR
            "Workday": ["workday"],
            "Greenhouse": ["greenhouse.io", "boards.greenhouse"],
            "Lever": ["lever.co", "jobs.lever"],
            "BambooHR": ["bamboohr"],
        }
    
    async def init_browser(self):
        """Initialize Playwright browser"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not installed")
        
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
    
    async def close(self):
        """Cleanup browser"""
        if self.browser:
            await self.browser.close()
            self.browser = None
    
    async def get_page(self) -> Page:
        """Get a new browser page with realistic settings"""
        await self.init_browser()
        context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        return await context.new_page()
    
    async def process(self, lead_data: Dict) -> Dict:
        """
        Main entry point - processes a lead and returns comprehensive research
        """
        company = lead_data.get("company", "")
        website = lead_data.get("website", "")
        email = lead_data.get("email", "")
        title = lead_data.get("title", "")
        
        # Infer website from email if not provided
        if not website and email:
            domain = email.split("@")[-1]
            if domain and domain not in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]:
                website = f"https://{domain}"
        
        # If still no website, try to find it
        if not website:
            website = await self._find_company_website(company)
        
        print(f"🔬 Researching {company} ({website})...")
        
        results = {
            "company_info": {},
            "contact_info": {},
            "tech_stack": [],
            "hiring_data": {},
            "recent_news": [],
            "competitors_detected": [],
            "hooks": [],
            "quality_score": 0,
            "research_type": "real",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Run all research in parallel
            tasks = [
                self._scrape_website(website, company),
                self._scrape_linkedin_jobs(company),
                self._scrape_google_news(company),
                self._search_reddit(company),
            ]
            
            website_data, hiring_data, news_data, reddit_data = await asyncio.gather(
                *tasks, return_exceptions=True
            )
            
            # Process website data
            if isinstance(website_data, dict):
                results["company_info"] = website_data.get("company_info", {})
                results["tech_stack"] = website_data.get("tech_stack", [])
                results["competitors_detected"] = self._identify_competitors(results["tech_stack"])
            
            # Process hiring data
            if isinstance(hiring_data, dict):
                results["hiring_data"] = hiring_data
            
            # Process news
            if isinstance(news_data, list):
                results["recent_news"] = news_data
            
            # Process Reddit data
            if isinstance(reddit_data, dict):
                results["reddit_mentions"] = reddit_data
            
            # Generate engagement hooks using AI
            results["hooks"] = await self._generate_hooks(results, lead_data)
            
            # Calculate quality score
            results["quality_score"] = self._calculate_quality_score(results)
            
            # Add contact analysis
            results["contact_info"] = self._analyze_contact(lead_data)
            
        except Exception as e:
            print(f"❌ Research error: {e}")
            results["error"] = str(e)
        
        finally:
            await self.close()
        
        return results
    
    async def _find_company_website(self, company: str) -> str:
        """Find company website via Google search"""
        try:
            page = await self.get_page()
            search_query = f"{company} official website"
            await page.goto(f"https://www.google.com/search?q={search_query}", timeout=15000)
            
            # Get first result
            first_result = await page.query_selector('div.g a[href^="http"]')
            if first_result:
                href = await first_result.get_attribute("href")
                await page.close()
                return href
            
            await page.close()
        except Exception as e:
            print(f"Could not find website: {e}")
        
        return ""
    
    async def _scrape_website(self, website: str, company: str) -> Dict:
        """Scrape company website for tech stack and company info"""
        if not website:
            return {}
        
        result = {
            "company_info": {
                "name": company,
                "website": website,
                "summary": "",
                "industry": "",
                "headquarters": "",
            },
            "tech_stack": []
        }
        
        try:
            page = await self.get_page()
            
            # Navigate to website
            await page.goto(website, timeout=30000, wait_until="domcontentloaded")
            
            # Get page HTML and scripts
            html = await page.content()
            
            # Detect tech stack from HTML
            detected_tech = []
            for tech, signatures in self.tech_signatures.items():
                for sig in signatures:
                    if sig.lower() in html.lower():
                        if tech not in detected_tech:
                            detected_tech.append(tech)
                        break
            
            result["tech_stack"] = detected_tech
            
            # Get meta description
            meta_desc = await page.query_selector('meta[name="description"]')
            if meta_desc:
                desc = await meta_desc.get_attribute("content")
                result["company_info"]["summary"] = desc
            
            # Get page title
            title = await page.title()
            if not result["company_info"]["summary"]:
                result["company_info"]["summary"] = title
            
            # Try to find About page
            about_link = await page.query_selector('a[href*="about"]')
            if about_link:
                try:
                    about_url = await about_link.get_attribute("href")
                    if about_url:
                        if not about_url.startswith("http"):
                            about_url = urljoin(website, about_url)
                        
                        await page.goto(about_url, timeout=15000)
                        
                        # Get about page content
                        about_content = await page.inner_text("body")
                        
                        # Extract key info using regex
                        # Look for employee count
                        emp_match = re.search(r'(\d{1,3}(?:,\d{3})*)\+?\s*(?:employees|team members|people)', about_content, re.I)
                        if emp_match:
                            result["company_info"]["employee_count"] = emp_match.group(1)
                        
                        # Look for founding year
                        year_match = re.search(r'(?:founded|established|since)\s*(?:in\s*)?(\d{4})', about_content, re.I)
                        if year_match:
                            result["company_info"]["founded"] = year_match.group(1)
                        
                        # Look for headquarters
                        hq_match = re.search(r'(?:headquartered|based|located)\s+(?:in\s+)?([A-Z][a-zA-Z\s,]+(?:CA|NY|TX|WA|MA|IL|CO|FL|GA|NC|VA|PA|OH|AZ|OR|NV))', about_content)
                        if hq_match:
                            result["company_info"]["headquarters"] = hq_match.group(1).strip()
                
                except Exception as e:
                    print(f"Could not scrape about page: {e}")
            
            # Try careers page for more hiring signals
            careers_link = await page.query_selector('a[href*="careers"], a[href*="jobs"]')
            if careers_link:
                try:
                    careers_url = await careers_link.get_attribute("href")
                    if careers_url:
                        if not careers_url.startswith("http"):
                            careers_url = urljoin(website, careers_url)
                        result["company_info"]["careers_url"] = careers_url
                except:
                    pass
            
            await page.close()
            
        except PlaywrightTimeout:
            print(f"⚠️ Timeout scraping {website}")
        except Exception as e:
            print(f"❌ Error scraping website: {e}")
        
        return result
    
    async def _scrape_linkedin_jobs(self, company: str) -> Dict:
        """Scrape LinkedIn for job postings to understand hiring patterns"""
        hiring_data = {
            "total_jobs": 0,
            "departments": {},
            "locations": [],
            "job_titles": [],
            "growth_signal": "unknown"
        }
        
        try:
            page = await self.get_page()
            
            # Search LinkedIn jobs (public, no login required)
            search_url = f"https://www.linkedin.com/jobs/search?keywords={company}&location=United%20States"
            await page.goto(search_url, timeout=20000)
            
            await asyncio.sleep(2)  # Wait for dynamic content
            
            # Get job count
            job_count_el = await page.query_selector('.results-context-header__job-count')
            if job_count_el:
                count_text = await job_count_el.inner_text()
                count_match = re.search(r'([\d,]+)', count_text)
                if count_match:
                    hiring_data["total_jobs"] = int(count_match.group(1).replace(",", ""))
            
            # Get job cards
            job_cards = await page.query_selector_all('.base-card')
            
            for card in job_cards[:15]:  # First 15 jobs
                try:
                    title_el = await card.query_selector('.base-search-card__title')
                    if title_el:
                        title = await title_el.inner_text()
                        hiring_data["job_titles"].append(title.strip())
                        
                        # Categorize by department
                        title_lower = title.lower()
                        if any(kw in title_lower for kw in ["engineer", "developer", "software", "devops", "sre", "data"]):
                            hiring_data["departments"]["Engineering"] = hiring_data["departments"].get("Engineering", 0) + 1
                        elif any(kw in title_lower for kw in ["sales", "account", "sdr", "bdr", "ae"]):
                            hiring_data["departments"]["Sales"] = hiring_data["departments"].get("Sales", 0) + 1
                        elif any(kw in title_lower for kw in ["marketing", "content", "seo", "growth"]):
                            hiring_data["departments"]["Marketing"] = hiring_data["departments"].get("Marketing", 0) + 1
                        elif any(kw in title_lower for kw in ["product", "pm", "ux", "design"]):
                            hiring_data["departments"]["Product"] = hiring_data["departments"].get("Product", 0) + 1
                        elif any(kw in title_lower for kw in ["hr", "recruit", "people", "talent"]):
                            hiring_data["departments"]["HR"] = hiring_data["departments"].get("HR", 0) + 1
                        elif any(kw in title_lower for kw in ["finance", "account", "controller"]):
                            hiring_data["departments"]["Finance"] = hiring_data["departments"].get("Finance", 0) + 1
                        elif any(kw in title_lower for kw in ["customer", "success", "support"]):
                            hiring_data["departments"]["Customer Success"] = hiring_data["departments"].get("Customer Success", 0) + 1
                    
                    location_el = await card.query_selector('.job-search-card__location')
                    if location_el:
                        location = await location_el.inner_text()
                        if location.strip() not in hiring_data["locations"]:
                            hiring_data["locations"].append(location.strip())
                
                except Exception:
                    continue
            
            # Determine growth signal
            total = hiring_data["total_jobs"]
            if total >= 100:
                hiring_data["growth_signal"] = "hypergrowth"
            elif total >= 50:
                hiring_data["growth_signal"] = "rapid"
            elif total >= 20:
                hiring_data["growth_signal"] = "growing"
            elif total >= 5:
                hiring_data["growth_signal"] = "moderate"
            else:
                hiring_data["growth_signal"] = "stable"
            
            await page.close()
            
        except Exception as e:
            print(f"❌ Error scraping LinkedIn jobs: {e}")
        
        return hiring_data
    
    async def _scrape_google_news(self, company: str) -> List[Dict]:
        """Scrape Google News for recent company mentions"""
        news = []
        
        try:
            page = await self.get_page()
            
            # Google News search
            search_url = f"https://www.google.com/search?q={company}&tbm=nws"
            await page.goto(search_url, timeout=15000)
            
            # Get news cards
            news_items = await page.query_selector_all('div.SoaBEf')
            
            for item in news_items[:5]:  # Top 5 news
                try:
                    title_el = await item.query_selector('div.MBeuO')
                    link_el = await item.query_selector('a')
                    source_el = await item.query_selector('div.MgUUmf')
                    time_el = await item.query_selector('div.LfVVr')
                    
                    if title_el and link_el:
                        news.append({
                            "title": await title_el.inner_text(),
                            "url": await link_el.get_attribute("href"),
                            "source": await source_el.inner_text() if source_el else "Unknown",
                            "date": await time_el.inner_text() if time_el else "Recent"
                        })
                except Exception:
                    continue
            
            await page.close()
            
        except Exception as e:
            print(f"❌ Error scraping news: {e}")
        
        return news
    
    async def _search_reddit(self, company: str) -> Dict:
        """Search Reddit for company mentions using Reddit's JSON API"""
        reddit_data = {
            "mentions": [],
            "sentiment": "neutral",
            "subreddits": []
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Reddit JSON API (no auth needed)
                url = f"https://www.reddit.com/search.json?q={company}&sort=relevance&limit=10"
                headers = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}
                
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for post in data.get("data", {}).get("children", []):
                            post_data = post.get("data", {})
                            reddit_data["mentions"].append({
                                "title": post_data.get("title", ""),
                                "subreddit": post_data.get("subreddit", ""),
                                "score": post_data.get("score", 0),
                                "url": f"https://reddit.com{post_data.get('permalink', '')}",
                                "created": post_data.get("created_utc", 0)
                            })
                            
                            sub = post_data.get("subreddit", "")
                            if sub and sub not in reddit_data["subreddits"]:
                                reddit_data["subreddits"].append(sub)
                        
                        # Simple sentiment based on scores
                        total_score = sum(m.get("score", 0) for m in reddit_data["mentions"])
                        if total_score > 100:
                            reddit_data["sentiment"] = "positive"
                        elif total_score < 0:
                            reddit_data["sentiment"] = "negative"
        
        except Exception as e:
            print(f"❌ Error searching Reddit: {e}")
        
        return reddit_data
    
    def _identify_competitors(self, tech_stack: List[str]) -> List[Dict]:
        """Identify what competitor tools they're using"""
        competitors = []
        
        competitor_categories = {
            "CRM": ["Salesforce", "HubSpot", "Pipedrive", "Zoho"],
            "Sales Engagement": ["Outreach", "Salesloft", "Apollo"],
            "Data Provider": ["ZoomInfo", "Apollo"],
            "Conversation Intelligence": ["Gong", "Chorus"],
            "Live Chat": ["Drift", "Intercom"],
            "Marketing Automation": ["Marketo", "Pardot", "Mailchimp", "ActiveCampaign", "Klaviyo"],
        }
        
        for category, tools in competitor_categories.items():
            for tool in tools:
                if tool in tech_stack:
                    competitors.append({
                        "tool": tool,
                        "category": category,
                        "detected": True
                    })
        
        return competitors
    
    async def _generate_hooks(self, research: Dict, lead_data: Dict) -> List[str]:
        """Generate personalized engagement hooks using AI"""
        hooks = []
        
        # Basic hooks without AI
        hiring = research.get("hiring_data", {})
        news = research.get("recent_news", [])
        tech = research.get("tech_stack", [])
        company = lead_data.get("company", "")
        
        # Hiring-based hooks
        if hiring.get("total_jobs", 0) > 20:
            top_dept = max(hiring.get("departments", {}).items(), key=lambda x: x[1], default=("", 0))
            if top_dept[0]:
                hooks.append(f"I noticed {company} is hiring {hiring['total_jobs']}+ roles, especially in {top_dept[0]} ({top_dept[1]} positions)")
        
        # News-based hooks
        if news:
            hooks.append(f"Congrats on the recent news: '{news[0].get('title', '')[:60]}...'")
        
        # Tech-based hooks
        competitors = research.get("competitors_detected", [])
        if competitors:
            comp = competitors[0]
            hooks.append(f"I see you're using {comp['tool']} for {comp['category']} - we integrate seamlessly with that")
        
        # Use AI for better hooks if available
        if self.openai_client and len(hooks) < 3:
            try:
                prompt = f"""Based on this research about {company}, generate 2 personalized sales engagement hooks.
                
Research:
- Hiring: {json.dumps(hiring)}
- Recent News: {json.dumps(news[:2])}
- Tech Stack: {tech[:5]}
- Contact Title: {lead_data.get('title', '')}

Rules:
- Each hook should be 1-2 sentences
- Reference specific facts from the research
- Be conversational, not salesy
- Focus on their growth/challenges

Return just the hooks, one per line."""

                response = await self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.7
                )
                
                ai_hooks = response.choices[0].message.content.strip().split("\n")
                hooks.extend([h.strip("- ").strip() for h in ai_hooks if h.strip()])
                
            except Exception as e:
                print(f"Could not generate AI hooks: {e}")
        
        return hooks[:5]  # Return top 5 hooks
    
    def _calculate_quality_score(self, research: Dict) -> int:
        """Calculate research quality score (0-100)"""
        score = 0
        
        # Company info completeness (30 points)
        company_info = research.get("company_info", {})
        if company_info.get("summary"):
            score += 10
        if company_info.get("headquarters"):
            score += 5
        if company_info.get("employee_count"):
            score += 5
        if company_info.get("founded"):
            score += 5
        if company_info.get("careers_url"):
            score += 5
        
        # Tech stack (20 points)
        tech_count = len(research.get("tech_stack", []))
        score += min(tech_count * 4, 20)
        
        # Hiring data (20 points)
        hiring = research.get("hiring_data", {})
        if hiring.get("total_jobs", 0) > 0:
            score += 10
        if hiring.get("departments"):
            score += 5
        if hiring.get("locations"):
            score += 5
        
        # News (15 points)
        news_count = len(research.get("recent_news", []))
        score += min(news_count * 3, 15)
        
        # Hooks (15 points)
        hooks_count = len(research.get("hooks", []))
        score += min(hooks_count * 3, 15)
        
        return min(score, 100)
    
    def _analyze_contact(self, lead_data: Dict) -> Dict:
        """Analyze contact seniority and decision-maker status"""
        title = lead_data.get("title", "").lower()
        
        seniority = "unknown"
        is_decision_maker = False
        
        if any(t in title for t in ["ceo", "cto", "cfo", "coo", "cmo", "cro", "president", "founder", "owner"]):
            seniority = "c-suite"
            is_decision_maker = True
        elif any(t in title for t in ["vp", "vice president", "svp", "evp"]):
            seniority = "vp"
            is_decision_maker = True
        elif any(t in title for t in ["director", "head of"]):
            seniority = "director"
            is_decision_maker = True
        elif any(t in title for t in ["manager", "lead", "senior"]):
            seniority = "manager"
            is_decision_maker = False
        else:
            seniority = "individual_contributor"
            is_decision_maker = False
        
        return {
            "email": lead_data.get("email", ""),
            "title": lead_data.get("title", ""),
            "seniority": seniority,
            "is_decision_maker": is_decision_maker,
            "linkedin_url": f"https://linkedin.com/in/{lead_data.get('email', '').split('@')[0]}"
        }


# ============================================================================
# WRAPPER FOR EXISTING CODEBASE
# ============================================================================

class ResearchAgent:
    """
    Drop-in replacement for the original ResearchAgent
    Uses RealResearchAgent under the hood
    """
    
    def __init__(self):
        self.real_agent = RealResearchAgent()
    
    async def process(self, lead_data: Dict) -> Dict:
        """Process a lead - compatible with existing orchestrator"""
        results = await self.real_agent.process(lead_data)
        
        # Format for compatibility with existing code
        return {
            "company_info": {
                **results.get("company_info", {}),
                "tech_stack": results.get("tech_stack", []),
                "hiring_departments": list(results.get("hiring_data", {}).get("departments", {}).keys()),
                "recent_news": [n.get("title", "") for n in results.get("recent_news", [])],
            },
            "contact_info": results.get("contact_info", {}),
            "quality_score": results.get("quality_score", 0),
            "hooks": results.get("hooks", []),
            "research_type": "real",
            # Include full data for frontend
            "full_research": results
        }
    
    async def research_company(self, company_name: str) -> Dict:
        """Research company - for backward compatibility"""
        return await self.real_agent._scrape_website(f"https://{company_name}.com", company_name)
    
    async def enrich_contact(self, email: str) -> Dict:
        """Enrich contact - for backward compatibility"""
        return self.real_agent._analyze_contact({"email": email})


# ============================================================================
# TEST
# ============================================================================

async def test_research():
    """Test the research agent"""
    agent = RealResearchAgent()
    
    test_lead = {
        "firstName": "Sarah",
        "lastName": "Chen",
        "email": "sarah@nvidia.com",
        "company": "NVIDIA",
        "title": "VP of Sales",
        "website": "https://nvidia.com"
    }
    
    print("🔬 Starting real research...")
    results = await agent.process(test_lead)
    
    print("\n" + "="*60)
    print("📊 RESEARCH RESULTS")
    print("="*60)
    print(json.dumps(results, indent=2, default=str))
    
    return results


if __name__ == "__main__":
    asyncio.run(test_research())
