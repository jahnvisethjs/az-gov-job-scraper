"""
Arizona Government Job Scraper - Streamlit Web Application
Phase 1: Basic UI with resume upload and profile creation
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
    validate_resume_size
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

# Page configuration
st.set_page_config(
    page_title="AZ Gov Jobs - AI Job Matcher",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """Main application function."""
    
    # Initialize session state
    init_session_state()
    
    # Initialize theme in session state
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'
    
    # Header
    st.markdown('<div class="main-header">🏛️ Arizona Government Job Finder</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Job Matching for Arizona Cities & Counties</div>', unsafe_allow_html=True)
    
    # Check for API key
    api_key = os.getenv("ASU_AI_API_KEY") or ASU_AI_API_KEY
    if not api_key:
        st.error("⚠️ **ASU AI API Key not found!**")
        st.info("Please create a `.env` file with your `ASU_AI_API_KEY` or set it in `config.py`")
        st.code("ASU_AI_API_KEY=your_api_key_here", language="bash")
        st.markdown("[Contact Ayat Sweid or Paul Alvarado for ASU AI API access](https://platform.aiml.asu.edu)")
        st.stop()
    
    # Apply dynamic CSS based on theme
    if st.session_state.theme == 'dark':
        st.markdown("""
        <style>
            /* Dark Theme */
            .stApp {
                background-color: #0E1117;
                color: #FAFAFA;
            }
            .main-header {
                font-size: 3rem;
                font-weight: 900;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-align: center;
                margin-bottom: 0.5rem;
                padding: 1rem 0;
            }
            .sub-header {
                font-size: 1.3rem;
                color: #B0B0B0;
                text-align: center;
                margin-bottom: 2rem;
                font-weight: 500;
            }
            .hero-section {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 3rem 2rem;
                border-radius: 16px;
                color: white;
                text-align: center;
                margin: 2rem 0;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            }
            .hero-title {
                font-size: 2.5rem;
                font-weight: bold;
                margin-bottom: 1rem;
            }
            .hero-subtitle {
                font-size: 1.2rem;
                opacity: 0.9;
            }
            .feature-card {
                background: #1E1E1E;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                border-left: 4px solid #667eea;
                margin: 1rem 0;
                transition: transform 0.2s;
                color: #FAFAFA;
            }
            .feature-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 8px 12px rgba(102, 126, 234, 0.4);
            }
            .feature-icon {
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }
            .stButton>button {
                width: 100%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 0.75rem 1.5rem;
                border: none;
                font-size: 1.1rem;
                transition: all 0.3s;
            }
            .stButton>button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
            }
            .stat-card {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                padding: 1.5rem;
                border-radius: 12px;
                color: white;
                text-align: center;
                margin: 0.5rem 0;
            }
            .stat-number {
                font-size: 2.5rem;
                font-weight: bold;
            }
            .stat-label {
                font-size: 0.9rem;
                opacity: 0.9;
            }
        </style>
        """, unsafe_allow_html=True)
    else:  # Light theme
        st.markdown("""
        <style>
            /* Light Theme */
            .stApp {
                background-color: #FFFFFF;
                color: #262730;
            }
            .main-header {
                font-size: 3rem;
                font-weight: 900;
                background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-align: center;
                margin-bottom: 0.5rem;
                padding: 1rem 0;
            }
            .sub-header {
                font-size: 1.3rem;
                color: #4B5563;
                text-align: center;
                margin-bottom: 2rem;
                font-weight: 500;
            }
            .hero-section {
                background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
                padding: 3rem 2rem;
                border-radius: 16px;
                color: white;
                text-align: center;
                margin: 2rem 0;
                box-shadow: 0 10px 30px rgba(79, 70, 229, 0.2);
            }
            .hero-title {
                font-size: 2.5rem;
                font-weight: bold;
                margin-bottom: 1rem;
            }
            .hero-subtitle {
                font-size: 1.2rem;
                opacity: 0.95;
            }
            .feature-card {
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border-left: 4px solid #4F46E5;
                margin: 1rem 0;
                transition: transform 0.2s;
                color: #1F2937;
            }
            .feature-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
            }
            .feature-icon {
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }
            .stButton>button {
                width: 100%;
                background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 0.75rem 1.5rem;
                border: none;
                font-size: 1.1rem;
                transition: all 0.3s;
            }
            .stButton>button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 16px rgba(79, 70, 229, 0.3);
            }
            .stat-card {
                background: linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%);
                padding: 1.5rem;
                border-radius: 12px;
                color: white;
                text-align: center;
                margin: 0.5rem 0;
            }
            .stat-number {
                font-size: 2.5rem;
                font-weight: bold;
            }
            .stat-label {
                font-size: 0.9rem;
                opacity: 0.95;
            }
        </style>
        """, unsafe_allow_html=True)
    
    # Sidebar: User Profile Input
    with st.sidebar:
        # Theme toggle at the top
        st.markdown("### 🎨 Theme")
        theme_col1, theme_col2 = st.columns(2)
        with theme_col1:
            if st.button("🌙 Dark", use_container_width=True, type="primary" if st.session_state.theme == 'dark' else "secondary"):
                st.session_state.theme = 'dark'
                st.rerun()
        with theme_col2:
            if st.button("☀️ Light", use_container_width=True, type="primary" if st.session_state.theme == 'light' else "secondary"):
                st.session_state.theme = 'light'
                st.rerun()
        
        st.markdown("---")
        
        st.header("📋 Your Profile")
        st.markdown("---")
        
        # Name input
        name = st.text_input(
            "Name",
            value=get_user_profile()["name"],
            placeholder="Enter your full name"
        )
        
        # Education
        degree = st.selectbox(
            "Highest Education Level",
            options=DEGREE_OPTIONS,
            index=DEGREE_OPTIONS.index(get_user_profile()["degree"]) if get_user_profile()["degree"] else 0
        )
        
        # Areas of interest
        interests = st.multiselect(
            "Areas of Interest",
            options=AREAS_OF_INTEREST,
            default=get_user_profile()["interests"],
            help="Select all that apply"
        )
        
        st.markdown("---")
        st.subheader("📄 Resume Upload")
        
        # Resume upload
        uploaded_file = st.file_uploader(
            "Upload your resume",
            type=[fmt.replace(".", "") for fmt in SUPPORTED_RESUME_FORMATS],
            help=f"Supported formats: {', '.join(SUPPORTED_RESUME_FORMATS)} (Max {MAX_RESUME_SIZE_MB}MB)"
        )
        
        # Process resume if uploaded
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            
            # Validate size
            if not validate_resume_size(file_bytes, MAX_RESUME_SIZE_MB):
                st.error(f"❌ File too large! Maximum size is {MAX_RESUME_SIZE_MB}MB")
            else:
                # Extract text
                with st.spinner("📖 Extracting text from resume..."):
                    try:
                        resume_text = ResumeExtractor.extract_text(file_bytes, uploaded_file.name)
                        
                        if resume_text:
                            # Store in session
                            update_user_profile(
                                resume_text=resume_text,
                                resume_filename=uploaded_file.name
                            )
                            st.success(f"✅ Resume uploaded: {uploaded_file.name}")
                        else:
                            st.error("❌ Could not extract text from resume")
                    except Exception as e:
                        st.error(f"❌ Error processing resume: {e}")
        
        # Show current resume if uploaded
        elif get_user_profile()["resume_filename"]:
            st.info(f"📄 Current resume: {get_user_profile()['resume_filename']}")
        
        st.markdown("---")
        
        # Save profile button
        if st.button("💾 Save Profile", type="primary"):
            if not name:
                st.warning("⚠️ Please enter your name")
            elif not degree:
                st.warning("⚠️ Please select your education level")
            elif not interests:
                st.warning("⚠️ Please select at least one area of interest")
            elif not get_user_profile()["resume_text"]:
                st.warning("⚠️ Please upload your resume")
            else:
                # Update profile
                update_user_profile(
                    name=name,
                    degree=degree,
                    interests=interests
                )
                
                # Parse resume with AI
                with st.spinner("🤖 Analyzing your resume with AI..."):
                    try:
                        parser = ResumeParser(api_key)
                        parsed_resume = parser.parse_resume_sync(get_user_profile()["resume_text"])
                        
                        update_user_profile(resume_parsed=parsed_resume)
                        
                        st.success("✅ Profile saved successfully!")
                    except Exception as e:
                        st.error(f"❌ Error parsing resume: {e}")
        
        # Clear session button
        if st.button("🗑️ Clear Session"):
            from utils import clear_session
            clear_session()
            st.rerun()
    
    # Main content area
    if not is_profile_complete():
        # Hero Section
        st.markdown("""
        <div class="hero-section">
            <div class="hero-title">🏛️ Find Your Perfect Government Job</div>
            <div class="hero-subtitle">AI-powered job matching across 15 Arizona cities • Personalized resume insights • Free to use</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick stats
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-number">15+</div>
                <div class="stat-label">Arizona Cities</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-number">AI</div>
                <div class="stat-label">Powered Matching</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.info("👈 **Get Started:** Complete your profile in the sidebar to begin finding your dream job!")
    
    else:
        # Profile is complete - show profile summary
        profile = get_user_profile()
        
        st.success("✅ **Profile Complete!** Ready to find matching jobs.")
        
        # Job scraping and matching (Phase 3)
        st.markdown("### 🔍 Find Matching Jobs")
        
        # City selection - automatically search all cities
        from config import ARIZONA_CITIES
        from scrapers import ScraperRegistry
        
        available_cities = ScraperRegistry.get_supported_cities()
        selected_cities = available_cities  # Search all cities by default
        
        # Show info about cities being searched
        st.info(f"🔍 Searching {len(selected_cities)} Arizona cities: {', '.join(selected_cities[:5])}{'...' if len(selected_cities) > 5 else ''}")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            find_jobs_btn = st.button("🚀 Find Matching Jobs", type="primary", disabled=not selected_cities)
        
        with col2:
            if st.session_state.matched_jobs:
                if st.button("🗑️ Clear Results"):
                    st.session_state.matched_jobs = []
                    st.session_state.scraped_jobs = []
                    st.rerun()
        
        # Process job search
        if find_jobs_btn and selected_cities:
            from rag import JobMatcher
            import asyncio
            
            # Create progress container
            progress_container = st.empty()
            status_container = st.empty()
            
            def update_progress(message: str):
                status_container.info(f"⏳ {message}")
            
            try:
                # Create detailed progress tracking
                progress_bar = st.progress(0)
                status_container.info("⏳ Starting job search...")
                
                def update_progress(message: str):
                    status_container.info(f"⏳ {message}")
                    # Log to console as well for debugging
                    print(f"[JobMatcher] {message}")
                
                
                # Initialize job matcher
                matcher = JobMatcher(api_key)
                
                # Run matching workflow with proper async handling for Streamlit
                import nest_asyncio
                nest_asyncio.apply()
                
                # Use ThreadPoolExecutor to run async code in Streamlit
                import concurrent.futures
                import asyncio
                
                # IMPORTANT: Capture profile BEFORE entering thread (session state not accessible in threads)
                user_profile = get_user_profile()
                
                # Create thread-safe progress callback (can't update Streamlit UI from thread)
                def thread_safe_progress(message: str):
                    # Only log to console, can't update Streamlit UI from thread
                    print(f"[JobMatcher] {message}")
                
                def run_async_match():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(
                            matcher.match_jobs_to_profile(
                                profile=user_profile,  # Use captured profile
                                cities=selected_cities,
                                progress_callback=thread_safe_progress  # Thread-safe callback
                            )
                        )
                    finally:
                        loop.close()
                
                # Show a simple progress message
                status_container.info("⏳ Searching for matching jobs... (check terminal for progress)")
                
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    matched_jobs = pool.submit(run_async_match).result()
                
                # Store results
                from utils import store_matched_jobs
                store_matched_jobs(matched_jobs)
                
                progress_bar.progress(1.0)
                status_container.success(f"✅ Found {len(matched_jobs)} total jobs from all cities!")
                
                # Show breakdown by city if available
                if len(matched_jobs) > 0:
                    st.info(f"💼 Jobs will be displayed below. Use the filter to adjust minimum match score.")
                else:
                    st.warning("⚠️ No jobs found. This could mean:")
                    st.write("- Some cities may have no current openings")
                    st.write("- Website structures may have changed (scraper needs update)")
                    st.write("- Check the console/terminal for detailed scraping logs")
                
                st.rerun()
                    
            except Exception as e:
                import traceback
                status_container.error(f"❌ Error finding jobs: {e}")
                # Show detailed traceback in expander
                with st.expander("🔍 Error Details"):
                    st.code(traceback.format_exc())
        
        # Display matched jobs
        if st.session_state.matched_jobs:
            from utils import get_matched_jobs
            
            st.markdown("---")
            st.markdown(f"### 💼 Matched Jobs ({len(st.session_state.matched_jobs)} total)")
            
            # Display filter
            st.markdown("**Filter Jobs by Match Score:**")
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                min_score_filter = st.slider(
                    "Minimum match score (%)",
                    min_value=0,
                    max_value=100,
                    value=0,  # Changed to 0 to show ALL jobs by default
                    step=5,
                    help="Filter jobs by minimum match score. Set to 0 to see all jobs."
                )
            
            filtered_jobs = get_matched_jobs(min_score=min_score_filter, limit=50)
            
            with col2:
                st.metric("Showing", f"{len(filtered_jobs)} jobs")
            
            # Display job cards
            for i, job in enumerate(filtered_jobs):
                display_job_card(job, i, api_key)
        



