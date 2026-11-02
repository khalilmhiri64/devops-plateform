import pytest

pytestmark = pytest.mark.unit


def test_liveness(client):
    r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_readiness_ok(client):
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert r.json()["checks"] == {"database": "ok", "redis": "ok"}


def test_readiness_fails_when_redis_down(client, redis_client, monkeypatch):
    monkeypatch.setattr(client.app.state.queue, "ping", lambda: False)
    r = client.get("/health/ready")
    assert r.status_code == 503
    assert r.json()["checks"]["redis"] == "down"


def test_version(client):
    body = client.get("/version").json()
    assert body["environment"] == "test"
    assert body["name"] == "jobs-api"


def test_metrics_exposed(client):
    client.get("/health/live")
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "http_requests_total" in r.text
    assert "jobs_queue_depth" in r.text
