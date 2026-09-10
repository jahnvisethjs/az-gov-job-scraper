"""
Test ASU AI embeddings endpoint directly
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from rag.asu_ai_provider import ASUAIProvider

async def test_asu_embeddings():
    """Test ASU AI embeddings with text-embedding-3-small"""
    
    print("=" * 70)
    print("ASU AI EMBEDDINGS TEST")
    print("=" * 70)
    
    # Check API key
    api_key = os.getenv("ASU_AI_API_KEY")
    if not api_key:
        print("❌ ASU_AI_API_KEY not found in environment")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Initialize provider
    provider = ASUAIProvider(api_key=api_key)
    print(f"✅ Provider initialized")
    print(f"   Base URL: {provider.base_url}")
    print(f"   Model: {provider.model}")
    
    # Test embedding generation
    test_texts = [
        "Software engineer with Python and machine learning experience",
        "Urban planner specializing in GIS and data analysis",
        "Public safety officer with emergency response training"
    ]
    
    print("\n" + "=" * 70)
    print("TESTING EMBEDDINGS GENERATION")
    print("=" * 70)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n[Test {i}/3] Text: '{text[:50]}...'")
        
        try:
            # Generate embedding
            embedding = await provider.generate_embedding(
                text=text,
                model="text-embedding-3-small",
                provider="openai",
                dimensions=1024
            )
            
            print(f"✅ SUCCESS!")
            print(f"   Dimensions: {len(embedding)}")
            print(f"   First 5 values: {embedding[:5]}")
            print(f"   Type: {type(embedding)}")
            
            # Verify dimensions
            if len(embedding) != 1024:
                print(f"⚠️  WARNING: Expected 1024 dimensions, got {len(embedding)}")
            
        except Exception as e:
            print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
            return False
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = asyncio.run(test_asu_embeddings())
    exit(0 if success else 1)
