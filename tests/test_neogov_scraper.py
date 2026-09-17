"""Regression tests for complete, paginated NEOGOV scraping."""

import asyncio
import json
import unittest

from scrapers.neogov_scraper import NeoGovScraper


def listing_item(posting_id, title, department="Technology Services"):
    return f"""
    <li class="list-item" data-job-id="{posting_id}">
      <h3><a class="item-details-link"
             data-department-name="{department}"
             href="/careers/tempe/jobs/{posting_id}/{title.lower().replace(' ', '-')}">
        {title}
      </a></h3>
      <ul class="list-meta">
        <li>Tempe, AZ</li>
        <li>Full-Time <span>-</span> $60,000.00 - $80,000.00 Annually</li>
        <li class="categories-list">Category: Information Technology</li>
      </ul>
      <div class="list-entry">Short listing summary for {title}.</div>
    </li>
    """


def listing_page(items, count=2, next_page=None):
    next_link = ""
    if next_page:
        next_link = (
            '<ul class="pagination"><li><a rel="next" aria-disabled="false" '
            f'aria-label="Go to Next Page" href="/careers/Home?page={next_page}">'
            "Next</a></li></ul>"
        )
    return f"""
    <span id="job-postings-number">{count}</span>
    <ul class="search-results-listing-container">{items}</ul>
    {next_link}
    """


def detail_page(title, job_number):
    structured = {
        "@context": "https://schema.org/",
        "@type": "JobPosting",
        "title": title,
        "description": "&lt;p&gt;Structured fallback description&lt;/p&gt;",
        "datePosted": "2026-04-01",
        "validThrough": "2026-04-30",
        "employmentType": "FULL_TIME",
        "baseSalary": {
            "value": {
                "minValue": 60000,
                "maxValue": 80000,
                "unitText": "YEAR",
            }
        },
    }
    return f"""
    <script type="application/ld+json">{json.dumps(structured)}</script>
    <div class="term-block">
      <div class="term-description">Salary</div><div class="span8">$60,000 - $80,000 Annually</div>
    </div>
    <div class="term-block">
      <div class="term-description">Location</div><div class="span8">Tempe, Arizona</div>
    </div>
    <div class="term-block">
      <div class="term-description">Job Type</div><div class="span8">Full-Time</div>
    </div>
    <div class="term-block">
      <div class="term-description">Job Number</div><div class="span8">{job_number}</div>
    </div>
    <div class="term-block">
      <div class="term-description">Division</div><div class="span8">IT Division</div>
    </div>
    <div class="term-block">
      <div class="term-description">Department</div><div class="span8">Technology Services</div>
    </div>
    <div class="term-block">
      <div class="term-description">Opening Date</div><div class="span8">04/01/2026</div>
    </div>
    <div class="term-block">
      <div class="term-description">Closing Date</div><div class="span8">04/30/2026</div>
    </div>
    <div id="details-info"><dl>
      <dt><h2>Introduction</h2></dt><dd>Build and maintain public systems.</dd>
      <dt><h2>Minimum Qualifications</h2></dt><dd>Three years of relevant experience.</dd>
      <dt><h2>Essential Functions</h2></dt><dd>Design reliable services.</dd>
    </dl></div>
    """


