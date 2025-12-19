# MCP Tool Servers for Arizona Government Job Scraper

This directory contains Model Context Protocol (MCP) servers that expose job scraping, resume parsing, and job matching capabilities to AI assistants.

## 📋 Available Servers

### 1. Job Scraper Server (`job_scraper_server.py`)

Exposes web scraping tools for Arizona government job sites.

**Tools**:
- `scrape_city` - Scrape jobs from a specific city
- `scrape_multiple_cities` - Batch scrape multiple cities
- `list_supported_cities` - Get list of available cities

**Usage**:
```bash
python mcp_servers/job_scraper_server.py
```

---

### 2. Resume Parser Server (`resume_parser_server.py`)

Exposes resume parsing capabilities using Gemini AI.

**Tools**:
- `parse_resume` - Full resume parsing (skills, experience, education)
- `extract_skills` - Extract only skills
- `extract_experience` - Extract only work experience

**Usage**:
```bash
export GEMINI_API_KEY="your-api-key"
python mcp_servers/resume_parser_server.py
```

---

### 3. Job Matcher Server (`job_matcher_server.py`)

Exposes job matching and ranking tools.

**Tools**:
- `match_jobs` - Match resume against multiple jobs
- `calculate_match_score` - Score a single job
- `rank_jobs` - Rank and filter jobs by score

**Usage**:
```bash
export GEMINI_API_KEY="your-api-key"
python mcp_servers/job_matcher_server.py
```

---

## 🔧 Installation

### Prerequisites

Install MCP SDK:
```bash
pip install mcp
```

Optional (for easier server management):
```bash
pip install fastmcp
```

### Configuration for Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "job-scraper": {
      "command": "python",
      "args": [
        "/absolute/path/to/mcp_servers/job_scraper_server.py"
      ]
    },
    "resume-parser": {
      "command": "python",
      "args": [
        "/absolute/path/to/mcp_servers/resume_parser_server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    },
    "job-matcher": {
      "command": "python",
      "args": [
        "/absolute/path/to/mcp_servers/job_matcher_server.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

---

## 💡 Example Usage in Claude

Once configured, you can ask Claude:

- "Scrape job postings from Phoenix and Tempe"
- "Parse this resume: [paste resume text]"
- "Match my resume against these jobs and show the top 5 matches"

Claude will use the appropriate MCP tools automatically!

---

## 🧪 Testing

Test each server individually:

```bash
# Test scraper
python -c "from scrapers.scraper_registry import ScraperRegistry; print(ScraperRegistry.get_supported_cities())"

# Test parser (requires API key)
export GEMINI_API_KEY="your-key"
python -c "from rag.resume_parser import parse_resume; print('Parser loaded')"

# Test matcher (requires API key)
python -c "from rag.rag_engine import JobRAG; print('Matcher loaded')"
```

---

## 📚 MCP Protocol

These servers implement the [Model Context Protocol](https://modelcontextprotocol.io/) standard, making them compatible with any MCP client.

**Key Concepts**:
- **Tools**: Functions AI can call (like API endpoints)
- **Resources**: Data AI can access (like files)
- **Transport**: stdio for local communication

---

## 🔒 Security Notes

1. **API Keys**: Never commit API keys to git
2. **Local Only**: These servers run locally, no network exposure
3. **Permissions**: Claude can only call explicitly defined tools

---

## 🚀 Next Steps

- Add more tools (export results, job tracking)
- Implement Resources (recent scrapes, saved matches)
- Add Prompts (resume tailoring templates)
