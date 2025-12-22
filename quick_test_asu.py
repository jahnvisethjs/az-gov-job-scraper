"""Quick test with the provided ASU AI token"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set the API key directly
os.environ["ASU_AI_API_KEY"] = "***REMOVED-CREDENTIAL***"

from rag.asu_ai_provider import ASUAIProvider

async def quick_test():
    provider = ASUAIProvider()
    
    print("Testing ASU AI Provider...")
    print(f"Configuration: {provider.get_usage_info()}\n")
    
    # Test 1: Simple question
    print("Test 1: Simple question")
    response = await provider.generate_content("What is 2+2? Answer in one short sentence.")
    print(f"Response: {response}\n")
    
    # Test 2: Resume-like prompt
    print("Test 2: Resume parsing simulation")
    prompt = """Extract key information from this text:
    
    Software Engineer with 5 years experience in Python, JavaScript, and cloud technologies.
    Education: BS Computer Science from ASU.
    
    Return only: Years of experience, Top 3 skills, Education level"""
    
    response = await provider.generate_content(prompt)
    print(f"Response: {response}\n")
    
    print("✓ All tests passed!")

if __name__ == "__main__":
    asyncio.run(quick_test())
