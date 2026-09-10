"""
End-to-end integration test for ASU AI embeddings with RAG engine
Tests the complete pipeline: embeddings -> ChromaDB -> semantic search
"""
import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

from rag.rag_engine import JobRAG

def test_rag_with_asu_embeddings():
    """Test RAG engine with ASU AI embeddings"""
    
    print("=" * 70)
    print("RAG ENGINE INTEGRATION TEST - ASU AI EMBEDDINGS")
    print("=" * 70)
    
    # Check API key
    api_key = os.getenv("ASU_AI_API_KEY")
    if not api_key:
        print("❌ ASU_AI_API_KEY not found in environment")
        return False
    
    print(f"✅ API Key found")
    
    try:
        # Initialize RAG engine
        print("\n[1/5] Initializing RAG engine...")
        rag = JobRAG(api_key=api_key)
        print(f"✅ RAG engine initialized")
        print(f"   ChromaDB path: {Path('./chroma_db').absolute()}")
        print(f"   Collection: jobs")
        
        # Test embedding generation
        print("\n[2/5] Testing embedding generation...")
        test_text = "Python developer with machine learning expertise"
        embedding = rag.generate_embedding(test_text)
        print(f"✅ Embedding generated")
        print(f"   Dimensions: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
        
        if len(embedding) != 1024:
            print(f"⚠️  WARNING: Expected 1024 dimensions, got {len(embedding)}")
        
        # Clear existing jobs
        print("\n[3/5] Clearing existing jobs from ChromaDB...")
        rag.clear_jobs()
        print(f"✅ ChromaDB cleared")
        
        # Add sample jobs
        print("\n[4/5] Adding sample jobs to ChromaDB...")
        sample_jobs = [
            {
                "title": "Software Engineer",
                "city": "Phoenix",
                "department": "IT",
                "description": "Develop Python applications with machine learning",
                "requirements": "Python, TensorFlow, 3+ years experience",
                "salary": "$80k-$100k",
                "url": "https://example.com/job1",
                "job_id": "phoenix_001"
            },
            {
                "title": "GIS Analyst",
                "city": "Tempe",
                "department": "Planning",
                "description": "Analyze spatial data using ArcGIS and Python",
                "requirements": "GIS, Python, SQL, 2+ years experience",
                "salary": "$65k-$85k",
                "url": "https://example.com/job2",
                "job_id": "tempe_001"
            },
            {
                "title": "Data Scientist",
                "city": "Mesa",
                "department": "Analytics",
                "description": "Build predictive models using Python and R",
                "requirements": "Python, R, Statistics, Machine Learning",
                "salary": "$90k-$110k",
                "url": "https://example.com/job3",
                "job_id": "mesa_001"
            }
        ]
        
        jobs_added = rag.add_jobs(sample_jobs)
        print(f"✅ Added {jobs_added} jobs to ChromaDB")
        print(f"   Total jobs in database: {rag.get_job_count()}")
        
        # Test semantic search
        print("\n[5/5] Testing semantic search...")
        test_profile = {
            "interests": ["Software Development", "Machine Learning"],
            "degree": "Bachelor's in Computer Science",
            "resume_parsed": {
                "skills": ["Python", "TensorFlow", "Machine Learning", "Data Analysis"],
                "experience": [
                    {
                        "title": "Junior Developer",
                        "company": "Tech Corp",
                        "description": "Built ML models with Python"
                    }
                ]
            }
        }
        
        matched_jobs = rag.search_jobs(test_profile, top_k=3)
        print(f"✅ Search completed")
        print(f"   Found {len(matched_jobs)} matching jobs")
        
        if matched_jobs:
            print("\n   Top matches:")
            for i, (job, score) in enumerate(matched_jobs[:3], 1):
                print(f"   {i}. {job['title']} in {job['city']} - Score: {score:.1f}%")
        
        print("\n" + "=" * 70)
        print("✅ ALL RAG INTEGRATION TESTS PASSED!")
        print("=" * 70)
        print("\nKey Findings:")
        print(f"  - ASU AI embeddings working: ✅")
        print(f"  - Embedding dimensions: {len(embedding)}")
        print(f"  - ChromaDB integration: ✅")
        print(f"  - Semantic search: ✅")
        print(f"  - Jobs matched: {len(matched_jobs)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_with_asu_embeddings()
    exit(0 if success else 1)
