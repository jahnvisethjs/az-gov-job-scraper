"""
Minimal test of ASU AI /embeddings endpoint using exact documentation format
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ASU_AI_API_KEY")

if not api_key:
    print("❌ API key not found")
    exit(1)

print("🔍 Testing ASU AI /embeddings endpoint")
print(f"API Key: {api_key[:30]}...")

url = "https://api-main.aiml.asu.edu/embeddings"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Test 1: Exact format from documentation
payload1 = {
    "query": "Hi what is your name?",
    "embeddings_provider": "openai",
    "embeddings_model": "ada",
    "dimensions": 1356,
    "normalize": True
}

print(f"\n[Test 1] Documentation example")
print(f"URL: {url}")
print(f"Payload: {payload1}")

response1 = requests.post(url, headers=headers, json=payload1)
print(f"Status: {response1.status_code}")
print(f"Response: {response1.text[:500]}")

# Test 2: Our configuration (te3s, 1024 dims)
payload2 = {
    "query": "Python developer with ML experience",
    "embeddings_provider": "openai",
    "embeddings_model": "text-embedding-3-small",
    "dimensions": 1024
}

print(f"\n[Test 2] Our configuration")
print(f"Payload: {payload2}")

response2 = requests.post(url, headers=headers, json=payload2)
print(f"Status: {response2.status_code}")
print(f"Response: {response2.text[:500]}")

# Test 3: Without dimensions (default)
payload3 = {
    "query": "Test query",
    "embeddings_provider": "openai",
    "embeddings_model": "te3s"
}

print(f"\n[Test 3] Model 'te3s' without dimensions")
print(f"Payload: {payload3}")

response3 = requests.post(url, headers=headers, json=payload3)
print(f"Status: {response3.status_code}")
print(f"Response: {response3.text[:500]}")

print("\n" + "="*70)
if response1.status_code == 200 or response2.status_code == 200 or response3.status_code == 200:
    print("✅ At least one configuration worked!")
else:
    print("❌ All tests failed")
    print("\nPossible issues:")
    print("1. /embeddings endpoint not yet deployed on ASU AI platform")
    print("2. Endpoint requires different authentication")
    print("3. Server-side issue (contact ASU AI support)")
print("="*70)
