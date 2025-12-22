"""
Compare requests vs aiohttp for ASU AI embeddings
"""
import asyncio
import aiohttp
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ASU_AI_API_KEY")
url = "https://api-main.aiml.asu.edu/embeddings"

payload = {
    "query": "Test embedding",
    "embeddings_provider": "openai",
    "embeddings_model": "te3s",
    "dimensions": 1024
}

print("="*70)
print("COMPARING REQUESTS VS AIOHTTP")
print("="*70)

# Test 1: requests library (working)
print("\n[1] Testing with requests library...")
headers_requests = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, headers=headers_requests, json=payload, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS with requests!")
        if "embeddings" in data:
            print(f"Embedding length: {len(data['embeddings'])}")
        print(f"Response keys: {list(data.keys())}")
    else:
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: aiohttp library
print("\n[2] Testing with aiohttp...")

async def test_aiohttp():
    headers_aiohttp = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers_aiohttp,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                status = response.status
                print(f"Status: {status}")
                
                if status == 200:
                    data = await response.json()
                    print(f"✅ SUCCESS with aiohttp!")
                    if "embeddings" in data:
                        print(f"Embedding length: {len(data['embeddings'])}")
                    print(f"Response keys: {list(data.keys())}")
                else:
                    text = await response.text()
                    print(f"Response: {text[:200]}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

asyncio.run(test_aiohttp())

print("\n" + "="*70)
print("If requests works but aiohttp fails, this is likely an aiohttp")
print("configuration issue or server-side behavior difference.")
print("="*70)
