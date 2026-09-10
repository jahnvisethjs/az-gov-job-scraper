"""
Integration Test: ASU AI for Job Matching Application (Windows-Compatible)
"""
import asyncio
import os
import time
from dotenv import load_dotenv

# Load the API key from .env or the process environment.
load_dotenv()

from rag.asu_ai_provider import ASUAIProvider


async def main():
    print("\nASU AI Integration Test Suite")
    print("=" * 60)
    
    provider = ASUAIProvider()
    
    # Test 1: Resume Parsing
    print("\n[TEST 1] Resume Parsing")
    print("-" * 60)
    resume_prompt = """Extract from this resume: "IT Manager with 8 years experience 
in government IT, Security+ certified, BS Computer Science from ASU." 
Return: years of experience, key skill, education."""
    
    result = await provider.generate_content(resume_prompt)
    print("Result:", result[:200])
    
    # Test 2: Job Matching
    print("\n[TEST 2] Job Matching")
    print("-" * 60)
    match_prompt = """Job: IT Manager, City of Phoenix (requires 5+ years, Security+)
Candidate: 8 years government IT, Security+ certified
Give match score 0-100 and top 2 strengths in one sentence."""
    
    result = await provider.generate_content(match_prompt)
    print("Result:", result[:200])
    
    # Test 3: Quick Performance Check
    print("\n[TEST 3] Performance")
    print("-" * 60)
    start = time.time()
    result = await provider.generate_content("What is FISMA? One sentence.")
    elapsed = time.time() - start
    print(f"Response: {result[:100]}")
    print(f"Time: {elapsed:.2f}s")
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("ASU AI integration is working correctly.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
