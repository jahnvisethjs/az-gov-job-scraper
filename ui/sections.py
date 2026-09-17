"""Streamlit page sections for the job-matching workflow."""

import logging
from typing import Tuple

import streamlit as st

from config import (
    AREAS_OF_INTEREST,
    DEGREE_OPTIONS,
    MAX_RESUME_SIZE_MB,
    SUPPORTED_RESUME_FORMATS,
)
from job_identity import ensure_job_id
from progress_events import SearchProgress
from scrapers import ScraperRegistry
from services import generate_tailoring_advice, process_resume, run_job_search
from utils import (
    dismiss_job,
    get_matched_jobs,
    get_user_profile,
    store_matched_jobs,
    update_user_profile,
    validate_resume_size,
)

from .components import render_job_card_html, render_tailoring_advice


LOGGER = logging.getLogger(__name__)


def render_header() -> None:
    """Render the application heading."""
    st.markdown(
        """
        <div class="app-header">
            <h1>🚀 AI Job Application Agent</h1>
            <div class="subtitle">Find jobs, score matches, and get tailored resumes automatically</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_resume_section(api_key: str) -> None:
    """Render resume upload controls and update the session profile."""
    st.markdown('<div class="dark-card"><h3>📁 Your Resume</h3>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF, DOCX, or TXT)",
        type=[file_format.replace(".", "") for file_format in SUPPORTED_RESUME_FORMATS],
        help=f"Supported: {', '.join(SUPPORTED_RESUME_FORMATS)} (Max {MAX_RESUME_SIZE_MB}MB)",
        label_visibility="collapsed",
    )

    profile = get_user_profile()
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        if not validate_resume_size(file_bytes, MAX_RESUME_SIZE_MB):
            st.error(f"❌ File too large! Maximum size is {MAX_RESUME_SIZE_MB}MB")
        else:
            with st.spinner("📖 Extracting text from resume..."):
                try:
                    result = process_resume(
                        file_bytes,
                        uploaded_file.name,
                        api_key,
                        previous_text=profile.get("resume_text", ""),
                        previous_parse=profile.get("resume_parsed"),
                    )
                    update_user_profile(
                        resume_text=result.text,
                        resume_filename=uploaded_file.name,
                        resume_parsed=result.parsed,
                    )
                    if result.candidate_name:
                        update_user_profile(name=result.candidate_name)
                    if result.parse_warning:
                        st.warning("Resume text was extracted, but AI parsing failed. Please try again.")
                    st.success(f"✅ Resume uploaded: {uploaded_file.name}")
                except Exception as exc:
                    LOGGER.exception("Resume processing failed")
                    st.error(f"❌ Error processing resume: {exc}")
    elif profile["resume_filename"]:
        if profile.get("name"):
            st.markdown(f"✅ Resume uploaded! Name: {profile['name']}")
        else:
            st.markdown(f"✅ Resume uploaded: {profile['resume_filename']}")

    st.markdown("</div>", unsafe_allow_html=True)


def render_profile_section() -> None:
    """Render editable candidate profile fields."""
    st.markdown('<div class="dark-card"><h3>📋 Your Profile</h3>', unsafe_allow_html=True)
    profile = get_user_profile()

    name = st.text_input(
        "Name",
        value=profile["name"],
        placeholder="Enter your full name",
        key="profile_name",
    )
    if name and name != get_user_profile()["name"]:
        update_user_profile(name=name)

    current_degree = get_user_profile()["degree"]
    degree = st.selectbox(
        "Highest Education Level",
        options=DEGREE_OPTIONS,
        index=DEGREE_OPTIONS.index(current_degree) if current_degree in DEGREE_OPTIONS else 0,
        key="profile_degree",
    )
    if degree:
        update_user_profile(degree=degree)

    interests = st.multiselect(
        "Areas of Interest",
        options=AREAS_OF_INTEREST,
        default=get_user_profile()["interests"],
        help="Select all that apply",
        key="profile_interests",
    )
    if interests != get_user_profile()["interests"]:
        update_user_profile(interests=interests)

    st.markdown("</div>", unsafe_allow_html=True)


def render_search_controls() -> Tuple[bool, str, str, int, int]:
    """Render search filters and return their current values."""
    st.markdown('<div class="dark-card">', unsafe_allow_html=True)
    job_title = st.text_input(
        "Job Title",
        value=st.session_state.get("search_job_title", ""),
        placeholder="e.g. Backend Developer",
        key="search_job_title",
    )
    location = st.text_input(
        "Location",
        value=st.session_state.get("search_location", ""),
        placeholder="e.g. Phoenix, Arizona",
        key="search_location",
    )

    score_column, jobs_column = st.columns(2)
    with score_column:
        min_score = st.slider(
            "Min Score",
            min_value=0,
            max_value=100,
            value=st.session_state.get("min_score_val", 25),
            step=5,
            key="min_score_val",
        )
    with jobs_column:
        max_jobs = st.slider(
            "Max Jobs",
            min_value=1,
            max_value=20,
            value=st.session_state.get("max_jobs_val", 5),
            step=1,
            key="max_jobs_val",
        )

    search_clicked = st.button("🔍 Search & Analyze Jobs", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)
    return search_clicked, job_title, location, min_score, max_jobs


def execute_search(api_key: str, job_title: str, location: str) -> None:
    """Validate the session, run the search service, and store its results."""
    profile = get_user_profile()
    if not profile["resume_text"]:
        st.warning("⚠️ Please upload your resume first before searching for jobs.")
        return

    if not profile["name"]:
        update_user_profile(name="User")
    if not profile["degree"]:
        update_user_profile(degree=DEGREE_OPTIONS[0])
    if not profile["interests"]:
        update_user_profile(interests=[AREAS_OF_INTEREST[0]])

    status_container = st.status("Preparing job search...", expanded=True)
    progress_bar = st.progress(0.0, text="Preparing job search...")
    force_refresh = st.session_state.get("force_refresh", False)
    st.session_state.force_refresh = False

    def update_progress(event: SearchProgress) -> None:
        """Render worker progress events from Streamlit's main thread."""
        LOGGER.info("Job search [%s]: %s", event.phase, event.message)
        progress_text = event.message
        if event.jobs_found is not None:
            progress_text = f"{progress_text} · {event.jobs_found} jobs found"
        progress_bar.progress(event.progress, text=progress_text)

        if event.phase == "complete":
            status_container.update(
                label=event.message,
                state="complete",
                expanded=False,
            )
            return

        status_container.update(label=event.message, state="running")
        if event.city_state in {"cached", "complete", "error"}:
            icon = {
                "cached": "⚡",
                "complete": "✅",
                "error": "⚠️",
            }[event.city_state]
            status_container.write(f"{icon} {event.message}")

    try:
        matched_jobs = run_job_search(
            api_key,
            get_user_profile(),
            ScraperRegistry.get_supported_cities(),
            force_refresh=force_refresh,
            job_title=job_title,
            location=location,
            progress_callback=update_progress,
        )
        store_matched_jobs(matched_jobs)
        progress_bar.progress(
            1.0,
            text=f"Complete · {len(matched_jobs)} matching jobs found",
        )
        status_container.update(
            label=f"Found {len(matched_jobs)} matching jobs",
            state="complete",
            expanded=False,
        )
        st.rerun()
    except Exception:
        LOGGER.exception("Job search failed")
        status_container.update(
            label="Job search failed. Check the server logs for details.",
            state="error",
            expanded=True,
        )


def render_results(api_key: str, min_score: int, max_jobs: int) -> None:
    """Render filtered job results and their actions."""
    if not st.session_state.matched_jobs:
        return

    filtered_jobs = get_matched_jobs(min_score=min_score, limit=max_jobs)
    st.markdown(
        f'<div class="results-header">Results ({len(filtered_jobs)} jobs shown)</div>',
        unsafe_allow_html=True,
    )
    if not filtered_jobs:
        st.info("No jobs match your current filters. Try lowering the minimum score.")
        return

    for job in filtered_jobs:
        job_id = ensure_job_id(job)
        advice_key = f"advice_{job_id}"
        toggle_key = f"show_advice_{job_id}"
        st.markdown(
            render_job_card_html(job, has_tailoring=advice_key in st.session_state),
            unsafe_allow_html=True,
        )

        apply_column, advice_column, dismiss_column = st.columns([2, 2, 1])
        with apply_column:
            if job.get("url"):
                st.link_button("🔗 Apply Now", job["url"], use_container_width=True)
        with advice_column:
            if toggle_key not in st.session_state:
                st.session_state[toggle_key] = False
            if st.button(
                "💡 Get Tailoring Advice",
                key=f"btn_advice_{job_id}",
                use_container_width=True,
            ):
                st.session_state[toggle_key] = not st.session_state[toggle_key]
                st.rerun()
        with dismiss_column:
            if st.button("🗑️", key=f"btn_clear_{job_id}", help="Dismiss"):
                dismiss_job(job_id)
                st.rerun()

        if st.session_state.get(toggle_key, False):
            _render_job_advice(job, api_key, advice_key)
        st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)


def _render_job_advice(job: dict, api_key: str, advice_key: str) -> None:
    """Load advice once per job and render the cached result."""
    if advice_key not in st.session_state:
        with st.spinner("🤖 Generating personalized advice..."):
            try:
                st.session_state[advice_key] = generate_tailoring_advice(
                    job,
                    get_user_profile(),
                    api_key,
                )
            except Exception:
                LOGGER.exception("Tailoring advice generation failed")
                st.error("Unable to generate tailoring advice. Check the server logs for details.")
                return

    render_tailoring_advice(st.session_state[advice_key])
