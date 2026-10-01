"""Streamlit page sections for the job-matching workflow."""

import logging
from typing import Tuple
from urllib.parse import urlsplit

import streamlit as st

from config import (
    AREAS_OF_INTEREST,
    DEGREE_OPTIONS,
    MAX_RESUME_SIZE_MB,
    SUPPORTED_RESUME_FORMATS,
)
from job_identity import ensure_job_id
from scrapers import ScraperRegistry
from services import (
    generate_tailoring_advice,
    get_background_search_manager,
    process_resume,
    run_job_search,
)
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
    refresh_running = bool(st.session_state.get("search_task_id"))
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF, DOCX, or TXT)",
        type=[file_format.replace(".", "") for file_format in SUPPORTED_RESUME_FORMATS],
        help=f"Supported: {', '.join(SUPPORTED_RESUME_FORMATS)} (Max {MAX_RESUME_SIZE_MB}MB)",
        label_visibility="collapsed",
        disabled=refresh_running,
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
    refresh_running = bool(st.session_state.get("search_task_id"))

    name = st.text_input(
        "Name",
        value=profile["name"],
        placeholder="Enter your full name",
        key="profile_name",
        disabled=refresh_running,
    )
    if name and name != get_user_profile()["name"]:
        update_user_profile(name=name)

    current_degree = get_user_profile()["degree"]
    degree = st.selectbox(
        "Highest Education Level",
        options=DEGREE_OPTIONS,
        index=DEGREE_OPTIONS.index(current_degree) if current_degree in DEGREE_OPTIONS else 0,
        key="profile_degree",
        disabled=refresh_running,
    )
    if degree:
        update_user_profile(degree=degree)

    interests = st.multiselect(
        "Areas of Interest",
        options=AREAS_OF_INTEREST,
        default=get_user_profile()["interests"],
        help="Select all that apply",
        key="profile_interests",
        disabled=refresh_running,
    )
    if interests != get_user_profile()["interests"]:
        update_user_profile(interests=interests)

    st.markdown("</div>", unsafe_allow_html=True)


