"""Process-local background search tasks for responsive Streamlit sessions."""

from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import Event, Lock
import time
from typing import Deque, Dict, List, Optional
from uuid import uuid4

from job_identity import ensure_job_id
from progress_events import SearchCancelled, SearchPartialResult, SearchProgress

from .job_search_service import run_job_search


@dataclass(frozen=True)
class SearchTaskSnapshot:
    task_id: str
    state: str
    latest: Optional[SearchProgress]
    events: tuple[SearchProgress, ...]
    partial_results: tuple[Dict, ...]
    error: Optional[str]


@dataclass
class _SearchTask:
    task_id: str
    state: str = "running"
    latest: Optional[SearchProgress] = None
    events: Deque[SearchProgress] = field(default_factory=lambda: deque(maxlen=50))
    partial_results: Dict[str, Dict] = field(default_factory=dict)
    result: Optional[List[Dict]] = None
    error: Optional[str] = None
    cancel_event: Event = field(default_factory=Event)
    updated_at: float = field(default_factory=time.monotonic)
    lock: Lock = field(default_factory=Lock)


class BackgroundSearchManager:
    """Run long refreshes outside Streamlit reruns and expose snapshots."""

    def __init__(self, max_workers: int = 2):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: Dict[str, _SearchTask] = {}
        self._lock = Lock()

    def start(self, **search_args) -> str:
        self._discard_expired()
        task_id = uuid4().hex
        task = _SearchTask(task_id=task_id)
        with self._lock:
            self._tasks[task_id] = task
        self._executor.submit(self._run, task, search_args)
        return task_id

    def _run(self, task: _SearchTask, search_args: Dict) -> None:
        def record(event: SearchProgress) -> None:
            with task.lock:
                task.latest = event
                task.events.append(event)
                task.updated_at = time.monotonic()

        def record_partial(result: SearchPartialResult) -> None:
            with task.lock:
                for job in result.jobs:
                    normalized = dict(job)
                    task.partial_results[ensure_job_id(normalized)] = normalized
                task.updated_at = time.monotonic()

        try:
            result = run_job_search(
                progress_callback=record,
                partial_results_callback=record_partial,
                cancel_check=task.cancel_event.is_set,
                **search_args,
            )
            with task.lock:
                if task.cancel_event.is_set():
                    task.state = "cancelled"
                else:
                    task.result = result
                    task.state = "complete"
                task.updated_at = time.monotonic()
        except SearchCancelled:
            with task.lock:
                task.state = "cancelled"
                task.updated_at = time.monotonic()
        except Exception as exc:
            with task.lock:
                task.error = str(exc)
                task.state = "error"
                task.updated_at = time.monotonic()

    def snapshot(self, task_id: str) -> Optional[SearchTaskSnapshot]:
        with self._lock:
            task = self._tasks.get(task_id)
        if not task:
            return None
        with task.lock:
            return SearchTaskSnapshot(
                task_id=task.task_id,
                state=task.state,
                latest=task.latest,
                events=tuple(task.events),
                partial_results=tuple(task.partial_results.values()),
                error=task.error,
            )

    def cancel(self, task_id: str) -> bool:
        """Request cooperative cancellation of a running search."""
        with self._lock:
            task = self._tasks.get(task_id)
        if not task:
            return False
        with task.lock:
            if task.state not in {"running", "cancelling"}:
                return False
            task.cancel_event.set()
            task.state = "cancelling"
            task.updated_at = time.monotonic()
        return True

    def take_result(self, task_id: str) -> Optional[List[Dict]]:
        with self._lock:
            task = self._tasks.get(task_id)
        if not task:
            return None
        with task.lock:
            if task.state != "complete":
                return None
            result = list(task.result or [])
        with self._lock:
            self._tasks.pop(task_id, None)
        return result

    def remove(self, task_id: str) -> None:
        with self._lock:
            self._tasks.pop(task_id, None)

    def _discard_expired(self, max_age_seconds: int = 3600) -> None:
        cutoff = time.monotonic() - max_age_seconds
        with self._lock:
            expired = [
                task_id
                for task_id, task in self._tasks.items()
                if task.state != "running" and task.updated_at < cutoff
            ]
            for task_id in expired:
                self._tasks.pop(task_id, None)


_SEARCH_MANAGER = BackgroundSearchManager()


def get_background_search_manager() -> BackgroundSearchManager:
    return _SEARCH_MANAGER
