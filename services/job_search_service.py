"""Synchronous application boundary for the asynchronous job workflow."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional

from rag import JobMatcher

from .browser_runtime import ensure_playwright_browser


ProgressCallback = Optional[Callable[[str], None]]


def run_job_search(
    api_key: str,
    profile: Dict,
    cities: List[str],
    *,
    force_refresh: bool = False,
    job_title: str = "",
    location: str = "",
    progress_callback: ProgressCallback = None,
) -> List[Dict]:
    """Run the async matcher without coupling it to Streamlit.

    The matcher and its event loop are created in the same worker thread. This
    avoids nested-event-loop failures while keeping Streamlit's render thread
    free of asyncio lifecycle management.
    """
    ensure_playwright_browser()

    def run_in_worker() -> List[Dict]:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            matcher = JobMatcher(api_key)
            return loop.run_until_complete(
                matcher.match_jobs_to_profile(
                    profile=profile,
                    cities=cities,
                    progress_callback=progress_callback,
                    force_refresh=force_refresh,
                    job_title=job_title,
                    location=location,
                )
            )
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(run_in_worker).result()
