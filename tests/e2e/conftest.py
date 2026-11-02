import os

import pytest
from selenium import webdriver

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
SELENIUM_URL = os.getenv("SELENIUM_URL", "http://localhost:4444/wd/hub")


def _options(browser: str):
    opts = webdriver.FirefoxOptions() if browser == "firefox" else webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--window-size=1280,900")
    return opts


@pytest.fixture(params=os.getenv("BROWSER", "chrome").split(","))
def driver(request):
    drv = webdriver.Remote(command_executor=SELENIUM_URL, options=_options(request.param))
    drv.implicitly_wait(2)
    yield drv
    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        os.makedirs("/reports/screenshots", exist_ok=True)
        drv.save_screenshot(f"/reports/screenshots/{request.node.name}.png")
    drv.quit()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture
def base_url():
    return BASE_URL
