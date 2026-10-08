"""Network-free tests for privacy, invalidation and worker cache sharing."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import Mock

import pytest

from progress_events import SearchCancelled
from rag.resume_embedding_cache import ResumeEmbeddingCache
from rag import rag_engine
from services import job_search_service, background_search
from utils import session_manager

CONFIG = ("https://example.invalid", "provider", "model", 2)


def cached(cache, text="synthetic profile", create=None, configuration=CONFIG, **kwargs):
    return cache.get_or_create(text, configuration=configuration,
                               create=create or (lambda: [0.5, 0.5]), **kwargs)


def test_cache_is_session_scoped_and_returns_copies():
    create = Mock(return_value=[0.5, 0.5])
    first, second = ResumeEmbeddingCache(), ResumeEmbeddingCache()
    value = cached(first, create=create)
    value[0] = 100
    assert cached(first, create=create) == [0.5, 0.5]
    cached(second, create=create)
    assert create.call_count == 2
    assert first._entry[0] != second._entry[0]
    assert "synthetic profile" not in repr(first.__dict__)


@pytest.mark.parametrize("text,configuration", [
    ("changed profile", CONFIG),
    ("synthetic profile", ("https://other.invalid", "provider", "model", 2)),
    ("synthetic profile", (CONFIG[0], "other", "model", 2)),
    ("synthetic profile", (CONFIG[0], "provider", "other", 2)),
    ("synthetic profile", (CONFIG[0], "provider", "model", 3)),
])
def test_input_and_model_changes_invalidate(text, configuration):
    cache = ResumeEmbeddingCache()
    cached(cache)
    create = Mock(return_value=[0.5] * configuration[-1])
    cached(cache, text, create=create, configuration=configuration)
    create.assert_called_once()


@pytest.mark.parametrize("value", [[0, 0], [float("nan"), 1], [float("inf"), 1], [1]])
def test_invalid_embeddings_and_failures_are_not_cached(value):
    cache = ResumeEmbeddingCache()
    with pytest.raises(ValueError):
        cached(cache, create=lambda: value)
    create = Mock(return_value=[0.5, 0.5])
    cached(cache, create=create)
    create.assert_called_once()


def test_provider_failure_can_be_retried():
    cache = ResumeEmbeddingCache()
    with pytest.raises(TimeoutError):
        cached(cache, create=Mock(side_effect=TimeoutError()))
    assert cached(cache) == [0.5, 0.5]


def test_concurrent_identical_requests_generate_once():
    cache = ResumeEmbeddingCache()
    started, finish = Event(), Event()
    def generate():
        started.set()
        assert finish.wait(2)
        return [0.5, 0.5]
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(cached, cache, create=generate)
        assert started.wait(1)
        second = pool.submit(cached, cache, create=lambda: pytest.fail("Duplicate API call"))
        finish.set()
        assert first.result(timeout=2) == second.result(timeout=2) == [0.5, 0.5]


def test_clear_during_request_does_not_wait_or_repopulate_cache():
    cache = ResumeEmbeddingCache()
    started, finish = Event(), Event()
    def generate():
        started.set()
        assert finish.wait(2)
        return [0.5, 0.5]
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(cached, cache, create=generate)
        assert started.wait(1)
        cache.clear()
        finish.set()
        pending.result(timeout=2)
    create = Mock(return_value=[1, 0])
    assert cached(cache, create=create) == [1, 0]
    create.assert_called_once()


def test_cancelled_generation_is_not_cached():
    cache = ResumeEmbeddingCache()
    cancelled = Event()
    def generate():
        cancelled.set()
        return [0.5, 0.5]
    with pytest.raises(SearchCancelled):
        cached(cache, create=generate, cancel_check=cancelled.is_set)
    create = Mock(return_value=[1, 0])
    cached(cache, create=create)
    create.assert_called_once()


def test_waiter_can_cancel_without_cancelling_other_request():
    cache = ResumeEmbeddingCache()
    started, finish = Event(), Event()
    checks = iter([False, True])
    def generate():
        started.set()
        assert finish.wait(2)
        return [0.5, 0.5]
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(cached, cache, create=generate)
        assert started.wait(1)
        try:
            with pytest.raises(SearchCancelled):
                cached(cache, cancel_check=lambda: next(checks))
        finally:
            finish.set()
        assert pending.result(timeout=2) == [0.5, 0.5]
    assert cached(cache) == [0.5, 0.5]


def test_new_rag_instances_reuse_vector_and_search_context_invalidates(monkeypatch):
    monkeypatch.setattr(rag_engine, "ASU_AI_EMBEDDINGS_DIMENSIONS", 2)
    create = Mock(return_value=[0.5, 0.5])
    cache = ResumeEmbeddingCache()
    profile = {"degree": "BSc", "resume_parsed": {"skills": ["Python"]}}
    for context in ("Analyst", "Analyst", "Engineer"):
        engine = rag_engine.JobRAG.__new__(rag_engine.JobRAG)
        engine.generate_embedding_sync = create
        engine.collection = Mock()
        engine.collection.query.return_value = {"metadatas": [[{"title": "Python Analyst"}]], "distances": [[0.2]]}
        matches = engine.search_jobs({**profile, "target_job_title": context}, resume_embedding_cache=cache)
        assert matches[0][1] == pytest.approx(86)
        assert engine.collection.query.call_args.kwargs["query_embeddings"] == [[0.5, 0.5]]
    assert create.call_count == 2


def test_cache_reaches_foreground_and_background_matcher(monkeypatch):
    cache = ResumeEmbeddingCache()
    seen = []
    class Matcher:
        def __init__(self, api_key):
            pass
        async def match_jobs_to_profile(self, **kwargs):
            seen.append(kwargs["resume_embedding_cache"])
            return []
    monkeypatch.setattr(job_search_service, "JobMatcher", Matcher)
    job_search_service.run_job_search("key", {}, [], resume_embedding_cache=cache, cached_only=True)
    manager = background_search.BackgroundSearchManager(max_workers=1)
    done = Event()
    original = manager._run
    def run(*args):
        try:
            return original(*args)
        finally:
            done.set()
    monkeypatch.setattr(manager, "_run", run)
    task = manager.start(api_key="key", profile={}, cities=[], resume_embedding_cache=cache)
    assert done.wait(2)
    assert manager.snapshot(task).state == "complete"
    assert seen == [cache, cache]
    manager.remove(task)
    manager._executor.shutdown()


class State(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def test_profile_change_and_session_reset_clear_vectors(monkeypatch):
    state = State()
    monkeypatch.setattr(session_manager.st, "session_state", state)
    session_manager.init_session_state()
    cache = state.resume_embedding_cache
    create = Mock(return_value=[0.5, 0.5])
    cached(cache, create=create)
    session_manager.update_user_profile(resume_text="new synthetic resume")
    cached(cache, create=create)
    session_manager.update_user_profile(resume_text="new synthetic resume")
    cached(cache, create=create)
    assert create.call_count == 2
    session_manager.clear_session()
    assert state.resume_embedding_cache is not cache
    assert cache._entry is None

def test_ui_shares_session_cache_with_both_search_passes(monkeypatch):
    from contextlib import nullcontext
    from ui import sections

    state = State()
    monkeypatch.setattr(session_manager.st, "session_state", state)
    session_manager.init_session_state()
    session_manager.update_user_profile(resume_text="synthetic resume", resume_parsed={})
    run = Mock(return_value=[])
    manager = Mock()
    manager.start.return_value = "background-task"
    monkeypatch.setattr(sections, "run_job_search", run)
    monkeypatch.setattr(sections, "get_background_search_manager", lambda: manager)
    monkeypatch.setattr(sections.st, "spinner", lambda *args: nullcontext())
    monkeypatch.setattr(sections.st, "rerun", lambda: None)

    sections.execute_search("test-key", "Analyst", "Tempe")

    assert run.call_args.kwargs["cached_only"] is True
    assert run.call_args.kwargs["resume_embedding_cache"] is state.resume_embedding_cache
    assert manager.start.call_args.kwargs["resume_embedding_cache"] is state.resume_embedding_cache
    assert state.search_task_id == "background-task"
