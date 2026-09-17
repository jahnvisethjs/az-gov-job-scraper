"""Tests for the title and location filters used by the job-search UI."""
import asyncio
import unittest
from unittest.mock import patch

from rag.job_matcher import JobMatcher, filter_jobs_by_search, narrow_cities_by_location
from rag.rag_engine import prepare_job_text, prepare_resume_text


JOBS = [
    {
        "title": "Senior Software Engineer",
        "department": "Information Technology",
        "city": "Phoenix",
        "location": "Phoenix, AZ",
    },
    {
        "title": "Human Resources Analyst",
        "department": "Human Resources",
        "city": "Tempe",
        "location": "City of Tempe, Arizona",
    },
    {
        "title": "IT Support Specialist",
        "department": "Technology Services",
        "city": "Pima County",
        "location": "Tucson, AZ",
    },
]


class SearchFilterTests(unittest.TestCase):
    def test_blank_criteria_keep_all_jobs(self):
        self.assertEqual(filter_jobs_by_search(JOBS), JOBS)

    def test_title_matching_is_case_and_punctuation_insensitive(self):
        matches = filter_jobs_by_search(JOBS, job_title="software-engineer")
        self.assertEqual(matches, [JOBS[0]])

    def test_title_can_match_department(self):
        matches = filter_jobs_by_search(JOBS, job_title="human resources")
        self.assertEqual(matches, [JOBS[1]])

    def test_city_and_state_location_matches_city(self):
        matches = filter_jobs_by_search(JOBS, location="Phoenix, Arizona")
        self.assertEqual(matches, [JOBS[0]])

    def test_state_only_location_keeps_arizona_jobs(self):
        self.assertEqual(filter_jobs_by_search(JOBS, location="AZ"), JOBS)

    def test_supported_city_narrows_scraping_scope(self):
        cities = ["Phoenix", "Tempe", "Pima County"]
        self.assertEqual(
            narrow_cities_by_location(cities, "Pima County, AZ"),
            ["Pima County"],
        )

    def test_unknown_location_defers_to_job_record_filtering(self):
        cities = ["Phoenix", "Tempe"]
        self.assertEqual(narrow_cities_by_location(cities, "Tucson"), cities)

    def test_embedding_text_includes_search_context(self):
        job_text = prepare_job_text(JOBS[0])
        profile_text = prepare_resume_text({
            "target_job_title": "Software Engineer",
            "target_location": "Phoenix",
        })

        self.assertIn("Location: Phoenix, AZ", job_text)
        self.assertIn("Target role: Software Engineer", profile_text)
        self.assertIn("Preferred location: Phoenix", profile_text)

    @patch("rag.job_matcher.get_cached_jobs")
    @patch("rag.job_matcher.is_cache_fresh", return_value=True)
    @patch("rag.job_matcher.JobRAG")
    def test_matcher_applies_filters_before_indexing(
        self,
        rag_class,
        _is_cache_fresh,
        get_cached_jobs,
    ):
        rag = rag_class.return_value
        get_cached_jobs.return_value = JOBS
        rag.search_jobs.return_value = [(JOBS[0].copy(), 87.5)]

        matcher = JobMatcher(api_key="test-key")
        results = asyncio.run(matcher.match_jobs_to_profile(
            profile={"resume_parsed": {}},
            cities=["Phoenix", "Tempe"],
            job_title="software engineer",
            location="Phoenix, Arizona",
        ))

        get_cached_jobs.assert_called_once_with("Phoenix")
        indexed_jobs = rag.add_jobs.call_args.args[0]
        self.assertEqual(len(indexed_jobs), 1)
        self.assertEqual(indexed_jobs[0]["title"], JOBS[0]["title"])
        self.assertRegex(indexed_jobs[0]["job_id"], r"^job_[0-9a-f]{24}$")
        search_profile = rag.search_jobs.call_args.args[0]
        self.assertEqual(search_profile["target_job_title"], "software engineer")
        self.assertEqual(search_profile["target_location"], "Phoenix, Arizona")
        self.assertEqual(results[0]["match_score"], 87.5)


if __name__ == "__main__":
    unittest.main()
