"""Scrapers package - Web scraping utilities for government job sites."""

from .base_scraper import BaseJobScraper, JobData, ScraperError, PlatformNotSupportedError, JobPortalError
from .neogov_scraper import NeoGovScraper
from .peoplesoft_scraper import PeopleSoftScraper
from .scraper_registry import ScraperRegistry

__all__ = [
    "BaseJobScraper",
    "JobData",
    "NeoGovScraper",
    "PeopleSoftScraper",
    "ScraperRegistry",
    "ScraperError",
    "PlatformNotSupportedError",
    "JobPortalError"
]
