from urllib.parse import parse_qs, urlsplit

from scrapers.peoplesoft_scraper import PeopleSoftScraper


PORTAL_URL = (
    "https://hcmprod.phoenix.gov/psc/hcmprodtam/EMPLOYEE/HRMS/c/"
    "HRS_HRAM_FL.HRS_CG_SEARCH_FL.GBL?Action=U&Page=HRS_APP_SCHJOB_FL"
)


def test_parse_listing_page_extracts_people_soft_fields_and_deduplicates():
    page_html = """
    <div class="psc_rowcount">2 rows</div>
    <ul class="ps_grid-body">
      <li class="ps_grid-row">
        <span id="SCH_JOB_TITLE$0">Systems Analyst</span>
        <span id="HRS_APP_JBSCH_I_HRS_JOB_OPENING_ID$0">12345</span>
        <span id="LOCATION$0">Information Technology</span>
        <span id="HRS_APP_JBSCH_I_HRS_DEPT_DESCR$0">ITS Department</span>
        <span id="SCH_OPENED$0">09/30/2026</span>
        <span id="HRS_CLS_DT_DESCR$0">10/15/2026</span>
      </li>
      <li class="ps_grid-row">
        <span id="SCH_JOB_TITLE$1">Systems Analyst duplicate</span>
        <span id="HRS_APP_JBSCH_I_HRS_JOB_OPENING_ID$1">12345</span>
      </li>
    </ul>
    """

    jobs = PeopleSoftScraper.parse_listing_page(
        page_html,
        city_name="Phoenix",
        portal_url=PORTAL_URL,
    )

    assert len(jobs) == 1
    job = jobs[0]
    assert job.title == "Systems Analyst"
    assert job.department == "ITS Department"
    assert job.location == "Phoenix"
    assert job.posted_date == "09/30/2026"
    assert job.closing_date == "10/15/2026"
    assert job.raw_data["posting_id"] == "12345"
    assert job.raw_data["category"] == "Information Technology"

    parsed_url = urlsplit(job.url)
    query = parse_qs(parsed_url.query)
    assert "/EMPLOYEE/HRMS/" in parsed_url.path
    assert query["Page"] == ["HRS_APP_JBPST_FL"]
    assert query["SiteId"] == ["10"]
    assert query["JobOpeningId"] == ["12345"]


def test_parse_job_details_separates_requirements_and_salary():
    page_html = """
    <div class="hrs_cg_groupbox_field_label_back">
      <span id="HRS_SCH_WRK_DESCR100$0lbl">ABOUT THIS POSITION</span>
      <span id="HRS_SCH_PSTDSC_DESCRLONG$0">Build reliable city systems.</span>
    </div>
    <div class="hrs_cg_groupbox_field_label_back">
      <span id="HRS_SCH_WRK_DESCR100$1lbl">MINIMUM QUALIFICATIONS</span>
      <span id="HRS_SCH_PSTDSC_DESCRLONG$1">Two years of experience.</span>
    </div>
    <div class="hrs_cg_groupbox_field_label_back">
      <span id="HRS_SCH_WRK_DESCR100$2lbl">SALARY</span>
      <span id="HRS_SCH_PSTDSC_DESCRLONG$2">$80,000 to $100,000 annually.</span>
    </div>
    """

    details = PeopleSoftScraper.parse_job_details(page_html)

    assert "ABOUT THIS POSITION\nBuild reliable city systems." in details["description"]
    assert "MINIMUM QUALIFICATIONS\nTwo years of experience." == details["requirements"]
    assert details["salary"] == "$80,000 to $100,000 annually."


def test_zero_row_page_is_recognized_as_valid():
    assert PeopleSoftScraper._reports_zero_jobs(
        '<div class="psc_rowcount">0 rows</div>'
    )
