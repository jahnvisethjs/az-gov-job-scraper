"""Tests for stable job identity across cache, session, and UI workflows."""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from job_identity import (
    canonicalize_job_url,
    deduplicate_jobs,
    ensure_job_id,
    stable_job_id,
)
from utils import job_cache, session_manager


def job(url, city="Tempe", title="Analyst", score=80):
    return {
        "title": title,
        "city": city,
        "url": url,
        "match_score": score,
        "raw_data": {"platform": "NeoGov"},
    }


class SessionState(dict):
    """Small attribute-access dictionary matching Streamlit session state."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


class JobIdentityTests(unittest.TestCase):
    def test_id_is_stable_across_tracking_url_variants(self):
        first = job(
            "https://www.governmentjobs.com/careers/tempe/jobs/123/analyst"
            "?utm_source=email#details"
        )
        second = job(
            "HTTPS://WWW.GOVERNMENTJOBS.COM/careers/tempe/jobs/123/analyst/"
        )

        self.assertEqual(stable_job_id(first), stable_job_id(second))
        self.assertEqual(ensure_job_id(first), ensure_job_id(second))
        self.assertRegex(first["job_id"], r"^job_[0-9a-f]{24}$")

    def test_same_title_at_different_urls_has_different_ids(self):
        first = job("https://example.gov/jobs/100", title="Police Officer")
        second = job("https://example.gov/jobs/200", title="Police Officer")

        self.assertNotEqual(stable_job_id(first), stable_job_id(second))

    def test_url_less_fallback_id_is_idempotent(self):
        record = job("", title="Seasonal Intern")
        first_id = ensure_job_id(record)
        second_id = ensure_job_id(record)

        self.assertEqual(first_id, second_id)

    def test_platform_and_city_are_part_of_identity(self):
        source = job("https://example.gov/jobs/100")
        other_city = job("https://example.gov/jobs/100", city="Mesa")
        other_platform = dict(source, raw_data={"platform": "PeopleSoft"})

        self.assertNotEqual(stable_job_id(source), stable_job_id(other_city))
        self.assertNotEqual(stable_job_id(source), stable_job_id(other_platform))

    def test_meaningful_query_parameters_are_retained(self):
        url = "https://hcm.example.gov/job?job=123&utm_source=email&lang=en#top"
        self.assertEqual(
            canonicalize_job_url(url),
            "https://hcm.example.gov/job?job=123&lang=en",
        )

    def test_deduplication_keeps_highest_scoring_record(self):
        url = "https://example.gov/jobs/100"
        jobs = [job(url, score=45), job(url + "?utm_source=test", score=91)]

        deduplicated = deduplicate_jobs(jobs)

        self.assertEqual(len(deduplicated), 1)
        self.assertEqual(deduplicated[0]["match_score"], 91)


class CacheIdentityTests(unittest.TestCase):
    def test_legacy_cache_ids_are_created_on_read(self):
        with tempfile.TemporaryDirectory() as directory:
            cache_path = Path(directory) / "jobs_tempe.json"
            cache_path.write_text(
                json.dumps({
                    "city": "Tempe",
                    "cached_at": datetime.now().isoformat(),
                    "job_count": 1,
                    "jobs": [{
                        "title": "Analyst",
                        "city": "Tempe",
                        "url": "https://example.gov/jobs/100",
                        "job_id": "",
                        "raw_data": {"platform": "NeoGov"},
                    }],
                }),
                encoding="utf-8",
            )

            with patch.object(job_cache, "CACHE_DIR", directory):
                cached_jobs = job_cache.get_cached_jobs("Tempe")

        self.assertEqual(len(cached_jobs), 1)
        self.assertRegex(cached_jobs[0]["job_id"], r"^job_[0-9a-f]{24}$")

    def test_cache_save_persists_ids_and_removes_duplicates(self):
        duplicate_url = "https://example.gov/jobs/100"
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(job_cache, "CACHE_DIR", directory):
                job_cache.save_cached_jobs(
                    "Tempe",
                    [job(duplicate_url), job(duplicate_url + "?utm_source=email")],
                )
                payload = json.loads(
                    (Path(directory) / "jobs_tempe.json").read_text(encoding="utf-8")
                )

        self.assertEqual(payload["job_count"], 1)
        self.assertRegex(payload["jobs"][0]["job_id"], r"^job_[0-9a-f]{24}$")


class SessionIdentityTests(unittest.TestCase):
    def test_same_title_jobs_do_not_share_dismissal_identity(self):
        state = SessionState()
        jobs = [
            job("https://example.gov/jobs/100", title="Police Officer"),
            job("https://example.gov/jobs/200", title="Police Officer"),
        ]

        with patch.object(session_manager.st, "session_state", state):
            session_manager.store_matched_jobs(jobs)
            stored_jobs = session_manager.get_matched_jobs()
            dismissed_id = stored_jobs[0]["job_id"]
            remaining_id = stored_jobs[1]["job_id"]
            session_manager.dismiss_job(dismissed_id)

            self.assertEqual(len(state.matched_jobs), 1)
            self.assertEqual(state.matched_jobs[0]["job_id"], remaining_id)


if __name__ == "__main__":
    unittest.main()
