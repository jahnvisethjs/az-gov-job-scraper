"""
Final validation test for ASU AI migration
Tests resume parsing and embeddings with the ASU AI API
"""
import asyncio
import os

# Set credentials
os.environ["ASU_AI_API_KEY"] = "***REMOVED-CREDENTIAL***"
os.environ["LLM_PROVIDER"] = "asu_ai"

from rag.resume_parser import ResumeParser
from rag.rag_engine import JobRAG

async def test_migration():
    """Test complete ASU AI migration"""
    
    print("=" * 70)
    print("ASU AI MIGRATION VALIDATION TEST")
    print("=" * 70)
    print()
    
    # Test resume from image/description
    alexi_resume_text = """
    Alexi E. Vogel
    Graduate Student in GIS and Community Engagement Spatial Data Analyst at Arizona State University
    Email: alexicvogel@asu.edu
    
    Education:
    - MS Geographic Information Science, Arizona State University (Upcoming Spring 2026)
    - BS Geography (Summa Cum Laude), Arizona State University (2022)
    - BA Data Science and Analytics (Summa Cum Laude), Arizona State University (2022)
    
    Employment:
    - Research/Data Analyst (2025-Current): Advanced GIS analysis, data management, statistical programming in R and Python
    - Graduate Teaching Assistant, ASU (2024): Teaching GIS courses
    - Graduate Research Assistant, ASU (2024): Geographic research
    - Undergraduate Research Assistant, ASU (2023-2024): Demographic research using GIS
    
    Technical Skills:
    - Advanced: R, SQL, ArcGIS Pro/Online/Experience Builder, Excel/Microsoft Office, Tableau
    - Intermediate: Python, AutoCAD, QGIS, SAS, Google Earth Engine
    
    Certifications:
    - Graduate Certificate in Statistics and Data Science, Arizona State University (2025)
    - Undergraduate Certificate in Geographic Information Science Methods, Arizona State University (2022)
    - Undergraduate Certificate in Social Science Research Methods, Arizona State University (2022)
    """
    
    # Test 1: Resume Parsing with gpt-4o
    print("TEST 1: Resume Parsing with ASU AI (gpt-4o)")
    print("-" * 70)
    try:
        parser = ResumeParser()
        print(f"✓ Using model: {parser.model_name}")
        
        parsed = await parser.parse_resume(alexi_resume_text)
        
        print(f"✓ Skills extracted: {len(parsed.get('skills', []))} skills")
        print(f"  Sample skills: {', '.join(parsed['skills'][:5])}")
        print(f"✓ Experience: {len(parsed.get('experience', []))} positions")
        print(f"✓ Education: {len(parsed.get('education', []))} degrees")
        print(f"✓ Certifications: {len(parsed.get('certifications', []))} certs")
        print("✓ Resume parsing SUCCESSFUL with ASU AI!")
    except Exception as e:
        print(f"✗ Resume parsing FAILED: {e}")
        return False
    
    print()
    
    # Test 2: Embeddings with text-embedding-3-small
    print("TEST 2: Embeddings with OpenAI (text-embedding-3-small via ASU AI)")
    print("-" * 70)
    try:
        rag = JobRAG()
        test_job = {
            "title": "GIS Analyst",
            "department": "IT Department",
            "description": "Seeking GIS analyst with Python and ArcGIS skills",
            "requirements": "BS in Geography or GIS, experience with R and Python",
            "city": "Tempe",
            "job_type": "Full-time"
        }
        
        embedding = await rag.generate_embedding("GIS Analyst with Python skills")
        print(f"✓ Embedding generated: {len(embedding)} dimensions")
        print(f"✓ Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ...]")
        print("✓ Embeddings SUCCESSFUL with ASU AI!")
    except Exception as e:
        print(f"✗ Embeddings FAILED: {e}")
        return False
    
    print()
    print("=" * 70)
    print("✅ ALL TESTS PASSED - ASU AI MIGRATION SUCCESSFUL!")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  - API URL: https://api-main.aiml.asu.edu/query")
    print(f"  - Text Model: gpt-4o")
    print(f"  - Embedding Model: text-embedding-3-small")
    print(f"  - Provider: ASU AI Platform")
    print()
    return True

if __name__ == "__main__":
    success = asyncio.run(test_migration())
    exit(0 if success else 1)
