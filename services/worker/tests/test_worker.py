import json
import uuid

import fakeredis
import pytest
from sqlalchemy import create_engine, insert, select

from worker.main import Worker, jobs, metadata

pytestmark = pytest.mark.unit


@pytest.fixture
def env(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/w.db")
    metadata.create_all(engine)
    client = fakeredis.FakeRedis(decode_responses=True)
    return engine, client, Worker(engine, client, "q", poll_timeout=1)


def _add(engine, client, type_, payload):
    job_id = str(uuid.uuid4())
    with engine.begin() as c:
        c.execute(insert(jobs).values(id=job_id, type=type_, payload=payload, status="queued"))
    client.lpush("q", json.dumps({"id": job_id, "type": type_}))
    return job_id


def _get(engine, job_id):
    with engine.connect() as c:
        return c.execute(select(jobs).where(jobs.c.id == job_id)).mappings().first()


def test_processes_job_successfully(env):
    engine, client, worker = env
    job_id = _add(engine, client, "reverse", {"text": "abc"})
    assert worker.run_once() == "completed"
    row = _get(engine, job_id)
    assert row["status"] == "completed"
    assert row["result"] == {"reversed": "cba"}
    assert client.llen("q:processing") == 0


def test_marks_bad_job_failed(env):
    engine, client, worker = env
    job_id = _add(engine, client, "fibonacci", {"n": -5})
    assert worker.run_once() == "failed"
    row = _get(engine, job_id)
    assert row["status"] == "failed"
    assert "n must be" in row["error"]


def test_missing_job_is_skipped(env):
    _, client, worker = env
    client.lpush("q", json.dumps({"id": "ghost", "type": "reverse"}))
    assert worker.run_once() == "missing"


def test_empty_queue_returns_none(env):
    assert env[2].run_once() is None


def test_recover_requeues_orphans(env):
    _, client, worker = env
    client.lpush("q:processing", "a", "b")
    assert worker.recover() == 2
    assert client.llen("q") == 2
    assert client.llen("q:processing") == 0
