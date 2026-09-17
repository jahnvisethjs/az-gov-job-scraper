"""Streamlit entry point for the Arizona government job matcher."""

import asyncio
import os
import sys

import streamlit as st


# Playwright requires the proactor loop on Windows. Configure it before the
# modules that initialize the scraping stack are imported.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from config import ASU_AI_API_KEY
from ui import (
    execute_search,
    inject_custom_css,
    render_header,
    render_profile_section,
    render_results,
    render_resume_section,
    render_search_controls,
)
from utils import init_session_state


st.set_page_config(
    page_title="AI Job Application Agent",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    """Compose the application from focused UI sections."""
    init_session_state()
    inject_custom_css()

    api_key = os.getenv("ASU_AI_API_KEY") or ASU_AI_API_KEY
    if not api_key:
        st.error("⚠️ **ASU AI API key not found.**")
        st.info("Set `ASU_AI_API_KEY` in `.env` or in the deployment secrets.")
        st.stop()

    render_header()
    render_resume_section(api_key)
    render_profile_section()
    search_clicked, job_title, location, min_score, max_jobs = render_search_controls()

    if search_clicked:
        execute_search(api_key, job_title, location)

    render_results(api_key, min_score, max_jobs)


if __name__ == "__main__":
    main()
