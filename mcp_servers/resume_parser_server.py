"""
MCP Server for Resume Parsing Tools.

Exposes resume parsing capabilities to AI assistants via the Model Context Protocol.
"""

from typing import List, Dict, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import asyncio

# Import our parsing infrastructure
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.resume_parser import parse_resume
from dotenv import load_dotenv

load_dotenv()

# Initialize MCP server
app = Server("resume-parser")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available parsing tools."""
    return [
        Tool(
            name="parse_resume",
            description="Parse a resume and extract structured information (skills, experience, education)",
            inputSchema={
                "type": "object",
                "properties": {
                    "resume_text": {
                        "type": "string",
                        "description": "The full text content of the resume"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "ASU AI API key (optional, uses environment variable if not provided)"
                    }
                },
                "required": ["resume_text"]
            }
        ),
        Tool(
            name="extract_skills",
            description="Extract only the skills from a resume",
            inputSchema={
                "type": "object",
                "properties": {
                    "resume_text": {
                        "type": "string",
                        "description": "The full text content of the resume"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "ASU AI API key (optional)"
                    }
                },
                "required": ["resume_text"]
            }
        ),
        Tool(
            name="extract_experience",
            description="Extract only work experience from a resume",
            inputSchema={
                "type": "object",
                "properties": {
                    "resume_text": {
                        "type": "string",
                        "description": "The full text content of the resume"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "ASU AI API key (optional)"
                    }
                },
                "required": ["resume_text"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls."""
    
    resume_text = arguments.get("resume_text", "")
    api_key = arguments.get("api_key", os.getenv("ASU_AI_API_KEY"))
    
    if not api_key:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": "API key required. Provide via 'api_key' parameter or ASU_AI_API_KEY environment variable."
            }, indent=2)
        )]
    
    try:
        if name == "parse_resume":
            result = parse_resume(resume_text, api_key)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "data": result
                }, indent=2)
            )]
        
        elif name == "extract_skills":
            result = parse_resume(resume_text, api_key)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "skills": result.get("skills", [])
                }, indent=2)
            )]
        
        elif name == "extract_experience":
            result = parse_resume(resume_text, api_key)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "experience": result.get("experience", [])
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


if __name == "__main__":
    asyncio.run(main())

