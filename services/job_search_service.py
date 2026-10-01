"""Synchronous application boundary for the asynchronous job workflow."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue
from typing import Callable, Dict, List, Optional, Tuple

from progress_events import (
    CancelCheck,
    SearchPartialResult,
    SearchProgress,
    raise_if_cancelled,
)
from rag.job_matcher import JobMatcher


ProgressCallback = Optional[Callable[[SearchProgress], None]]
PartialResultsCallback = Optional[Callable[[SearchPartialResult], None]]


def run_job_search(
    api_key: str,
    profile: Dict,
    cities: List[str],
    *,
    force_refresh: bool = False,
    cached_only: bool = False,
    catalog_only: bool = False,
    job_title: str = "",
    location: str = "",
    progress_callback: ProgressCallback = None,
    partial_results_callback: PartialResultsCallback = None,
    cancel_check: CancelCheck = None,
) -> List[Dict]:
    """Run the async matcher without coupling it to Streamlit.

    The matcher and its event loop are created in the same worker thread. This
    avoids nested-event-loop failures while keeping Streamlit's render thread
    free of asyncio lifecycle management.
    """
    raise_if_cancelled(cancel_check)
    updates: Queue[Tuple[str, object]] = Queue()

    def publish_progress(event: SearchProgress) -> None:
        updates.put(("progress", event))

    def publish_partial(result: SearchPartialResult) -> None:
        updates.put(("partial", result))

    def dispatch_update(update: Tuple[str, object]) -> None:
        kind, payload = update
        if kind == "progress" and progress_callback:
            progress_callback(payload)
        elif kind == "partial" and partial_results_callback:
            partial_results_callback(payload)

    def run_in_worker() -> List[Dict]:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            matcher = JobMatcher(api_key)
            return loop.run_until_complete(
                matcher.match_jobs_to_profile(
                    profile=profile,
                    cities=cities,
                    progress_callback=publish_progress if progress_callback else None,
                    partial_results_callback=(
                        publish_partial if partial_results_callback else None
                    ),
                    cancel_check=cancel_check,
                    force_refresh=force_refresh,
                    cached_only=cached_only,
                    catalog_only=catalog_only,
                    job_title=job_title,
                    location=location,
                )
            )
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(run_in_worker)

        if progress_callback or partial_results_callback:
            while not future.done():
                try:
                    dispatch_update(updates.get(timeout=0.1))
                except Empty:
                    continue

            while True:
                try:
                    dispatch_update(updates.get_nowait())
                except Empty:
                    break

        return future.result()
