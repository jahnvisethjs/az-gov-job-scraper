"""Playwright browser provisioning outside the Streamlit import path."""

from functools import lru_cache
import subprocess
import sys

from config import PLAYWRIGHT_SKIP_BROWSER_INSTALL


@lru_cache(maxsize=1)
def ensure_playwright_browser() -> None:
    """Install Chromium once per Linux process when deployment requires it.

    Local development and non-Linux environments use the browser installed by
    the documented ``playwright install chromium`` setup step. Setting
    ``PLAYWRIGHT_SKIP_BROWSER_INSTALL=true`` disables deployment provisioning.
    """
    if not sys.platform.startswith("linux"):
        return

    if PLAYWRIGHT_SKIP_BROWSER_INSTALL:
        return

    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
        capture_output=True,
        text=True,
    )
