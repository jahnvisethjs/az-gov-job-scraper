"""Utils package for AZ Government Job Scraper."""

from .pdf_extractor import ResumeExtractor, validate_resume_size
from .session_manager import (
    init_session_state,
    update_user_profile,
    get_user_profile,
    is_profile_complete,
    store_scraped_jobs,
    store_matched_jobs,
    get_matched_jobs,
    set_processing_status,
    is_processing,
    clear_session,
    get_session_age,
    dismiss_job
)
from .job_cache import (
    is_cache_fresh,
    get_cached_jobs,
    save_cached_jobs,
    clear_cache,
    get_cache_summary,
    get_cache_age,
    get_cached_resume_parse,
    save_cached_resume_parse
)


__all__ = [
    "ResumeExtractor",
    "validate_resume_size",
    "init_session_state",
    "update_user_profile",
    "get_user_profile",
    "is_profile_complete",
    "store_scraped_jobs",
    "store_matched_jobs",
    "get_matched_jobs",
    "set_processing_status",
    "is_processing",
    "clear_session",
    "get_session_age",
    "dismiss_job",
    "is_cache_fresh",
    "get_cached_jobs",
    "save_cached_jobs",
    "clear_cache",
    "get_cache_summary",
    "get_cache_age",
    "get_cached_resume_parse",
    "save_cached_resume_parse",
]

