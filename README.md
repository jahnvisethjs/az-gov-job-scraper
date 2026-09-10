# 🏛️ Arizona Government Job Scraper

AI-powered job matching platform that scrapes 15+ Arizona city and county government job sites, uses RAG (Retrieval-Augmented Generation) for semantic matching, and provides personalized resume tailoring advice.

## ✨ Features

- **🤖 AI-Powered Matching**: Gemini 1.5 Flash for resume parsing and job analysis
- **🎯 Smart Resume Parsing**: Extracts skills, experience, education, and projects automatically
- **📊 Match Scores**: AI-calculated match scores (0-100%) for each job
- **💡 Tailoring Advice**: Personalized tips to improve your resume for specific jobs
- **🏛️ 15 Cities**: Scrapes Arizona government job sites including Phoenix, Tempe, Mesa, Scottsdale, and more
- **🔒 Session-Based**: No database, no authentication - data lives in your browser session

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Gemini API Key ([Get one free here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone or navigate to the project**
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
   playwright install
   ```

5. **Set up environment variables**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and add your API key
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### Run the App

```bash
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

## 📖 Usage

### Phase 1 (Complete) - Profile Setup ✅

1. **Upload Resume**: PDF, DOCX, or TXT format (max 5MB)
2. **Fill Profile**: Name, education level, areas of interest
3. **AI Analysis**: Gemini automatically parses your resume
4. **View Results**: See extracted skills, experience, education, and projects

### Phase 2 (Complete) - Job Scraping ✅

- Real-time scraping of Arizona government job sites
- Normalized job data across different platforms
- Support for NeoGov and PeopleSoft platforms

### Phase 3 (Complete) - RAG Job Matching ✅

- Semantic job matching using ChromaDB vector database
- AI-powered match scores (0-100%) combining semantic similarity and keyword matching
- Personalized resume tailoring advice for each job
- Smart filtering and ranking by relevance
- On-demand tailoring suggestions powered by Gemini

### Phase 4+ (Planned)

- LangGraph agent workflows
- MCP tool servers
- Enhanced UI with job tracking

## 🏗️ Project Structure

```
az-gov-job-scraper/
├── streamlit_app.py          # Main Streamlit application
├── config.py                 # Configuration (cities, API settings)
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
│
├── utils/
│   ├── pdf_extractor.py      # PDF/DOCX text extraction
│   └── session_manager.py    # Streamlit session state
│
├── rag/
│   ├── resume_parser.py      # AI resume parsing
│   └── rag_engine.py         # (Phase 3) ChromaDB + embeddings
│
├── scrapers/                 # (Phase 2) Web scrapers
│   ├── base_scraper.py
│   └── ...
│
└── agents/                   # (Phase 4) LangGraph workflows
    └── ...
```

## 🎓 Learning Objectives

This project teaches:

- ✅ **Resume Parsing**: AI-powered data extraction from documents
- ✅ **Streamlit**: Building interactive web UIs with Python
- ✅ **Session Management**: Stateful applications without databases
- 🔲 **Web Scraping**: Playwright, BeautifulSoup, multi-site strategies
- 🔲 **RAG**: Vector embeddings, ChromaDB, semantic search
- 🔲 **LangGraph**: Agent workflows, tool use, state machines

## 🔑 API Key Setup

### Get Gemini API Key (Free)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Get API Key"
4. Copy the key and add to `.env`

### Free Tier Limits

- 15 requests/minute
- 1,500 requests/day
- 1M tokens/day

The app automatically handles rate limiting!

## 🏛️ Supported Cities

- City of Phoenix
- City of Tempe
- City of Mesa
- City of Scottsdale
- Apache Junction
- Cottonwood
- Pima County
- Buckeye
- Goodyear
- Snowflake
- City of Prescott
- Flagstaff
- Nogales
- El Mirage
- Avondale

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **UI** | Streamlit |
| **AI/LLM** | Google Gemini 1.5 Flash |
| **Resume Parsing** | PyPDF2, pdfplumber, python-docx |
| **Web Scraping** | Playwright, BeautifulSoup4 |
| **Vector DB** | ChromaDB (Phase 3) |
| **Orchestration** | LangGraph (Phase 4) |

## 📝 Roadmap

- [x] **Phase 1**: Project setup, resume upload, AI parsing ✅
- [x] **Phase 2**: Web scraping engine ✅
- [x] **Phase 3**: RAG implementation ✅
- [ ] **Phase 4**: LangGraph agents
- [ ] **Phase 5**: UI polish & job tracking

## 🤝 Contributing

This is a learning project! Feel free to:
- Add more cities
- Improve scrapers
- Enhance AI prompts
- Optimize match algorithms

## 📄 License

MIT License - feel free to use and modify!

## 🙏 Acknowledgments

- Inspired by [Job-Search-Agent](https://github.com/bhargavi-potu/Job-Search-Agent)
- Built with Google Gemini AI
- Uses LangChain ecosystem

---

**Status**: Phase 3 Complete ✅ | Phase 4 Up Next 🚀

Made with ❤️ for Arizona job seekers

