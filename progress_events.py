"""Shared control and progress types for long-running job searches."""

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple


CancelCheck = Optional[Callable[[], bool]]


class SearchCancelled(Exception):
    """Raised when a user requests cooperative search cancellation."""


def raise_if_cancelled(cancel_check: CancelCheck) -> None:
    """Stop at a safe pipeline boundary when cancellation was requested."""
    if cancel_check and cancel_check():
        raise SearchCancelled("Job search cancelled")


@dataclass(frozen=True)
class SearchProgress:
    """A UI-neutral update emitted by the job-search pipeline."""

    phase: str
    message: str
    progress: float
    city: Optional[str] = None
    city_state: Optional[str] = None
    jobs_found: Optional[int] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "progress", max(0.0, min(1.0, self.progress)))


@dataclass(frozen=True)
class SearchPartialResult:
    """Newly refreshed, unranked listings emitted when one city completes."""

    city: str
    jobs: Tuple[Dict, ...]
    completed_cities: int
    total_cities: int
