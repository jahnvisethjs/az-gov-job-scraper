"""Job-catalog cache facade backed by local JSON or shared PostgreSQL."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from config import JOB_CACHE_HOURS
from storage import get_job_store


def _now_for(timestamp: datetime) -> datetime:
    """Return a clock compatible with naive or timezone-aware timestamps."""
    return datetime.now(timezone.utc) if timestamp.tzinfo else datetime.now()


def is_cache_fresh(city: str, max_age_hours: int = None) -> bool:
    """Return whether a city snapshot exists within the configured TTL."""
    snapshot = get_job_store().get_city_snapshot(city)
    if not snapshot:
        return False
    max_age = JOB_CACHE_HOURS if max_age_hours is None else max_age_hours
    return _now_for(snapshot.refreshed_at) - snapshot.refreshed_at < timedelta(hours=max_age)


def get_cached_jobs(city: str, allow_stale: bool = False) -> Optional[List[Dict]]:
    """Return a city snapshot, optionally allowing stale data."""
    snapshot = get_job_store().get_city_snapshot(city)
    if not snapshot:
        return None
    if not allow_stale and (
        _now_for(snapshot.refreshed_at) - snapshot.refreshed_at
        >= timedelta(hours=JOB_CACHE_HOURS)
    ):
        return None
    return snapshot.jobs


def save_cached_jobs(city: str, jobs: List[Dict]) -> None:
    """Atomically replace the current job snapshot for a city."""
    get_job_store().replace_city_jobs(city, jobs)


def get_cache_age(city: str) -> Optional[float]:
    """Return snapshot age in hours, or ``None`` if it is unavailable."""
    snapshot = get_job_store().get_city_snapshot(city)
    if not snapshot:
        return None
    delta = _now_for(snapshot.refreshed_at) - snapshot.refreshed_at
    return delta.total_seconds() / 3600


def clear_cache(city: Optional[str] = None) -> None:
    """Clear one city or the complete configured job store."""
    get_job_store().clear(city)


def get_cache_summary() -> Dict:
    """Return job counts, age, and freshness for all available snapshots."""
    summary = {"cities": {}, "total_jobs": 0}
    for snapshot in get_job_store().list_snapshots():
        age_hours = (
            _now_for(snapshot.refreshed_at) - snapshot.refreshed_at
        ).total_seconds() / 3600
        fresh = age_hours < JOB_CACHE_HOURS
        summary["cities"][snapshot.city] = {
            "job_count": len(snapshot.jobs),
            "age_hours": round(age_hours, 1),
            "fresh": fresh,
        }
        if fresh:
            summary["total_jobs"] += len(snapshot.jobs)
    return summary
