"""Page Object for the Jobs Platform home page."""
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


def _tid(value: str):
    return By.CSS_SELECTOR, f'[data-testid="{value}"]'


class HomePage:
    JOB_TYPE = _tid("job-type")
    JOB_INPUT = _tid("job-input")
    SUBMIT = _tid("submit-btn")
    FORM_ERROR = _tid("form-error")
    ROWS = (By.CSS_SELECTOR, '[data-testid="jobs-table"] tr')
    VERSION = _tid("version")
    STATS = _tid("stats")

    def __init__(self, driver: WebDriver, base_url: str, timeout: int = 15):
        self.driver = driver
        self.base_url = base_url
        # The job table re-renders every 2s, so element references go stale often.
        self.wait = WebDriverWait(driver, timeout, poll_frequency=0.25,
                                  ignored_exceptions=(StaleElementReferenceException, NoSuchElementException))

    def open(self) -> "HomePage":
        self.driver.get(self.base_url)
        self.wait.until(lambda d: d.find_element(*self.VERSION).text not in ("", "…"))
        return self

    def submit_job(self, job_type: str, value: str) -> None:
        Select(self.driver.find_element(*self.JOB_TYPE)).select_by_value(job_type)
        field = self.driver.find_element(*self.JOB_INPUT)
        field.clear()
        field.send_keys(value)
        self.driver.find_element(*self.SUBMIT).click()

    def latest_row(self):
        return self.wait.until(EC.presence_of_element_located(self.ROWS))

    def wait_for_latest_status(self, status: str, expected_input: str | None = None) -> list[str]:
        """Wait until the newest row (optionally the one for ``expected_input``) has ``status``.

        Returns the cell texts captured in one read, so callers never touch stale elements.
        """
        def _check(_):
            cells = [td.text for td in self.driver.find_element(*self.ROWS).find_elements(By.TAG_NAME, "td")]
            if expected_input is not None and cells[1] != expected_input:
                return False
            return cells if cells[2] == status else False
        return self.wait.until(_check)

    def form_error(self) -> str:
        el = self.wait.until(EC.visibility_of_element_located(self.FORM_ERROR))
        return el.text

    def version_text(self) -> str:
        return self.driver.find_element(*self.VERSION).text
