"""Application stylesheet loader."""

from pathlib import Path

import streamlit as st


STYLESHEET = Path(__file__).resolve().parents[1] / "assets" / "styles.css"


def inject_custom_css() -> None:
    """Load the application stylesheet from the assets directory."""
    css = STYLESHEET.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