class NeoGovParserTests(unittest.TestCase):
    def test_listing_parser_deduplicates_and_extracts_metadata(self):
        duplicate = listing_item("12345", "Software Engineer")
        jobs, next_page, reported_count = NeoGovScraper.parse_listing_page(
            listing_page(duplicate + duplicate, count=12, next_page=2),
            city_name="Tempe",
            portal_origin="https://www.governmentjobs.com",
            agency_code="tempe",
        )

        self.assertEqual(len(jobs), 1)
        self.assertRegex(jobs[0].job_id, r"^job_[0-9a-f]{24}$")
        self.assertEqual(jobs[0].location, "Tempe, AZ")
        self.assertEqual(jobs[0].department, "Technology Services")
        self.assertEqual(jobs[0].job_type, "Full-Time")
        self.assertEqual(jobs[0].salary, "$60,000.00 - $80,000.00 Annually")
        self.assertTrue(jobs[0].description.startswith("Short listing summary"))
        self.assertEqual(next_page, 2)
        self.assertEqual(reported_count, 12)

    def test_detail_parser_extracts_all_supported_fields(self):
        details = NeoGovScraper.parse_job_details(
            detail_page("Software Engineer", "T-2026-42")
        )

        self.assertIn("Build and maintain public systems", details["description"])
        self.assertIn("Design reliable services", details["description"])
        self.assertIn("Three years", details["requirements"])
        self.assertEqual(details["location"], "Tempe, Arizona")
        self.assertEqual(details["department"], "Technology Services")
        self.assertEqual(details["salary"], "$60,000 - $80,000 Annually")
        self.assertEqual(details["posted_date"], "04/01/2026")
        self.assertEqual(details["closing_date"], "04/30/2026")
        self.assertEqual(details["job_number"], "T-2026-42")
        self.assertEqual(details["job_type"], "Full-Time")

    def test_structured_metadata_is_used_as_a_fallback(self):
        structured = {
            "@type": "JobPosting",
            "description": "&lt;p&gt;A useful description.&lt;/p&gt;",
            "datePosted": "2026-05-01",
            "validThrough": "2026-05-31",
            "employmentType": "PART_TIME",
            "jobLocation": {
                "address": {
                    "addressLocality": "Mesa",
                    "addressRegion": "AZ",
                    "postalCode": "85201",
                }
            },
            "baseSalary": {
                "value": {
                    "minValue": 20,
                    "maxValue": 25,
                    "unitText": "HOUR",
                }
            },
        }
        page = (
            '<script type="application/ld+json">'
            + json.dumps(structured)
            + "</script>"
        )

        details = NeoGovScraper.parse_job_details(page)

        self.assertEqual(details["description"], "A useful description.")
        self.assertEqual(details["posted_date"], "2026-05-01")
        self.assertEqual(details["closing_date"], "2026-05-31")
        self.assertEqual(details["location"], "Mesa, AZ, 85201")
        self.assertEqual(details["salary"], "$20.00 - $25.00 Hour")

    def test_canonical_url_removes_tracking_and_fragment(self):
        url = "HTTPS://WWW.GOVERNMENTJOBS.COM/careers/tempe/jobs/12345/test/?x=1#top"
        self.assertEqual(
            NeoGovScraper.canonicalize_job_url(url),
            "https://www.governmentjobs.com/careers/tempe/jobs/12345/test",
        )


class NeoGovFlowTests(unittest.TestCase):
    def test_scrape_follows_pages_deduplicates_and_enriches(self):
        scraper = NeoGovScraper(
            "Tempe",
            "https://www.governmentjobs.com/careers/tempe",
            {"detail_concurrency": 2},
        )
        first_page = listing_page(
            listing_item("100", "Engineer") + listing_item("100", "Engineer"),
            count=2,
            next_page=2,
        )
        second_page = listing_page(
            listing_item("100", "Engineer") + listing_item("200", "Analyst"),
            count=2,
        )

        async def fake_fetch(_session, url, params=None):
            if params:
                return first_page if params["page"] == 1 else second_page
            if "/100/" in url:
                return detail_page("Engineer", "T-100")
            return detail_page("Analyst", "T-200")

        scraper._fetch_text = fake_fetch
        jobs = asyncio.run(scraper._scrape_with_session(object()))

        self.assertEqual(len({job.job_id for job in jobs}), 2)
        self.assertTrue(all(job.job_id.startswith("job_") for job in jobs))
        self.assertTrue(all(job.requirements for job in jobs))
        self.assertTrue(all(job.description for job in jobs))
        self.assertEqual(jobs[0].raw_data["job_number"], "T-100")
        self.assertEqual(jobs[1].raw_data["source_page"], 2)


if __name__ == "__main__":
    unittest.main()
