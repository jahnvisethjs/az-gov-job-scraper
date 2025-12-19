"""
Test script for RAG engine functionality.
Tests embedding generation, ChromaDB storage, and semantic search.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag import JobRAG
from scrapers import ScraperRegistry
from config import GEMINI_API_KEY


def test_embedding_generation():
    """Test that embeddings can be generated."""
    print("\n" + "="*60)
    print("Test 1: Embedding Generation")
    print("="*60)
    
    try:
        rag = JobRAG(api_key=GEMINI_API_KEY)
        
        test_text = "Software Engineer position requiring Python, JavaScript, and experience with databases."
        
        print(f"Generating embedding for: '{test_text[:50]}...'")
        embedding = rag.generate_embedding(test_text)
        
        print(f"✅ Success! Generated embedding with {len(embedding)} dimensions")
        print(f"   First 5 values: {embedding[:5]}")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_job_storage_and_search():
    """Test adding jobs to ChromaDB and searching."""
    print("\n" + "="*60)
    print("Test 2: Job Storage and Semantic Search")
    print("="*60)
    
    try:
        rag = JobRAG(api_key=GEMINI_API_KEY)
        
        # Clear any existing data
        print("Clearing existing database...")
        rag.clear_jobs()
        
        # Scrape sample jobs
        print("Scraping sample jobs from Scottsdale...")
        scraper = ScraperRegistry.get_scraper("Scottsdale")
        jobs = await scraper.scrape_with_retry(max_retries=1)
        
        if not jobs:
            print("⚠️ No jobs scraped, cannot test")
            return False
        
        print(f"Scraped {len(jobs)} jobs")
        
        # Convert to dict
        jobs_dict = [job.to_dict() for job in jobs[:5]]  # Test with first 5 jobs
        
        # Add to RAG
        print(f"Adding {len(jobs_dict)} jobs to vector database...")
        count = rag.add_jobs(jobs_dict)
        
        print(f"✅ Added {count} jobs to database")
        print(f"   Total jobs in database: {rag.get_job_count()}")
        
        # Test search with a sample profile
        print("\nTesting semantic search...")
        test_profile = {
            "interests": ["Information Technology", "Engineering"],
            "degree": "Bachelor's Degree",
            "resume_parsed": {
                "skills": ["Python", "JavaScript", "SQL", "Data Analysis"],
                "experience": [
                    {
                        "title": "Software Developer",
                        "company": "Tech Corp",
                        "description": "Built web applications using Python and JavaScript"
                    }
                ]
            }
        }
        
        results = rag.search_jobs(test_profile, top_k=3)
        
        print(f"✅ Search returned {len(results)} matching jobs")
        
        for i, (job, score) in enumerate(results, 1):
            print(f"\n{i}. {job['title']} - Score: {score:.1f}%")
            print(f"   City: {job['city']}")
            print(f"   Department: {job['department']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_score_calculation():
    """Test match score calculation logic."""
    print("\n" + "="*60)
    print("Test 3: Match Score Calculation")
    print("="*60)
    
    try:
        from rag.rag_engine import calculate_keyword_overlap
        
        # Test job
        job = {
            "title": "Software Engineer",
            "description": "Looking for a developer with Python, JavaScript, and SQL experience",
            "requirements": "Bachelor's degree in Computer Science. Experience with web development."
        }
        
        # Test profile with matching skills
        profile_match = {
            "interests": ["Information Technology"],
            "resume_parsed": {
                "skills": ["Python", "JavaScript", "SQL", "React"]
            }
        }
        
        # Test profile with no matching skills
        profile_no_match = {
            "interests": ["Public Safety"],
            "resume_parsed": {
                "skills": ["First Aid", "Emergency Management"]
            }
        }
        
        score_match = calculate_keyword_overlap(job, profile_match)
        score_no_match = calculate_keyword_overlap(job, profile_no_match)
        
        print(f"Matching profile score: {score_match:.2f} (expected: > 0.5)")
        print(f"Non-matching profile score: {score_no_match:.2f} (expected: < 0.3)")
        
        if score_match > score_no_match:
            print("✅ Score calculation working correctly!")
            return True
        else:
            print("❌ Scores don't make sense")
            return False
            
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all RAG tests."""
    print("\n" + "="*60)
    print("RAG Engine Test Suite")
    print("="*60)
    
    # Check API key
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found in environment!")
        print("Please set it in .env file")
        return
    
    results = []
    
    # Test 1: Embeddings
    results.append(("Embedding Generation", test_embedding_generation()))
    
    # Test 2: Storage and Search
    results.append(("Job Storage & Search", await test_job_storage_and_search()))
    
    # Test 3: Scoring
    results.append(("Score Calculation", test_score_calculation()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nPassed: {passed}/{total} tests")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed. Please review errors above.")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
