"""
NeoGov (governmentjobs.com) platform scraper.
Used by Scottsdale, Pima County, and many other Arizona cities.
"""
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser
from .base_scraper import BaseJobScraper, JobData, JobPortalError
import asyncio


class NeoGovScraper(BaseJobScraper):
    """
   Scraper for NeoGov (governmentjobs.com) job portals.
    
    NeoGov is a standard platform used by many government agencies.
    URL pattern: https://www.governmentjobs.com/careers/{agency_code}
    """
    
    def __init__(self, city_name: str, base_url: str, config: Optional[Dict] = None):
        super().__init__(city_name, base_url, config)
        
        # Extract agency code from URL
        # Example: https://www.governmentjobs.com/careers/scottsdaleaz
        if "governmentjobs.com/careers/" in base_url:
            self.agency_code = base_url.split("/careers/")[-1].strip("/")
        else:
            # Try to construct the URL
            # This assumes base_url might be the city page, not the jobs page
            self.agency_code = None
    
    def get_platform_name(self) -> str:
        return "NeoGov"
    
    async def scrape_jobs(self) -> List[JobData]:
        """Scrape jobs from NeoGov portal using Playwright."""
        jobs = []
        
        async with async_playwright() as p:
            # Launch browser in headless mode
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                # Navigate to jobs page
                jobs_url = f"https://www.governmentjobs.com/careers/{self.agency_code}" if self.agency_code else self.base_url
                
                print(f"🔍 Scraping {self.city_name} from {jobs_url}")
                
                await page.goto(jobs_url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait a bit for JS to load
                await asyncio.sleep(3)
                
                # Wait for job listings to load
                # NeoGov uses "a.item-details-link" for job titles
                await page.wait_for_selector("a.item-details-link", timeout=15000)
                
                # Extract all job links
                job_links = await page.query_selector_all("a.item-details-link")
                
                print(f"Found {len(job_links)} job listings")
                
                for link in job_links:
                    try:
                        # Extract job title and URL
                        title = await link.text_content()
                        title = title.strip() if title else "Unknown Title"
                        
                        # Job URL
                        job_url = await link.get_attribute("href")
                        if job_url and not job_url.startswith("http"):
                            job_url = "https://www.governmentjobs.com" + job_url
                        
                        # For NeoGov, most details are on the details page
                        # We'll just grab title and URL for now
                        # The details page has more structured info
                        
                        # Create JobData object
                        job = JobData(
                            title=title,
                            city=self.city_name,
                            url=job_url,
                            location=self.city_name,
                            raw_data={"platform": "NeoGov"}
                        )
                        
                        jobs.append(job)
                        
                    except Exception as e:
                        print(f"⚠️  Error extracting job: {e}")
                        continue
                
                # Get job descriptions (optional, can be slow)
                # We'll do this in a separate method if needed
                
            except Exception as e:
                raise JobPortalError(f"Failed to scrape {self.city_name}: {e}")
            
            finally:
                await browser.close()
        
        self.jobs = jobs
        return jobs
    
    async def get_job_details(self, job_url: str, page: Page) -> Dict:
        """
        Get full job description and requirements from individual job page.
        
        Args:
            job_url: URL of the job posting
            page: Playwright page object
            
        Returns:
            Dict with description and requirements
        """
        try:
            await page.goto(job_url, wait_until="networkidle", timeout=30000)
            
            # Description
            desc_elem = await page.query_selector(".opening-description, .job-description, #job-description")
            description = await desc_elem.text_content() if desc_elem else ""
            
            # Requirements
            req_elem = await page.query_selector(".opening-qualifications, .job-requirements, #job-requirements")
            requirements = await req_elem.text_content() if req_elem else ""
            
            return {
                "description": description.strip(),
                "requirements": requirements.strip()
            }
        except Exception as e:
            print(f"⚠️  Could not get job details: {e}")
            return {"description": "", "requirements": ""}
