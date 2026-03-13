"""
Job cache layer for persisting scraped jobs to disk.
Avoids re-scraping cities when cached results are still fresh.
"""
import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from config import CACHE_DIR, JOB_CACHE_HOURS


def _get_cache_dir() -> Path:
    """Get and ensure cache directory exists."""
    cache_dir = Path(CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _city_cache_path(city: str) -> Path:
    """Get cache file path for a city."""
    safe_name = city.lower().replace(" ", "_").replace("/", "_")
    return _get_cache_dir() / f"jobs_{safe_name}.json"


def _resume_cache_path() -> Path:
    """Get cache file path for parsed resumes."""
    return _get_cache_dir() / "resume_cache.json"


def is_cache_fresh(city: str, max_age_hours: int = None) -> bool:
    """
    Check if cached jobs for a city are still fresh.
    
    Args:
        city: City name
        max_age_hours: Override for cache TTL (defaults to config)
        
    Returns:
        True if cache exists and is within TTL
    """
    max_age = max_age_hours or JOB_CACHE_HOURS
    cache_file = _city_cache_path(city)
    
    if not cache_file.exists():
        return False
    
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        cached_at = datetime.fromisoformat(data.get("cached_at", ""))
        return datetime.now() - cached_at < timedelta(hours=max_age)
    except (json.JSONDecodeError, ValueError, KeyError):
        return False


def get_cached_jobs(city: str) -> Optional[List[Dict]]:
    """
    Get cached jobs for a city (if cache is fresh).
    
    Args:
        city: City name
        
    Returns:
        List of job dicts, or None if cache is stale/missing
    """
    if not is_cache_fresh(city):
        return None
    
    cache_file = _city_cache_path(city)
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("jobs", [])
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def save_cached_jobs(city: str, jobs: List[Dict]):
    """
    Save scraped jobs to cache.
    
    Args:
        city: City name
        jobs: List of job dictionaries
    """
    cache_file = _city_cache_path(city)
    data = {
        "city": city,
        "cached_at": datetime.now().isoformat(),
        "job_count": len(jobs),
        "jobs": jobs
    }
    
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def get_cache_age(city: str) -> Optional[float]:
    """
    Get cache age in hours for a city.
    
    Returns:
        Age in hours, or None if no cache exists
    """
    cache_file = _city_cache_path(city)
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        cached_at = datetime.fromisoformat(data.get("cached_at", ""))
        delta = datetime.now() - cached_at
        return delta.total_seconds() / 3600
    except (json.JSONDecodeError, ValueError):
        return None


def clear_cache(city: Optional[str] = None):
    """
    Clear cache. If city is specified, clear only that city's cache.
    If city is None, clear ALL cache files.
    """
    if city:
        cache_file = _city_cache_path(city)
        if cache_file.exists():
            cache_file.unlink()
    else:
        cache_dir = _get_cache_dir()
        for f in cache_dir.glob("jobs_*.json"):
            f.unlink()


def get_cache_summary() -> Dict:
    """Get a summary of all cached data."""
    cache_dir = _get_cache_dir()
    summary = {"cities": {}, "total_jobs": 0}
    
    for f in cache_dir.glob("jobs_*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            city = data.get("city", f.stem)
            age_hours = get_cache_age(city)
            fresh = is_cache_fresh(city)
            summary["cities"][city] = {
                "job_count": data.get("job_count", 0),
                "age_hours": round(age_hours, 1) if age_hours else None,
                "fresh": fresh
            }
            if fresh:
                summary["total_jobs"] += data.get("job_count", 0)
        except (json.JSONDecodeError, Exception):
            continue
    
    return summary


# --- Resume Cache ---

def _resume_hash(resume_text: str) -> str:
    """Generate a hash for resume text to use as cache key."""
    return hashlib.md5(resume_text.encode("utf-8")).hexdigest()


def get_cached_resume_parse(resume_text: str) -> Optional[Dict]:
    """
    Get cached parsed resume data if available.
    
    Args:
        resume_text: Raw resume text
        
    Returns:
        Parsed resume dict, or None if not cached
    """
    cache_file = _resume_cache_path()
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)
        
        key = _resume_hash(resume_text)
        entry = cache.get(key)
        if entry:
            return entry.get("parsed_data")
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    
    return None


def save_cached_resume_parse(resume_text: str, parsed_data: Dict):
    """
    Save parsed resume data to cache.
    
    Args:
        resume_text: Raw resume text (used for cache key)
        parsed_data: Parsed resume dictionary from LLM
    """
    cache_file = _resume_cache_path()
    
    # Load existing cache
    cache = {}
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            cache = {}
    
    key = _resume_hash(resume_text)
    cache[key] = {
        "cached_at": datetime.now().isoformat(),
        "parsed_data": parsed_data
    }
    
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, default=str)
