"""Scraper for NEOGOV (governmentjobs.com) agency job portals."""

import asyncio
import html as html_lib
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit

import aiohttp
from bs4 import BeautifulSoup

from .base_scraper import BaseJobScraper, JobData, JobPortalError


class NeoGovScraper(BaseJobScraper):
    """Collect complete, de-duplicated jobs from a NEOGOV agency portal."""

    LISTING_PATH = "/careers/home/index"
    DEFAULT_MAX_PAGES = 100
    DEFAULT_DETAIL_CONCURRENCY = 5
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )

    def __init__(
        self,
        city_name: str,
        base_url: str,
        config: Optional[Dict] = None,
    ):
        super().__init__(city_name, base_url, config)

        path = urlsplit(base_url).path
        match = re.search(r"/careers/([^/?#]+)", path, flags=re.IGNORECASE)
        self.agency_code = match.group(1) if match else None

        parsed_url = urlsplit(base_url)
        self.portal_origin = urlunsplit(
            (
                parsed_url.scheme or "https",
                parsed_url.netloc or "www.governmentjobs.com",
                "",
                "",
                "",
            )
        )

    def get_platform_name(self) -> str:
        return "NeoGov"

    async def scrape_jobs(self) -> List[JobData]:
        """Scrape every listing page and enrich each unique job from its detail page."""
        if not self.agency_code:
            raise JobPortalError(
                f"Could not determine the NEOGOV agency code from {self.base_url}"
            )

        timeout = aiohttp.ClientTimeout(
            total=float(self.config.get("request_timeout_seconds", 30))
        )
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        }

        try:
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                jobs = await self._scrape_with_session(session)
        except JobPortalError:
            raise
        except Exception as exc:
            raise JobPortalError(f"Failed to scrape {self.city_name}: {exc}") from exc

        self.jobs = jobs
        return jobs

    async def _scrape_with_session(self, session: aiohttp.ClientSession) -> List[JobData]:
        listing_url = urljoin(self.portal_origin, self.LISTING_PATH)
        max_pages = max(1, int(self.config.get("max_pages", self.DEFAULT_MAX_PAGES)))
        jobs_by_key: Dict[str, JobData] = {}
        seen_pages = set()
        page_number = 1

        print(f"Scraping {self.city_name} from {self.base_url}")

        while page_number and page_number <= max_pages and page_number not in seen_pages:
            seen_pages.add(page_number)
            listing_html = await self._fetch_text(
                session,
                listing_url,
                params={"agency": self.agency_code, "page": page_number},
            )
            page_jobs, next_page, reported_count = self.parse_listing_page(
                listing_html,
                city_name=self.city_name,
                portal_origin=self.portal_origin,
                agency_code=self.agency_code,
                source_page=page_number,
            )

            if page_number == 1 and not page_jobs and reported_count != 0:
                raise JobPortalError(
                    "NEOGOV returned no recognizable job listings; its markup may have changed"
                )

            new_jobs = 0
            for job in page_jobs:
                key = job.job_id or self.canonicalize_job_url(job.url)
                if key not in jobs_by_key:
                    jobs_by_key[key] = job
                    new_jobs += 1

            if reported_count is not None and len(jobs_by_key) >= reported_count:
                break
            if next_page is None or next_page in seen_pages:
                break
            if page_number > 1 and new_jobs == 0:
                break

            page_number = next_page

        jobs = list(jobs_by_key.values())
        print(f"Found {len(jobs)} unique job listings across {len(seen_pages)} page(s)")

        if jobs:
            await self._enrich_jobs(session, jobs)

        return jobs

    async def _fetch_text(
        self,
        session: aiohttp.ClientSession,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        request_headers = (
            {"X-Requested-With": "XMLHttpRequest"} if params is not None else None
        )
        async with session.get(
            url,
            params=params,
            headers=request_headers,
        ) as response:
            response.raise_for_status()
            return await response.text()

    async def _enrich_jobs(
        self,
        session: aiohttp.ClientSession,
        jobs: List[JobData],
    ) -> None:
        concurrency = max(
            1,
            int(
                self.config.get(
                    "detail_concurrency",
                    self.DEFAULT_DETAIL_CONCURRENCY,
                )
            ),
        )
        semaphore = asyncio.Semaphore(concurrency)

        async def enrich(job: JobData) -> None:
            async with semaphore:
                try:
                    details = await self.get_job_details(job.url, session)
                except Exception as exc:
                    print(f"Could not load details for {job.url}: {exc}")
                    return

                for field in (
                    "description",
                    "requirements",
                    "location",
                    "department",
                    "salary",
                    "posted_date",
                    "closing_date",
                    "job_type",
                ):
                    value = details.get(field)
                    if value:
                        setattr(job, field, value)

                job_number = details.get("job_number")
                if job_number:
                    job.raw_data["job_number"] = job_number

        await asyncio.gather(*(enrich(job) for job in jobs))

    async def get_job_details(
        self,
        job_url: str,
        session: aiohttp.ClientSession,
    ) -> Dict[str, str]:
        """Fetch and parse one NEOGOV posting."""
        detail_html = await self._fetch_text(session, job_url)
        return self.parse_job_details(detail_html)

    @classmethod
    def parse_listing_page(
        cls,
        page_html: str,
        city_name: str,
        portal_origin: str,
        agency_code: str,
        source_page: int = 1,
    ) -> Tuple[List[JobData], Optional[int], Optional[int]]:
        """Parse one server-rendered listing page into unique jobs."""
        soup = BeautifulSoup(page_html, "lxml")
        jobs: List[JobData] = []
        seen_keys = set()

        for item in soup.select("li.list-item"):
            link = item.select_one("a.item-details-link[href]")
            if not link:
                continue

            title = cls._clean_text(link.get_text(" ", strip=True))
            raw_url = link.get("href", "")
            job_url = cls.canonicalize_job_url(urljoin(portal_origin, raw_url))
            posting_id = cls._extract_posting_id(
                item.get("data-job-id", "") or job_url
            )
            if not title or not job_url or not posting_id:
                continue

            stable_id = f"neogov:{agency_code.lower()}:{posting_id}"
            if stable_id in seen_keys:
                continue
            seen_keys.add(stable_id)

            meta_items = item.select("ul.list-meta > li")
            location = (
                cls._clean_text(meta_items[0].get_text(" ", strip=True))
                if meta_items
                else city_name
            )

            job_type = ""
            salary = ""
            if len(meta_items) > 1:
                employment_parts = [
                    cls._clean_text(value)
                    for value in meta_items[1].stripped_strings
                    if cls._clean_text(value) not in {"", "-"}
                ]
                if employment_parts:
                    job_type = employment_parts[0]
                if len(employment_parts) > 1:
                    salary = " - ".join(employment_parts[1:])

            department = cls._clean_text(link.get("data-department-name", ""))
            if not department:
                department = cls._prefixed_meta_value(meta_items, ("Department:", "Division:"))

            summary = item.select_one(".list-entry")
            description = (
                cls._clean_text(summary.get_text(" ", strip=True)) if summary else ""
            )
            categories = cls._prefixed_meta_value(meta_items, ("Category:",))

            jobs.append(
                JobData(
                    title=title,
                    city=city_name,
                    url=job_url,
                    description=description,
                    location=location or city_name,
                    department=department,
                    salary=salary,
                    job_id=stable_id,
                    job_type=job_type,
                    raw_data={
                        "platform": "NeoGov",
                        "posting_id": posting_id,
                        "agency_code": agency_code,
                        "source_page": source_page,
                        "categories": categories,
                    },
                )
            )

        next_page = cls._next_page_number(soup)
        reported_count = cls._reported_job_count(soup)
        return jobs, next_page, reported_count

    @classmethod
    def parse_job_details(cls, page_html: str) -> Dict[str, str]:
        """Parse metadata and content sections from a NEOGOV job page."""
        soup = BeautifulSoup(page_html, "lxml")
        structured = cls._job_posting_json(soup)
        details: Dict[str, str] = {
            "description": "",
            "requirements": "",
            "location": "",
            "department": "",
            "salary": "",
            "posted_date": "",
            "closing_date": "",
            "job_number": "",
            "job_type": "",
        }

        term_map = {
            "salary": "salary",
            "location": "location",
            "job type": "job_type",
            "job number": "job_number",
            "department": "department",
            "division": "department",
            "opening date": "posted_date",
            "closing date": "closing_date",
        }
        for block in soup.select(".term-block"):
            label_element = block.select_one(".term-description")
            value_element = block.select_one(".span8")
            if not label_element or not value_element:
                continue
            label = cls._clean_text(label_element.get_text(" ", strip=True)).lower()
            value = cls._clean_text(value_element.get_text(" ", strip=True))
            field = term_map.get(label)
            if field and value:
                # Prefer the explicitly labelled Department over Division.
                if field != "department" or label == "department" or not details[field]:
                    details[field] = value

        description_sections = []
        requirement_sections = []
        for heading_container in soup.select("#details-info dl > dt"):
            heading = cls._clean_text(heading_container.get_text(" ", strip=True))
            content = heading_container.find_next_sibling("dd")
            if not heading or not content:
                continue
            content_text = cls._clean_text(content.get_text(" ", strip=True))
            if not content_text:
                continue
            section_text = f"{heading}\n{content_text}"
            if re.search(r"qualification|requirement|education|experience", heading, re.I):
                requirement_sections.append(section_text)
            else:
                description_sections.append(section_text)

        details["description"] = "\n\n".join(description_sections)
        details["requirements"] = "\n\n".join(requirement_sections)

        if structured:
            if not details["description"]:
                details["description"] = cls._html_fragment_to_text(
                    structured.get("description", "")
                )
            details["posted_date"] = details["posted_date"] or cls._clean_text(
                structured.get("datePosted", "")
            )
            details["closing_date"] = details["closing_date"] or cls._clean_text(
                structured.get("validThrough", "")
            )
            details["job_type"] = details["job_type"] or cls._clean_text(
                structured.get("employmentType", "")
            )
            details["location"] = details["location"] or cls._structured_location(
                structured
            )
            details["salary"] = details["salary"] or cls._structured_salary(structured)

        return details

    @staticmethod
    def canonicalize_job_url(url: str) -> str:
        """Remove tracking parameters/fragments without changing posting identity."""
        if not url:
            return ""
        parsed = urlsplit(url)
        path = parsed.path.rstrip("/") or "/"
        return urlunsplit(
            (parsed.scheme.lower(), parsed.netloc.lower(), path, "", "")
        )

    @staticmethod
    def _extract_posting_id(value: str) -> str:
        match = re.search(r"(?:/jobs/|^)(\d+)(?:/|$)", str(value))
        return match.group(1) if match else ""

    @staticmethod
    def _clean_text(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()

    @classmethod
    def _html_fragment_to_text(cls, value: Any) -> str:
        decoded = html_lib.unescape(str(value or ""))
        return cls._clean_text(BeautifulSoup(decoded, "lxml").get_text(" ", strip=True))

    @classmethod
    def _prefixed_meta_value(
        cls,
        meta_items: List[Any],
        prefixes: Tuple[str, ...],
    ) -> str:
        for item in meta_items:
            text = cls._clean_text(item.get_text(" ", strip=True))
            for prefix in prefixes:
                if text.lower().startswith(prefix.lower()):
                    return text[len(prefix):].strip()
        return ""

    @staticmethod
    def _next_page_number(soup: BeautifulSoup) -> Optional[int]:
        next_link = soup.select_one(
            "ul.pagination a[rel='next'][aria-disabled='false'], "
            "ul.pagination a[aria-label='Go to Next Page'][aria-disabled='false']"
        )
        if not next_link:
            return None
        query = parse_qs(urlsplit(next_link.get("href", "")).query)
        try:
            return int(query.get("page", [""])[0])
        except (TypeError, ValueError):
            return None

    @classmethod
    def _reported_job_count(cls, soup: BeautifulSoup) -> Optional[int]:
        count_element = soup.select_one("#job-postings-number")
        if not count_element:
            return None
        match = re.search(r"\d[\d,]*", count_element.get_text(" ", strip=True))
        return int(match.group(0).replace(",", "")) if match else None

    @staticmethod
    def _job_posting_json(soup: BeautifulSoup) -> Dict[str, Any]:
        for script in soup.select("script[type='application/ld+json']"):
            try:
                payload = json.loads(script.string or script.get_text())
            except (TypeError, json.JSONDecodeError):
                continue

            candidates = payload if isinstance(payload, list) else [payload]
            for candidate in candidates:
                if isinstance(candidate, dict) and candidate.get("@type") == "JobPosting":
                    return candidate
        return {}

    @classmethod
    def _structured_location(cls, structured: Dict[str, Any]) -> str:
        location = structured.get("jobLocation", {})
        if isinstance(location, list):
            location = location[0] if location else {}
        address = location.get("address", {}) if isinstance(location, dict) else {}
        if not isinstance(address, dict):
            return ""
        return ", ".join(
            cls._clean_text(address.get(field, ""))
            for field in ("streetAddress", "addressLocality", "addressRegion", "postalCode")
            if cls._clean_text(address.get(field, ""))
        )

    @classmethod
    def _structured_salary(cls, structured: Dict[str, Any]) -> str:
        salary = structured.get("baseSalary", {})
        value = salary.get("value", {}) if isinstance(salary, dict) else {}
        if not isinstance(value, dict):
            return ""

        minimum = value.get("minValue")
        maximum = value.get("maxValue")
        unit = cls._clean_text(value.get("unitText", "")).title()
        if minimum is None and maximum is None:
            return ""
        if minimum is not None and maximum is not None:
            amount = f"${minimum:,.2f} - ${maximum:,.2f}"
        else:
            amount = f"${(minimum if minimum is not None else maximum):,.2f}"
        return f"{amount} {unit}".strip()
