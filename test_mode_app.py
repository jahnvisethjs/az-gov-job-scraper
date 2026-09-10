"""
Test Mode Streamlit App - ASU AI Resume Parser Demo
Shows what ASU AI extracts from resumes without embeddings/job matching.
"""
# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from pathlib import Path
import json
from utils.pdf_extractor import ResumeExtractor
from rag.resume_parser import ResumeParser
import asyncio

st.set_page_config(
    page_title="ASU AI Resume Parser - Test Mode",
    page_icon="🔬",
    layout="wide"
)

# Title
st.title("🔬 ASU AI Resume Parser - Test Mode")
st.markdown("**Test ASU AI GPT-4o resume parsing without embeddings**")
st.divider()

# Sidebar instructions
with st.sidebar:
    st.header("📋 Instructions")
    st.markdown("""
    1. Upload your resume (PDF or DOCX)
    2. Click "Parse Resume with ASU AI"
    3. View extracted data below
    
    **Note:** This test mode only uses ASU AI for parsing.
    No embeddings or job matching (avoids Gemini quota).
    """)
    
    st.divider()
    st.markdown("**Status:**")
    st.success("✅ ASU AI GPT-4o Ready")
    st.info("ℹ️ Gemini Embeddings Disabled (test mode)")

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📤 Upload Resume")
    
    uploaded_file = st.file_uploader(
        "Choose a resume file",
        type=["pdf", "docx", "txt"],
        help="Upload PDF, DOCX, or TXT resume"
    )
    
    if uploaded_file:
        st.success(f"✅ Loaded: {uploaded_file.name}")
        st.caption(f"Size: {len(uploaded_file.getvalue()) / 1024:.1f} KB")
        
        # Parse button
        if st.button("🚀 Parse Resume with ASU AI", type="primary", use_container_width=True):
            with st.spinner("🤖 ASU AI GPT-4o is parsing your resume..."):
                try:
                    # Extract text
                    resume_bytes = uploaded_file.getvalue()
                    resume_text = ResumeExtractor.extract_text(resume_bytes, uploaded_file.name)
                    
                    st.session_state.resume_text = resume_text
                    st.session_state.resume_filename = uploaded_file.name
                    
                    # Parse with ASU AI
                    parser = ResumeParser()
                    parsed_data = asyncio.run(parser.parse_resume(resume_text))
                    
                    st.session_state.parsed_data = parsed_data
                    st.session_state.parsing_complete = True
                    
                    st.success("✅ Parsing complete!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.exception(e)

with col2:
    st.header("📊 Extracted Text Preview")
    
    if 'resume_text' in st.session_state:
        with st.expander("👁️ View Raw Resume Text", expanded=False):
            st.text_area(
                "Resume Text",
                st.session_state.resume_text,
                height=300,
                disabled=True
            )
            st.caption(f"Total characters: {len(st.session_state.resume_text)}")
    else:
        st.info("Upload and parse a resume to see the extracted text")

# Results section
if 'parsing_complete' in st.session_state and st.session_state.parsing_complete:
    st.divider()
    st.header("🎯 ASU AI Parsing Results")
    
    parsed = st.session_state.parsed_data
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Summary", 
        "💡 Skills", 
        "💼 Experience", 
        "🎓 Education", 
        "🚀 Projects",
        "📜 Raw JSON"
    ])
    
    with tab1:
        st.subheader("Resume Summary")
        if parsed.get('summary'):
            st.info(parsed['summary'])
        else:
            st.warning("No summary extracted")
    
    with tab2:
        st.subheader("Skills Extracted")
        skills = parsed.get('skills', [])
        if skills:
            st.success(f"Found {len(skills)} skills")
            
            # Display as tags
            cols = st.columns(3)
            for i, skill in enumerate(skills):
                with cols[i % 3]:
                    st.markdown(f"`{skill}`")
        else:
            st.warning("No skills extracted")
    
    with tab3:
        st.subheader("Work Experience")
        experience = parsed.get('experience', [])
        if experience:
            st.success(f"Found {len(experience)} experience entries")
            
            for i, exp in enumerate(experience):
                with st.expander(f"**{exp.get('title', 'Position')}** at {exp.get('company', 'Company')}", expanded=True):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**Duration:** {exp.get('duration', 'N/A')}")
                    with col_b:
                        st.markdown(f"**Location:** {exp.get('location', 'N/A')}")
                    
                    if exp.get('description'):
                        st.markdown("**Description:**")
                        st.write(exp['description'])
        else:
            st.warning("No experience extracted")
    
    with tab4:
        st.subheader("Education")
        education = parsed.get('education', [])
        if education:
            st.success(f"Found {len(education)} education entries")
            
            for edu in education:
                with st.expander(f"**{edu.get('degree', 'Degree')}** - {edu.get('institution', 'Institution')}", expanded=True):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**Field:** {edu.get('field', 'N/A')}")
                    with col_b:
                        st.markdown(f"**Year:** {edu.get('year', 'N/A')}")
                    
                    if edu.get('gpa'):
                        st.markdown(f"**GPA:** {edu['gpa']}")
        else:
            st.warning("No education extracted")
    
    with tab5:
        st.subheader("Projects")
        projects = parsed.get('projects', [])
        if projects:
            st.success(f"Found {len(projects)} projects")
            
            for proj in projects:
                with st.expander(f"**{proj.get('name', 'Project')}**", expanded=True):
                    st.markdown(f"**Description:** {proj.get('description', 'N/A')}")
                    
                    if proj.get('technologies'):
                        st.markdown("**Technologies:**")
                        tech_cols = st.columns(4)
                        for i, tech in enumerate(proj['technologies']):
                            with tech_cols[i % 4]:
                                st.markdown(f"`{tech}`")
                    
                    if proj.get('url'):
                        st.markdown(f"**URL:** {proj['url']}")
        else:
            st.warning("No projects extracted")
    
    with tab6:
        st.subheader("Raw JSON Data")
        st.json(parsed, expanded=False)
        
        # Download button
        st.download_button(
            label="📥 Download JSON",
            data=json.dumps(parsed, indent=2),
            file_name=f"{st.session_state.resume_filename}_parsed.json",
            mime="application/json"
        )

# Footer
st.divider()
st.caption("🔬 Test Mode: ASU AI GPT-4o | No Embeddings | No Job Matching")
