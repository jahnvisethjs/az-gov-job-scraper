"""
Test script for ASU AI Platform API - Save results to JSON
"""
import requests
import json
import sys
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
    
    results = {}
    
    # Test 1: Simple text generation
    print("Testing simple prompt...", file=sys.stderr)
    
    payload = {
        "prompt": "Say hello",
        "model": "gpt-4o-mini"
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        results['test1'] = {
            'payload': payload,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'response_text': response.text,
            'success': response.status_code == 200
        }
        try:
            results['test1']['response_json'] = response.json()
        except:
            pass
    except Exception as e:
        results['test1'] = {
            'payload': payload,
            'error': str(e),
            'error_type': type(e).__name__
        }
    
    # Test 2: Different Payload Format (with messages)
    print("Testing messages format...", file=sys.stderr)
    
    payload2 = {
        "messages": [
            {"role": "user", "content": "What is 2+2?"}
        ],
        "model": "gpt-4o-mini"
    }
    
    try:
        response2 = requests.post(API_URL, headers=headers, json=payload2, timeout=30)
        results['test2'] = {
            'payload': payload2,
            'status_code': response2.status_code,
            'headers': dict(response2.headers),
            'response_text': response2.text,
            'success': response2.status_code == 200
        }
        try:
            results['test2']['response_json'] = response2.json()
        except:
            pass
    except Exception as e:
        results['test2'] = {
            'payload': payload2,
            'error': str(e),
            'error_type': type(e).__name__
        }
    
    # Save to file
    with open('apitest_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("Results saved to apitest_results.json", file=sys.stderr)
    print("Done", file=sys.stderr)

if __name__ == "__main__":
    test_api()
