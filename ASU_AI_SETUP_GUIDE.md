# ASU AI Integration - Setup and Usage Guide

## ✅ Integration Complete

The ASU AI Platform (CreateAI) has been successfully integrated into your project! You can now use ChatGPT and other LLM models for resume parsing and job matching.

---

## 🚀 Quick Start

### 1. Set Your API Token

Create or update your `.env` file:

```bash
# Copy the example file
cp .env.example .env
```
Run the quick test:

```bash
python quick_test_asu.py
```

You should see:
```
Testing ASU AI Provider...
Configuration: {'provider': 'ASU AI Platform', 'base_url': '...', ...}

Test 1: Simple question
Response: 2+2 equals 4.

Test 2: Resume parsing simulation  
Response: [extracted information]

✓ All tests passed!
```

### 3. Run Examples

See comprehensive examples:

```bash
python example_asu_ai_usage.py
```

---

## 📋 What Was Added

### New Files Created

1. **`rag/asu_ai_provider.py`** - Main ASU AI integration class
   - `ASUAIProvider` class with async support
   - `generate_content()` - Text generation
   - `generate_embedding()` - Embeddings (if endpoint available)
   - `chat_completion()` - ChatGPT-style messages

2. **`example_asu_ai_usage.py`** - Comprehensive usage examples
   - Basic text generation
   - Resume parsing
   - Job matching
   - Different models

3. **`quick_test_asu.py`** - Quick verification test

### Modified Files

1. **`config.py`**
   - Added `LLM_PROVIDER` selection
   - Added `ASU_AI_*` configuration variables

2. **`.env.example`**
   - Added ASU AI configuration template

---

## 💻 How to Use in Your Code

### Basic Usage

```python
from rag.asu_ai_provider import ASUAIProvider
import asyncio

async def my_function():
    # Initialize provider
    provider = ASUAIProvider()
    
    # Generate response
    response = await provider.generate_content("Your prompt here")
    print(response)

# Run async function
asyncio.run(my_function())
```

###Using Different Models

```python
provider = ASUAIProvider(model="gpt-4o")  # or "gpt-4o-mini", "claude-3-5-sonnet", etc.

response = await provider.generate_content(
    "Explain machine learning",
    model="gpt-4o"  # Override default model
)
```

### Resume Parsing Example

```python
async def parse_resume(resume_text):
    provider = ASUAIProvider()
    
    prompt = f"""
    Extract structured information from this resume:
    {resume_text}
    
    Return JSON with: skills, experience_years, education, strengths
    """
    
    result = await provider.generate_content(prompt)
    return result
```

### Job Matching Example

```python
async def get_job_advice(job_description, candidate_profile):
    provider = ASUAIProvider()
    
    prompt = f"""
    Job: {job_description}
    Candidate: {candidate_profile}
    
    Provide tailored application advice with:
    1. Match score (0-100)
    2. Strengths to highlight
    3. Gaps to address
    """
    
    advice = await provider.generate_content(prompt)
    return advice
```

---

## 🔧 API Details

### Endpoint

```
POST https://api-main.aiml.asu.edu/query
```

### Request Format

```json
{
  "prompt": "Your prompt here",
  "model": "gpt-4o-mini"
}
```

### Response Format

```json
{
  "response": "The AI's text response",
  "metadata": {
    "query_id": "unique-id",
    "usage_metric": {
      "input_token_count": 30,
      "output_token_count": 10,
      "input_token_cost": 0.00006,
      "output_token_cost": 0.00002
    }
  }
}
```

### Available Models

Based on the ASU AI Platform documentation, you have access to 25+ models including:
- `gpt-4o` - Latest GPT-4 Omni
- `gpt-4o-mini` - Faster, cost-effective GPT-4 (default)
- `gpt-4` - Standard GPT-4
- Claude models (if available)
- And more...

---

## 🔄 Switching Between Providers

Your project supports both Gemini and ASU AI. Switch by changing the `LLM_PROVIDER` in `.env`:

```bash
# Use ASU AI (CreateAI)
LLM_PROVIDER=asu_ai

# Use Google Gemini (original)
LLM_PROVIDER=gemini
```

---

## 📊 Benefits of ASU AI Integration

| Feature | Google Gemini | ASU AI Platform |
|---------|---------------|-----------------|
| **Cost** | Free tier limits | Institutional (possibly free) |
| **Rate Limits** | 15 RPM, 1500 RPD | Likely higher for ASU |
| **Models** | Gemini only | 25+ models (GPT, Claude, etc.) |
| **Support** | Community | ASU institutional |
| **Token Tracking** | Limited | Detailed in metadata |

---

## 🐛 Troubleshooting

### Error: "ASU AI API key is required"

Make sure you've set `ASU_AI_API_KEY` in your `.env` file.

### Error: "Unexpected response format"

The API might be returning an error. Check the response message. Common issues:
- Invalid model name
- Rate limit exceeded
- Token expired

### Error: Connection timeout

Increase timeout in the provider:

```python
# In asu_ai_provider.py, line ~75
timeout=aiohttp.ClientTimeout(total=120)  # Increase from 60 to 120 seconds
```

### Embeddings Not Working

The embeddings endpoint may have a different format. Currently using Gemini for embeddings is recommended. To use Gemini embeddings while using ASU AI for text:

Set in `.env`:
```bash
LLM_PROVIDER=gemini  # This will use Gemini for embeddings
ASU_AI_ENABLED=true  # Enable ASU AI for text generation
```

Then modify your code to use ASU AI specifically for text generation.

---

## 📚 Next Steps

### Option 1: Keep Current Setup (Gemini)
No changes needed. Continue using Gemini.

### Option 2: Switch to ASU AI Only
1. Update `.env` with your ASU AI token
2. Set `LLM_PROVIDER=asu_ai`
3. Test with `python quick_test_asu.py`

### Option 3: Integration into Resume Parser
To update your `resume_parser.py` to use ASU AI:

```python
# In rag/resume_parser.py
from config import LLM_PROVIDER
from rag.asu_ai_provider import ASUAIProvider

class ResumeParser:
    def __init__(self):
        if LLM_PROVIDER == "asu_ai":
            self.provider = ASUAIProvider()
        else:
            # Use Gemini (current implementation)
            ...
```

### Option 4: Hybrid Approach
Use ASU AI for text generation and Gemini for embeddings (recommended).

---

## 🔗 Resources

- **API Documentation**: https://platform.aiml.asu.edu/api
- **Your Project API**: https://api-main.aiml.asu.edu/query
- **Integration Guide**: `ASU_AI_API_INTEGRATION.md`
- **Provider Code**: `rag/asu_ai_provider.py`
- **Examples**: `example_asu_ai_usage.py`

---

## ✨ Summary

You now have full access to ChatGPT and other LLMs through the ASU AI Platform! 

**Key Points:**
- ✅ ASU AI provider class created and tested
- ✅ Configuration files updated
- ✅ Examples and tests provided
- ✅ Easy to switch between Gemini and ASU AI
- ✅ Your token is working and verified

**To use it:**
1. Set `LLM_PROVIDER=asu_ai` in `.env`
2. Add your API token
3. Run `python quick_test_asu.py` to verify
4. Use `ASUAIProvider()` in your code

Enjoy using ChatGPT for your job search application! 🎉
