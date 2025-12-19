"""
MCP Server for Job Matching Tools.

Exposes job matching and tailoring capabilities to AI assistants via the Model Context Protocol.
"""

from typing import List, Dict, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import asyncio

# Import our matching infrastructure
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.rag_engine import JobRAG, calculate_keyword_overlap
from dotenv import load_dotenv

load_dotenv()

# Initialize MCP server
app = Server("job-matcher")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available matching tools."""
    return [
        Tool(
            name="match_jobs",
            description="Match a resume against multiple job postings and return ranked results",
            inputSchema={
                "type": "object",
                "properties": {
                    "resume_data": {
                        "type": "object",
                        "description": "Parsed resume data with skills, experience, etc."
                    },
                    "jobs": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of job postings to match against"
                   },
                    "threshold": {
                        "type": "number",
                        "description": "Minimum match score (0-1), default 0.5",
                        "default": 0.5
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Maximum number of results to return, default 10",
                        "default": 10
                    },
                    "api_key": {
                        "type": "string",
                        "description": "Gemini API key (optional)"
                    }
                },
                "required": ["resume_data", "jobs"]
            }
        ),
        Tool(
            name="calculate_match_score",
            description="Calculate match score between a resume and a single job",
            inputSchema={
                "type": "object",
                "properties": {
                    "resume_data": {
                        "type": "object",
                        "description": "Parsed resume data"
                    },
                    "job": {
                        "type": "object",
                        "description": "Job posting to match against"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "Gemini API key (optional)"
                    }
                },
                "required": ["resume_data", "job"]
            }
        ),
        Tool(
            name="rank_jobs",
            description="Rank jobs by relevance and filter by threshold",
            inputSchema={
                "type": "object",
                "properties": {
                    "jobs": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Jobs with match_score field"
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Minimum score (0-1)",
                        "default": 0.5
                    }
                },
                "required": ["jobs"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls."""
    
    api_key = arguments.get("api_key", os.getenv("GEMINI_API_KEY"))
    
    try:
        if name == "match_jobs":
            resume_data = arguments.get("resume_data", {})
            jobs = arguments.get("jobs", [])
            threshold = arguments.get("threshold", 0.5)
            top_n = arguments.get("top_n", 10)
            
            # Initialize RAG
            rag = JobRAG(api_key=api_key)
            
            # Add jobs to vector database
            rag.add_jobs(jobs)
            
            # Search for matches
            matches = rag.search_jobs(resume_data, top_k=len(jobs))
            
            # Filter and format
            filtered_matches = [
                {
                    "job": job,
                    "score": score
                }
                for job, score in matches
                if score >= threshold
            ][:top_n]
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "matches": filtered_matches,
                    "total_matches": len(filtered_matches),
                    "total_jobs": len(jobs)
                }, indent=2)
            )]
        
        elif name == "calculate_match_score":
            resume_data = arguments.get("resume_data", {})
            job = arguments.get("job", {})
            
            # Calculate keyword overlap
            score = calculate_keyword_overlap(job, {"resume_parsed": resume_data})
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "score": score,
                    "job_title": job.get("title", "N/A")
                }, indent=2)
            )]
        
        elif name =="rank_jobs":
            jobs = arguments.get("jobs", [])
            threshold = arguments.get("threshold", 0.5)
            
            # Filter and sort
            filtered = [j for j in jobs if j.get("match_score", 0) >= threshold]
            ranked = sorted(filtered, key=lambda x: x.get("match_score", 0), reverse=True)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "ranked_jobs": ranked,
                    "count": len(ranked)
                }, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
