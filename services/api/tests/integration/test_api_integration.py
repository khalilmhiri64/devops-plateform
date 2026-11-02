"""Integration tests: run against the real stack (API + Postgres + Redis + worker).

    docker compose up -d
    API_URL=http://localhost:8000 pytest -m integration
"""
import os
import time

import pytest
import requests

pytestmark = pytest.mark.integration

API_URL = os.getenv("API_URL", "http://localhost:8000")


@pytest.fixture(scope="module", autouse=True)
def wait_for_api():
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            if requests.get(f"{API_URL}/health/ready", timeout=2).status_code == 200:
                return
        except requests.ConnectionError:
            pass
        time.sleep(2)
    pytest.fail(f"API at {API_URL} never became ready")


def _wait_for_completion(job_id: str, timeout: float = 30) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = requests.get(f"{API_URL}/api/jobs/{job_id}", timeout=5).json()
        if job["status"] in ("completed", "failed"):
            return job
        time.sleep(0.5)
    pytest.fail(f"job {job_id} did not finish in {timeout}s")


@pytest.mark.parametrize(
    "type_,payload,expected",
    [
        ("wordcount", {"text": "the quick brown fox"}, {"words": 4, "characters": 19}),
        ("reverse", {"text": "devops"}, {"reversed": "spoved"}),
        ("fibonacci", {"n": 10}, {"value": 55}),
        ("prime_check", {"n": 97}, {"is_prime": True}),
    ],
)
def test_job_round_trip_through_worker(type_, payload, expected):
    r = requests.post(f"{API_URL}/api/jobs", json={"type": type_, "payload": payload}, timeout=5)
    assert r.status_code == 201
    job = _wait_for_completion(r.json()["id"])
    assert job["status"] == "completed", job
    for key, value in expected.items():
        assert job["result"][key] == value


def test_readiness_reports_all_dependencies():
    body = requests.get(f"{API_URL}/health/ready", timeout=5).json()
    assert body["checks"] == {"database": "ok", "redis": "ok"}


def test_metrics_scrapeable():
    r = requests.get(f"{API_URL}/metrics", timeout=5)
    assert r.status_code == 200
    assert "jobs_created_total" in r.text
