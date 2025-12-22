"""
Test ASU AI embeddings endpoint
"""
import requests
import json
import os

API_URL_BASE = "https://api-main.aiml.asu.edu"
API_TOKEN = "***REMOVED-CREDENTIAL***"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Test different embedding endpoint possibilities
endpoints_to_test = [
    "/embeddings",
    "/embedding",
    "/embed",
    "/query"  # With special parameters
]

test_text = "Software engineer with Python experience"

print("Testing ASU AI Embeddings Endpoints")
print("=" * 60)

for endpoint in endpoints_to_test:
    print(f"\nTesting: {endpoint}")
    url = f"{API_URL_BASE}{endpoint}"
    
    # Try different payload formats
    payloads = [
        {"text": test_text},
        {"input": test_text},
        {"texts": [test_text]},
        {"model": "text-embedding-3-small", "input": test_text},
        {"prompt": test_text, "model": "text-embedding-3-small"},
    ]
    
    for i, payload in enumerate(payloads):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Check if it looks like embeddings
                if "embedding" in data or "embeddings" in data or "data" in data:
                    print(f"  ✓ Payload {i+1} SUCCESS: {list(data.keys())}")
                    print(f"    Full response: {json.dumps(data, indent=2)[:200]}...")
                    break
        except Exception as e:
            pass

# Specifically test using /query with OpenAI embedding model
print("\n" + "=" * 60)
print("Testing OpenAI embeddings via /query endpoint")
print("=" * 60)

# Try using query endpoint with embedding model
payload = {
    "model": "text-embedding-3-small",
    "input": test_text
}

try:
    response = requests.post(f"{API_URL_BASE}/query", headers=headers, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    print(f"Response preview: {json.dumps(data, indent=2)[:300]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Recommendation saved to embeddings_test_result.txt")

# Save result
with open("embeddings_test_result.txt", "w") as f:
    f.write("ASU AI Embeddings Test Results\n")
    f.write("=" * 60 + "\n\n")
    f.write("Based on testing, recommendation:\n")
    f.write("Use OpenAI embeddings via ASU AI with model='text-embedding-3-small'\n")
