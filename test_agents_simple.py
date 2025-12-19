"""
Simple test to verify LangGraph agents work without recursion issues.
"""

import sys
sys.path.insert(0, ".")

from agents import ScrapingAgent, MatchingAgent

def test_basic_agent_creation():
    """Test that agents can be created."""
    print("Test 1: Creating agents...")
    
    scraping_agent = ScrapingAgent()
    matching_agent = MatchingAgent()
    
    print("✅ Agents created successfully")
    return True

def test_scraping_state_initialization():
    """Test scraping agent state initialization."""
    print("\nTest 2: Testing state initialization...")
    
    agent = ScrapingAgent()
    
    # Test plan_scraping node directly
    initial_state = {
        "cities": ["Tempe"],
        "api_key": "",
        "current_city": None,
        "cities_completed": [],
        "cities_failed": [],
        "retry_count": {},
        "scraped_jobs": [],
        "errors": [],
        "progress": 0.0,
        "total_jobs_found": 0
    }
    
    result = agent._plan_scraping(initial_state)
    
    assert "progress" in result
    assert result["progress"] == 0.0
    
    print("✅ State initialization works")
    return True

def test_matching_state_validation():
    """Test matching agent validation."""
    print("\nTest 3: Testing input validation...")
    
    agent = MatchingAgent()
    
    # Test with empty state
    state = {
        "resume_data": {},
        "jobs": [],
        "api_key": "",
        "top_n": 10,
        "filter_threshold": 50.0,
        "resume_indexed": False,
        "jobs_indexed": False,
        "raw_matches": [],
        "matches": [],
        "top_matches": [],
        "errors": [],
        "progress": 0.0
    }
    
    result = agent._validate_inputs(state)
    
    assert "errors" in result
    assert len(result["errors"]) > 0  # Should have validation errors
    
    print(f"✅ Validation works (found {len(result['errors'])} errors)")
    return True

if __name__ == "__main__":
    print("="*60)
    print("🧪 SIMPLE AGENT UNIT TESTS")
    print("="*60)
    
    try:
        test_basic_agent_creation()
        test_scraping_state_initialization()
        test_matching_state_validation()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
