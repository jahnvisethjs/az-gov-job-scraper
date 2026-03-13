"""
AI Job Application Agent - Streamlit Web Application
Redesigned UI: centered layout, dark theme, resume upload, job search & results
"""
import streamlit as st
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
from typing import Dict

# Fix for Windows + Playwright asyncio issue
if sys.platform == 'win32':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Import local utilities
from utils import (
    init_session_state,
    update_user_profile,
    get_user_profile,
    is_profile_complete,
    ResumeExtractor,
    validate_resume_size,
    get_cached_resume_parse,
    save_cached_resume_parse,
    get_cache_summary,
    clear_cache
)
from rag import ResumeParser
from config import (
    AREAS_OF_INTEREST,
    DEGREE_OPTIONS,
    MAX_RESUME_SIZE_MB,
    SUPPORTED_RESUME_FORMATS,
    ASU_AI_API_KEY
)

# Load environment variables
load_dotenv()

# Automatically install Playwright browsers if running on Streamlit Cloud (Linux)
if sys.platform.startswith('linux'):
    @st.cache_resource
    def install_playwright():
        os.system("playwright install chromium")
        os.system("playwright install-deps chromium")
    
    install_playwright()


# Page configuration
st.set_page_config(
    page_title="AI Job Application Agent",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS: Dark theme matching the target design
# ─────────────────────────────────────────────────────────────────────────────
def inject_custom_css():
    st.markdown("""
    <style>
        /* ── Import Google Font ────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* ── Global Dark Theme ─────────────────────────────────────── */
        .stApp {
            background-color: #0d1117 !important;
            color: #e6edf3 !important;
            font-family: 'Inter', sans-serif !important;
        }

        /* Hide default Streamlit sidebar toggle & footer */
        [data-testid="collapsedControl"] { display: none !important; }
        footer { display: none !important; }
        #MainMenu { display: none !important; }

        /* ── Header Styling ────────────────────────────────────────── */
        .app-header {
            text-align: center;
            padding: 2.5rem 0 0.5rem 0;
        }
        .app-header h1 {
            font-size: 2.4rem;
            font-weight: 800;
            color: #e6edf3;
            margin: 0;
        }
        .app-header .subtitle {
            font-size: 1.05rem;
            color: #8b949e;
            margin-top: 0.4rem;
            font-weight: 400;
        }

        /* ── Card Container ────────────────────────────────────────── */
        .dark-card {
            background: #161b22;
            border: 1px solid #21262d;
            border-radius: 12px;
            padding: 1.5rem 1.8rem;
            margin-bottom: 1.2rem;
        }
        .dark-card h3 {
            color: #e6edf3;
            font-size: 1.15rem;
            font-weight: 700;
            margin: 0 0 1rem 0;
        }

        /* ── Streamlit Input Overrides ─────────────────────────────── */
        .stTextInput > div > div > input {
            background-color: #0d1117 !important;
            color: #e6edf3 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
            padding: 0.65rem 0.9rem !important;
            font-size: 0.95rem !important;
        }
        .stTextInput > label {
            color: #8b949e !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #388bfd !important;
            box-shadow: 0 0 0 3px rgba(56, 139, 253, 0.15) !important;
        }

        /* ── File Uploader Overrides ───────────────────────────────── */
        [data-testid="stFileUploader"] {
            background-color: transparent !important;
        }
        [data-testid="stFileUploader"] section {
            background-color: #0d1117 !important;
            border: 2px dashed #30363d !important;
            border-radius: 10px !important;
            padding: 1rem !important;
        }
        [data-testid="stFileUploader"] section:hover {
            border-color: #388bfd !important;
        }
        [data-testid="stFileUploader"] label {
            color: #8b949e !important;
        }
        [data-testid="stFileUploader"] small {
            color: #6e7681 !important;
        }

        /* ── Slider Overrides ──────────────────────────────────────── */
        .stSlider > label {
            color: #8b949e !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
        }
        .stSlider [data-testid="stThumbValue"] {
            color: #e6edf3 !important;
        }
        .stSlider [data-baseweb="slider"] div[role="slider"] {
            background-color: #388bfd !important;
            border-color: #388bfd !important;
        }
        .stSlider [data-baseweb="slider"] div[data-testid="stTickBarMin"],
        .stSlider [data-baseweb="slider"] div[data-testid="stTickBarMax"] {
            color: #6e7681 !important;
        }

        /* ── Primary Button ────────────────────────────────────────── */
        .stButton > button[kind="primary"],
        .stButton > button {
            width: 100% !important;
            background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%) !important;
            color: white !important;
            font-weight: 700 !important;
            font-size: 1.05rem !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.75rem 1.5rem !important;
            transition: all 0.25s ease !important;
            letter-spacing: 0.02em !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(56, 139, 253, 0.35) !important;
        }
        .stButton > button:active {
            transform: translateY(0) !important;
        }

        /* ── Results Header ────────────────────────────────────────── */
        .results-header {
            font-size: 1.5rem;
            font-weight: 800;
            color: #e6edf3;
            margin: 2rem 0 1rem 0;
        }

        /* ── Job Result Card ───────────────────────────────────────── */
        .job-card {
            background: #161b22;
            border: 1px solid #21262d;
            border-radius: 12px;
            padding: 1.3rem 1.6rem;
            margin-bottom: 0.9rem;
            transition: border-color 0.2s ease;
        }
        .job-card:hover {
            border-color: #388bfd;
        }
        .job-card-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #e6edf3;
            display: inline;
        }
        .score-badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.82rem;
            font-weight: 700;
            margin-left: 10px;
            vertical-align: middle;
        }
        .score-high {
            background: rgba(63, 185, 80, 0.15);
            color: #3fb950;
            border: 1px solid rgba(63, 185, 80, 0.3);
        }
        .score-med {
            background: rgba(210, 153, 34, 0.15);
            color: #d29922;
            border: 1px solid rgba(210, 153, 34, 0.3);
        }
        .score-low {
            background: rgba(248, 81, 73, 0.15);
            color: #f85149;
            border: 1px solid rgba(248, 81, 73, 0.3);
        }
        .job-company {
            color: #8b949e;
            font-size: 0.95rem;
            margin-top: 0.3rem;
        }
        .job-location {
            color: #8b949e;
            font-size: 0.88rem;
            margin-top: 0.2rem;
        }
        .job-location .pin {
            color: #f85149;
        }
        .status-badge {
            display: inline-block;
            padding: 3px 12px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-top: 0.5rem;
        }
        .status-tailored {
            background: rgba(63, 185, 80, 0.15);
            color: #3fb950;
            border: 1px solid rgba(63, 185, 80, 0.3);
        }
        .status-skipped {
            background: rgba(139, 148, 158, 0.15);
            color: #8b949e;
            border: 1px solid rgba(139, 148, 158, 0.3);
        }

        /* ── Alert / Info box overrides ─────────────────────────────── */
        [data-testid="stAlert"] {
            background-color: #161b22 !important;
            border: 1px solid #21262d !important;
            color: #e6edf3 !important;
            border-radius: 8px !important;
        }

        /* ── Spinner ───────────────────────────────────────────────── */
        .stSpinner > div {
            color: #388bfd !important;
        }

        /* ── Expander overrides ─────────────────────────────────────── */
        .streamlit-expanderHeader {
            background-color: #161b22 !important;
            color: #e6edf3 !important;
            border-radius: 8px !important;
        }

        /* ── Link button override ──────────────────────────────────── */
        .stLinkButton > a {
            background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
        }

        /* ── Metric overrides ──────────────────────────────────────── */
        [data-testid="stMetricLabel"] {
            color: #8b949e !important;
        }
        [data-testid="stMetricValue"] {
            color: #e6edf3 !important;
        }

        /* ── Markdown text color fix ───────────────────────────────── */
        .stMarkdown, .stMarkdown p, .stMarkdown li {
            color: #e6edf3 !important;
        }

        /* ── Selectbox / Multiselect Overrides ─────────────────────── */
        .stSelectbox > label,
        .stMultiSelect > label {
            color: #8b949e !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
        }
        .stSelectbox [data-baseweb="select"],
        .stMultiSelect [data-baseweb="select"] {
            background-color: #0d1117 !important;
            border-color: #30363d !important;
            border-radius: 8px !important;
        }
        .stSelectbox [data-baseweb="select"] > div,
        .stMultiSelect [data-baseweb="select"] > div {
            background-color: #0d1117 !important;
            color: #e6edf3 !important;
        }
        [data-baseweb="popover"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
        }
        [data-baseweb="popover"] li {
            color: #e6edf3 !important;
        }
        [data-baseweb="popover"] li:hover {
            background-color: #21262d !important;
        }
        [data-baseweb="tag"] {
            background-color: rgba(56, 139, 253, 0.15) !important;
            color: #58a6ff !important;
            border: 1px solid rgba(56, 139, 253, 0.3) !important;
        }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Job card HTML renderer
# ─────────────────────────────────────────────────────────────────────────────
def render_job_card_html(job: Dict, has_tailoring: bool = False) -> str:
    """Render a single job result card as HTML."""
    title = job.get("title", "Untitled")
    score = job.get("match_score", 0)
    company = job.get("city", "") or job.get("department", "") or ""
    location = job.get("location", "") or job.get("city", "")

    # Score badge class
    if score >= 60:
        badge_cls = "score-high"
    elif score >= 40:
        badge_cls = "score-med"
    else:
        badge_cls = "score-low"

    score_display = f"{int(round(score))}/100"

    # Status badge
    if has_tailoring:
        status_html = '<div><span class="status-badge status-tailored">✅ Resume Tailored</span></div>'
    elif score < 50:
        status_html = '<div><span class="status-badge status-skipped">⏭️ Skipped</span></div>'
    else:
        status_html = ""

    return f"""
    <div class="job-card">
        <div>
            <span class="job-card-title">{title}</span>
            <span class="score-badge {badge_cls}">{score_display}</span>
        </div>
        <div class="job-company">{company}</div>
        <div class="job-location"><span class="pin">📍</span> {location}</div>
        {status_html}
    </div>
    """


# ─────────────────────────────────────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────────────────────────────────────
def main():
    """Main application function."""

    # Initialize session state
    init_session_state()

    # Inject custom CSS
    inject_custom_css()

    # Check for API key
    api_key = os.getenv("ASU_AI_API_KEY") or ASU_AI_API_KEY
    if not api_key:
        st.error("⚠️ **ASU AI API Key not found!**")
        st.info("Please create a `.env` file with your `ASU_AI_API_KEY` or set it in `config.py`")
        st.code("ASU_AI_API_KEY=your_api_key_here", language="bash")
        st.stop()

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="app-header">
        <h1>🚀 AI Job Application Agent</h1>
        <div class="subtitle">Find jobs, score matches, and get tailored resumes automatically</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Resume Upload Section ───────────────────────────────────────────────
    st.markdown('<div class="dark-card"><h3>📁 Your Resume</h3>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload your resume (PDF, DOCX, or TXT)",
        type=[fmt.replace(".", "") for fmt in SUPPORTED_RESUME_FORMATS],
        help=f"Supported: {', '.join(SUPPORTED_RESUME_FORMATS)} (Max {MAX_RESUME_SIZE_MB}MB)",
        label_visibility="collapsed"
    )

    # Process resume if uploaded
    profile = get_user_profile()
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()

        if not validate_resume_size(file_bytes, MAX_RESUME_SIZE_MB):
            st.error(f"❌ File too large! Maximum size is {MAX_RESUME_SIZE_MB}MB")
        else:
            with st.spinner("📖 Extracting text from resume..."):
                try:
                    resume_text = ResumeExtractor.extract_text(file_bytes, uploaded_file.name)
                    if resume_text:
                        update_user_profile(
                            resume_text=resume_text,
                            resume_filename=uploaded_file.name
                        )

                        # Auto-parse the resume with AI
                        cached_parse = get_cached_resume_parse(resume_text)
                        if cached_parse:
                            update_user_profile(resume_parsed=cached_parse)
                        else:
                            try:
                                parser = ResumeParser(api_key)
                                parsed_resume = parser.parse_resume_sync(resume_text)
                                save_cached_resume_parse(resume_text, parsed_resume)
                                update_user_profile(resume_parsed=parsed_resume)
                            except Exception:
                                pass  # Non-critical, still have raw text

                        # Extract name from parsed resume
                        parsed = get_user_profile().get("resume_parsed")
                        if parsed and parsed.get("name"):
                            update_user_profile(name=parsed["name"])

                        st.success(f"✅ Resume uploaded: {uploaded_file.name}")
                    else:
                        st.error("❌ Could not extract text from resume")
                except Exception as e:
                    st.error(f"❌ Error processing resume: {e}")

    elif profile["resume_filename"]:
        resume_name = profile.get("name", "")
        if resume_name:
            st.markdown(f"✅ Resume uploaded! Name: {resume_name}", unsafe_allow_html=True)
        else:
            st.markdown(f"✅ Resume uploaded: {profile['resume_filename']}", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Your Profile Section ────────────────────────────────────────────────
    st.markdown('<div class="dark-card"><h3>📋 Your Profile</h3>', unsafe_allow_html=True)

    name = st.text_input(
        "Name",
        value=get_user_profile()["name"],
        placeholder="Enter your full name",
        key="profile_name"
    )
    if name and name != get_user_profile()["name"]:
        update_user_profile(name=name)

    degree = st.selectbox(
        "Highest Education Level",
        options=DEGREE_OPTIONS,
        index=DEGREE_OPTIONS.index(get_user_profile()["degree"]) if get_user_profile()["degree"] in DEGREE_OPTIONS else 0,
        key="profile_degree"
    )
    if degree:
        update_user_profile(degree=degree)

    interests = st.multiselect(
        "Areas of Interest",
        options=AREAS_OF_INTEREST,
        default=get_user_profile()["interests"],
        help="Select all that apply",
        key="profile_interests"
    )
    if interests != get_user_profile()["interests"]:
        update_user_profile(interests=interests)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Job Search Inputs ───────────────────────────────────────────────────
    st.markdown('<div class="dark-card">', unsafe_allow_html=True)

    job_title = st.text_input(
        "Job Title",
        value=st.session_state.get("search_job_title", ""),
        placeholder="e.g. Backend Developer",
        key="search_job_title"
    )

    location = st.text_input(
        "Location",
        value=st.session_state.get("search_location", ""),
        placeholder="e.g. Phoenix, Arizona",
        key="search_location"
    )

    # Sliders side-by-side
    col_score, col_jobs = st.columns(2)
    with col_score:
        min_score = st.slider(
            "Min Score",
            min_value=0,
            max_value=100,
            value=st.session_state.get("min_score_val", 60),
            step=5,
            key="min_score_val"
        )
    with col_jobs:
        max_jobs = st.slider(
            "Max Jobs",
            min_value=1,
            max_value=20,
            value=st.session_state.get("max_jobs_val", 5),
            step=1,
            key="max_jobs_val"
        )

    # Search button
    search_clicked = st.button("🔍 Search & Analyze Jobs", type="primary")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Handle Search ───────────────────────────────────────────────────────
    if search_clicked:
        # Need resume to be uploaded
        current_profile = get_user_profile()
        if not current_profile["resume_text"]:
            st.warning("⚠️ Please upload your resume first before searching for jobs.")
        else:
            # Auto-fill profile fields if not set (for the matching engine)
            if not current_profile["name"]:
                update_user_profile(name="User")
            if not current_profile["degree"]:
                update_user_profile(degree=DEGREE_OPTIONS[0])
            if not current_profile["interests"]:
                update_user_profile(interests=[AREAS_OF_INTEREST[0]])

            from rag import JobMatcher
            from scrapers import ScraperRegistry
            from config import ARIZONA_CITIES
            import concurrent.futures

            available_cities = ScraperRegistry.get_supported_cities()
            selected_cities = available_cities

            # Create progress tracking
            progress_bar = st.progress(0)
            status_container = st.empty()
            status_container.info("⏳ Searching for matching jobs...")

            try:
                matcher = JobMatcher(api_key)

                # Capture profile before entering thread
                user_profile = get_user_profile()

                # Capture force_refresh flag
                force_refresh = st.session_state.get('force_refresh', False)
                st.session_state.force_refresh = False

                def thread_safe_progress(message: str):
                    print(f"[JobMatcher] {message}")

                def run_async_match():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(
                            matcher.match_jobs_to_profile(
                                profile=user_profile,
                                cities=selected_cities,
                                progress_callback=thread_safe_progress,
                                force_refresh=force_refresh
                            )
                        )
                    finally:
                        loop.close()

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    matched_jobs = pool.submit(run_async_match).result()

                # Store results
                from utils import store_matched_jobs
                store_matched_jobs(matched_jobs)

                progress_bar.progress(1.0)
                status_container.success(f"✅ Found {len(matched_jobs)} jobs!")

                st.rerun()

            except Exception as e:
                import traceback
                status_container.error(f"❌ Error: {e}")
                with st.expander("🔍 Error Details"):
                    st.code(traceback.format_exc())

    # ── Display Results ─────────────────────────────────────────────────────
    if st.session_state.matched_jobs:
        from utils import get_matched_jobs

        # Apply filters
        filtered_jobs = get_matched_jobs(min_score=min_score, limit=max_jobs)

        st.markdown(
            f'<div class="results-header">Results ({len(filtered_jobs)} jobs analyzed)</div>',
            unsafe_allow_html=True
        )

        if len(filtered_jobs) == 0:
            st.info("No jobs match your current filters. Try lowering the minimum score.")
        else:
            for i, job in enumerate(filtered_jobs):
                # Check if tailoring advice has been generated
                advice_key = f"advice_{job.get('job_id', '')}"
                has_tailoring = advice_key in st.session_state

                # Render card HTML
                st.markdown(
                    render_job_card_html(job, has_tailoring=has_tailoring),
                    unsafe_allow_html=True
                )

                # Action buttons under each card
                btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 1])
                with btn_col1:
                    if job.get('url'):
                        st.link_button("🔗 Apply Now", job['url'], use_container_width=True)
                with btn_col2:
                    tailor_key = f"show_advice_{i}"
                    if tailor_key not in st.session_state:
                        st.session_state[tailor_key] = False

                    if st.button("💡 Get Tailoring Advice", key=f"btn_advice_{i}", use_container_width=True):
                        st.session_state[tailor_key] = not st.session_state[tailor_key]
                        st.rerun()
                with btn_col3:
                    if st.button("🗑️", key=f"btn_clear_{i}", help="Dismiss"):
                        pass

                # Show tailoring advice if toggled
                if st.session_state.get(f"show_advice_{i}", False):
                    display_tailoring_advice(job, api_key)

                st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)


def display_tailoring_advice(job: Dict, api_key: str):
    """Display personalized tailoring advice for a job."""

    advice_cache_key = f"advice_{job.get('job_id', '')}"

    # Check cache
    if advice_cache_key not in st.session_state:
        with st.spinner("🤖 Generating personalized advice..."):
            try:
                from rag import TailoringAdvisor
                from utils import get_user_profile

                advisor = TailoringAdvisor(api_key)
                advice = advisor.generate_advice(job, get_user_profile())
                st.session_state[advice_cache_key] = advice
            except Exception as e:
                st.error(f"Error generating advice: {e}")
                return

    advice = st.session_state[advice_cache_key]

    # Display advice in a styled container
    st.markdown("---")
    st.markdown("### 💡 Personalized Resume Tailoring Advice")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**✅ Your Strengths:**")
        if advice.get("strengths"):
            for strength in advice["strengths"]:
                st.markdown(f"- {strength}")
        else:
            st.info("No specific strengths identified")

        st.markdown("**🔑 Keywords to Add:**")
        if advice.get("keywords"):
            keywords_html = " ".join([
                f'<span style="background-color: rgba(56, 139, 253, 0.15); color: #58a6ff; '
                f'padding: 4px 12px; border-radius: 12px; margin: 4px; display: inline-block; '
                f'border: 1px solid rgba(56, 139, 253, 0.3);">{kw}</span>'
                for kw in advice["keywords"]
            ])
            st.markdown(keywords_html, unsafe_allow_html=True)
        else:
            st.info("No keywords suggested")

    with col2:
        st.markdown("**⚠️ Skill Gaps to Address:**")
        if advice.get("skill_gaps"):
            for gap in advice["skill_gaps"]:
                st.markdown(f"- {gap}")
        else:
            st.success("No major skill gaps!")

        st.markdown("**📈 Resume Improvements:**")
        if advice.get("improvements"):
            for improvement in advice["improvements"]:
                st.markdown(f"- {improvement}")
        else:
            st.info("No specific improvements suggested")


if __name__ == "__main__":
    main()
