import json

import pytest
import redis

pytestmark = pytest.mark.unit


def _create(client, type_="wordcount", payload=None):
    return client.post("/api/jobs", json={"type": type_, "payload": payload if payload is not None else {"text": "hello world"}})


def test_create_job_persists_and_enqueues(client, redis_client):
    r = _create(client)
    assert r.status_code == 201
    job = r.json()
    assert job["status"] == "queued"
    assert job["type"] == "wordcount"
    msg = json.loads(redis_client.rpop("jobs:queue"))
    assert msg == {"id": job["id"], "type": "wordcount"}


@pytest.mark.parametrize(
    "type_,payload",
    [
        ("wordcount", {"text": "a b c"}),
        ("reverse", {"text": "abc"}),
        ("fibonacci", {"n": 10}),
        ("prime_check", {"n": 97}),
    ],
)
def test_create_all_job_types(client, type_, payload):
    assert _create(client, type_, payload).status_code == 201


@pytest.mark.parametrize(
    "type_,payload",
    [
        ("wordcount", {}),
        ("wordcount", {"text": "   "}),
        ("reverse", {"text": 123}),
        ("fibonacci", {"n": -1}),
        ("fibonacci", {"n": 91}),
        ("fibonacci", {"n": "10"}),
        ("prime_check", {"n": True}),
        ("unknown", {"text": "x"}),
    ],
)
def test_create_job_validation(client, type_, payload):
    assert _create(client, type_, payload).status_code == 422


def test_text_too_long_rejected(client):
    assert _create(client, "reverse", {"text": "x" * 10_001}).status_code == 422


def test_get_job(client):
    job_id = _create(client).json()["id"]
    r = client.get(f"/api/jobs/{job_id}")
    assert r.status_code == 200
    assert r.json()["id"] == job_id


def test_get_missing_job_returns_404(client):
    assert client.get("/api/jobs/does-not-exist").status_code == 404


def test_list_jobs_pagination_and_filter(client):
    for i in range(5):
        _create(client, "fibonacci", {"n": i})
    r = client.get("/api/jobs", params={"limit": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert client.get("/api/jobs", params={"status": "completed"}).json()["total"] == 0
    assert client.get("/api/jobs", params={"status": "queued"}).json()["total"] == 5


def test_list_jobs_limit_bounds(client):
    assert client.get("/api/jobs", params={"limit": 0}).status_code == 422
    assert client.get("/api/jobs", params={"limit": 101}).status_code == 422


def test_delete_job(client):
    job_id = _create(client).json()["id"]
    assert client.delete(f"/api/jobs/{job_id}").status_code == 204
    assert client.get(f"/api/jobs/{job_id}").status_code == 404
    assert client.delete(f"/api/jobs/{job_id}").status_code == 404


def test_stats(client):
    _create(client)
    _create(client, "fibonacci", {"n": 5})
    body = client.get("/api/stats").json()
    assert body["total"] == 2
    assert body["by_status"] == {"queued": 2}
    assert body["by_type"] == {"wordcount": 1, "fibonacci": 1}


def test_queue_failure_marks_job_failed(client, monkeypatch):
    def boom(*_a, **_k):
        raise redis.ConnectionError("down")

    monkeypatch.setattr(client.app.state.queue, "enqueue", boom)
    r = _create(client)
    assert r.status_code == 503
    jobs = client.get("/api/jobs").json()["items"]
    assert jobs[0]["status"] == "failed"
    assert jobs[0]["error"] == "queue unavailable"
