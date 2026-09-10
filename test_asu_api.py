"""
Test script for ASU AI Platform API
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_URL = "https://api-main.aiml.asu.edu/query"
API_TOKEN = os.getenv("ASU_AI_API_KEY")

def test_api():
    """Test basic API call"""
    if not API_TOKEN:
        raise RuntimeError("Set ASU_AI_API_KEY in .env or the process environment before running this test.")
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Simple text generation
    print("=" * 60)
    print("Test 1: Simple Text Generation")
    print("=" * 60)
    
    payload = {
        "prompt": "Hello! Can you tell me what models are available?",
        "model": "gpt-4o-mini"
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print(f"\nResponse Body:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        if 'response' in locals():
            print(f"Response text: {response.text}")
    
    print("\n" + "=" * 60)
    print("Test 2: Different Payload Format (with messages)")
    print("=" * 60)
    
    payload2 = {
        "messages": [
            {"role": "user", "content": "What is 2+2?"}
        ],
        "model": "gpt-4o-mini"
    }
    
    try:
        response2 = requests.post(API_URL, headers=headers, json=payload2, timeout=30)
        print(f"Status Code: {response2.status_code}")
        print(f"\nResponse Body:")
        try:
            print(json.dumps(response2.json(), indent=2))
        except:
            print(response2.text)
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        if 'response2' in locals():
            print(f"Response text: {response2.text}")

if __name__ == "__main__":
    test_api()
