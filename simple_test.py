"""
Simple test of ASU AI API
"""
import requests
import json

API_URL = "https://api-main.aiml.asu.edu/query"
API_TOKEN = "***REMOVED-CREDENTIAL***"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "prompt": "Say hello in one word",
    "model": "gpt-4o-mini"
}

response = requests.post(API_URL, headers=headers, json=payload)
data = response.json()

# Extract just the text response
if 'text' in data:
    print(f"SUCCESS: {data['text']}")
elif 'message' in data:
    print(f"API Response: {data['message']}")
else:
    print(f"Unknown response format")
    
# Save full response for analysis
with open('simple_test_result.json', 'w') as f:
    json.dump({'status': response.status_code, 'data': data}, f, indent=2)
