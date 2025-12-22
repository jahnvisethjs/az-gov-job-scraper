"""
Test different models available on ASU AI Platform
"""
import asyncio
import os

os.environ["ASU_AI_API_KEY"] = "***REMOVED-CREDENTIAL***"

from rag.asu_ai_provider import ASUAIProvider

async def test_models():
    """Test which models are available"""
    
    # Common models that might be available on ASU AI Platform
    models_to_test = [
        "gpt-4o-mini",           # Fast, efficient GPT-4
        "gpt-4o",                # Latest GPT-4 Omni
        "gpt-4-turbo",           # GPT-4 Turbo
        "gpt-4",                 # Standard GPT-4
        "gpt-3.5-turbo",         # GPT-3.5
        "claude-3-5-sonnet",     # Claude 3.5 Sonnet
        "claude-3-opus",         # Claude 3 Opus
        "claude-3-sonnet",       # Claude 3 Sonnet
        "claude-3-haiku",        # Claude 3 Haiku
        "gemini-1.5-pro",        # Gemini Pro
        "gemini-1.5-flash",      # Gemini Flash
    ]
    
    provider = ASUAIProvider()
    test_prompt = "Say 'OK' if you can read this."
    
    print("\n" + "=" * 70)
    print("TESTING AVAILABLE MODELS ON ASU AI PLATFORM")
    print("=" * 70 + "\n")
    
    available = []
    unavailable = []
    
    for model in models_to_test:
        print(f"Testing: {model}...", end=" ")
        try:
            response = await provider.generate_content(test_prompt, model=model)
            if response and len(response) > 0:
                print(f"✓ AVAILABLE - Response: {response[:50]}")
                available.append(model)
            else:
                print("✗ No response")
                unavailable.append(model)
        except Exception as e:
            error_msg = str(e)[:60]
            print(f"✗ ERROR - {error_msg}")
            unavailable.append(model)
        
        await asyncio.sleep(0.5)  # Small delay between tests
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {len(available)} available, {len(unavailable)} unavailable")
    print("=" * 70 + "\n")
    
    if available:
        print("✓ AVAILABLE MODELS:")
        for model in available:
            print(f"  - {model}")
    
    if unavailable:
        print(f"\n✗ UNAVAILABLE MODELS:")
        for model in unavailable:
            print(f"  - {model}")
    
    print("\n")

if __name__ == "__main__":
    asyncio.run(test_models())
