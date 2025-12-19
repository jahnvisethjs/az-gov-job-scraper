"""
MCP Server for Job Scraping Tools.

Exposes job scraping capabilities to AI assistants via the Model Context Protocol.
"""

from typing import List, Dict, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import asyncio

# Import our scraping infrastructure
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.scraper_registry import ScraperRegistry
from scrapers.base_scraper import PlatformNotSupportedError


# Initialize MCP server
app = Server("job-scraper")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available scraping tools."""
    return [
        Tool(
            name="scrape_city",
            description="Scrape job postings from a specific Arizona city government website",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city (e.g., 'Phoenix', 'Tempe', 'Scottsdale')"
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="scrape_multiple_cities",
            description="Scrape job postings from multiple Arizona cities at once",
            inputSchema={
                "type": "object",
                "properties": {
                    "cities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of city names to scrape"
                    }
                },
                "required": ["cities"]
            }
        ),
        Tool(
            name="list_supported_cities",
            description="Get a list of all supported Arizona cities",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls."""
    
    if name == "list_supported_cities":
        cities = ScraperRegistry.get_supported_cities()
        return [TextContent(
            type="text",
            text=json.dumps({
                "cities": cities,
                "count": len(cities)
            }, indent=2)
        )]
    
    elif name == "scrape_city":
        city = arguments.get("city")
        
        try:
            # Get scraper for city
            scraper = ScraperRegistry.get_scraper(city)
            
            # Scrape jobs
            jobs = scraper.scrape()
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "city": city,
                    "jobs_found": len(jobs),
                    "jobs": jobs[:10],  # Return first 10 for preview
                    "message": f"Successfully scraped {len(jobs)} jobs from {city}"
                }, indent=2)
            )]
            
        except PlatformNotSupportedError as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "city": city
                }, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Failed to scrape {city}: {str(e)}",
                    "city": city
                }, indent=2)
            )]
    
    elif name == "scrape_multiple_cities":
        cities = arguments.get("cities", [])
        results = []
        
        for city in cities:
            try:
                scraper = ScraperRegistry.get_scraper(city)
                jobs = scraper.scrape()
                results.append({
                    "city": city,
                    "status": "success",
                    "jobs_found": len(jobs)
                })
            except Exception as e:
                results.append({
                    "city": city,
                    "status": "error",
                    "error": str(e)
                })
        
        total_jobs = sum(r.get("jobs_found", 0) for r in results)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "results": results,
                "total_jobs": total_jobs,
                "cities_scraped": len([r for r in results if r["status"] == "success"])
            }, indent=2)
        )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
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
