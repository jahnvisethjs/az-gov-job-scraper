# Arizona Government Job Scraper — Technical Architecture

**Maintained system pipeline and architecture documentation**

Last updated: 2026-09-17

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Data Flow](#3-data-flow)
4. [Core Components](#4-core-components)
5. [Resume Parsing Pipeline](#5-resume-parsing-pipeline)
6. [RAG Engine & Scoring](#6-rag-engine--scoring)
7. [Job Scraping & Caching](#7-job-scraping--caching)
8. [Runtime Orchestration](#8-runtime-orchestration)
9. [Tech Stack & Configuration](#9-tech-stack--configuration)

---

## 1. System Overview

### Purpose
AI-powered job search application that matches user resumes with Arizona government job postings using semantic embedding search and ASU AI LLM analysis.

### Key Capabilities
- **Resume Parsing**: Structured data extraction from PDF/DOCX/TXT via ASU AIML API (`claude-opus-4-7`)
- **Semantic Job Matching**: ChromaDB vector search using ASU AI `text-embedding-3-small` (1024-dim)
- **Hybrid Scoring**: 70% semantic similarity + 30% keyword overlap, scaled 0–100
- **Tailoring Advice**: Per-job resume improvement advice via ASU AI
- **Multi-City Scraping**: Parallel Playwright scraping across NeoGov and PeopleSoft platforms
- **Disk Cache**: JSON-based job cache with configurable TTL (default 6 hours)

### User Journey
```
Upload resume → AI parses skills/experience →
Scrape government job portals (or load from cache) →
Embed jobs + resume via ASU AI →
Semantic + keyword hybrid scoring →
Ranked results with per-job tailoring advice
```

---

## 2. Architecture Diagram

```text
streamlit_app.py (page composition)
        |
        v
ui/ (inputs, sections, rendering) ------> assets/styles.css
        |
        v
services/ (resume, search, browser, advice workflows)
        |
        +--> rag/resume_parser.py ------> ASU AI Claude Opus 4.7
        |
        +--> rag/job_matcher.py
                 |
                 +--> utils/job_cache.py
                 +--> scrapers/ -------> Playwright job portals
                 +--> rag/rag_engine.py -> ASU embeddings -> ChromaDB
        |
        +--> rag/TailoringAdvisor ------> ASU AI Claude Opus 4.7
```

---

## 3. Data Flow

### Step 1 — Resume Upload & Parsing
```
User uploads PDF/DOCX/TXT
    ↓
ResumeExtractor (PyPDF2 / pdfplumber / python-docx)
    ↓
Raw plain text
    ↓
[Session check: reuse parse when this session already processed the same resume]
    ↓ (new resume or no successful parse)
ASU AIML API  POST https://api-main.aiml.asu.edu/query
    model: claude-opus-4-7
    prompt: structured JSON extraction template
    ↓
Parsed resume:
{
  "skills": [...],
  "experience": [{title, company, duration, description}],
  "education": [{degree, field, institution, year}],
  "projects": [{name, description, technologies}],
  "certifications": [...],
  "summary": "..."
}
    ↓
Stored only in st.session_state["user_profile"]["resume_parsed"]
```

### Step 2 — Job Scraping & Caching
```
User clicks Search
    ↓
For each city in ScraperRegistry:
    is_cache_fresh(city)?  →  YES → load from data/cache/jobs_{city}.json
                           →  NO  → scrape with Playwright (max 3 concurrent)
                                     ↓
                                   scraper.scrape_with_retry(max_retries=2)
                                     ↓
                                   save_cached_jobs(city, jobs)
    ↓
All jobs merged into single list
```

### Step 3 — Embedding & Vector Storage
```
For each job in the searched city scope:
    prepare_job_text(job) → "Title: ...\n\nDepartment: ...\n\nDescription: ..."
    ↓
SHA-256(text + embedding model configuration)
    ↓
Compare with the hash stored in ChromaDB metadata
    ↓
Unchanged → refresh metadata only; reuse existing embedding
Changed/new → ASU AI generate_embeddings_batch()
    model: text-embedding-3-small (te3s)
    dimensions: 1024
    parallel workers: EMBEDDING_BATCH_WORKERS (default: 2)
    ↓
ChromaDB collection.upsert(documents, embeddings, ids, metadatas)
    collection: "jobs"
    distance metric: cosine
    ↓
Delete expired jobs only within the refreshed city scope
```

### Step 4 — Semantic Search & Hybrid Scoring
```
prepare_resume_text(profile)
    → "Interests: ...\n\nEducation: ...\n\nSkills: ...\n\nExperience: ..."
    ↓
ASU AI generate_embedding_sync() → 1024-dim resume vector
    ↓
ChromaDB.collection.query(query_embeddings=[resume_vec], n_results=index_size)
    → returns (job_metadata, cosine_distance) pairs
    ↓
For each result:
    semantic_similarity = 1.0 - cosine_distance
    keyword_score = matched_profile_keywords / total_profile_keywords
    final_score = (0.7 × semantic_similarity + 0.3 × keyword_score) × 100
    ↓
Apply the user's eligible job IDs and MIN_MATCH_SCORE_THRESHOLD
Sort descending → return the top 100 ranked jobs
```

### Step 5 — Tailoring Advice
```
User clicks "Get Tailoring Advice" on a job card
    ↓
[Check st.session_state[f"advice_{job_id}"]]  → cached → display immediately
    ↓ (cache miss)
TailoringAdvisor.generate_advice(job, profile)
    ASU AI Claude Opus 4.7 prompt:
        - Job details (title, department, description, requirements)
        - Candidate skills, education, interests
        → Returns JSON: {skill_gaps, keywords, improvements, strengths}
    ↓
Stored in st.session_state for instant re-display
```

---

## 4. Core Components

### 4.1 Presentation and Application Services

**Responsibilities:**
- `streamlit_app.py`: page configuration and high-level section composition
- `ui/sections.py`: resume, profile, search, results, and advice interactions
- `ui/components.py`: escaped job-card HTML and advice presentation
- `ui/styles.py` + `assets/styles.css`: stylesheet loading and visual rules
- `services/resume_service.py`: text extraction and one-time AI parsing
- `services/job_search_service.py`: synchronous boundary around the async matcher and thread-safe progress-event relay
- `services/browser_runtime.py`: deferred Linux Chromium provisioning
- `services/tailoring_service.py`: UI-independent advice generation

**Key session state keys:**
```python
st.session_state = {
    "user_profile": {
        "name": str,
        "degree": str,
        "interests": List[str],
        "resume_text": str,
        "resume_filename": str,
        "resume_parsed": Dict    # Set after ASU AI parsing
    },
    "matched_jobs": List[Dict],  # Full ranked results
    "advice_{job_id}": Dict,     # Cached tailoring advice per job
    "show_advice_{job_id}": bool # Toggle state per card
}
```

**Score badge logic:**
| Score | Badge Color |
|-------|-------------|
| ≥ 60 | Green (`score-high`) |
| 40–59 | Yellow (`score-med`) |
| < 40 | Red (`score-low`) |

---

### 4.2 `rag/asu_ai_provider.py` — ASU AIML API Client

The central API client for all AI operations. Makes all calls to `https://api-main.aiml.asu.edu`.

**Text Generation** (resume parsing, tailoring advice):
```python
POST /query
Headers: Authorization: Bearer {ASU_AI_API_KEY}
Body: {"prompt": "...", "model": "claude-opus-4-7"}
Response: {"response": "...", "metadata": {...}}
```

**Embeddings**:
```python
POST /embeddings   (or provider-specific endpoint)
Body: {
    "input": "text to embed",
    "model": "te3s",           # text-embedding-3-small
    "provider": "openai",
    "dimensions": 1024
}
Response: {"data": [{"embedding": [...1024 floats...]}]}
```

Both sync and async variants are implemented. Batch embedding uses `ThreadPoolExecutor` with configurable `max_workers`.

---

### 4.3 `rag/rag_engine.py` — Vector Store & Scoring

**`JobRAG` class responsibilities:**
- Initializes ChromaDB persistent client at `./chroma_db` (cosine metric)
- `add_jobs(jobs, scope_cities)`: synchronizes a city-scoped corpus with ChromaDB
  - Reuses unchanged embeddings across new `JobRAG` instances
  - Embeds only new or content-changed jobs
  - Preserves indexed jobs belonging to cities outside the current scope
  - Removes expired jobs within the refreshed scope
- `search_jobs(profile, top_k)`: embeds resume, queries ChromaDB, applies hybrid scoring
- `clear_jobs()`: drops and recreates ChromaDB collection

**Scoring formula:**
```
semantic_similarity = 1.0 - cosine_distance
keyword_score       = matched_keywords / total_profile_keywords
final_score         = (0.7 × semantic_similarity + 0.3 × keyword_score) × 100
```

---

### 4.4 `scrapers/` — Web Scraping Layer

**`BaseJobScraper` (abstract)**:
- Defines `scrape_jobs()` (async, abstract) and `get_platform_name()` (abstract)
- Provides `scrape_with_retry(max_retries=3)` with exponential backoff
- `JobData` dataclass normalizes all scraped data to a common schema:
  ```
  title, city, url, description, location, department,
  salary, posted_date, closing_date, job_id, requirements,
  job_type, scraped_at, raw_data
  ```

**`NeoGovScraper`**: Targets `governmentjobs.com` portals used by ~13 cities.

**`PeopleSoftScraper`**: Targets Phoenix's PeopleSoft portal (`hcmprod.phoenix.gov`).

**`ScraperRegistry`**:
- `CITY_MAPPINGS` dict: city name → (platform, URL)
- `get_scraper(city_name)` returns correct scraper instance
- `get_supported_cities()` lists all configured cities
- `add_city()` allows runtime extension

**Supported cities (from `CITY_MAPPINGS`):**

Phoenix, Scottsdale, Pima County, Tempe, Mesa, Glendale, Chandler, Gilbert, Apache Junction, Avondale, Buckeye, Flagstaff, Goodyear, Prescott, Cottonwood

---

### 4.5 `utils/job_cache.py` — Disk-Based Job Cache

Persists scraped jobs to `/data/cache/jobs_{city}.json` to avoid redundant Playwright sessions.

| Function | Description |
|---|---|
| `is_cache_fresh(city)` | Returns True if cache file exists and is within TTL |
| `get_cached_jobs(city)` | Returns job list from cache, or None if stale |
| `save_cached_jobs(city, jobs)` | Writes jobs + timestamp to disk |
| `get_cache_age(city)` | Returns cache age in hours |
| `clear_cache(city=None)` | Deletes one city or all cache files |

Parsed resumes are deliberately excluded from the disk cache and remain in the user's Streamlit session only.

**Cache TTL**: Configured via `JOB_CACHE_HOURS` env var (default: 6 hours).

---

### 4.6 Runtime Orchestration

The application does not use a separate agent framework. `streamlit_app.py`
composes the presentation layer, which calls the service layer. The search
service owns worker-thread and event-loop setup; `JobMatcher` coordinates
scraping, caching, embedding, hybrid scoring, and ranking through `JobRAG`.
Tailoring advice is generated separately and only on demand.

The worker emits typed `SearchProgress` events into a thread-safe queue. The
service drains that queue on Streamlit's main thread, allowing `st.status` and
`st.progress` to show cache hits, per-city completion or failure, embedding
progress, and final matching without making Streamlit calls from a worker.

---

## 5. Resume Parsing Pipeline

```
PDF / DOCX / TXT file bytes
    ↓
ResumeExtractor.extract_text(file_bytes, filename)
    PDF:  PyPDF2 page-by-page + pdfplumber fallback
    DOCX: python-docx paragraph iteration
    TXT:  direct decode
    ↓
Plain text string (no formatting)
    ↓
Check whether the same resume has a successful parse in this session
    ↓ (new resume or no successful parse)
ResumeParser.parse_resume_sync(text)
    ↓
ASUAIProvider.generate_content_sync()
    POST https://api-main.aiml.asu.edu/query
    model: claude-opus-4-7
    prompt: strict JSON extraction template
            (truncated to 10,000 chars)
    ↓
JSON response extracted + parsed
    ↓
Stored only in session_state["user_profile"]["resume_parsed"]
```

**Prompt template enforces** (no markdown, strict JSON only):
```json
{
  "skills": [...],
  "experience": [{"title", "company", "duration", "description"}],
  "education": [{"degree", "field", "institution", "year"}],
  "projects": [{"name", "description", "technologies": [...]}],
  "certifications": [...],
  "summary": "..."
}
```

---

## 6. RAG Engine & Scoring

### Embedding Model
- **Provider**: ASU AIML API (`https://api-main.aiml.asu.edu`)
- **Model**: `text-embedding-3-small` (abbreviated `te3s` in config)
- **Dimensions**: 1024 (configurable via `ASU_AI_EMBEDDINGS_DIMENSIONS`)
- **Batch**: `generate_embeddings_batch()` uses `ThreadPoolExecutor(max_workers=2)`

### ChromaDB Schema
```
Collection: "jobs"
├── Document:  "Title: ...\n\nDepartment: ...\n\nDescription: ...\n\nRequirements: ..."
├── Embedding: [float × 1024]
├── Metadata:  full job dict (nested dicts serialized to JSON strings)
└── ID:        stable job_id
```

### Hybrid Scoring Algorithm
```python
semantic_similarity = 1.0 - cosine_distance   # from ChromaDB
keyword_score = matched_keywords / total_profile_keywords
final_score = (0.7 * semantic_similarity + 0.3 * keyword_score) * 100
```

**Keyword source for scoring**: candidate skills + interests (from session profile)
**Keyword target**: merged `title + description + requirements` of the job (lowercase)

### Incremental Index Synchronization
Each job stores a SHA-256 fingerprint derived from its embedding text and the
active embedding-model configuration. `add_jobs()` compares incoming jobs with
the metadata already persisted in ChromaDB. Unchanged vectors are reused,
changed/new jobs are upserted, and expired records are deleted only for cities
included in the current refresh. This works across application reruns and new
`JobRAG` instances; it does not depend on an in-memory batch hash.

---

## 7. Job Scraping & Caching

### Parallel Scraping
`JobMatcher.match_jobs_to_profile()` separates cities into cached vs stale.
Stale cities are scraped concurrently with `asyncio.gather()` bounded by `asyncio.Semaphore(3)` — maximum 3 headless browser instances at a time.

```python
semaphore = asyncio.Semaphore(3)

async def scrape_city(city):
    async with semaphore:
        scraper = ScraperRegistry.get_scraper(city)
        jobs = await scraper.scrape_with_retry(max_retries=2)
        save_cached_jobs(city, [j.to_dict() for j in jobs])
        return jobs

results = await asyncio.gather(*[scrape_city(c) for c in stale_cities])
```

### Cache File Format
`data/cache/jobs_{city_name}.json`:
```json
{
  "city": "Tempe",
  "cached_at": "2026-04-25T14:30:00",
  "job_count": 42,
  "jobs": [{ ...JobData.to_dict()... }]
}
```

---

## 8. Runtime Orchestration

```
Streamlit entry point → UI sections → application services
                                      ├──→ JobMatcher → cache/scrapers → JobRAG
                                      └──→ TailoringAdvisor (on demand)
```

`services.run_job_search()` is the synchronous UI boundary. It creates a worker
event loop and calls `JobMatcher.match_jobs_to_profile()`, which handles the
scraping/cache decision and delegates vector operations to `JobRAG`. Tailoring
advice is generated only when the user requests it for a result.

---

## 9. Tech Stack & Configuration

### Tech Stack

| Component | Technology |
|---|---|
| **UI** | Streamlit (dark theme, Inter font, custom CSS) |
| **LLM** | ASU AIML API → Claude Opus 4.7 (`claude-opus-4-7`) |
| **Embeddings** | ASU AIML API → `text-embedding-3-small` (1024 dims) |
| **Vector DB** | ChromaDB (local persistent, cosine similarity) |
| **Orchestration** | Direct Python flow through `JobMatcher` and `JobRAG` |
| **Web Scraping** | Playwright (headless Chromium) + BeautifulSoup4 |
| **Resume Extraction** | PyPDF2, pdfplumber, python-docx |
| **Job Cache** | JSON files on disk (TTL-based) |
| **Async Runtime** | asyncio plus bounded worker pools for UI execution and embeddings |

### Key Configuration Variables (`config.py` / `.env`)

| Variable | Default | Description |
|---|---|---|
| `ASU_AI_API_KEY` | (required) | Bearer token for ASU AIML API |
| `ASU_AI_BASE_URL` | `https://api-main.aiml.asu.edu` | API base URL |
| `ASU_AI_MODEL` | `claude-opus-4-7` | LLM model for text tasks |
| `ASU_AI_EMBEDDINGS_MODEL` | `te3s` | Embedding model shorthand |
| `ASU_AI_EMBEDDINGS_DIMENSIONS` | `1024` | Embedding vector size |
| `EMBEDDING_BATCH_WORKERS` | `2` | Parallel embedding threads |
| `JOB_CACHE_HOURS` | `6` | Cache TTL in hours |
| `CACHE_DIR` | `./data/cache` | Cache directory path |
| `PLAYWRIGHT_SKIP_BROWSER_INSTALL` | `false` | Skip deferred Linux Chromium provisioning |
| `VECTOR_DB_PATH` | `./chroma_db` | ChromaDB persistence path |
| `MIN_MATCH_SCORE_THRESHOLD` | `0` | Filter threshold (0 = show all) |
| `TOP_JOBS_TO_DISPLAY` | `50` | Max results from RAG search |
