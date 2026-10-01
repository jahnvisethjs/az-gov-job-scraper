"""Direct HTTP scraper for Phoenix's public PeopleSoft Candidate Gateway."""

import asyncio
import re
from typing import Any, Dict, List
from urllib.parse import urlencode, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

from progress_events import SearchCancelled
from .base_scraper import BaseJobScraper, JobData, JobPortalError


class PeopleSoftScraper(BaseJobScraper):
    """Collect PeopleSoft listings without launching a browser."""

    DEFAULT_DETAIL_CONCURRENCY = 5
    PHOENIX_SITE_ID = "10"
    def get_platform_name(self) -> str:
        return "PeopleSoft"

    async def scrape_jobs(self) -> List[JobData]:
        """Fetch the server-rendered result list and enrich its postings."""
        self.raise_if_cancelled()
        self._request_timeout = float(
            self.config.get("request_timeout_seconds", 30)
        )
        try:
            listing_html = await self._fetch_text(self.base_url)
            jobs = self.parse_listing_page(
                listing_html,
                city_name=self.city_name,
                portal_url=self.base_url,
                site_id=str(self.config.get("site_id", self.PHOENIX_SITE_ID)),
            )
            if not jobs and not self._reports_zero_jobs(listing_html):
                raise JobPortalError(
                    "PeopleSoft returned no recognizable listings; its markup may have changed"
                )
            if jobs:
                await self._enrich_jobs(jobs)
        except SearchCancelled:
            raise
        except JobPortalError:
            raise
        except Exception as exc:
            raise JobPortalError(f"Failed to scrape {self.city_name}: {exc}") from exc

        self.jobs = jobs
        return jobs

    async def _fetch_text(
        self,
        url: str,
    ) -> str:
        self.raise_if_cancelled()
        response = await asyncio.to_thread(
            requests.get,
            url,
            timeout=self._request_timeout,
        )
        response.raise_for_status()
        self.raise_if_cancelled()
        return response.text

    async def _enrich_jobs(
        self,
        jobs: List[JobData],
    ) -> None:
        concurrency = max(
            1,
            int(self.config.get("detail_concurrency", self.DEFAULT_DETAIL_CONCURRENCY)),
        )
        semaphore = asyncio.Semaphore(concurrency)

        async def enrich(job: JobData) -> None:
            async with semaphore:
                self.raise_if_cancelled()
                try:
                    details = await self.get_job_details(job.url)
                except SearchCancelled:
                    raise
                except Exception as exc:
                    print(f"Could not load PeopleSoft details for {job.url}: {exc}")
                    return

                for field in ("description", "requirements", "salary"):
                    value = details.get(field)
                    if value:
                        setattr(job, field, value)

        await asyncio.gather(*(enrich(job) for job in jobs))

    async def get_job_details(
        self,
        job_url: str,
    ) -> Dict[str, str]:
        """Fetch and parse one public Candidate Gateway posting."""
        detail_html = await self._fetch_text(job_url)
        return self.parse_job_details(detail_html)

    @classmethod
    def parse_listing_page(
        cls,
        page_html: str,
        *,
        city_name: str,
        portal_url: str,
        site_id: str = PHOENIX_SITE_ID,
    ) -> List[JobData]:
        """Parse PeopleSoft's server-rendered grid into normalized jobs."""
        soup = BeautifulSoup(page_html, "lxml")
        jobs: List[JobData] = []
        seen_ids = set()

        for row in soup.select("li.ps_grid-row"):
            title = cls._field_text(row, "SCH_JOB_TITLE")
            source_job_id = cls._field_text(
                row,
                "HRS_APP_JBSCH_I_HRS_JOB_OPENING_ID",
            )
            if not title or not source_job_id or source_job_id in seen_ids:
                continue
            seen_ids.add(source_job_id)

            category = cls._field_text(row, "LOCATION")
            department = cls._field_text(row, "HRS_APP_JBSCH_I_HRS_DEPT_DESCR")
            posted_date = cls._field_text(row, "SCH_OPENED")
            closing_date = cls._field_text(row, "HRS_CLS_DT_DESCR")
            job_url = cls.build_detail_url(portal_url, source_job_id, site_id)

            jobs.append(JobData(
                title=title,
                city=city_name,
                url=job_url,
                location=city_name,
                department=department,
                posted_date=posted_date,
                closing_date=closing_date,
                job_id=source_job_id,
                raw_data={
                    "platform": "PeopleSoft",
                    "posting_id": source_job_id,
                    "category": category,
                    "site_id": site_id,
                },
            ))

        return jobs

    @classmethod
    def parse_job_details(cls, page_html: str) -> Dict[str, str]:
        """Extract labelled description, qualification, and salary sections."""
        soup = BeautifulSoup(page_html, "lxml")
        description_sections = []
        requirement_sections = []
        salary = ""

        for group in soup.select(".hrs_cg_groupbox_field_label_back"):
            heading_element = group.select_one(
                "[id^='HRS_SCH_WRK_DESCR100'][id$='lbl']"
            )
            content_element = group.select_one(
                "span[id^='HRS_SCH_PSTDSC_DESCRLONG']"
            )
            heading = cls._clean_text(
                heading_element.get_text(" ", strip=True) if heading_element else ""
            )
            content = cls._clean_text(
                content_element.get_text(" ", strip=True) if content_element else ""
            )
            if not heading or not content:
                continue

            section = f"{heading}\n{content}"
            if re.search(r"qualification|requirement|education|experience", heading, re.I):
                requirement_sections.append(section)
            else:
                description_sections.append(section)
            if heading.casefold() == "salary":
                salary = content

        return {
            "description": "\n\n".join(description_sections),
            "requirements": "\n\n".join(requirement_sections),
            "salary": salary,
        }

    @staticmethod
    def build_detail_url(portal_url: str, source_job_id: str, site_id: str) -> str:
        """Build the public, stable Candidate Gateway URL for one posting."""
        parsed = urlsplit(portal_url)
        path = parsed.path.replace("/COP_TAM/", "/HRMS/")
        query = urlencode({
            "Page": "HRS_APP_JBPST_FL",
            "Action": "U",
            "FOCUS": "Applicant",
            "SiteId": site_id,
            "JobOpeningId": source_job_id,
            "PostingSeq": "1",
        })
        return urlunsplit((parsed.scheme, parsed.netloc, path, query, ""))

    @classmethod
    def _field_text(cls, row: Any, field_name: str) -> str:
        element = row.find(id=re.compile(rf"^{re.escape(field_name)}\$\d+$"))
        return cls._clean_text(element.get_text(" ", strip=True) if element else "")

    @staticmethod
    def _clean_text(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()

    @staticmethod
    def _reports_zero_jobs(page_html: str) -> bool:
        soup = BeautifulSoup(page_html, "lxml")
        row_count = soup.select_one(".psc_rowcount")
        return bool(
            row_count
            and re.search(
                r"\b0\s+rows?\b",
                row_count.get_text(" ", strip=True),
                re.I,
            )
        )
