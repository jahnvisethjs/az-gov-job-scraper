"""
PeopleSoft/Oracle HCM scraper.
Used by City of Phoenix and potentially other large municipalities.
"""
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page
from .base_scraper import BaseJobScraper, JobData, JobPortalError
import asyncio


class PeopleSoftScraper(BaseJobScraper):
    """
    Scraper for PeopleSoft/Oracle HCM job portals.
    
    PeopleSoft is an enterprise HR system with a custom web interface.
    Phoenix URL: https://hcmprod.phoenix.gov/psc/hcmprodtam/EMPLOYEE/COP_TAM/c/HRS_HRAM_FL.HRS_CG_SEARCH_FL.GBL
    """
    
    def get_platform_name(self) -> str:
        return "PeopleSoft"
    
    async def scrape_jobs(self) -> List[JobData]:
        """Scrape jobs from PeopleSoft portal using Playwright."""
        jobs = []
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                print(f"🔍 Scraping {self.city_name} from {self.base_url}")
                
                await page.goto(self.base_url, wait_until="networkidle", timeout=30000)
                
                # Wait for page to load
                await asyncio.sleep(2)
                
                # Click "View All Jobs" if button exists
                try:
                    view_all_button = await page.wait_for_selector("a:has-text('View All Jobs'), button:has-text('View All Jobs')", timeout=5000)
                    if view_all_button:
                        await view_all_button.click()
                        await page.wait_for_load_state("networkidle")
                except:
                    print("'View All Jobs' button not found, proceeding...")
                
                # Wait for job listings table or grid
                await page.wait_for_selector("table.PSLEVEL1GRIDWBO, table#HRS_CE_RSLT_nav, .PSLEVEL1GRIDROW", timeout=15000)
                
                # Extract jobs from table rows
                # PeopleSoft typically uses table structure
                rows = await page.query_selector_all("tr.PSLEVEL1GRIDROW, tr.ps_grid-row")
                
                print(f"Found {len(rows)} job rows")
                
                for row in rows:
                    try:
                        # Extract data from row cells
                        cells = await row.query_selector_all("td, span")
                        
                        # Title (usually in a link)
                        title_link = await row.query_selector("a")
                        title = await title_link.text_content() if title_link else ""
                        job_url = await title_link.get_attribute("href") if title_link else ""
                        
                        # Make URL absolute if needed
                        if job_url and not job_url.startswith("http"):
                            base = self.base_url.split("/psc/")[0]
                            job_url = base + job_url
                        
                        # Extract other fields from cells (order may vary)
                        # Typically: Job ID, Title, Department, Location, Posted Date, Closing Date
                        cell_texts = []
                        for cell in cells[:8]:  # Limit to first 8 cells
                            text = await cell.text_content()
                            cell_texts.append(text.strip() if text else "")
                        
                        # Heuristic field extraction (may need adjustment)
                        job_id = cell_texts[0] if len(cell_texts) > 0 else ""
                        department = cell_texts[2] if len(cell_texts) > 2 else ""
                        location = cell_texts[3] if len(cell_texts) > 3 else self.city_name
                        posted_date = cell_texts[4] if len(cell_texts) > 4 else ""
                        closing_date = cell_texts[5] if len(cell_texts) > 5 else ""
                        
                        if title and title.strip():
                            job = JobData(
                                title=title.strip(),
                                city=self.city_name,
                                url=job_url,
                                job_id=job_id,
                                department=department,
                                location=location if location else self.city_name,
                                posted_date=self.normalize_date(posted_date),
                                closing_date=self.normalize_date(closing_date),
                                raw_data={"platform": "PeopleSoft"}
                            )
                            
                            jobs.append(job)
                    
                    except Exception as e:
                        print(f"⚠️  Error extracting job: {e}")
                        continue
                
            except Exception as e:
                raise JobPortalError(f"Failed to scrape {self.city_name}: {e}")
            
            finally:
                await browser.close()
        
        self.jobs = jobs
        return jobs
    
    async def get_job_details(self, job_url: str, page: Page) -> Dict:
        """Get full job description from individual job page."""
        try:
            await page.goto(job_url, wait_until="networkidle", timeout=30000)
            
            # Description is usually in a specific div or span
            desc_elem = await page.query_selector("#win0divHRS_CE_WRK_POSTING_DESCR, .PSLONGEDITBOX, #POSTING_DESCR")
            description = await desc_elem.text_content() if desc_elem else ""
            
            return {
                "description": description.strip(),
                "requirements": ""  # Often mixed with description in PeopleSoft
            }
        except Exception as e:
            print(f"⚠️  Could not get job details: {e}")
            return {"description": "", "requirements": ""}
