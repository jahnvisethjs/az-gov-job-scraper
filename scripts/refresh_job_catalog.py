"""Refresh every configured city and precompute reusable job embeddings."""

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import ASU_AI_API_KEY, DATABASE_URL  # noqa: E402
from progress_events import SearchProgress  # noqa: E402
from scrapers import ScraperRegistry  # noqa: E402
from services import run_job_search  # noqa: E402


def report(event: SearchProgress) -> None:
    """Write compact progress suitable for CI and scheduler logs."""
    suffix = f" ({event.jobs_found} jobs)" if event.jobs_found is not None else ""
    print(f"[{event.phase}] {event.progress:>5.0%} {event.message}{suffix}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--city",
        action="append",
        dest="cities",
        choices=ScraperRegistry.get_supported_cities(),
        help="Refresh only this city; repeat the option for multiple cities.",
    )
    args = parser.parse_args()

    if not ASU_AI_API_KEY:
        parser.error("ASU_AI_API_KEY is required")
    if not DATABASE_URL:
        print(
            "Warning: DATABASE_URL is unset; this run updates only local JSON/Chroma storage.",
            file=sys.stderr,
        )

    cities = args.cities or ScraperRegistry.get_supported_cities()
    run_job_search(
        api_key=ASU_AI_API_KEY,
        profile={},
        cities=cities,
        force_refresh=True,
        catalog_only=True,
        progress_callback=report,
    )
    print("Catalog refresh and pre-indexing complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
