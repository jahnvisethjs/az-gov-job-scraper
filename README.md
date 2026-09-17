# Arizona Government Job Scraper

An AI-assisted Streamlit application that collects Arizona municipal job postings, ranks them against a resume, and generates job-specific resume advice through the ASU AIML API.

## What it does

- Scrapes 15 Arizona city and county portals through NeoGov and PeopleSoft adapters.
- Extracts structured resume data from PDF, DOCX, and TXT uploads.
- Builds 1,024-dimensional job and resume embeddings through ASU AIML.
- Ranks jobs with a hybrid score: 70% semantic similarity and 30% keyword overlap.
- Generates resume-tailoring advice with `claude-opus-4-7`.
- Caches public job listings for six hours and keeps uploaded resume data in the Streamlit session.

## Quick start

Requirements: Python 3.10+ and an ASU AIML API key.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
Copy-Item .env.example .env
```

Set `ASU_AI_API_KEY` in `.env`, then run:

```powershell
streamlit run streamlit_app.py
```

The application opens at `http://localhost:8501`.

## Documentation

- [Setup, configuration, and deployment](docs/setup.md)
- [Architecture, data flow, and scoring](docs/architecture.md)
- [Manual diagnostics](docs/diagnostics.md)
- [Documentation index](docs/README.md)

## Runtime flow

```text
Resume upload -> text extraction -> Claude resume parsing
                                    |
Job cache -> web scrapers -> ASU embeddings -> ChromaDB search
                                    |
                        70/30 hybrid score -> ranked jobs
                                    |
                         on-demand tailoring advice
```

The runtime is a direct Python flow: `streamlit_app.py` composes modules from `ui/`; the UI invokes focused `services/`, and `JobMatcher` coordinates the cache, scrapers, `JobRAG`, and the tailoring advisor. There is no agent framework in the active application.

## Repository layout

```text
az-gov-job-scraper/
|-- streamlit_app.py          # Streamlit user interface
|-- config.py                 # Environment-backed application settings
|-- assets/                   # Application stylesheet
|-- ui/                       # Streamlit sections and rendering components
|-- services/                 # Resume, search, browser, and advice workflows
|-- rag/                      # ASU AI client, parsing, embeddings, and scoring
|-- scrapers/                 # NeoGov and PeopleSoft scraping adapters
|-- utils/                    # Session, cache, and document extraction helpers
|-- scripts/diagnostics/      # Explicitly-run external service checks
|-- tests/                    # Network-free automated tests
|-- docs/                     # Maintained project documentation
`-- data/cache/               # Generated public job cache (ignored by Git)
```

## Tests

```powershell
python -m pytest
```

Automated tests do not make live API or scraping calls. Use the documented manual diagnostics when external integration checks are required.
