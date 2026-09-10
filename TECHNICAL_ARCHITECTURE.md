# Arizona Government Job Scraper - Technical Architecture

**Complete System Pipeline & Architecture Documentation**

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Data Flow](#data-flow)
4. [Core Components](#core-components)
5. [Resume Parsing Pipeline](#resume-parsing-pipeline)
6. [RAG Engine Architecture](#rag-engine-architecture)
7. [Job Matching Workflow](#job-matching-workflow)
8. [Technology Stack](#technology-stack)
9. [Configuration & Environment](#configuration--environment)

---

## 1. System Overview

### Purpose
AI-powered job search application that matches user resumes with Arizona government job postings using semantic search and LLM-based analysis.

### Key Features
- **Resume Parsing**: Extract structured data from PDFs/DOCX using ASU AI (gpt-4o)
- **Semantic Job Matching**: ChromaDB vector search with Gemini embeddings
- **Personalized Advice**: LLM-generated tailoring recommendations
- **Multi-City Scraping**: Web scraping across 15+ Arizona cities

### User Journey
```
User uploads resume → AI parses skills/experience → 
Scrapes government jobs → Semantic matching → 
Ranked results with tailoring advice
```

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      STREAMLIT WEB UI                            │
│  (streamlit_app.py - User interface & session management)       │
└─────────┬───────────────────────────────────────────────────────┘
          │
          ├──────────────────────────────────────────────┐
          │                                              │
┌─────────▼──────────┐                     ┌────────────▼──────────┐
│  RESUME PARSER     │                     │    JOB SCRAPERS       │
│  (ASU AI gpt-4o)   │                     │  (Playwright/Selenium)│
│                    │                     │                       │
│ • PDF extraction   │                     │ • Multi-city support  │
│ • Text parsing     │                     │ • Dynamic content     │
│ • Structured JSON  │                     │ • Error handling      │
└─────────┬──────────┘                     └────────────┬──────────┘
          │                                             │
          │                                             │
          │                                   ┌─────────▼──────────┐
          │                                   │   SCRAPED JOBS     │
          │                                   │   (Raw JSON data)  │
          │                                   └─────────┬──────────┘
          │                                             │
          │                     ┌───────────────────────┘
          │                     │
┌─────────▼─────────────────────▼──────────────────────────────────┐
│                         RAG ENGINE                                │
│                    (JobRAG + ChromaDB)                            │
│                                                                   │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────────┐  │
│  │  EMBEDDINGS  │────▶│  CHROMA DB   │────▶│  SEMANTIC       │  │
│  │   (Gemini)   │     │ Vector Store │     │  SEARCH         │  │
│  └──────────────┘     └──────────────┘     └─────────────────┘  │
│                                                                   │
│  ┌──────────────┐     ┌──────────────┐                          │
│  │   JOB TEXT   │────▶│ RESUME TEXT  │                          │
│  │ prepare_job  │     │prepare_resume│                          │
│  └──────────────┘     └──────────────┘                          │
└──────────────────────────────┬────────────────────────────────────┘
                               │

### Complete Request Flow

#### **Step 1: User Profile Creation**
```
User Input (Streamlit) 
    ↓
Session State (utils/session.py)
    ↓
Profile Dictionary:
{
    "name": str,
    "degree": str,
    "interests": List[str],
    "resume_text": str,
    "resume_filename": str,
    "resume_parsed": Dict  # Filled after parsing
}
```

#### **Step 2: Resume Parsing**
```
Raw Resume (PDF/DOCX)
    ↓
ResumeExtractor.extract_text() → Plain text
    ↓
ASU AI gpt-4o API Call
    URL: https://api-main.aiml.asu.edu/query
    Payload: {
        "prompt": "Extract skills from: ...",
        "model": "gpt-4o"
    }
    ↓
Structured JSON Response:
{
    "skills": [...],
    "experience": [{...}],
    "education": [{...}],
    "projects": [{...}],
    "certifications": [...],
    "summary": str
}
```

#### **Step 3: Job Scraping**
```
Selected Cities (User input)
    ↓
ScraperRegistry.get_scraper(city)
    ↓
Playwright/Selenium Automation
    • Navigate to city career page
    • Extract job listings
    • Parse HTML content
    ↓
Raw Job Data:
{
    "title": str,
    "city": str,
    "department": str,
    "description": str,
    "requirements": str,
    "salary": str,
    "url": str,
    "job_id": str
}
```

#### **Step 4: Vector Embedding & Storage**
```
Job Data
    ↓
prepare_job_text() → Formatted text
{
    "Title: Software Engineer\n\n
     Department: IT\n\n
     Description: ...\n\n
     Requirements: ..."
}
    ↓
Gemini Embedding API
    Model: models/embedding-001
    Task: retrieval_document
    ↓
Vector: [0.123, -0.456, 0.789, ...] (768 dimensions)
    ↓
ChromaDB.collection.add()
    • document: job_text
    • embedding: vector
    • metadata: job dictionary
    • id: unique job_id
```

#### **Step 5: Semantic Search**
```
User Profile
    ↓
prepare_resume_text() → Formatted resume
{
    "Interests: GIS, Data Analysis\n\n
     Skills: Python, R, ArcGIS\n\n
     Experience: ...\n\n
     Education: ..."
}
    ↓
Gemini Embedding API → Resume vector
    ↓
ChromaDB.collection.query()
    query_embeddings: [resume_vector]
    n_results: 50
    ↓
Results with cosine similarity distances
    [
        (job_metadata, distance: 0.15),
        (job_metadata, distance: 0.23),
        ...
    ]
```

#### **Step 6: Scoring & Ranking**
```
For each job:
    semantic_score = 1 - cosine_distance  # 0.85
    keyword_overlap = calculate_overlap()  # 0.70
    
    final_score = (0.7 * semantic_score) + (0.3 * keyword_overlap)
    final_score = final_score * 100  # Convert to 0-100 scale
    
    if final_score >= MIN_THRESHOLD:
        matched_jobs.append((job, final_score))

Sort by score (desc) → Return top N jobs
```

#### **Step 7: Display & Advice**
```
Matched Jobs (with scores)
    ↓
Streamlit UI Display
    • Job cards with match badges
    • Expandable details
    • Apply buttons
    ↓
User clicks "Get Tailoring Advice"
    ↓
TailoringAdvisor.generate_advice()
    ASU AI gpt-4o:
    "Job: {job_description}
     Resume: {user_skills}
     Provide: strengths, gaps, keywords"
    ↓
Personalized Advice JSON:
{
    "strengths": ["Strong GIS background", ...],
    "skill_gaps": ["Need SQL experience", ...],
    "keywords": ["spatial analysis", "data viz"],
    "improvements": [...]
}
```

---

## 4. Core Components

### 4.1 Frontend: Streamlit Application (`streamlit_app.py`)

**Responsibilities:**
- User interface rendering
- Session state management
- File upload handling
- Progress tracking
- Results display

**Key Functions:**
```python
def main():
    # Entry point
    - Initialize session state
    - Render sidebar (profile form)
    - Display main content
    - Handle job search

def display_job_card(job, index, api_key):
    # Render individual job
    - Show match score with color coding
    - Display job details
    - Provide apply link
    - Trigger tailoring advice

def display_tailoring_advice(job, api_key):
    # Show personalized advice
    - Generate or retrieve cached advice
    - Display strengths, gaps, keywords
```

**Session State Structure:**
```python
st.session_state = {
    "profile": {
        "name": str,
        "degree": str,
        "interests": List[str],
        "resume_text": str,
        "resume_parsed": Dict
    },
    "matched_jobs": List[Dict],
    "scraped_jobs": List[Dict],
    "theme": "dark" | "light"
}
```

### 4.2 Utilities (`utils/`)

#### `session.py`
```python
def init_session_state():
    """Initialize all session variables"""

def update_user_profile(**kwargs):
    """Update profile fields"""

def get_user_profile() -> Dict:
    """Retrieve current profile"""

def is_profile_complete() -> bool:
    """Check if ready to search jobs"""
```

#### `resume_extractor.py`
```python
class ResumeExtractor:
    @staticmethod
    def extract_text(file_bytes, filename) -> str:
        """Extract text from PDF/DOCX/TXT"""
        if filename.endswith('.pdf'):
            return extract_from_pdf(file_bytes)
        elif filename.endswith('.docx'):
            return extract_from_docx(file_bytes)
        else:
            return file_bytes.decode()
```



---

## 5. Resume Parsing Pipeline

### Architecture

```
Resume File (PDF/DOCX)
    ↓
┌──────────────────────────────┐
│   ResumeExtractor            │
│   • PyPDF2 (PDF)             │
│   • python-docx (DOCX)       │
└────────────┬─────────────────┘
             │ Plain text
             ↓
┌──────────────────────────────┐
│   ResumeParser               │
│   (rag/resume_parser.py)     │
│                              │
│  Uses: ASU AI Provider       │
│  Model: gpt-4o               │
└────────────┬─────────────────┘
             │
             ↓
┌──────────────────────────────┐
│   ASU AI gpt-4o API          │
│   POST /query                │
│                              │
│   Prompt: Structured JSON    │
│   extraction template        │
└────────────┬─────────────────┘
             │ JSON response
             ↓
┌──────────────────────────────┐
│   Parsed Resume Data         │
│   {                          │
│     "skills": [...],         │
│     "experience": [...],     │
│     "education": [...],      │
│     "projects": [...],       │
│     "certifications": [...], │
│     "summary": "..."         │
│   }                          │
└──────────────────────────────┘
```

### Implementation Details

**File: `rag/resume_parser.py`**

```python
class ResumeParser:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with ASU AI provider"""
        self.provider = ASUAIProvider(
            api_key=api_key or os.getenv("ASU_AI_API_KEY"),
            model="gpt-4o"
        )
        self.model_name = "gpt-4o"
    
    async def parse_resume(self, resume_text: str) -> Dict:
        """Parse resume using structured prompt"""
        
        # Structured prompt template
        prompt = f"""
        You are a resume parser. Extract structured information.
        
        Return ONLY a valid JSON object with:
        {{
          "skills": ["skill1", "skill2", ...],
          "experience": [{{
            "title": "Job Title",
            "company": "Company Name",
            "duration": "2020 - 2023",
            "description": "Responsibilities"
          }}],
          "education": [{{
            "degree": "Bachelor of Science",
            "field": "Computer Science",
            "institution": "University",
            "year": "2020"
          }}],
          "projects": [{{
            "name": "Project Name",
            "description": "What it does",
            "technologies": ["Python", "React"]
          }}],
          "certifications": ["cert1", "cert2"],
          "summary": "Professional summary"
        }}
        
        Resume Text:
        {resume_text[:10000]}
        
        Return ONLY the JSON object:
        """
        
        # Call ASU AI
        response = await self.provider.generate_content(prompt)
        
        # Parse JSON from response
        json_str = extract_json_from_response(response)
        parsed_data = json.loads(json_str)
        
        return parsed_data
    
    def parse_resume_sync(self, resume_text: str) -> Dict:
        """Synchronous wrapper"""
        return asyncio.run(self.parse_resume(resume_text))
```

**File: `rag/asu_ai_provider.py`**

```python
class ASUAIProvider:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.base_url = "https://api-main.aiml.asu.edu"
        self.model = model
    
    async def generate_content(
        self,
        prompt: str,
        model: Optional[str] = None
    ) -> str:
        """Generate text completion"""
        
        url = f"{self.base_url}/query"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "model": model or self.model
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                result = await resp.json()
                
                # ASU AI response format
                return result["response"]
```

### Prompt Engineering Strategy

**Key Design Decisions:**
1. **Explicit JSON Structure**: Template shows exact format expected
2. **No Markdown**: Instructs model to return ONLY JSON (no ```json blocks)
3. **Comprehensive Sections**: Covers all resume components
4. **Fallback Handling**: Empty arrays [] for missing sections
5. **Token Limit**: Truncates resume to 10K chars to prevent errors

---

## 6. RAG Engine Architecture

### Overview

The RAG (Retrieval-Augmented Generation) engine combines vector similarity search with keyword matching for intelligent job recommendations.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       RAG ENGINE                             │
│                    (rag/rag_engine.py)                       │
│                                                              │
│  ┌────────────────┐          ┌──────────────────┐          │
│  │  JobRAG Class  │          │   ChromaDB       │          │
│  │                │          │   Vector Store   │          │
│  │  • Embeddings  │◄────────▶│                  │          │
│  │  • Search      │          │  • Collections   │          │
│  │  • Scoring     │          │  • Persistence   │          │
│  └────────────────┘          └──────────────────┘          │
│         │                             │                     │
│         │                             │                     │
│         ▼                             ▼                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │           DATA FLOW                                 │    │
│  │                                                     │    │
│  │  1. add_jobs(jobs) → Embed & Store                │    │
│  │  2. search_jobs(profile) → Retrieve & Rank        │    │
│  │  3. get_tailoring_advice() → Generate Advice      │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### **6.1 Embedding Generation (Gemini)**

```python
class JobRAG:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize RAG with Gemini embeddings"""
        self.api_key = api_key or GEMINI_API_KEY
        
        # Configure Gemini for embeddings
        genai.configure(api_key=self.api_key)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=VECTOR_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.chroma_client.get_or_create_collection(
            name="jobs",
            metadata={"hnsw:space": "cosine"}  # Cosine similarity
        )
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini"""
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return result["embedding"]  # Returns 768-dim vector
```

**Why Gemini for Embeddings?**
- ASU AI embeddings endpoint not available yet
- Hybrid approach: ASU AI for text, Gemini for vectors
- Proven performance with ChromaDB integration

#### **6.2 Text Preparation**

```python
def prepare_job_text(job: Dict) -> str:
    """Format job for embedding"""
    parts = []
    
    if job.get("title"):
        parts.append(f"Title: {job['title']}")
    if job.get("department"):
        parts.append(f"Department: {job['department']}")
    if job.get("description"):
        parts.append(f"Description: {job['description']}")
    if job.get("requirements"):
        parts.append(f"Requirements: {job['requirements']}")
    if job.get("job_type"):
        parts.append(f"Type: {job['job_type']}")
    
    return "\n\n".join(parts)

def prepare_resume_text(profile: Dict) -> str:
    """Format resume for embedding"""
    parts = []
    
    # Add interests
    if profile.get("interests"):
        parts.append(f"Interests: {', '.join(profile['interests'])}")
    
    # Add education
    if profile.get("degree"):
        parts.append(f"Education: {profile['degree']}")
    
    # Parse resume data
    resume_data = profile.get("resume_parsed", {})
    
    # Add skills
    if resume_data.get("skills"):
        parts.append(f"Skills: {', '.join(resume_data['skills'])}")
    
    # Add experience (formatted)
    if resume_data.get("experience"):
        exp_texts = []
        for exp in resume_data["experience"]:
            exp_text = f"{exp.get('title', '')} at {exp.get('company', '')}"
            if exp.get("description"):
                exp_text += f": {exp['description']}"
            exp_texts.append(exp_text)
        parts.append(f"Experience:\n" + "\n".join(exp_texts))
    
    return "\n\n".join(parts)
```

**Design Rationale:**
- Structured format improves embedding quality
- Hierarchical organization (Title > Department > Description)
- Consistent formatting for jobs and resumes
- Includes context labels ("Title:", "Skills:")

#### **6.3 Job Storage**

```python
def add_jobs(self, jobs: List[Dict]) -> int:
    """Add jobs to vector database"""
    
    documents = []
    embeddings = []
    ids = []
    metadatas = []
    
    for i, job in enumerate(jobs):
        # Prepare text
        job_text = prepare_job_text(job)
        documents.append(job_text)
        
        # Generate embedding
        embedding = self.generate_embedding(job_text)
        embeddings.append(embedding)
        
        # Create unique ID
        job_id = job.get("job_id") or f"{job['city']}_{i}"
        ids.append(job_id)
        
        # Store full job as metadata
        metadatas.append(job)
    
    # Batch insert into ChromaDB
    self.collection.add(
        documents=documents,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )
    
    return len(jobs)
```

**ChromaDB Schema:**
```
Collection: "jobs"
├── Document: "Title: Software Engineer\n\nDepartment: IT\n\n..."
├── Embedding: [0.123, -0.456, ...]  (768 dimensions)
├── Metadata: {
│     "title": "Software Engineer",
│     "city": "Phoenix",
│     "department": "IT",
│     "description": "...",
│     "requirements": "...",
│     "salary": "$80k-$100k",
│     "url": "https://...",
│     "job_id": "phoenix_123"
│   }
└── ID: "phoenix_123"
```

#### **6.4 Semantic Search**

```python
def search_jobs(
    self,
    profile: Dict,
    top_k: int = 50
) -> List[Tuple[Dict, float]]:
    """Search for matching jobs"""
    
    # Prepare resume for embedding
    resume_text = prepare_resume_text(profile)
    
    # Generate resume embedding
    resume_embedding = self.generate_embedding(resume_text)
    
    # Query ChromaDB
    results = self.collection.query(
        query_embeddings=[resume_embedding],
        n_results=top_k
    )
    
    # Process results
    matched_jobs = []
    
    if results["metadatas"] and len(results["metadatas"]) > 0:
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        
        for i, job_metadata in enumerate(metadatas):
            # Convert distance to similarity
            semantic_similarity = 1.0 - distances[i]
            
            # Calculate keyword overlap
            keyword_score = calculate_keyword_overlap(job_metadata, profile)
            
            # Combined score: 70% semantic, 30% keyword
            final_score = (0.7 * semantic_similarity) + (0.3 * keyword_score)
            final_score = final_score * 100  # Scale to 0-100
            
            if final_score >= MIN_MATCH_SCORE_THRESHOLD:
                matched_jobs.append((job_metadata, final_score))
    
    # Sort by score descending
    matched_jobs.sort(key=lambda x: x[1], reverse=True)
    
    return matched_jobs
```

**Scoring Algorithm:**

```
For each job-resume pair:

1. SEMANTIC SIMILARITY (70% weight)
   - ChromaDB returns cosine distance: 0.15
   - Convert to similarity: 1 - 0.15 = 0.85
   
2. KEYWORD OVERLAP (30% weight)
   - Extract user skills/interests
   - Count matches in job description
   - Score = matches / total_keywords = 0.70
   
3. FINAL SCORE
   - Combined = (0.7 × 0.85) + (0.3 × 0.70)
   - Combined = 0.595 + 0.210 = 0.805
   - Scaled = 0.805 × 100 = 80.5%

4. THRESHOLD FILTER
   - if score >= MIN_THRESHOLD (40%):
       include in results
```

**Why Hybrid Scoring?**
- **Semantic (70%)**: Captures conceptual similarity
  - "data analysis" ≈ "statistical programming"
  - "GIS" ≈ "geospatial analysis"
- **Keyword (30%)**: Ensures explicit matches
  - Required certifications
  - Specific tools/technologies
  - Job-critical terms

---



### What is MCP?

**Model Context Protocol (MCP)** = Standard protocol for external tools to augment LLM capabilities

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│               Claude Desktop / External Client            │
│                 (MCP Client)                              │
└────────────────────┬─────────────────────────────────────┘
                     │ stdio communication
                     │
┌────────────────────▼─────────────────────────────────────┐
│           resume_parser_server.py                         │
│              (MCP Server)                                 │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  TOOLS                                          │    │
│  │                                                 │    │
│  │  1. parse_resume                                │    │
│  │     Input: resume_text                          │    │
│  │     Output: structured JSON                     │    │
│  │                                                 │    │
│  │  2. get_resume_summary                          │    │
│  │     Input: parsed_resume                        │    │
│  │     Output: text summary                        │    │
│  │                                                 │    │
│  │  3. extract_skills                              │    │
│  │     Input: resume_text                          │    │
│  │     Output: skill list                          │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  Uses: rag/resume_parser.py (ASU AI gpt-4o)             │
└───────────────────────────────────────────────────────────┘
```

### Implementation


```python
#!/usr/bin/env python3
"""MCP Server for Resume Parsing"""

import asyncio
from mcp.server.fastmcp import FastMCP
from rag import ResumeParser
import os

# Initialize MCP server
mcp = FastMCP("Resume Parser")

@mcp.tool()
async def parse_resume(resume_text: str) -> dict:
    """
    Parse a resume and extract structured information
    
    Args:
        resume_text: The full text content of the resume
        
    Returns:
        Structured resume data with skills, experience, education, etc.
    """
    api_key = os.getenv("ASU_AI_API_KEY")
    if not api_key:
        raise ValueError("ASU AI API key not found")
    
    parser = ResumeParser(api_key)
    parsed_data = await parser.parse_resume(resume_text)
    
    return parsed_data

@mcp.tool()
async def get_resume_summary(parsed_resume: dict) -> str:
    """
    Generate a concise summary from parsed resume data
    
    Args:
        parsed_resume: Structured resume data from parse_resume
        
    Returns:
        Human-readable summary string
    """
    summary_parts = []
    
    # Skills
    if parsed_resume.get("skills"):
        skills = ", ".join(parsed_resume["skills"][:5])
        summary_parts.append(f"Key Skills: {skills}")
    
    # Experience
    if parsed_resume.get("experience"):
        years = len(parsed_resume["experience"])
        summary_parts.append(f"{years} work experiences")
    
    # Education
    if parsed_resume.get("education"):
        degrees = [edu.get("degree", "Degree") for edu in parsed_resume["education"]]
        summary_parts.append(f"Education: {', '.join(degrees)}")
    
    return " | ".join(summary_parts)

@mcp.tool()
async def extract_skills(resume_text: str) -> list:
    """
    Extract just the skills from a resume
    
    Args:
        resume_text: The full text content of the resume
        
    Returns:
        List of extracted skills
    """
    parsed = await parse_resume(resume_text)
    return parsed.get("skills", [])

if __name__ == "__main__":
    mcp.run()
```

### Usage Example

**From Claude Desktop:**

```
User: "Parse this resume and tell me the key skills"

Claude → Calls MCP tool `parse_resume`:
    Input: <resume text>
    ↓
MCP Server → Uses ASU AI gpt-4o
    ↓
Returns: {
    "skills": ["Python", "GIS", "R", "SQL"],
    "experience": [...],
    ...
}
    ↓
Claude: "This resume shows expertise in Python, GIS, R, and SQL..."
```

### Configuration


```json
{
  "mcpServers": {
    "resume-parser": {
      "command": "python",
      "env": {
        "ASU_AI_API_KEY": "${ASU_AI_API_KEY}"
      }
    }
  }
}
```

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`)

---

## 8. Job Matching Workflow

### Complete End-to-End Flow

```python
# File: rag/job_matcher.py

class JobMatcher:
    """Orchestrates the complete job matching workflow"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.rag_engine = JobRAG(api_key)
    
    async def match_jobs_to_profile(
        self,
        profile: Dict,
        cities: List[str],
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """Complete matching workflow"""
        
        # Step 1: Scrape jobs
        progress_callback("Scraping jobs from selected cities...")
        scraped_jobs = await self._scrape_jobs(cities, progress_callback)
        
        # Step 2: Add to vector database
        progress_callback(f"Indexing {len(scraped_jobs)} jobs...")
        self.rag_engine.add_jobs(scraped_jobs)
        
        # Step 3: Semantic search
        progress_callback("Performing semantic job matching...")
        matched_jobs = self.rag_engine.search_jobs(profile, top_k=50)
        
        # Step 4: Format and return
        progress_callback(f"Found {len(matched_jobs)} matching jobs!")
        return matched_jobs
    
    async def _scrape_jobs(
        self,
        cities: List[str],
        progress_callback: Callable
    ) -> List[Dict]:
        """Scrape jobs from multiple cities"""
        all_jobs = []
        
        for i, city in enumerate(cities):
            progress_callback(f"Scraping {city} ({i+1}/{len(cities)})...")
            
            try:
                scraper = ScraperRegistry.get_scraper(city)
                jobs = await scraper.scrape()
                all_jobs.extend(jobs)
            except Exception as e:
                progress_callback(f"Error scraping {city}: {e}")
                continue
        
        return all_jobs
```

### Workflow Diagram

```
START
  │
  ▼
┌─────────────────────┐
│ User Completes      │
│ Profile + Resume    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Resume Parsing      │
│ (ASU AI gpt-4o)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ User Selects Cities │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Job Scraping (Parallel)                 │
│  • Playwright/Selenium automation       │
│  • Extract HTML content                 │
│  • Parse into structured JSON           │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Vector Embedding (Gemini)               │
│  • prepare_job_text()                   │
│  • generate_embedding()                 │
│  • Store in ChromaDB                    │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Resume Embedding (Gemini)               │
│  • prepare_resume_text()                │
│  • generate_embedding()                 │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Semantic Search (ChromaDB)              │
│  • Cosine similarity                    │
│  • Top-K retrieval                      │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Hybrid Scoring                          │
│  • 70% semantic similarity              │
│  • 30% keyword overlap                  │
│  • Apply threshold filter               │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Ranked Results Display                  │
│  • Sort by score                        │
│  • Color-coded badges                   │
│  • Expandable job cards                 │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ Tailoring Advice (Optional)             │
│  • ASU AI gpt-4o                        │
│  • Personalized recommendations         │
│  • Keyword suggestions                  │
└─────────────────────────────────────────┘
           │
           ▼
          END
```

---

## 9. Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Framework** | Streamlit | UI rendering & state management |
| **LLM (Text)** | ASU AI (gpt-4o) | Resume parsing, advice generation |
| **LLM (Embeddings)** | Google Gemini | Vector embeddings for semantic search |
| **Vector DB** | ChromaDB | Persistent vector storage & similarity search |
| **Web Scraping** | Playwright, Selenium | Dynamic website automation |
| **PDF Parsing** | PyPDF2 | Extract text from PDF resumes |
| **DOCX Parsing** | python-docx | Extract text from Word resumes |
| **Async Runtime** | asyncio, aiohttp | Asynchronous API calls|
| **Environment** | python-dotenv | Environment variable management |

### Frontend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **UI Components** | Streamlit widgets | Forms, buttons, file upload |
| **Styling** | Custom CSS | Theme-based styling (dark/light) |
| **State Management** | st.session_state | Client-side state persistence |
| **Progress Tracking** | st.progress, st.spinner | User feedback during operations |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Package Management** | pip, requirements.txt | Dependency management |
| **Version Control** | Git | Code versioning |
| **Configuration** | config.py, .env | Centralized settings |
| **Database Storage** | File system (chroma_db/) | Vector database persistence |

---

## 10. Configuration & Environment

### Environment Variables (`.env`)

```bash
# LLM Provider Selection
LLM_PROVIDER=asu_ai

# ASU AI Configuration
ASU_AI_ENABLED=true
ASU_AI_API_KEY=eyJhbGci...  # Your API token
ASU_AI_MODEL=gpt-4o
ASU_AI_BASE_URL=https://api-main.aiml.asu.edu

# Gemini Configuration (for embeddings)
GEMINI_API_KEY=your_gemini_key_here
```

### Configuration File (`config.py`)

```python
# LLM Provider
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "asu_ai")

# ASU AI Settings
ASU_AI_ENABLED = os.getenv("ASU_AI_ENABLED", "true").lower() == "true"
ASU_AI_API_KEY = os.getenv("ASU_AI_API_KEY", "")
ASU_AI_BASE_URL = "https://api-main.aiml.asu.edu"
ASU_AI_MODEL = os.getenv("ASU_AI_MODEL", "gpt-4o")

# Gemini Settings (embeddings)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_EMBEDDING_MODEL = "models/embedding-001"

# Application Settings
MAX_RESUME_SIZE_MB = 5
SUPPORTED_RESUME_FORMATS = [".pdf", ".docx", ".txt"]
TOP_JOBS_TO_DISPLAY = 50
MIN_MATCH_SCORE_THRESHOLD = 40

# RAG Settings
EMBEDDING_CHUNK_SIZE = 500
VECTOR_DB_PATH = "./chroma_db"

# Supported Cities
ARIZONA_CITIES = [
    {"name": "City of Tempe", "url": "...", "state": "enabled"},
    {"name": "City of Phoenix", "url": "...", "state": "enabled"},
    # ... more cities
]
```

### Directory Structure

```
az-gov-job-scraper/
├── streamlit_app.py          # Main application
├── config.py                  # Configuration
├── .env                       # Environment variables (gitignored)
├── .env.example               # Template for .env
├── requirements.txt           # Python dependencies
│
├── rag/                       # RAG & AI modules
│   ├── __init__.py
│   ├── resume_parser.py       # ASU AI resume parsing
│   ├── rag_engine.py          # Vector search engine
│   ├── job_matcher.py         # Main orchestrator
│   ├── tailoring_advisor.py   # Advice generation
│   └── asu_ai_provider.py     # ASU AI API client
│
├── scrapers/                  # Web scraping modules
│   ├── __init__.py
│   ├── base_scraper.py        # Abstract base class
│   ├── tempe_scraper.py       # City-specific scrapers
│   ├── phoenix_scraper.py
│   └── ...
│
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── session.py             # Session management
│   ├── resume_extractor.py    # PDF/DOCX parsing
│   └── validators.py          # Input validation
│
│   ├── resume_parser_server.py
│   └── mcp_config.json
│
├── chroma_db/                 # ChromaDB persistence (gitignored)
│   └── ...
│
└── data/                      # Temporary data storage
    └── temp_resumes/          # Uploaded resumes (gitignored)
```

---

## Summary

This Arizona Government Job Scraper uses a modern, AI-powered architecture:

1. **User uploads resume** → Extracted with PyPDF2/python-docx
2. **Resume parsed** → ASU AI gpt-4o extracts structured data (JSON)
3. **Jobs scraped** → Playwright/Selenium from 15+ cities
4. **Jobs embedded** → Gemini embedding-001 creates vectors
5. **Semantic search** → ChromaDB finds similar jobs via cosine similarity
6. **Hybrid scoring** → 70% semantic + 30% keyword matching
7. **Results displayed** → Streamlit UI with match scores
8. **Tailoring advice** → ASU AI gpt-4o generates personalized tips
9. **MCP integration** → External tools can access resume parsing

**Key Technologies**: Streamlit • ASU AI (gpt-4o) • Gemini (embeddings) • ChromaDB • Playwright

**Hybrid LLM Strategy**: ASU AI for text generation, Gemini for embeddings (until ASU AI embeddings available)
