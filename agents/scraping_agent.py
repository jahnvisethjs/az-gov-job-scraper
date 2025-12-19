"""
Scraping Orchestrator Agent - Multi-city scraping workflow with error handling.

This agent orchestrates the scraping of multiple cities in a structured,
stateful manner using LangGraph.
"""

from typing import Optional, Callable
from langgraph.graph import StateGraph, END
from .state_schemas import ScrapingState
from scrapers.scraper_registry import ScraperRegistry
from scrapers.base_scraper import PlatformNotSupportedError
import time


class ScrapingAgent:
    """
    LangGraph agent for orchestrating multi-city job scraping.
    
    Features:
    - Sequential or parallel city scraping
    - Automatic retry logic with exponential backoff
    - Progress tracking and callbacks
    - Comprehensive error handling
    """
    
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 2  # seconds
    
    def __init__(self, progress_callback: Optional[Callable[[float, str], None]] = None):
        """
        Initialize the scraping agent.
        
        Args:
            progress_callback: Optional callback function(progress, message) for UI updates
        """
        self.progress_callback = progress_callback
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(ScrapingState)
        
        # Add nodes
        workflow.add_node("plan_scraping", self._plan_scraping)
        workflow.add_node("scrape_city", self._scrape_city)
        workflow.add_node("handle_errors", self._handle_errors)
        workflow.add_node("aggregate_results", self._aggregate_results)
        
        # Define edges
        workflow.set_entry_point("plan_scraping")
        workflow.add_edge("plan_scraping", "scrape_city")
        workflow.add_conditional_edges(
            "scrape_city",
            self._should_retry_or_continue,
            {
                "handle_errors": "handle_errors",
                "aggregate_results": "aggregate_results",
                "scrape_city": "scrape_city"
            }
        )
        workflow.add_edge("handle_errors", "scrape_city")
        workflow.add_edge("aggregate_results", END)
        
        return workflow.compile()
    
    def _plan_scraping(self, state: ScrapingState) -> ScrapingState:
        """Initialize scraping workflow."""
        self._update_progress(0.0, "Planning scraping workflow...")
        
        return {
            "cities_completed": [],
            "cities_failed": [],
            "retry_count": {},
            "scraped_jobs": [],
            "errors": [],
            "progress": 0.0,
            "total_jobs_found": 0,
            "current_city": None
        }
    
    def _scrape_city(self, state: ScrapingState) -> ScrapingState:
        """Scrape jobs from a single city."""
        # Find next city to scrape
        cities_to_scrape = [
            city for city in state["cities"]
            if city not in state["cities_completed"] and city not in state["cities_failed"]
        ]
        
        if not cities_to_scrape:
            return state
        
        city = cities_to_scrape[0]
        self._update_progress(
            state["progress"],
            f"Scraping {city}... ({len(state['cities_completed'])}/{len(state['cities'])} cities completed)"
        )
        
        try:
            # Get appropriate scraper
            scraper = ScraperRegistry.get_scraper(city)
            
            # Scrape the city
            jobs = scraper.scrape()
            
            # Success - update state
            return {
                "current_city": city,
                "cities_completed": [city],
                "scraped_jobs": jobs,
                "total_jobs_found": state.get("total_jobs_found", 0) + len(jobs),
                "progress": (len(state.get("cities_completed", [])) + 1) / len(state["cities"])
            }
            
        except PlatformNotSupportedError as e:
            # Platform not supported - don't retry
            return {
                "current_city": city,
                "cities_failed": [city],
                "errors": [{
                    "city": city,
                    "error": str(e),
                    "type": "PlatformNotSupported",
                    "retry_count": 0
                }],
                "progress": (len(state.get("cities_completed", [])) + len(state.get("cities_failed", [])) + 1) / len(state["cities"])
            }
            
        except Exception as e:
            # Other errors - may retry
            retry_count = state.get("retry_count", {}).get(city, 0)
            
            return {
                "current_city": city,
                "errors": [{
                    "city": city,
                    "error": str(e),
                    "type": type(e).__name__,
                    "retry_count": retry_count
                }]
            }
    
    def _handle_errors(self, state: ScrapingState) -> ScrapingState:
        """Handle errors and implement retry logic."""
        city = state.get("current_city")
        if not city:
            return state
        
        retry_count = state.get("retry_count", {}).get(city, 0)
        
        if retry_count < self.MAX_RETRIES:
            # Retry with exponential backoff
            delay = self.RETRY_DELAY_BASE ** retry_count
            self._update_progress(
                state["progress"],
                f"Retrying {city} in {delay}s... (attempt {retry_count + 1}/{self.MAX_RETRIES})"
            )
            time.sleep(delay)
            
            # Update retry count
            new_retry_count = state.get("retry_count", {}).copy()
            new_retry_count[city] = retry_count + 1
            
            return {"retry_count": new_retry_count}
        else:
            # Max retries reached - mark as failed
            self._update_progress(
                state["progress"],
                f"Failed to scrape {city} after {self.MAX_RETRIES} attempts"
            )
            
            return {
                "cities_failed": [city],
                "progress": (len(state.get("cities_completed", [])) + len(state.get("cities_failed", [])) + 1) / len(state["cities"])
            }
    
    def _should_retry_or_continue(self, state: ScrapingState) -> str:
        """Determine next step based on current state."""
        city = state.get("current_city")
        
        # First check if all cities are processed
        cities_completed = set(state.get("cities_completed", []))
        cities_failed = set(state.get("cities_failed", []))
        all_cities = set(state["cities"])
        total_processed = cities_completed | cities_failed
        
        if len(total_processed) >= len(all_cities):
            return "aggregate_results"
        
        # Check if current city has errors that need handling
        if city and state.get("errors"):
            latest_error = state["errors"][-1]
            if latest_error.get("city") == city and city not in total_processed:
                # Don't retry platform errors
                if latest_error.get("type") == "PlatformNotSupported":
                    return "scrape_city"
                
                # Check retry count
                retry_count = state.get("retry_count", {}).get(city, 0)
                if retry_count < self.MAX_RETRIES:
                    return "handle_errors"
        
        # Continue with next city
        return "scrape_city"
    
    def _aggregate_results(self, state: ScrapingState) -> ScrapingState:
        """Finalize results and report summary."""
        total_cities = len(state["cities"])
        successful = len(state.get("cities_completed", []))
        failed = len(state.get("cities_failed", []))
        total_jobs = state.get("total_jobs_found", 0)
        
        self._update_progress(
            1.0,
            f"Scraping complete! {successful}/{total_cities} cities successful, {total_jobs} jobs found"
        )
        
        return {"progress": 1.0}
    
    def _update_progress(self, progress: float, message: str):
        """Send progress update via callback if available."""
        if self.progress_callback:
            self.progress_callback(progress, message)
    
    def run(
        self,
        cities: list[str],
        api_key: str = ""
    ) -> ScrapingState:
        """
        Run the scraping workflow.
        
        Args:
            cities: List of city names to scrape
            api_key: Gemini API key (for scrapers that need it)
            
        Returns:
            Final state with scraped jobs and errors
        """
        initial_state: ScrapingState = {
            "cities": cities,
            "api_key": api_key,
            "current_city": None,
            "cities_completed": [],
            "cities_failed": [],
            "retry_count": {},
            "scraped_jobs": [],
            "errors": [],
            "progress": 0.0,
            "total_jobs_found": 0
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state
