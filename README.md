# 🏛️ Arizona Government Job Scraper

AI-powered job matching platform that scrapes 14 Arizona city and county government job portals, uses a RAG (Retrieval-Augmented Generation) pipeline with ASU AI embeddings for semantic job matching, and provides personalized resume tailoring advice — all via the ASU AIML API.

## ✨ Features

- **🤖 AI-Powered Matching**: ASU AIML API (GPT-4o) for resume parsing and tailoring advice
- **🔢 Semantic Embeddings**: ASU AI `text-embedding-3-small` (1024 dimensions) for vector search
- **🎯 Smart Resume Parsing**: Extracts skills, experience, education, projects, and certifications automatically
- **📊 Hybrid Match Scores**: 70% semantic similarity + 30% keyword overlap, scored 0–100
- **💡 Tailoring Advice**: Personalized per-job tips (strengths, skill gaps, keywords, improvements)
- **🏛️ 14 Cities**: Scrapes Arizona government job portals via NeoGov and PeopleSoft adapters
- **⚡ Job Cache**: Scraped jobs cached to disk (6-hour TTL) to avoid redundant scraping
- **🔒 Session-Based**: No user database or authentication — data lives in your browser session

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- ASU AIML API Key

### Installation

1. **Navigate to the project**
   ```bash
   cd az-gov-job-scraper
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers** (for web scraping)
   ```bash
   playwright install chromium
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your ASU AI API key
   ASU_AI_API_KEY=your_actual_api_key_here
   ```

### Run the App

```bash
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

## 📖 Usage

### Step 1 — Upload Resume
Upload your resume in PDF, DOCX, or TXT format (max 5MB). The ASU AI API automatically parses it into structured data: skills, experience, education, projects, and certifications.

### Step 2 — Fill Your Profile
Enter your name, highest education level, and areas of interest. These feed directly into the semantic matching.

### Step 3 — Search Jobs
Click **Search & Analyze Jobs**. The system will:
- Check the local disk cache (fresh within 6 hours) for each city
- Scrape stale cities in parallel (max 3 concurrent browsers)
- Embed all jobs using ASU AI `text-embedding-3-small`
- Score matches using the hybrid 70/30 algorithm
- Display ranked results with color-coded match badges

### Step 4 — Get Tailoring Advice
Click **💡 Get Tailoring Advice** on any job card. The ASU AI API generates position-specific advice:
- ✅ Your Strengths
- ⚠️ Skill Gaps to Address
- 🔑 Keywords to Add
- 📈 Resume Improvements

Advice is cached per job in your session — clicking again retrieves it instantly.

## 🏗️ Project Structure

```
az-gov-job-scraper/
├── streamlit_app.py          # Main Streamlit UI
├── config.py                 # All configuration (cities, models, cache settings)
├── requirements.txt
├── .env.example
│
├── rag/
│   ├── asu_ai_provider.py    # ASU AIML API client (LLM + embeddings)
│   ├── rag_engine.py         # ChromaDB vector store + hybrid scoring
│   ├── job_matcher.py        # Orchestrates scraping → embedding → matching
│   ├── resume_parser.py      # AI resume parsing via ASU AI
│   └── llm_helper.py         # Sync helper wrapper
│
├── scrapers/
│   ├── base_scraper.py       # Abstract base class + JobData schema
│   ├── neogov_scraper.py     # NeoGov (governmentjobs.com) adapter
│   ├── peoplesoft_scraper.py # PeopleSoft (Phoenix) adapter
│   └── scraper_registry.py  # City → scraper mapping + platform detection
│
├── utils/
│   ├── job_cache.py          # Disk-based public job-listing cache
│   ├── session_manager.py    # Streamlit session state helpers
│   └── pdf_extractor.py      # PDF/DOCX text extraction
│
└── data/cache/               # Auto-created: cached job JSON files
```

## 🏛️ Supported Cities

These cities are configured in `ScraperRegistry` and actively scraped:

| City | Platform | Portal |
|------|----------|--------|
| Phoenix | PeopleSoft | hcmprod.phoenix.gov |
| Tempe | NeoGov | governmentjobs.com/careers/tempe |
| Mesa | NeoGov | governmentjobs.com/careers/mesaaz |
| Scottsdale | NeoGov | governmentjobs.com/careers/scottsdaleaz |
| Pima County | NeoGov | governmentjobs.com/careers/pima |
| Apache Junction | NeoGov | governmentjobs.com/careers/apachejunctionaz |
| Avondale | NeoGov | governmentjobs.com/careers/avondale |
| Buckeye | NeoGov | governmentjobs.com/careers/buckeyeaz |
| Flagstaff | NeoGov | governmentjobs.com/careers/flagstaffaz |
| Goodyear | NeoGov | governmentjobs.com/careers/goodyearaz |
| Prescott | NeoGov | governmentjobs.com/careers/prescott |
| Cottonwood | NeoGov | governmentjobs.com/careers/cottonwoodaz |
| Chandler | NeoGov | governmentjobs.com/careers/chandleraz |
| Gilbert | NeoGov | governmentjobs.com/careers/gilbert |
| Glendale | NeoGov | governmentjobs.com/careers/glendaleaz |

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **UI** | Streamlit |
| **LLM (Resume Parsing + Tailoring)** | ASU AIML API → Claude Opus 4.7 |
| **Embeddings** | ASU AIML API → `text-embedding-3-small` (1024 dims) |
| **Vector DB** | ChromaDB (cosine similarity, persistent) |
| **Orchestration** | Direct Python flow through `JobMatcher` and `JobRAG` |
| **Web Scraping** | Playwright (headless Chromium) + BeautifulSoup4 |
| **Resume Parsing** | PyPDF2, pdfplumber, python-docx |
| **Job Cache** | Local JSON files (6-hour TTL) |

## ⚙️ Configuration (`.env`)

```bash
ASU_AI_API_KEY=your_token_here
ASU_AI_MODEL=claude-opus-4-7           # LLM model for parsing + advice
ASU_AI_EMBEDDINGS_MODEL=te3s           # text-embedding-3-small
ASU_AI_EMBEDDINGS_DIMENSIONS=1024
JOB_CACHE_HOURS=6                      # How long cached jobs stay fresh
CACHE_DIR=./data/cache
EMBEDDING_BATCH_WORKERS=2             # Parallel embedding workers
```

## 📝 Roadmap

- [x] **Phase 1**: Resume upload + AI parsing ✅
- [x] **Phase 2**: Multi-city web scraping (NeoGov + PeopleSoft) ✅
- [x] **Phase 3**: RAG pipeline + hybrid scoring ✅
- [x] **Phase 4**: Direct job-matching orchestration ✅
- [ ] **Phase 5**: UI polish, job tracking, application history

---

Made with ❤️ for Arizona job seekers
