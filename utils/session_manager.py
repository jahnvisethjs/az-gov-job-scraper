"""
Streamlit session state management utilities.
Handles user profile, resume data, and job results in session.
"""
import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime


def init_session_state():
    """Initialize all session state variables if they don't exist."""
    
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {
            "name": "",
            "degree": "",
            "interests": [],
            "resume_text": "",
            "resume_filename": "",
            "resume_parsed": None,
            "created_at": None
        }
    
    if "scraped_jobs" not in st.session_state:
        st.session_state.scraped_jobs = []
    
    if "matched_jobs" not in st.session_state:
        st.session_state.matched_jobs = []
    
    if "last_scrape_time" not in st.session_state:
        st.session_state.last_scrape_time = None
    
    if "processing_status" not in st.session_state:
        st.session_state.processing_status = {
            "scraping": False,
            "matching": False,
            "error": None
        }


def update_user_profile(
    name: Optional[str] = None,
    degree: Optional[str] = None,
    interests: Optional[List[str]] = None,
    resume_text: Optional[str] = None,
    resume_filename: Optional[str] = None,
    resume_parsed: Optional[Dict] = None
):
    """
    Update user profile in session state.
    
    Args:
        name: User's name
        degree: Educational degree
        interests: List of areas of interest
        resume_text: Extracted resume text
        resume_filename: Original resume filename
        resume_parsed: Parsed resume data from AI
    """
    if name is not None:
        st.session_state.user_profile["name"] = name
    if degree is not None:
        st.session_state.user_profile["degree"] = degree
    if interests is not None:
        st.session_state.user_profile["interests"] = interests
    if resume_text is not None:
        st.session_state.user_profile["resume_text"] = resume_text
    if resume_filename is not None:
        st.session_state.user_profile["resume_filename"] = resume_filename
    if resume_parsed is not None:
        st.session_state.user_profile["resume_parsed"] = resume_parsed
    
    if st.session_state.user_profile["created_at"] is None:
        st.session_state.user_profile["created_at"] = datetime.now()


def get_user_profile() -> Dict[str, Any]:
    """Get current user profile from session."""
    return st.session_state.user_profile


def is_profile_complete() -> bool:
    """Check if user has completed minimum profile requirements."""
    profile = st.session_state.user_profile
    return bool(
        profile["name"] and
        profile["degree"] and
        profile["interests"] and
        profile["resume_text"]
    )


def store_scraped_jobs(jobs: List[Dict]):
    """Store scraped jobs in session."""
    st.session_state.scraped_jobs = jobs
    st.session_state.last_scrape_time = datetime.now()


def store_matched_jobs(jobs: List[Dict]):
    """Store matched jobs with scores in session."""
    st.session_state.matched_jobs = jobs


def get_matched_jobs(
    min_score: Optional[int] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Get matched jobs from session with optional filtering.
    
    Args:
        min_score: Minimum match score (0-100)
        limit: Maximum number of jobs to return
        
    Returns:
        List of matched job dictionaries
    """
    jobs = st.session_state.matched_jobs
    
    if min_score is not None:
        jobs = [j for j in jobs if j.get("match_score", 0) >= min_score]
    
    # Deduplicate jobs based on job_id (keep highest scoring version)
    seen_ids = {}
    deduped_jobs = []
    for job in jobs:
        job_id = job.get("job_id") or job.get("title")  # Use title as fallback
        if job_id not in seen_ids:
            seen_ids[job_id] = True
            deduped_jobs.append(job)
    
    # Sort by match score descending
    deduped_jobs = sorted(deduped_jobs, key=lambda x: x.get("match_score", 0), reverse=True)
    
    if limit is not None:
        deduped_jobs = deduped_jobs[:limit]
    
    return deduped_jobs


def dismiss_job(identifier: str):
    """Remove a job from matched_jobs in session state."""
    if "matched_jobs" in st.session_state:
        st.session_state.matched_jobs = [
            j for j in st.session_state.matched_jobs
            if (j.get("job_id") or j.get("title")) != identifier
        ]


def set_processing_status(scraping: bool = False, matching: bool = False, error: Optional[str] = None):
    """Update processing status."""
    st.session_state.processing_status = {
        "scraping": scraping,
        "matching": matching,
        "error": error
    }


def is_processing() -> bool:
    """Check if any background processing is happening."""
    return (
        st.session_state.processing_status["scraping"] or
        st.session_state.processing_status["matching"]
    )


def clear_session():
    """Clear all session state (for logout/reset)."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()


def get_session_age() -> Optional[int]:
    """Get session age in minutes."""
    profile = st.session_state.user_profile
    if profile["created_at"]:
        delta = datetime.now() - profile["created_at"]
        return int(delta.total_seconds() / 60)
    return None