def render_search_controls() -> Tuple[bool, str, str, int, int]:
    """Render search filters and return their current values."""
    refresh_running = bool(st.session_state.get("search_task_id"))
    st.markdown('<div class="dark-card">', unsafe_allow_html=True)
    job_title = st.text_input(
        "Job Title",
        value=st.session_state.get("search_job_title", ""),
        placeholder="e.g. Backend Developer",
        key="search_job_title",
        disabled=refresh_running,
    )
    location = st.text_input(
        "Location",
        value=st.session_state.get("search_location", ""),
        placeholder="e.g. Phoenix, Arizona",
        key="search_location",
        disabled=refresh_running,
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

    search_clicked = st.button(
        "Refreshing jobs..." if refresh_running else "🔍 Search & Analyze Jobs",
        type="primary",
        disabled=refresh_running,
    )
    if st.session_state.get("background_search_error"):
        st.error(st.session_state.background_search_error)
    st.markdown("</div>", unsafe_allow_html=True)
    return search_clicked, job_title, location, min_score, max_jobs


def execute_search(api_key: str, job_title: str, location: str) -> None:
    """Show saved results immediately and refresh the catalog in the background."""
    profile = get_user_profile()
    if not profile["resume_text"]:
        st.warning("⚠️ Please upload your resume first before searching for jobs.")
        return

    if st.session_state.get("search_task_id"):
        return

    if not profile["name"]:
        update_user_profile(name="User")
    if not profile["degree"]:
        update_user_profile(degree=DEGREE_OPTIONS[0])
    if not profile["interests"]:
        update_user_profile(interests=[AREAS_OF_INTEREST[0]])

    force_refresh = st.session_state.get("force_refresh", False)
    st.session_state.force_refresh = False
    st.session_state.background_search_error = None
    st.session_state.partial_jobs = []
    st.session_state.partial_results_notice = None
    search_args = {
        "api_key": api_key,
        "profile": dict(get_user_profile()),
        "cities": ScraperRegistry.get_supported_cities(),
        "job_title": job_title,
        "location": location,
    }

    # This pass never opens a browser. It ranks the latest saved catalog so a
    # returning user gets useful results while the live refresh continues.
    store_matched_jobs([])
    st.session_state.results_source = None
    try:
        with st.spinner("Loading saved jobs..."):
            cached_jobs = run_job_search(**search_args, cached_only=True)
        store_matched_jobs(cached_jobs)
        if cached_jobs:
            st.session_state.results_source = "cached"
    except Exception:
        # A corrupt or unavailable cache should not prevent the live refresh.
        LOGGER.exception("Cached job search failed")

    manager = get_background_search_manager()
    st.session_state.search_task_id = manager.start(
        **search_args,
        force_refresh=force_refresh,
        cached_only=False,
    )
    st.rerun()


@st.fragment(run_every="1s")
def render_search_activity() -> None:
    """Poll and render a background catalog refresh without blocking results."""
    task_id = st.session_state.get("search_task_id")
    if not task_id:
        return

    manager = get_background_search_manager()
    snapshot = manager.snapshot(task_id)
    if snapshot is None:
        st.session_state.search_task_id = None
        st.session_state.background_search_error = (
            "The background refresh expired. Start a new search to try again."
        )
        st.rerun()
        return

    if snapshot.state == "complete":
        matched_jobs = manager.take_result(task_id) or []
        store_matched_jobs(matched_jobs)
        st.session_state.search_task_id = None
        st.session_state.results_source = "fresh"
        st.session_state.partial_jobs = []
        st.session_state.partial_results_notice = None
        st.toast(f"Job refresh complete: {len(matched_jobs)} matches found")
        st.rerun()
        return

    if snapshot.state == "error":
        st.session_state.partial_jobs = list(snapshot.partial_results)
        st.session_state.partial_results_notice = (
            "The refresh stopped after returning these unranked live listings."
        )
        manager.remove(task_id)
        st.session_state.search_task_id = None
        st.session_state.background_search_error = (
            "The live job refresh failed. Saved results are still available. "
            "Check the server logs and try again."
        )
        LOGGER.error("Background job refresh failed: %s", snapshot.error)
        st.rerun()
        return

    if snapshot.state == "cancelled":
        st.session_state.partial_jobs = list(snapshot.partial_results)
        st.session_state.partial_results_notice = (
            "Refresh cancelled. These listings were collected before cancellation "
            "and have not received final resume-match scores."
        )
        manager.remove(task_id)
        st.session_state.search_task_id = None
        st.toast("Job refresh cancelled; saved matches were kept")
        st.rerun()
        return

    latest = snapshot.latest
    label = (
        "Stopping job refresh safely..."
        if snapshot.state == "cancelling"
        else latest.message if latest else "Starting live job refresh..."
    )
    progress = latest.progress if latest else 0.01
    jobs_found = latest.jobs_found if latest else None
    progress_text = label
    if jobs_found is not None:
        progress_text = f"{label} · {jobs_found} jobs found"

    with st.status(label, state="running", expanded=False) as status:
        st.progress(progress, text=progress_text)
        terminal_events = [
            event
            for event in snapshot.events
            if event.city_state in {"cached", "complete", "error"}
        ][-4:]
        icons = {"cached": "⚡", "complete": "✅", "error": "⚠️"}
        for event in terminal_events:
            status.write(f"{icons[event.city_state]} {event.message}")
        _render_partial_job_preview(snapshot.partial_results)
        status.update(
            label=(
                "Stopping job refresh safely..."
                if snapshot.state == "cancelling"
                else "Refreshing job listings in the background"
            ),
            state="running",
            expanded=False,
        )

    if st.button(
        "Cancel refresh",
        key=f"cancel_search_{task_id}",
        disabled=snapshot.state == "cancelling",
    ):
        manager.cancel(task_id)
        st.rerun()


def _render_partial_job_preview(jobs, limit: int = 8) -> None:
    """Show newly scraped listings before final resume scoring completes."""
    if not jobs:
        return
    st.markdown(f"**Live partial results ({len(jobs)} listings)**")
    st.caption("These listings are refreshed but not yet scored against your resume.")
    for job in list(jobs)[:limit]:
        title = str(job.get("title") or "Untitled role")
        city = str(job.get("city") or job.get("location") or "Arizona")
        url = str(job.get("url") or "")
        parsed_url = urlsplit(url)
        if parsed_url.scheme in {"http", "https"} and parsed_url.netloc:
            st.link_button(
                f"{title} — {city}",
                url,
                key=f"partial_job_{ensure_job_id(job)}",
            )
        else:
            st.write(f"• {title} — {city}")
    if len(jobs) > limit:
        st.caption(f"Plus {len(jobs) - limit} more refreshed listings.")


def render_partial_results() -> None:
    """Retain useful live listings when a refresh is cancelled or fails."""
    if st.session_state.get("search_task_id"):
        return
    jobs = st.session_state.get("partial_jobs", [])
    if not jobs:
        return
    notice = st.session_state.get("partial_results_notice")
    if notice:
        st.warning(notice)
    _render_partial_job_preview(jobs)


def render_results(api_key: str, min_score: int, max_jobs: int) -> None:
    """Render filtered job results and their actions."""
    if not st.session_state.matched_jobs:
        return

    filtered_jobs = get_matched_jobs(min_score=min_score, limit=max_jobs)
    if (
        st.session_state.get("results_source") == "cached"
        and st.session_state.get("search_task_id")
    ):
        st.info("Showing saved matches while current job listings refresh.")
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
