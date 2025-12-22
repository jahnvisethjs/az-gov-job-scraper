"""
Test to see what exact parameters are being used
"""
import os
from dotenv import load_dotenv

load_dotenv()

from config import ASU_AI_EMBEDDINGS_PROVIDER, ASU_AI_EMBEDDINGS_MODEL, ASU_AI_EMBEDDINGS_DIMENSIONS

print("="*70)
print("CONFIG VALUES")
print("="*70)
print(f"Provider: {ASU_AI_EMBEDDINGS_PROVIDER}")
print(f"Model: {ASU_AI_EMBEDDINGS_MODEL}")
print(f"Dimensions: {ASU_AI_EMBEDDINGS_DIMENSIONS}")

# Test with these exact values
from rag.asu_ai_provider import ASUAIProvider

provider = ASUAIProvider()

test_text = "Software engineer with Python experience"

print(f"\n{'='*70}")
print("TESTING WITH CONFIG VALUES")
print(f"{'='*70}")

try:
    embedding = provider.generate_embedding(
        text=test_text,
        model=ASU_AI_EMBEDDINGS_MODEL,
        provider=ASU_AI_EMBEDDINGS_PROVIDER,
        dimensions=ASU_AI_EMBEDDINGS_DIMENSIONS
    )
    print(f"✅ SUCCESS with config values!")
    print(f"Embedding length: {len(embedding)}")
except Exception as e:
    print(f"❌ FAILED: {type(e).__name__}: {e}")
    
# Also test with te3s which we know works
print(f"\n{'='*70}")
print("TESTING WITH te3s")
print(f"{'='*70}")

try:
    embedding = provider.generate_embedding(
        text=test_text,
        model="te3s",
        provider="openai",
        dimensions=1024
    )
    print(f"✅ SUCCESS with te3s!")
    print(f"Embedding length: {len(embedding)}")
except Exception as e:
    print(f"❌ FAILED: {type(e).__name__}: {e}")

print("="*70)
