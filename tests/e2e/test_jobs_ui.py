import uuid

import pytest

from pages.home_page import HomePage


@pytest.mark.smoke
def test_page_loads_and_shows_version(driver, base_url):
    page = HomePage(driver, base_url).open()
    assert "·" in page.version_text()
    assert driver.title == "Jobs Platform"


@pytest.mark.smoke
def test_submit_reverse_job_completes(driver, base_url):
    page = HomePage(driver, base_url).open()
    marker = f"e2e-{uuid.uuid4().hex[:8]}"
    page.submit_job("reverse", marker)
    cells = page.wait_for_latest_status("completed", expected_input=marker)
    assert cells[3] == marker[::-1]


@pytest.mark.parametrize("job_type,value,expected", [
    ("fibonacci", "10", "55"),
    ("prime_check", "97", "prime"),
    ("prime_check", "91", "not prime (÷7)"),
    ("wordcount", "one two three", "3 words, 13 chars"),
])
def test_job_types_produce_expected_results(driver, base_url, job_type, value, expected):
    page = HomePage(driver, base_url).open()
    page.submit_job(job_type, value)
    assert page.wait_for_latest_status("completed", expected_input=value)[3] == expected


def test_invalid_fibonacci_shows_validation_error(driver, base_url):
    page = HomePage(driver, base_url).open()
    page.submit_job("fibonacci", "500")
    assert "between 0 and 90" in page.form_error()
