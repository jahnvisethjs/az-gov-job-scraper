"""
Scraper registry to map cities to appropriate scraper implementations.
Automatically detects which platform to use based on URL patterns.
"""
from typing import Dict, Type, Optional
from .base_scraper import BaseJobScraper, PlatformNotSupportedError
from .neogov_scraper import NeoGovScraper
from .peoplesoft_scraper import PeopleSoftScraper


class ScraperRegistry:
    """
    Registry that maps cities/URLs to appropriate scraper classes.
    """
    
    # Platform detection patterns
    PLATFORM_PATTERNS = {
        "governmentjobs.com": NeoGovScraper,
        "neogov.com": NeoGovScraper,
        "hcmprod": PeopleSoftScraper,  # PeopleSoft hostname pattern
        "peoplesoft": PeopleSoftScraper,
    }
    
    # Manual city-to-scraper mappings (for special cases)
    CITY_MAPPINGS = {
        "Phoenix": ("PeopleSoft", "https://hcmprod.phoenix.gov/psc/hcmprodtam/EMPLOYEE/COP_TAM/c/HRS_HRAM_FL.HRS_CG_SEARCH_FL.GBL?FOCUS=Applicant"),
        "Scottsdale": ("NeoGov", "https://www.governmentjobs.com/careers/scottsdaleaz"),
        "Pima County": ("NeoGov", "https://www.governmentjobs.com/careers/pima"),
        "Tempe": ("NeoGov", "https://www.governmentjobs.com/careers/tempe"),
        "Mesa": ("NeoGov", "https://www.governmentjobs.com/careers/mesaaz"),
        "Glendale": ("NeoGov", "https://www.governmentjobs.com/careers/glendaleaz"),
        "Chandler": ("NeoGov", "https://www.governmentjobs.com/careers/chandleraz"),
        "Gilbert": ("NeoGov", "https://www.governmentjobs.com/careers/gilbert"),
        "Apache Junction": ("NeoGov", "https://www.governmentjobs.com/careers/apachejunctionaz"),
        "Avondale": ("NeoGov", "https://www.governmentjobs.com/careers/avondale"),
        "Buckeye": ("NeoGov", "https://www.governmentjobs.com/careers/buckeyeaz"),
        "Flagstaff": ("NeoGov", "https://www.governmentjobs.com/careers/flagstaffaz"),
        "Goodyear": ("NeoGov", "https://www.governmentjobs.com/careers/goodyearaz"),
        "Prescott": ("NeoGov", "https://www.governmentjobs.com/careers/prescott"),
        "Cottonwood": ("NeoGov", "https://www.governmentjobs.com/careers/cottonwoodaz"),
    }
    
    @classmethod
    def get_scraper(cls, city_name: str, url: Optional[str] = None) -> BaseJobScraper:
        """
        Get appropriate scraper instance for a city.
        
        Args:
            city_name: Name of the city
            url: Optional URL (if not in CITY_MAPPINGS)
            
        Returns:
            Scraper instance
            
        Raises:
            PlatformNotSupportedError: If platform cannot be determined
        """
        # First, check manual mappings
        if city_name in cls.CITY_MAPPINGS:
            platform_name, city_url = cls.CITY_MAPPINGS[city_name]
            scraper_class = cls._get_scraper_class_by_platform(platform_name)
            return scraper_class(city_name, city_url)
        
        # If URL provided, detect platform
        if url:
            scraper_class = cls._detect_platform(url)
            if scraper_class:
                return scraper_class(city_name, url)
        
        raise PlatformNotSupportedError(
            f"No scraper configured for {city_name}. "
            f"Please add to CITY_MAPPINGS or provide a URL."
        )
    
    @classmethod
    def _detect_platform(cls, url: str) -> Optional[Type[BaseJobScraper]]:
        """
        Detect platform from URL.
        
        Args:
            url: Job portal URL
            
        Returns:
            Scraper class or None
        """
        url_lower = url.lower()
        
        for pattern, scraper_class in cls.PLATFORM_PATTERNS.items():
            if pattern in url_lower:
                return scraper_class
        
        return None
    
    @classmethod
    def _get_scraper_class_by_platform(cls, platform_name: str) -> Type[BaseJobScraper]:
        """Get scraper class by platform name."""
        platform_map = {
            "NeoGov": NeoGovScraper,
            "PeopleSoft": PeopleSoftScraper,
        }
        
        if platform_name not in platform_map:
            raise PlatformNotSupportedError(f"Platform {platform_name} not supported")
        
        return platform_map[platform_name]
    
    @classmethod
    def get_supported_cities(cls) -> list[str]:
        """Get list of cities with configured scrapers."""
        return list(cls.CITY_MAPPINGS.keys())
    
    @classmethod
    def add_city(cls, city_name: str, platform: str, url: str):
        """
        Add a new city to the registry.
        
        Args:
            city_name: Name of the city
            platform: Platform name ('NeoGov', 'PeopleSoft', etc.)
            url: Job portal URL
        """
        cls.CITY_MAPPINGS[city_name] = (platform, url)
