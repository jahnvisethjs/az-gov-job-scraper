"""
State schemas for LangGraph agent workflows.

This module defines type-safe state structures for:
- Scraping orchestrator agent
- Job matching agent
"""

from typing import TypedDict, List, Dict, Optional, Annotated
import operator


class ScrapingState(TypedDict):
    """State for the scraping orchestrator agent workflow.
    
    This state tracks multi-city scraping progress, accumulated results,
    and any errors encountered during the process.
    """
    # Input
    cities: List[str]  # Cities to scrape
    api_key: str  # Gemini API key for scrapers that need it
    
    # Working state
    current_city: Optional[str]  # Current city being scraped
    cities_completed: Annotated[List[str], operator.add]  # Cities successfully scraped
    cities_failed: Annotated[List[str], operator.add]  # Cities that failed
    retry_count: Dict[str, int]  # Retry attempts per city
    
    # Output
    scraped_jobs: Annotated[List[Dict], operator.add]  # Accumulated job data
    errors: Annotated[List[Dict], operator.add]  # Error tracking
    progress: float  # Completion percentage (0.0 to 1.0)
    total_jobs_found: int  # Total number of jobs across all cities


class MatchingState(TypedDict):
    """State for the job matching agent workflow.
    
    This state manages the resume-job matching pipeline including
    indexing, scoring, ranking, and tailoring advice generation.
    """
    # Input
    resume_data: Dict  # Parsed resume information (from resume_parser)
    jobs: List[Dict]  # Jobs to match against
    api_key: str  # Gemini API key for RAG and advice generation
    
    # Configuration
    top_n: int  # Number of top matches to return (default: 10)
    filter_threshold: float  # Minimum match score 0-100 (default: 50.0)
    
    # Working state
    resume_indexed: bool  # Whether resume has been indexed in RAG
    jobs_indexed: bool  # Whether jobs have been indexed in RAG
    raw_matches: List[Dict]  # All matches before filtering
    
    # Output
    matches: List[Dict]  # Matched jobs with scores (sorted, filtered)
    top_matches: List[Dict]  # Top N matches with tailoring advice
    errors: Annotated[List[str], operator.add]  # Error messages
    progress: float  # Completion percentage (0.0 to 1.0)


# Type aliases for cleaner code
JobDict = Dict
ErrorDict = Dict
