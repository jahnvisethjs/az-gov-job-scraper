# ASU AI Quick Reference Card

## Instant Copy-Paste Examples

### Example 1: Simple Question
```python
from rag.asu_ai_provider import ASUAIProvider
import asyncio

async def ask():
    provider = ASUAIProvider()
    response = await provider.generate_content("What is Python?")
    print(response)

asyncio.run(ask())
```

### Example 2: Resume Parsing
```python
from rag.asu_ai_provider import ASUAIProvider
import asyncio

async def parse_resume():
    provider = ASUAIProvider()
    
    resume = "Software Engineer with 5 years Python experience, BS in CS"
    
    prompt = f"""
    Extract from this resume:
    {resume}
    
    Return JSON: {{years: X, top_skill: "...", education: "..."}}
    """
    
    result = await provider.generate_content(prompt)
    print(result)

asyncio.run(parse_resume())
```

### Example 3: Job Matching
```python
from rag.asu_ai_provider import ASUAIProvider
import asyncio

async def match_job():
    provider = ASUAIProvider()
    
    job = "IT Manager - requires 5 years experience, Security+ cert"
    candidate = "8 years IT experience, Security+ certified"
    
    prompt = f"""
    Job: {job}
    Candidate: {candidate}
    
    Match score (0-100) and top 2 strengths:
    """
    
    advice = await provider.generate_content(prompt)
    print(advice)

asyncio.run(match_job())
```

### Example 4: Different Model
```python
provider = ASUAIProvider(model="gpt-4o")  # Use more capable model
response = await provider.generate_content("Complex prompt...")
```

### Example 5: Helper Function
```python
from rag.llm_helper import ask_llm_sync

# Synchronous (no async/await needed)
response = ask_llm_sync("What is FISMA compliance?")
print(response)
```

---

## Configuration (.env file)

```bash
LLM_PROVIDER=asu_ai
ASU_AI_ENABLED=true
ASU_AI_API_KEY=your_token_here
ASU_AI_MODEL=gpt-4o-mini
```

---

## Common Models

- `gpt-4o-mini` - Fast, cost-effective (DEFAULT)
- `gpt-4o` - Latest, most capable
- `gpt-4` - Standard GPT-4

---

## Response Format

```json
{
  "response": "The actual text answer",
  "metadata": {
    "query_id": "unique-id",
    "usage_metric": {
      "input_token_count": 30,
      "output_token_count": 10
    }
  }
}
```

You only need `response["response"]` - the provider handles parsing for you!

---

## Quick Test

```bash
python quick_test_asu.py
```

---

## Need Help?

1. **Setup Guide**: `ASU_AI_SETUP_GUIDE.md`
2. **Examples**: `example_asu_ai_usage.py`
3. **Code**: `rag/asu_ai_provider.py`
