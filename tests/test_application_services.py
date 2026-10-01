import asyncio
import threading
import time

from progress_events import (
    SearchPartialResult,
    SearchProgress,
    raise_if_cancelled,
)
from services import background_search, job_search_service, resume_service
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
        ["Phoenix"],
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
    assert callback_threads == [(caller_thread, "scraping")]


def test_background_search_manager_records_progress_and_result(monkeypatch):
    event = SearchProgress("complete", "Finished", 1.0, jobs_found=1)

    def fake_search(progress_callback, **kwargs):
        progress_callback(event)
        return [{"job_id": "one"}]

    monkeypatch.setattr(background_search, "run_job_search", fake_search)
    manager = background_search.BackgroundSearchManager(max_workers=1)
    task_id = manager.start(api_key="test-key", profile={}, cities=[])

    deadline = time.monotonic() + 2
    snapshot = manager.snapshot(task_id)
    while snapshot.state == "running" and time.monotonic() < deadline:
        time.sleep(0.01)
        snapshot = manager.snapshot(task_id)

    assert snapshot.state == "complete"
    assert snapshot.latest == event
    assert manager.take_result(task_id) == [{"job_id": "one"}]
    assert manager.snapshot(task_id) is None


def test_job_search_service_relays_partial_results_on_caller_thread(monkeypatch):
    caller_thread = threading.get_ident()
    received = []

    class FakeMatcher:
        def __init__(self, api_key):
            pass

        async def match_jobs_to_profile(self, **kwargs):
            kwargs["partial_results_callback"](SearchPartialResult(
                city="Tempe",
                jobs=({"job_id": "one", "title": "Analyst"},),
                completed_cities=1,
                total_cities=1,
            ))
            return []

    monkeypatch.setattr(job_search_service, "JobMatcher", FakeMatcher)
    result = job_search_service.run_job_search(
        "test-key",
        {},
        ["Tempe"],
        partial_results_callback=lambda partial: received.append(
            (threading.get_ident(), partial.city)
        ),
    )

    assert result == []
    assert received == [(caller_thread, "Tempe")]


def test_background_search_manager_cancels_cooperatively(monkeypatch):
    started = threading.Event()

    def cancellable_search(cancel_check, **kwargs):
        started.set()
        while True:
            raise_if_cancelled(cancel_check)
            time.sleep(0.01)

    monkeypatch.setattr(background_search, "run_job_search", cancellable_search)
    manager = background_search.BackgroundSearchManager(max_workers=1)
    task_id = manager.start(api_key="test-key", profile={}, cities=[])
    assert started.wait(timeout=1)
    assert manager.cancel(task_id) is True

    deadline = time.monotonic() + 2
    snapshot = manager.snapshot(task_id)
    while snapshot.state != "cancelled" and time.monotonic() < deadline:
        time.sleep(0.01)
        snapshot = manager.snapshot(task_id)

    assert snapshot.state == "cancelled"
    assert manager.cancel(task_id) is False


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
