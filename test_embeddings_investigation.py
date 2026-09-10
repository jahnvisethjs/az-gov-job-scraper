"""
Test ASU AI embeddings endpoint with actual API token
Testing different endpoint possibilities based on API documentation
"""
import asyncio
import aiohttp
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

async def test_embeddings_direct():
    """Test embeddings endpoint directly with raw HTTP requests"""
    
    api_key = os.getenv("ASU_AI_API_KEY")
    if not api_key:
        print("❌ ASU_AI_API_KEY not found")
        return False
    
    print("="*70)
    print("ASU AI EMBEDDINGS ENDPOINT INVESTIGATION")
    print("="*70)
    print(f"✅ API Key loaded: {api_key[:20]}...")
    
    # Test different endpoint possibilities
    base_url = "https://api-main.aiml.asu.edu"
    test_text = "Python developer with machine learning experience"
    
    endpoints_to_test = [
        {
            "url": f"{base_url}/embeddings",
            "payload": {
                "query": test_text,
                "embeddings_provider": "openai",
                "embeddings_model": "text-embedding-3-small",
                "dimensions": 1024
            },
            "description": "Original /embeddings endpoint"
        },
        {
            "url": f"{base_url}/embeddings",
            "payload": {
                "query": test_text,
                "embeddings_provider": "openai",
                "embeddings_model": "te3s"
            },
            "description": "/embeddings with te3s model"
        },
        {
            "url": f"{base_url}/query",
            "payload": {
                "prompt": test_text,
                "model": "text-embedding-3-small",
                "endpoint": "embedding"
            },
            "description": "/query endpoint with embedding model"
        }
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        for i, test in enumerate(endpoints_to_test, 1):
            print(f"\n[Test {i}/{len(endpoints_to_test)}] {test['description']}")
            print(f"URL: {test['url']}")
            print(f"Payload: {test['payload']}")
            
            try:
                async with session.post(
                    test['url'],
                    headers=headers,
                    json=test['payload'],
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    status = response.status
                    print(f"Status Code: {status}")
                    
                    if status == 200:
                        result = await response.json()
                        print(f"✅ SUCCESS!")
                        print(f"Response keys: {list(result.keys())}")
                        
                        # Check for embedding in response
                        if "embeddings" in result:
                            print(f"Embedding length: {len(result['embeddings'])}")
                            return True
                        elif "embedding" in result:
                            print(f"Embedding length: {len(result['embedding'])}")
                            return True
                        elif "data" in result:
                            print(f"Data structure: {type(result['data'])}")
                            return True
                        else:
                            print(f"Response: {str(result)[:200]}")
                    else:
                        error_text = await response.text()
                        print(f"❌ Error {status}")
                        print(f"Response: {error_text[:300]}")
                        
            except Exception as e:
                print(f"❌ Exception: {type(e).__name__}: {str(e)}")
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_embeddings_direct())
    print("\n" + "="*70)
    if success:
        print("✅ Found working embeddings endpoint!")
    else:
        print("❌ No working embeddings endpoint found")
        print("Next steps: Check ASU AI documentation or contact support")
    print("="*70)
