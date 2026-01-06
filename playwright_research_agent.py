"""
Playwright Research Agent - Live Web Scraping for Lead Research

This agent uses Playwright to scrape real-time data from:
- Company websites
- News articles
- Job postings
"""

import os
import asyncio
from typing import Dict, Optional
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()


class PlaywrightResearchAgent:
    """Agent that uses Playwright for live web research"""
    
    def __init__(self):
        self.browser = None
        self.playwright = None
        self.context = None
    
    async def start(self):
        """Start the browser with anti-detection settings"""
        self.playwright = await async_playwright().start()
        
        # Launch with anti-detection settings
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
        )
        
        print("🎭 Playwright browser started")
    
    async def stop(self):
        """Stop the browser"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("🎭 Playwright browser stopped")
    
    async def research_company_website(self, url: str) -> Dict:
        """
        Scrape company website for useful information
        """
        if not self.browser:
            await self.start()
        
        page = await self.context.new_page()
        result = {
            "url": url,
            "status": "success",
            "data": {}
        }
        
        try:
            # Navigate with longer timeout
            print(f"     Navigating to {url}...")
            response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait a bit for dynamic content
            await page.wait_for_timeout(2000)
            
            # Check response status
            if response:
                result["data"]["http_status"] = response.status
            
            # Extract basic info
            result["data"]["title"] = await page.title()
            print(f"     Page title: {result['data']['title']}")
            
            # Extract meta description
            try:
                meta_desc = await page.locator('meta[name="description"]').get_attribute("content", timeout=5000)
                result["data"]["description"] = meta_desc
            except:
                result["data"]["description"] = None
            
            # Extract main heading
            try:
                h1_text = await page.locator('h1').first.inner_text(timeout=5000)
                result["data"]["main_heading"] = h1_text
                print(f"     Main heading: {h1_text[:50]}...")
            except:
                result["data"]["main_heading"] = None
            
            # Extract all visible text for analysis
            try:
                body_text = await page.locator('body').inner_text(timeout=10000)
                result["data"]["text_preview"] = body_text[:1000]  # First 1000 chars
            except:
                result["data"]["text_preview"] = None
            
            # Extract technology stack from page source
            page_content = await page.content()
            tech_indicators = []
            
            tech_patterns = {
                "React": ["react", "__NEXT_DATA__", "gatsby"],
                "Vue.js": ["vue", "nuxt"],
                "Angular": ["angular", "ng-"],
                "WordPress": ["wp-content", "wordpress"],
                "Shopify": ["shopify", "myshopify"],
                "HubSpot": ["hubspot", "hs-scripts"],
                "Salesforce": ["salesforce", "pardot"],
                "Google Analytics": ["google-analytics", "gtag", "ga.js"],
                "Intercom": ["intercom"],
                "Drift": ["drift"],
                "Zendesk": ["zendesk"],
                "Segment": ["segment.com", "analytics.js"],
                "Mixpanel": ["mixpanel"],
                "Hotjar": ["hotjar"],
                "Cloudflare": ["cloudflare"],
            }
            
            for tech, patterns in tech_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in page_content.lower():
                        tech_indicators.append(tech)
                        break
            
            result["data"]["tech_stack"] = list(set(tech_indicators))
            print(f"     Tech stack detected: {result['data']['tech_stack']}")
            
            # Look for social links
            try:
                social_links = await page.evaluate('''() => {
                    const links = document.querySelectorAll('a[href*="linkedin.com"], a[href*="twitter.com"], a[href*="facebook.com"], a[href*="github.com"]');
                    return Array.from(links).map(a => ({
                        platform: a.href.includes('linkedin') ? 'LinkedIn' : 
                                  a.href.includes('twitter') ? 'Twitter' : 
                                  a.href.includes('github') ? 'GitHub' : 'Facebook',
                        url: a.href
                    })).filter((v, i, a) => a.findIndex(t => t.url === v.url) === i).slice(0, 5);
                }''')
                result["data"]["social_links"] = social_links
                print(f"     Social links found: {len(social_links)}")
            except:
                result["data"]["social_links"] = []
            
            # Look for email patterns
            try:
                emails = await page.evaluate('''() => {
                    const text = document.body.innerText;
                    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/g;
                    const found = text.match(emailRegex) || [];
                    return [...new Set(found)].filter(e => 
                        !e.includes('example') && 
                        !e.includes('test@') &&
                        !e.includes('email@')
                    ).slice(0, 5);
                }''')
                result["data"]["emails_found"] = emails
                print(f"     Emails found: {len(emails)}")
            except:
                result["data"]["emails_found"] = []
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"     ❌ Error: {str(e)[:100]}")
        
        finally:
            await page.close()
        
        return result
    
    async def find_contact_page(self, base_url: str) -> Dict:
        """Find and scrape contact page for email/phone"""
        if not self.browser:
            await self.start()
        
        page = await self.context.new_page()
        result = {
            "base_url": base_url,
            "status": "success",
            "contacts": [],
            "contact_page_url": None
        }
        
        try:
            await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)
            
            # Try to find contact link
            contact_selectors = [
                'a[href*="contact"]',
                'a[href*="about"]',
                'a[href*="support"]',
                'a:has-text("Contact")',
                'a:has-text("About")',
            ]
            
            contact_url = None
            for selector in contact_selectors:
                try:
                    link = page.locator(selector).first
                    if await link.count() > 0:
                        href = await link.get_attribute("href", timeout=3000)
                        if href:
                            if href.startswith("/"):
                                contact_url = base_url.rstrip("/") + href
                            elif href.startswith("http"):
                                contact_url = href
                            else:
                                contact_url = base_url.rstrip("/") + "/" + href
                            break
                except:
                    continue
            
            if contact_url:
                result["contact_page_url"] = contact_url
                print(f"     Found contact page: {contact_url}")
                await page.goto(contact_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(2000)
            
            # Extract emails
            emails = await page.evaluate('''() => {
                const text = document.body.innerText + ' ' + document.body.innerHTML;
                const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/g;
                const found = text.match(emailRegex) || [];
                return [...new Set(found)].filter(e => 
                    !e.includes('example') && 
                    !e.includes('test@') &&
                    !e.includes('sentry') &&
                    !e.includes('webpack')
                ).slice(0, 10);
            }''')
            
            result["contacts"] = [{"type": "email", "value": e} for e in emails]
            print(f"     Contacts found: {len(result['contacts'])}")
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"     ❌ Error: {str(e)[:100]}")
        
        finally:
            await page.close()
        
        return result
    
    async def analyze_job_postings(self, company_url: str) -> Dict:
        """Find and analyze job postings"""
        if not self.browser:
            await self.start()
        
        page = await self.context.new_page()
        result = {
            "company_url": company_url,
            "status": "success",
            "insights": {
                "careers_page": None,
                "open_positions": "Unknown",
                "hiring_departments": []
            }
        }
        
        try:
            await page.goto(company_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2000)
            
            # Find careers link
            careers_selectors = [
                'a[href*="careers"]',
                'a[href*="jobs"]',
                'a[href*="hiring"]',
                'a[href*="work-with-us"]',
                'a:has-text("Careers")',
                'a:has-text("Jobs")',
            ]
            
            careers_url = None
            for selector in careers_selectors:
                try:
                    link = page.locator(selector).first
                    if await link.count() > 0:
                        href = await link.get_attribute("href", timeout=3000)
                        if href:
                            if href.startswith("/"):
                                careers_url = company_url.rstrip("/") + href
                            elif href.startswith("http"):
                                careers_url = href
                            else:
                                careers_url = company_url.rstrip("/") + "/" + href
                            break
                except:
                    continue
            
            if careers_url:
                result["insights"]["careers_page"] = careers_url
                print(f"     Found careers page: {careers_url}")
                
                await page.goto(careers_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(2000)
                
                # Try to count job listings
                job_selectors = [
                    '[class*="job"]',
                    '[class*="position"]',
                    '[class*="opening"]',
                    '[class*="role"]',
                    'li:has(a[href*="job"])',
                ]
                
                for selector in job_selectors:
                    try:
                        count = await page.locator(selector).count()
                        if count > 0 and count < 500:
                            result["insights"]["open_positions"] = count
                            print(f"     Open positions: ~{count}")
                            break
                    except:
                        continue
                
                # Look for department keywords
                page_text = await page.locator('body').inner_text()
                departments = []
                for dept in ["Engineering", "Sales", "Marketing", "Product", "Design", "Data", "Finance", "Operations", "HR", "Legal"]:
                    if dept.lower() in page_text.lower():
                        departments.append(dept)
                
                result["insights"]["hiring_departments"] = departments
                print(f"     Hiring departments: {departments}")
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"     ❌ Error: {str(e)[:100]}")
        
        finally:
            await page.close()
        
        return result


# Test function
async def test_playwright_agent():
    """Test the Playwright agent"""
    agent = PlaywrightResearchAgent()
    
    try:
        await agent.start()
        
        print("\n" + "=" * 60)
        print("  🎭 PLAYWRIGHT RESEARCH AGENT TEST")
        print("=" * 60)
        
        # Test with a simpler website first (Wikipedia)
        print("\n1️⃣ Testing with Wikipedia (simple site)...")
        result = await agent.research_company_website("https://www.wikipedia.org")
        print(f"   Status: {result['status']}")
        print(f"   Title: {result['data'].get('title', 'N/A')}")
        
        # Test 2: Try HubSpot (marketing friendly)
        print("\n2️⃣ Testing with HubSpot...")
        result = await agent.research_company_website("https://www.hubspot.com")
        print(f"   Status: {result['status']}")
        print(f"   Title: {result['data'].get('title', 'N/A')}")
        print(f"   Tech Stack: {result['data'].get('tech_stack', [])}")
        print(f"   Social Links: {len(result['data'].get('social_links', []))} found")
        
        # Test 3: Find contact info
        print("\n3️⃣ Finding contact info on HubSpot...")
        contacts = await agent.find_contact_page("https://www.hubspot.com")
        print(f"   Status: {contacts['status']}")
        print(f"   Contact page: {contacts.get('contact_page_url', 'Not found')}")
        print(f"   Contacts found: {len(contacts['contacts'])}")
        
        # Test 4: Job postings
        print("\n4️⃣ Analyzing job postings...")
        jobs = await agent.analyze_job_postings("https://www.hubspot.com")
        print(f"   Status: {jobs['status']}")
        print(f"   Careers page: {jobs['insights'].get('careers_page', 'Not found')}")
        print(f"   Open positions: {jobs['insights'].get('open_positions', 'Unknown')}")
        print(f"   Hiring departments: {jobs['insights'].get('hiring_departments', [])}")
        
        print("\n✅ Playwright agent test complete!")
        
    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(test_playwright_agent())
