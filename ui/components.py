"""Reusable rendering helpers for job results and tailoring advice."""

from html import escape
from typing import Dict

import streamlit as st


def render_job_card_html(job: Dict, has_tailoring: bool = False) -> str:
    """Return escaped HTML for a single job result card."""
    title = escape(str(job.get("title") or "Untitled"))
    company = escape(str(job.get("city") or job.get("department") or ""))
    location = escape(str(job.get("location") or job.get("city") or ""))

    try:
        score = float(job.get("match_score", 0))
    except (TypeError, ValueError):
        score = 0.0

    if score >= 60:
        badge_class = "score-high"
    elif score >= 40:
        badge_class = "score-med"
    else:
        badge_class = "score-low"

    status_html = ""
    if has_tailoring:
        status_html = (
            '<div><span class="status-badge status-tailored">'
            "✅ Resume Tailored</span></div>"
        )

    return f"""
    <div class="job-card">
        <div>
            <span class="job-card-title">{title}</span>
            <span class="score-badge {badge_class}">{int(round(score))}/100</span>
        </div>
        <div class="job-company">{company}</div>
        <div class="job-location"><span class="pin">📍</span> {location}</div>
        {status_html}
    </div>
    """


def render_tailoring_advice(advice: Dict) -> None:
    """Render previously generated tailoring advice."""
    st.markdown("---")
    st.markdown("### 💡 Personalized Resume Tailoring Advice")

    left_column, right_column = st.columns(2)
    with left_column:
        st.markdown("**✅ Your Strengths:**")
        if advice.get("strengths"):
            for strength in advice["strengths"]:
                st.markdown(f"- {strength}")
        else:
            st.info("No specific strengths identified")

        st.markdown("**🔑 Keywords to Add:**")
        if advice.get("keywords"):
            keywords_html = " ".join(
                '<span class="keyword-badge">{}</span>'.format(escape(str(keyword)))
                for keyword in advice["keywords"]
            )
            st.markdown(keywords_html, unsafe_allow_html=True)
        else:
            st.info("No keywords suggested")

    with right_column:
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
