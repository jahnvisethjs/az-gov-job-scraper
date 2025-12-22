# ASU AI API Integration Guide

## Overview

This document provides guidance on integrating the ASU AI Platform API (`https://platform-beta.aiml.asu.edu/api`) into the Arizona Government Job Scraper project as a potential alternative or complement to the current Google Gemini API implementation.

## Current Implementation

The project currently uses **Google Gemini API** for:

1. **Resume Parsing** ([`rag/resume_parser.py`](file:///c:/Users/jahnv/OneDrive/Desktop/Jahnvi/ASU/SocialEmbededdness%20Job/jobScrape/az-gov-job-scraper/rag/resume_parser.py))
   - Model: `gemini-2.5-flash`
   - Extracts structured data from resume text (skills, experience, education, projects)
   
2. **Job Matching & Embeddings** ([`rag/rag_engine.py`](file:///c:/Users/jahnv/OneDrive/Desktop/Jahnvi/ASU/SocialEmbededdness%20Job/jobScrape/az-gov-job-scraper/rag/rag_engine.py))
   - Embedding Model: `models/embedding-001`
   - Semantic job matching using ChromaDB vector database
   - Tailoring advice generation

3. **API Configuration** ([`config.py`](file:///c:/Users/jahnv/OneDrive/Desktop/Jahnvi/ASU/SocialEmbededdness%20Job/jobScrape/az-gov-job-scraper/config.py))
   - Rate limiting: 15 RPM, 1500 RPD, 1M TPD (Gemini free tier)

---

## ASU AI Platform API

### Introduction

The ASU AI Platform (CreateAI) provides:
- **25+ Large Language Models** (Text, Audio, Image, Vision capabilities)
- **REST and WebSocket** interfaces
- **Multi-modal endpoints** (speech, image, vision, audio, text)
- **Institutional access** for ASU departments/teams

### Getting Access

> [!IMPORTANT]
> **To use the ASU AI API, you must obtain an access token:**
> - Contact: **Ayat Sweid** or **Paul Alvarado**
> - You will receive a dedicated API endpoint for your department/team
> - API format: `https://api-{your_api}-beta.aiml.asu.edu/{method}`
>   - `{your_api}` is typically `main`

### API Architecture

#### Base URLs

**REST API:**
```
https://api-{your_api}-beta.aiml.asu.edu/{method}
```

**WebSocket API:**
```
wss://apiws-{your_api}-beta.aiml.asu.edu/?access_token={access_token}
```

#### Available Methods

Based on the API documentation structure, the following methods are available:

1. **`queryV2`** - Primary query endpoint
   - Multi-modal support via `endpoint` parameter
   - Endpoints: `"speech"`, `"image"`, `"vision"`, `"audio"`, `"text"`

2. **`query`** - Legacy query method
   
3. **`search`** - Search functionality
   
4. **`embeddings`** - Generate embeddings for semantic search
   
5. **`chunk`** - Text chunking for RAG applications

#### Authentication

**REST:**
- Token in `Authorization` header: `Bearer {access_token}`

**WebSocket:**
- Token in URL parameter: `?access_token={access_token}`

---

## Integration Plan for This Project

### Why Consider ASU AI API?

1. **Institutional Support** - Direct ASU support and potentially higher/flexible rate limits
2. **Cost Efficiency** - May be covered by ASU institutional subscription vs. personal Gemini API costs
3. **Multi-Model Access** - Access to 25+ models vs. single Gemini model
4. **Embeddings API** - Native embeddings endpoint (currently uses Gemini embeddings)

### Recommended Approach: Hybrid Integration

Instead of completely replacing Gemini, implement an **abstraction layer** that supports both APIs:

```python
# New file: rag/llm_factory.py

class LLMProvider:
    """Abstract base class for LLM providers."""
    
    async def generate_content(self, prompt: str) -> str:
        raise NotImplementedError
    
    async def generate_embedding(self, text: str) -> List[float]:
        raise NotImplementedError

class GeminiProvider(LLMProvider):
    """Google Gemini implementation (current)."""
    # ... existing code
    
class ASUAIProvider(LLMProvider):
    """ASU AI Platform implementation (new)."""
    # ... new implementation
```

### Migration Steps

#### Phase 1: Add ASU AI Configuration

**Update `config.py`:**

```python
# ASU AI Platform Configuration
ASU_AI_ENABLED = os.getenv("ASU_AI_ENABLED", "true").lower() == "true"
ASU_AI_API_KEY = os.getenv("ASU_AI_API_KEY", "")
ASU_AI_BASE_URL = os.getenv("ASU_AI_BASE_URL", "https://api-main-beta.aiml.asu.edu")
ASU_AI_MODEL = os.getenv("ASU_AI_MODEL", "gpt-4o")  # Adjust based on available models
ASU_AI_EMBEDDING_MODEL = "text-embedding-3-small"

# LLM Provider (gemini or asu_ai)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "asu_ai")
```

**Update `.env.example`:**

```env
# Primary LLM Provider (gemini or asu_ai)
LLM_PROVIDER=gemini

# Google Gemini API (current)
GEMINI_API_KEY=your_gemini_api_key_here

# ASU AI Platform (optional)
ASU_AI_ENABLED=false
ASU_AI_API_KEY=your_asu_ai_token_here
ASU_AI_BASE_URL=https://api-main-beta.aiml.asu.edu
ASU_AI_MODEL=gpt-4
```

#### Phase 2: Implement ASU AI Provider

**Create `rag/asu_ai_provider.py`:**

```python
"""
ASU AI Platform provider for resume parsing and embeddings.
"""
import aiohttp
from typing import List, Dict
from config import ASU_AI_API_KEY, ASU_AI_BASE_URL, ASU_AI_MODEL

class ASUAIProvider:
    """ASU AI Platform API client."""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or ASU_AI_API_KEY
        self.base_url = base_url or ASU_AI_BASE_URL
        self.model = model or ASU_AI_MODEL
        
    async def generate_content(self, prompt: str) -> str:
        """
        Generate text content using queryV2 endpoint.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated text response
        """
        url = f"{self.base_url}/queryV2"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "endpoint": "text",  # or appropriate endpoint
            "model": self.model,
            "prompt": prompt,
            # Add other parameters as needed based on API docs
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                return result.get("text", "")  # Adjust based on actual response format
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector using embeddings endpoint.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            # Add model/parameters as needed
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                return result.get("embedding", [])  # Adjust based on actual response format
```

#### Phase 3: Update Resume Parser

**Modify `rag/resume_parser.py`:**

```python
from config import LLM_PROVIDER, GEMINI_API_KEY, ASU_AI_ENABLED
from rag.asu_ai_provider import ASUAIProvider

class ResumeParser:
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.5-flash"):
        self.provider_type = LLM_PROVIDER
        
        if self.provider_type == "asu_ai" and ASU_AI_ENABLED:
            self.provider = ASUAIProvider()
        else:
            # Use existing Gemini implementation
            genai.configure(api_key=api_key or GEMINI_API_KEY)
            self.model = genai.GenerativeModel(model_name)
            self.provider = None
        
        self.rate_limiter = get_rate_limiter()
    
    async def parse_resume(self, resume_text: str) -> Dict:
        await self.rate_limiter.wait_if_needed()
        
        # Same prompt as before
        prompt = f"""..."""
        
        if self.provider:
            # Use ASU AI
            response_text = await self.provider.generate_content(prompt)
        else:
            # Use Gemini (existing code)
            response = await self.model.generate_content_async(prompt)
            response_text = response.text.strip()
        
        # Rest of the parsing logic remains the same
        # ...
```

#### Phase 4: Update RAG Engine

**Modify `rag/rag_engine.py`:**

```python
from config import LLM_PROVIDER, ASU_AI_ENABLED
from rag.asu_ai_provider import ASUAIProvider

class JobRAG:
    def __init__(self, api_key: Optional[str] = None):
        self.provider_type = LLM_PROVIDER
        
        # Initialize LLM provider
        if self.provider_type == "asu_ai" and ASU_AI_ENABLED:
            self.llm_provider = ASUAIProvider()
        else:
            genai.configure(api_key=api_key or GEMINI_API_KEY)
            self.llm_provider = None
        
        # ChromaDB setup remains the same
        # ...
    
    def generate_embedding(self, text: str) -> List[float]:
        if self.llm_provider:
            # Use ASU AI embeddings
            import asyncio
            return asyncio.run(self.llm_provider.generate_embedding(text))
        else:
            # Use Gemini embeddings (existing)
            result = genai.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
```

---

## Testing Strategy

### 1. Unit Tests

Create test file `test_asu_ai_provider.py`:

```python
import pytest
from rag.asu_ai_provider import ASUAIProvider

@pytest.mark.asyncio
async def test_generate_content():
    provider = ASUAIProvider()
    result = await provider.generate_content("Hello, world!")
    assert isinstance(result, str)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_generate_embedding():
    provider = ASUAIProvider()
    embedding = await provider.generate_embedding("Test text")
    assert isinstance(embedding, list)
    assert len(embedding) > 0
```

### 2. Integration Testing

```bash
# Test with ASU AI
LLM_PROVIDER=asu_ai streamlit run streamlit_app.py

# Test with Gemini (existing)
LLM_PROVIDER=gemini streamlit run streamlit_app.py
```

### 3. Comparison Testing

Compare results between providers:
- Resume parsing accuracy
- Embedding quality (job match scores)
- Response latency
- Rate limits and quotas

---

## Deployment Checklist

- [ ] **Obtain ASU AI API token** from Ayat Sweid or Paul Alvarado
- [ ] **Verify API endpoint** and available models
- [ ] **Review API documentation** (sections that couldn't be accessed: Methods details, Error codes)
- [ ] **Test API calls** manually (Postman/curl) before integration
- [ ] **Implement provider abstraction layer**
- [ ] **Add ASU AI configuration** to `config.py` and `.env`
- [ ] **Update README.md** with ASU AI setup instructions
- [ ] **Add provider selection** to Streamlit UI (optional: let users choose)
- [ ] **Monitor rate limits** and error handling
- [ ] **Compare costs/quotas** between Gemini and ASU AI
- [ ] **Document API differences** and edge cases

---

## Potential Benefits

| Feature | Google Gemini (Current) | ASU AI Platform (Potential) |
|---------|------------------------|----------------------------|
| **Cost** | Free tier limits, paid above | Institutional (potentially free) |
| **Rate Limits** | 15 RPM / 1500 RPD | Unknown (likely higher for ASU) |
| **Models Available** | Gemini family only | 25+ models (GPT, Claude, etc.) |
| **Support** | Community/Google | ASU institutional support |
| **Embeddings** | Gemini embeddings | Native embeddings API |
| **Multi-modal** | Yes | Yes (speech, vision, audio) |

---

## Risks & Considerations

> [!WARNING]
> **API Documentation Incomplete**
> - Full API documentation sections (Methods, Errors) were not accessible during review
> - Request format, response schemas, and error codes need verification
> - Contact API owners for complete documentation

> [!CAUTION]
> **Migration Risks**
> - Different prompt formats may affect resume parsing accuracy
> - Embedding dimensions may differ (require ChromaDB schema changes)
> - Rate limits and error handling may need adjustment
> - Dependency on ASU infrastructure

---

## Next Steps

1. **Contact ASU AI Team**
   - Reach out to Ayat Sweid or Paul Alvarado
   - Request API token and complete documentation
   - Ask about available models, rate limits, and best practices

2. **Prototype and Test**
   - Implement basic ASU AI provider for one use case (e.g., embeddings only)
   - Compare performance with Gemini
   - Measure latency, accuracy, and costs

3. **Gradual Migration**
   - Start with non-critical features (e.g., embeddings)
   - Keep Gemini as fallback
   - Monitor production performance before full migration

4. **Document Findings**
   - Update this document with API response formats
   - Create troubleshooting guide
   - Share learnings with team

---

## Resources

- **ASU AI Platform Docs**: https://platform-beta.aiml.asu.edu/api
- **Current Project**: [README.md](file:///c:/Users/jahnv/OneDrive/Desktop/Jahnvi/ASU/SocialEmbededdness%20Job/jobScrape/az-gov-job-scraper/README.md)
- **Resume Parser**: [rag/resume_parser.py](file:///c:/Users/jahnv/OneDrive/Desktop/Jahnvi/ASU/SocialEmbededdness%20Job/jobScrape/az-gov-job-scraper/rag/resume_parser.py)
- **RAG Engine**: [rag/rag_engine.py](file:///c:/Users/jahnv/OneDrive/Desktop/Jahnvi/ASU/SocialEmbededdness%20Job/jobScrape/az-gov-job-scraper/rag/rag_engine.py)
- **Configuration**: [config.py](file:///c:/Users/jahnv/OneDrive/Desktop/Jahnvi/ASU/SocialEmbededdness%20Job/jobScrape/az-gov-job-scraper/config.py)

---

**Status**: Planning Phase - Awaiting API Token & Complete Documentation

**Last Updated**: December 19, 2025