def display_job_card(job: Dict, index: int, api_key: str):
    """Display a single job card with match score and tailoring advice."""
    
    # Determine score color
    score = job.get("match_score", 0)
    if score >= 80:
        score_color = "#4CAF50"  # Green
        badge_text = "Strong Match"
    elif score >= 60:
        score_color = "#FF9800"  # Orange
        badge_text = "Good Match"
    else:
        score_color = "#F44336"  # Red
        badge_text = "Fair Match"
    
    # Create expandable card
    with st.expander(f"**{job.get('title', 'N/A')}** - {badge_text} ({score:.1f}%)", expanded=(index < 3)):
        
        # Score badge
        st.markdown(
            f'<div style="background-color: {score_color}; color: white; padding: 8px 16px; '
            f'border-radius: 20px; display: inline-block; margin-bottom: 10px; font-weight: bold;">'
            f'Match Score: {score:.1f}%</div>',
            unsafe_allow_html=True
        )
        
        # Job details
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**🏛️ City:** {job.get('city', 'N/A')}")
            st.markdown(f"**📍 Location:** {job.get('location', 'N/A')}")
            st.markdown(f"**🏢 Department:** {job.get('department', 'N/A')}")
        
        with col2:
            if job.get('salary'):
                st.markdown(f"**💰 Salary:** {job['salary']}")
            if job.get('closing_date'):
                st.markdown(f"**📅 Closes:** {job['closing_date']}")
            if job.get('job_type'):
                st.markdown(f"**📋 Type:** {job['job_type']}")
        
        # Description
        if job.get('description'):
            st.markdown("**Description:**")
            desc = job['description']
            st.markdown(desc[:300] + "..." if len(desc) > 300 else desc)
        
        # Requirements
        if job.get('requirements'):
            with st.expander("📋 Requirements"):
                st.markdown(job['requirements'])
        
        # Apply button and tailoring advice
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if job.get('url'):
                st.link_button("🔗 Apply Now", job['url'], use_container_width=True)
        
        with col2:
            advice_key = f"show_advice_{index}"
            if advice_key not in st.session_state:
                st.session_state[advice_key] = False
            
            if st.button("💡 Get Tailoring Advice", key=f"btn_advice_{index}", use_container_width=True):
                st.session_state[advice_key] = not st.session_state[advice_key]
                st.rerun()
        
        # Show tailoring advice if requested
        if st.session_state.get(advice_key, False):
            display_tailoring_advice(job, api_key)


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
    
    # Display advice
    st.markdown("---")
    st.markdown("### 💡 Personalized Resume Tailoring Advice")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Strengths
        st.markdown("**✅ Your Strengths:**")
        if advice.get("strengths"):
            for strength in advice["strengths"]:
                st.markdown(f"- {strength}")
        else:
            st.info("No specific strengths identified")
        
        # Keywords to add
        st.markdown("**🔑 Keywords to Add:**")
        if advice.get("keywords"):
            keywords_html = " ".join([
                f'<span style="background-color: #E0E7FF; color: #3730A3; '
                f'padding: 4px 12px; border-radius: 12px; margin: 4px; display: inline-block;">{kw}</span>'
                for kw in advice["keywords"]
            ])
            st.markdown(keywords_html, unsafe_allow_html=True)
        else:
            st.info("No keywords suggested")
    
    with col2:
        # Skill gaps
        st.markdown("**⚠️ Skill Gaps to Address:**")
        if advice.get("skill_gaps"):
            for gap in advice["skill_gaps"]:
                st.markdown(f"- {gap}")
        else:
            st.success("No major skill gaps!")
        
        # Improvements
        st.markdown("**📈 Resume Improvements:**")
        if advice.get("improvements"):
            for improvement in advice["improvements"]:
                st.markdown(f"- {improvement}")
        else:
            st.info("No specific improvements suggested")



if __name__ == "__main__":
    main()
