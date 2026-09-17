"""Run one configured city scraper manually and summarize its results."""

import argparse
import asyncio
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scrapers import ScraperRegistry  # noqa: E402


async def run(city: str, limit: int) -> int:
    scraper = ScraperRegistry.get_scraper(city)
    print(f"Scraping {city} with {scraper.get_platform_name()}...")

    try:
        jobs = await scraper.scrape_with_retry(max_retries=1)
    except Exception as exc:
        print(f"Scraper failed: {exc}", file=sys.stderr)
        return 1

    print(f"Found {len(jobs)} jobs.")
    for job in jobs[:limit]:
        print(f"- {job.title}: {job.url}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("city", choices=ScraperRegistry.get_supported_cities())
    parser.add_argument("--limit", type=int, default=5, help="Jobs to display (default: 5)")
    args = parser.parse_args()
    return asyncio.run(run(args.city, max(0, args.limit)))


if __name__ == "__main__":
    raise SystemExit(main())
