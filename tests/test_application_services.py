import asyncio
import threading

from progress_events import SearchProgress
from services import browser_runtime, job_search_service, resume_service
from ui.components import render_job_card_html


def test_resume_service_reuses_successful_session_parse(monkeypatch):
    previous_parse = {"name": "Test Candidate", "skills": ["Python"]}
    monkeypatch.setattr(
        resume_service.ResumeExtractor,
        "extract_text",
        lambda file_bytes, filename: "same resume text",
    )

    class UnexpectedParser:
        def __init__(self, api_key):
            raise AssertionError("A cached parse should not call the API")

    monkeypatch.setattr(resume_service, "ResumeParser", UnexpectedParser)
    result = resume_service.process_resume(
        b"resume",
        "resume.pdf",
        "test-key",
        previous_text="same resume text",
        previous_parse=previous_parse,
    )

    assert result.parsed == previous_parse
    assert result.candidate_name == "Test Candidate"
    assert result.parse_warning is None


def test_resume_service_preserves_text_when_ai_parse_fails(monkeypatch):
    monkeypatch.setattr(
        resume_service.ResumeExtractor,
        "extract_text",
        lambda file_bytes, filename: "extracted resume text",
    )

    class FailingParser:
        def __init__(self, api_key):
            pass

        def parse_resume_sync(self, text):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(resume_service, "ResumeParser", FailingParser)
    result = resume_service.process_resume(b"resume", "resume.pdf", "test-key")

    assert result.text == "extracted resume text"
    assert result.parsed is None
    assert result.parse_warning


def test_job_search_service_owns_worker_event_loop(monkeypatch):
    calls = {}
    callback_threads = []
    caller_thread = threading.get_ident()
    monkeypatch.setattr(job_search_service, "ensure_playwright_browser", lambda: None)

    class FakeMatcher:
        def __init__(self, api_key):
            calls["api_key"] = api_key

        async def match_jobs_to_profile(self, **kwargs):
            calls["loop_running"] = asyncio.get_running_loop().is_running()
            calls["kwargs"] = kwargs
            kwargs["progress_callback"](SearchProgress(
                phase="scraping",
                message="Completed Tempe",
                progress=0.5,
            ))
            return [{"job_id": "test-job"}]

    monkeypatch.setattr(job_search_service, "JobMatcher", FakeMatcher)
    result = job_search_service.run_job_search(
        "test-key",
        {"skills": ["Python"]},
        ["Tempe"],
        job_title="Developer",
        location="Tempe",
        progress_callback=lambda event: callback_threads.append(
            (threading.get_ident(), event.phase)
        ),
    )

    assert result == [{"job_id": "test-job"}]
    assert calls["api_key"] == "test-key"
    assert calls["loop_running"] is True
    assert calls["kwargs"]["job_title"] == "Developer"
    assert callback_threads == [
        (caller_thread, "browser"),
        (caller_thread, "scraping"),
    ]


def test_browser_install_is_skipped_outside_linux(monkeypatch):
    browser_runtime.ensure_playwright_browser.cache_clear()
    monkeypatch.setattr(browser_runtime.sys, "platform", "win32")
    monkeypatch.setattr(
        browser_runtime.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Browser installation should not run")
        ),
    )

    browser_runtime.ensure_playwright_browser()
    browser_runtime.ensure_playwright_browser.cache_clear()


def test_job_card_escapes_untrusted_scraped_fields():
    html = render_job_card_html(
        {
            "title": "<script>alert(1)</script>",
            "city": "<b>Tempe</b>",
            "location": "Downtown & Rural",
            "match_score": "61.4",
        }
    )

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;Tempe&lt;/b&gt;" in html
    assert "Downtown &amp; Rural" in html
    assert "61/100" in html
