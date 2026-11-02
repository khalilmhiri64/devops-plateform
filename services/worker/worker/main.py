"""Background worker: pops jobs from Redis, processes them, writes results to Postgres."""
import json
import logging
import os
import signal
import sys
import time

import redis
from prometheus_client import Counter, Histogram, start_http_server
from pythonjsonlogger.json import JsonFormatter
from sqlalchemy import JSON, Column, DateTime, MetaData, String, Table, Text, create_engine, func, update
from sqlalchemy.engine import Engine

from .processors import process

log = logging.getLogger("jobs-worker")

JOBS_PROCESSED = Counter("worker_jobs_processed_total", "Jobs processed", ["type", "outcome"])
JOB_DURATION = Histogram("worker_job_duration_seconds", "Job processing time", ["type"])

metadata = MetaData()
# Mirrors the table owned by the API (the API creates it on start-up).
jobs = Table(
    "jobs", metadata,
    Column("id", String(36), primary_key=True),
    Column("type", String(32)),
    Column("payload", JSON),
    Column("status", String(16)),
    Column("result", JSON),
    Column("error", Text),
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
)


class Worker:
    def __init__(self, engine: Engine, client: redis.Redis, queue: str, poll_timeout: int = 5):
        self.engine = engine
        self.redis = client
        self.queue = queue
        self.processing_queue = f"{queue}:processing"
        self.poll_timeout = poll_timeout
        self.running = True

    def stop(self, *_):
        log.info("shutdown signal received")
        self.running = False

    def _set(self, job_id: str, **values) -> None:
        with self.engine.begin() as conn:
            conn.execute(update(jobs).where(jobs.c.id == job_id).values(updated_at=func.now(), **values))

    def handle(self, raw: str) -> str:
        """Process one queue message. Returns the final job status."""
        msg = json.loads(raw)
        job_id, job_type = msg["id"], msg["type"]
        with self.engine.connect() as conn:
            row = conn.execute(jobs.select().where(jobs.c.id == job_id)).mappings().first()
        if row is None:
            log.warning("job vanished before processing", extra={"job_id": job_id})
            return "missing"

        self._set(job_id, status="processing")
        start = time.perf_counter()
        try:
            result = process(job_type, row["payload"] or {})
        except Exception as exc:  # noqa: BLE001
            self._set(job_id, status="failed", error=str(exc))
            JOBS_PROCESSED.labels(job_type, "failed").inc()
            log.exception("job failed", extra={"job_id": job_id, "job_type": job_type})
            return "failed"
        finally:
            JOB_DURATION.labels(job_type).observe(time.perf_counter() - start)

        self._set(job_id, status="completed", result=result, error=None)
        JOBS_PROCESSED.labels(job_type, "completed").inc()
        log.info("job completed", extra={"job_id": job_id, "job_type": job_type})
        return "completed"

    def run_once(self) -> str | None:
        # Reliable-queue pattern: atomically move the message to a processing list
        # so it is not lost if the worker crashes mid-job.
        raw = self.redis.blmove(self.queue, self.processing_queue, self.poll_timeout, "RIGHT", "LEFT")
        if raw is None:
            return None
        try:
            return self.handle(raw)
        finally:
            self.redis.lrem(self.processing_queue, 1, raw)

    def recover(self) -> int:
        """Re-queue messages left in the processing list by a crashed worker."""
        moved = 0
        while self.redis.rpoplpush(self.processing_queue, self.queue):
            moved += 1
        if moved:
            log.warning("re-queued orphaned jobs", extra={"count": moved})
        return moved

    def run(self) -> None:
        self.recover()
        log.info("worker started", extra={"queue": self.queue})
        while self.running:
            try:
                self.run_once()
            except redis.RedisError as exc:
                log.error("redis error, backing off", extra={"error": str(exc)})
                time.sleep(2)


def main() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s",
                                       rename_fields={"levelname": "level", "asctime": "ts"},
                                       static_fields={"service": "jobs-worker"}))
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), handlers=[handler])

    start_http_server(int(os.getenv("METRICS_PORT", "9100")))
    engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///./jobs.db"), pool_pre_ping=True)
    client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    worker = Worker(engine, client, os.getenv("QUEUE_NAME", "jobs:queue"))
    signal.signal(signal.SIGTERM, worker.stop)
    signal.signal(signal.SIGINT, worker.stop)
    worker.run()


if __name__ == "__main__":
    main()
