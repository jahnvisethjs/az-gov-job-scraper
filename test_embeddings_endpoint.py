"""Test embeddings endpoint directly"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("ASU_AI_API_KEY")
if not API_TOKEN:
    raise RuntimeError("Set ASU_AI_API_KEY in .env or the process environment before running this test.")

# Try different endpoint formats
endpoints = [
    "https://api-main.aiml.asu.edu/embeddings",
    "https://platform.aiml.asu.edu/embeddings",
    "https://api-main.aiml.asu.edu/api/embeddings",
]

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "query": "Test embedding",
    "embeddings_provider": "openai",
    "embeddings_model": "te3s"
}

for url in endpoints:
    print(f"\nTrying: {url}")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✓ SUCCESS!")
            result = response.json()
            print(f"  Response keys: {list(result.keys()) if isinstance(result, dict) else 'list'}")
            if isinstance(result, dict) and 'embeddings' in result:
                print(f"  Embedding length: {len(result['embeddings'])}")
        else:
            print(f"  Error: {response.text[:200]}")
    except Exception as e:
        print(f"  Exception: {e}")
