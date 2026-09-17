"""Shared progress events for long-running job searches."""

from dataclasses import dataclass
from typing import Optional


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
