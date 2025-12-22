"""
Direct test of the ASU AI provider embedding method
"""
import os
from dotenv import load_dotenv

load_dotenv()

from rag.asu_ai_provider import ASUAIProvider

print("Testing ASUAIProvider.generate_embedding()...")
print("="*70)

provider = ASUAIProvider()

try:
    embedding = provider.generate_embedding(
        text="Python developer with ML experience",
        model="te3s",
        provider="openai",
        dimensions=1024
    )
    
    print(f"✅ SUCCESS!")
    print(f"Embedding length: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    
except Exception as e:
    print(f"❌ FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("="*70)
