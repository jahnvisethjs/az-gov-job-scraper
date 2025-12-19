"""
Agents package - LangGraph agent workflows.

This package provides LangGraph-based agents for orchestrating:
- Multi-city job scraping with error handling
- Resume-job matching with RAG integration

Usage:
    from agents import ScrapingAgent, MatchingAgent
    
    # Scraping
    scraping_agent = ScrapingAgent(progress_callback=my_callback)
    result = scraping_agent.run(cities=["Phoenix", "Tempe"], api_key="...")
    
    # Matching
    matching_agent = MatchingAgent(progress_callback=my_callback)
    result = matching_agent.run(resume_data={...}, jobs=[...], api_key="...")
"""

from .scraping_agent import ScrapingAgent
from .matching_agent import MatchingAgent
from .state_schemas import ScrapingState, MatchingState

__all__ = [
    "ScrapingAgent",
    "MatchingAgent",
    "ScrapingState",
    "MatchingState"
]

