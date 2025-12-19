"""
Test suite for LangGraph agents.

Tests both scraping and matching agent workflows.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import ScrapingAgent, MatchingAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_scraping_agent_single_city():
    """Test scraping agent with a single city."""
    print("\n" + "="*60)
    print("TEST 1: Scraping Agent - Single City")
    print("="*60)
    
    def progress_callback(progress, message):
        print(f"[{progress*100:.0f}%] {message}")
    
    agent = ScrapingAgent(progress_callback=progress_callback)
    
    # Test with a single city
    result = agent.run(
        cities=["Tempe"],
        api_key=os.getenv("GEMINI_API_KEY", "")
    )
    
    print("\n--- Results ---")
    print(f"Cities completed: {result.get('cities_completed', [])}")
    print(f"Cities failed: {result.get('cities_failed', [])}")
    print(f"Total jobs found: {result.get('total_jobs_found', 0)}")
    print(f"Errors: {len(result.get('errors', []))}")
    
    if result.get('scraped_jobs'):
        print(f"\nSample job:")
        print(f"  Title: {result['scraped_jobs'][0].get('title', 'N/A')}")
        print(f"  City: {result['scraped_jobs'][0].get('city', 'N/A')}")
    
    assert len(result.get('cities_completed', [])) + len(result.get('cities_failed', [])) == 1
    print("\n✅ Test passed!\n")


def test_scraping_agent_multi_city():
    """Test scraping agent with multiple cities."""
    print("\n" + "="*60)
    print("TEST 2: Scraping Agent - Multiple Cities")
    print("="*60)
    
    def progress_callback(progress, message):
        print(f"[{progress*100:.0f}%] {message}")
    
    agent = ScrapingAgent(progress_callback=progress_callback)
    
    # Test with multiple cities
    result = agent.run(
        cities=["Tempe", "Scottsdale", "Mesa"],
        api_key=os.getenv("GEMINI_API_KEY", "")
    )
    
    print("\n--- Results ---")
    print(f"Cities completed: {result.get('cities_completed', [])}")
    print(f"Cities failed: {result.get('cities_failed', [])}")
    print(f"Total jobs found: {result.get('total_jobs_found', 0)}")
    print(f"Errors: {len(result.get('errors', []))}")
    
    total_processed = len(result.get('cities_completed', [])) + len(result.get('cities_failed', []))
    assert total_processed == 3
    print("\n✅ Test passed!\n")


def test_scraping_agent_error_handling():
    """Test scraping agent error handling with invalid city."""
    print("\n" + "="*60)
    print("TEST 3: Scraping Agent - Error Handling")
    print("="*60)
    
    def progress_callback(progress, message):
        print(f"[{progress*100:.0f}%] {message}")
    
    agent = ScrapingAgent(progress_callback=progress_callback)
    
    # Test with invalid city (should fail gracefully)
    result = agent.run(
        cities=["InvalidCity", "Tempe"],
        api_key=os.getenv("GEMINI_API_KEY", "")
    )
    
    print("\n--- Results ---")
    print(f"Cities completed: {result.get('cities_completed', [])}")
    print(f"Cities failed: {result.get('cities_failed', [])}")
    print(f"Errors: {result.get('errors', [])}")
    
    # Should have processed both cities (one failed, one succeeded)
    total_processed = len(result.get('cities_completed', [])) + len(result.get('cities_failed', []))
    assert total_processed == 2
    assert "InvalidCity" in result.get('cities_failed', [])
    print("\n✅ Test passed!\n")


def test_matching_agent_workflow():
    """Test matching agent workflow."""
    print("\n" + "="*60)
    print("TEST 4: Matching Agent - Full Workflow")
    print("="*60)
    
    def progress_callback(progress, message):
        print(f"[{progress*100:.0f}%] {message}")
    
    agent = MatchingAgent(progress_callback=progress_callback)
    
    # Sample resume data
    resume_data = {
        "name": "John Doe",
        "skills": ["Python", "JavaScript", "SQL", "Project Management"],
        "experience": [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "duration": "2 years",
                "description": "Developed web applications"
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "school": "University of Arizona",
                "year": "2020"
            }
        ]
    }
    
    # Sample jobs
    jobs = [
        {
            "title": "Software Developer",
            "city": "Phoenix",
            "description": "We are seeking a Python developer with web development experience.",
            "requirements": "Python, JavaScript, 2+ years experience",
            "url": "https://example.com/job1"
        },
        {
            "title": "Data Analyst",
            "city": "Tempe",
            "description": "Looking for someone to analyze data using SQL and Python.",
            "requirements": "SQL, Python, statistics background",
            "url": "https://example.com/job2"
        },
        {
            "title": "Project Manager",
            "city": "Scottsdale",
            "description": "Manage software development projects.",
            "requirements": "Project management, agile, communication skills",
            "url": "https://example.com/job3"
        }
    ]
    
    # Run matching
    result = agent.run(
        resume_data=resume_data,
        jobs=jobs,
        api_key=os.getenv("GEMINI_API_KEY", ""),
        top_n=5,
        filter_threshold=0.0  # Low threshold for testing
    )
    
    print("\n--- Results ---")
    print(f"Total matches: {len(result.get('matches', []))}")
    print(f"Top matches: {len(result.get('top_matches', []))}")
    print(f"Errors: {result.get('errors', [])}")
    
    if result.get('matches'):
        print("\nTop 3 matches:")
        for i, match in enumerate(result['matches'][:3], 1):
            print(f"  {i}. {match.get('title', 'N/A')} - Score: {match.get('match_score', 0):.1f}%")
    
    # Verify we got matches
    assert len(result.get('matches', [])) > 0
    print("\n✅ Test passed!\n")


def test_matching_agent_validation():
    """Test matching agent input validation."""
    print("\n" + "="*60)
    print("TEST 5: Matching Agent - Input Validation")
    print("="*60)
    
    agent = MatchingAgent()
    
    # Test with missing resume data
    result = agent.run(
        resume_data={},
        jobs=[{"title": "Test Job"}],
        api_key=""
    )
    
    print(f"Errors: {result.get('errors', [])}")
    
    # Should have validation errors
    assert len(result.get('errors', [])) > 0
    print("\n✅ Test passed!\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 LANGGRAPH AGENT TEST SUITE")
    print("="*60)
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("\n⚠️  WARNING: GEMINI_API_KEY not set in environment")
        print("Some tests may fail or be skipped.\n")
    
    try:
        # Run all tests
        test_scraping_agent_single_city()
        test_scraping_agent_multi_city()
        test_scraping_agent_error_handling()
        test_matching_agent_workflow()
        test_matching_agent_validation()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        raise
