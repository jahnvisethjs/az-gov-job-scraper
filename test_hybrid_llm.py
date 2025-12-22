import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from rag.rag_engine import JobRAG
from rag.resume_parser import ResumeParser
from utils.pdf_extractor import ResumeExtractor

async def test_hybrid_llm():
    print("=" * 60)
    print("HYBRID LLM TEST - Gemini Embeddings + ASU AI Text")
    print("=" * 60)
    
    # Test 1: Initialize RAG Engine
    print("\n[1/4] Initializing RAG engine...")
    try:
        rag = JobRAG()
        print("[OK] RAG engine initialized")
        print(f"  - Jobs in ChromaDB: {rag.get_job_count()}")
    except Exception as e:
        print(f"[FAIL] {e}")
        return
    
    # Test 2: Load resume
    print("\n[2/4] Loading resume...")
    resume_path = Path(r'C:\Users\jahnv\OneDrive\Desktop\Jahnvi\ASU\JahnviSethResumeASU.pdf')
    
    if not resume_path.exists():
        print(f"[FAIL] Resume not found")
        return
    
    try:
        with open(resume_path, 'rb') as f:
            resume_bytes = f.read()
        resume_text = ResumeExtractor.extract_text(resume_bytes, resume_path.name)
        print(f"[OK] Resume loaded - {len(resume_text)} chars")
    except Exception as e:
        print(f"[FAIL] {e}")
        return
    
    # Test 3: Parse resume with ASU AI
    print("\n[3/4] Parsing resume with ASU AI GPT-4o...")
    try:
        parser = ResumeParser()
        parsed = await parser.parse_resume(resume_text)
        print("[OK] Resume parsed with ASU AI")
        print(f"  - Skills: {len(parsed.get('skills', []))}")
        print(f"  - Experience: {len(parsed.get('experience', []))}")
        if parsed.get('skills'):
            print(f"  - Top skills: {', '.join(parsed['skills'][:5])}")
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 4: Generate embedding with Gemini
    print("\n[4/4] Generating embedding with Gemini...")
    try:
        test_text = f"Skills: {', '.join(parsed.get('skills', [])[:10])}"
        embedding = await rag.generate_embedding(test_text)
        print(f"[OK] Embedding generated with Gemini")
        print(f"  - Dimensions: {len(embedding)}")
    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"\n{'=' * 60}")
    print("[SUCCESS] All tests passed!")
    print(f"{'=' * 60}")
    print("\nHybrid Configuration Working:")
    print("  - Embeddings: Gemini embedding-001")  
    print("  - Text Gen: ASU AI GPT-4o")
    print("  - Vector DB: ChromaDB")

if __name__ == "__main__":
    asyncio.run(test_hybrid_llm())
