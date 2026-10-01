from datetime import datetime

from storage import LocalJsonJobStore
from storage import job_store


def _job(job_id, city="Tempe"):
    return {
        "job_id": job_id,
        "title": "Analyst",
        "city": city,
        "url": f"https://example.gov/jobs/{job_id}",
    }


def test_local_store_replaces_and_reads_city_snapshot(tmp_path):
    store = LocalJsonJobStore(str(tmp_path))

    store.replace_city_jobs("Tempe", [_job("one"), _job("two")])
    snapshot = store.get_city_snapshot("Tempe")

    assert snapshot is not None
    assert snapshot.city == "Tempe"
    assert isinstance(snapshot.refreshed_at, datetime)
    assert len(snapshot.jobs) == 2
    assert all(job["job_id"].startswith("job_") for job in snapshot.jobs)


def test_local_store_lists_and_clears_snapshots(tmp_path):
    store = LocalJsonJobStore(str(tmp_path))
    store.replace_city_jobs("Tempe", [_job("one")])
    store.replace_city_jobs("Phoenix", [_job("two", city="Phoenix")])

    assert {snapshot.city for snapshot in store.list_snapshots()} == {
        "Tempe",
        "Phoenix",
    }

    store.clear("Tempe")
    assert store.get_city_snapshot("Tempe") is None
    assert store.get_city_snapshot("Phoenix") is not None

    store.clear()
    assert store.list_snapshots() == []


def test_store_factory_uses_postgres_when_database_url_is_configured(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(job_store, "DATABASE_URL", "postgresql://example/test")
    monkeypatch.setattr(job_store, "PostgresJobStore", lambda url: (sentinel, url))
    job_store.get_job_store.cache_clear()
    try:
        assert job_store.get_job_store() == (
            sentinel,
            "postgresql://example/test",
        )
    finally:
        job_store.get_job_store.cache_clear()
