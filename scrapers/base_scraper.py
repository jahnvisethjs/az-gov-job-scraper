"""
Base scraper class for government job sites.
Defines the interface that all platform-specific scrapers must implement.
"""
from abc import ABC, abstractmethod
from typing import List,Dict, Optional
from datetime import datetime
import asyncio


class JobData:
    """Standardized job data structure."""
    
    def __init__(
        self,
        title: str,
        city: str,
        url: str,
        description: str = "",
        location: str = "",
        department: str = "",
        salary: str = "",
        posted_date: str = "",
        closing_date: str = "",
        job_id: str = "",
        requirements: str = "",
        job_type: str = "",  # Full-time, Part-time, Intern, etc.
        raw_data: Optional[Dict] = None
    ):
        self.title = title
        self.city = city
        self.url = url
        self.description = description
        self.location = location
        self.department = department
        self.salary = salary
        self.posted_date = posted_date
        self.closing_date = closing_date
        self.job_id = job_id
        self.requirements = requirements
        self.job_type = job_type
        self.raw_data = raw_data or {}
        self.scraped_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/display."""
        return {
            "title": self.title,
            "city": self.city,
            "url": self.url,
            "description": self.description,
            "location": self.location,
            "department": self.department,
            "salary": self.salary,
            "posted_date": self.posted_date,
            "closing_date": self.closing_date,
            "job_id": self.job_id,
            "requirements": self.requirements,
            "job_type": self.job_type,
            "scraped_at": self.scraped_at,
            "raw_data": self.raw_data
        }


class BaseJobScraper(ABC):
    """
    Abstract base class for job scrapers.
    Each platform (NeoGov, PeopleSoft, etc.) should subclass this.
    """
    
    def __init__(self, city_name: str, base_url: str, config: Optional[Dict] = None):
        """
        Initialize scraper.
        
        Args:
            city_name: Name of the city/county (e.g., "Phoenix", "Pima County")
            base_url: Base URL for the job portal
            config: Optional configuration dict
        """
        self.city_name = city_name
        self.base_url = base_url
        self.config = config or {}
        self.jobs: List[JobData] = []
    
    @abstractmethod
    async def scrape_jobs(self) -> List[JobData]:
        """
        Scrape jobs from the portal.
        Must be implemented by subclasses.
        
        Returns:
            List of JobData objects
        """
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the name of the platform (e.g., 'NeoGov', 'PeopleSoft')."""
        pass
    
    def normalize_date(self, date_str: str) -> str:
        """
        Normalize date string to consistent format.
        Override if platform has specific date format.
        
        Args:
            date_str: Raw date string
            
        Returns:
            Normalized date string (ISO format if possible)
        """
        # Default: return as-is
        # Subclasses can implement platform-specific parsing
        return date_str.strip() if date_str else ""
    
    def normalize_salary(self, salary_str: str) -> str:
        """
        Normalize salary string.
        
        Args:
            salary_str: Raw salary string
            
        Returns:
            Normalized salary string
        """
        return salary_str.strip() if salary_str else ""
    
    def get_jobs_dict(self) -> List[Dict]:
        """Get scraped jobs as list of dictionaries."""
        return [job.to_dict() for job in self.jobs]
    
    async def scrape_with_retry(self, max_retries: int = 3) -> List[JobData]:
        """
        Scrape with retry logic.
        
        Args:
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of JobData objects
        """
        for attempt in range(max_retries):
            try:
                self.jobs = await self.scrape_jobs()
                return self.jobs
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to scrape {self.city_name} after {max_retries} attempts: {e}")
                print(f"Retry {attempt + 1}/{max_retries} for {self.city_name}: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return []


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class PlatformNotSupportedError(ScraperError):
    """Raised when a platform is not yet supported."""
    pass


class JobPortalError(ScraperError):
    """Raised when there's an issue with the job portal itself."""
    pass
