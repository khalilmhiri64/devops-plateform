"""Jobs API: accepts jobs, stores them in Postgres and queues them in Redis."""
import logging
from contextlib import asynccontextmanager

import redis
from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from . import db
from .config import Settings, get_settings
from .logging_config import configure_logging
from .metrics import JOBS_CREATED, QUEUE_DEPTH, MetricsMiddleware
from .models import Job
from .queue import JobQueue
from .schemas import JobCreate, JobList, JobOut, JobStatus, Stats
from .secrets import resolve_database_url

log = logging.getLogger("jobs-api")


def create_app(settings: Settings | None = None, redis_client: redis.Redis | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.app_name)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db.init_engine(resolve_database_url(settings))
        client = redis_client or redis.Redis.from_url(settings.redis_url, decode_responses=True)
        app.state.queue = JobQueue(client, settings.queue_name)
        log.info("api started", extra={"environment": settings.environment, "version": settings.app_version})
        yield

    app = FastAPI(title="Jobs API", version=settings.app_version, lifespan=lifespan)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    def get_queue() -> JobQueue:
        return app.state.queue

    # ---- health ---------------------------------------------------------
    @app.get("/health/live", tags=["health"])
    def liveness():
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    def readiness(response: Response, session: Session = Depends(db.get_session),
                  queue: JobQueue = Depends(get_queue)):
        checks = {"database": "ok", "redis": "ok"}
        try:
            session.execute(text("SELECT 1"))
        except Exception:  # noqa: BLE001
            checks["database"] = "down"
        if not queue.ping():
            checks["redis"] = "down"
        ready = all(v == "ok" for v in checks.values())
        response.status_code = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "ready" if ready else "not_ready", "checks": checks}

    @app.get("/version", tags=["health"])
    def version():
        return {"name": settings.app_name, "version": settings.app_version, "environment": settings.environment}

    @app.get("/metrics", include_in_schema=False)
    def metrics(queue: JobQueue = Depends(get_queue)):
        try:
            QUEUE_DEPTH.set(queue.depth())
        except redis.RedisError:
            pass
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # ---- jobs -----------------------------------------------------------
    @app.post("/api/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED, tags=["jobs"])
    def create_job(body: JobCreate, session: Session = Depends(db.get_session),
                   queue: JobQueue = Depends(get_queue)):
        job = Job(type=body.type.value, payload=body.payload, status=JobStatus.QUEUED.value)
        session.add(job)
        session.commit()
        try:
            queue.enqueue(job.id, job.type)
        except redis.RedisError as exc:
            job.status, job.error = JobStatus.FAILED.value, "queue unavailable"
            session.commit()
            log.error("enqueue failed", extra={"job_id": job.id, "error": str(exc)})
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "queue unavailable") from exc
        JOBS_CREATED.labels(job.type).inc()
        log.info("job created", extra={"job_id": job.id, "job_type": job.type})
        return job

    @app.get("/api/jobs", response_model=JobList, tags=["jobs"])
    def list_jobs(session: Session = Depends(db.get_session),
                  status_filter: JobStatus | None = Query(None, alias="status"),
                  limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
        query = select(Job)
        count_q = select(func.count()).select_from(Job)
        if status_filter:
            query = query.where(Job.status == status_filter.value)
            count_q = count_q.where(Job.status == status_filter.value)
        items = session.scalars(query.order_by(Job.created_at.desc()).limit(limit).offset(offset)).all()
        return {"items": items, "total": session.scalar(count_q)}

    @app.get("/api/jobs/{job_id}", response_model=JobOut, tags=["jobs"])
    def get_job(job_id: str, session: Session = Depends(db.get_session)):
        job = session.get(Job, job_id)
        if not job:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "job not found")
        return job

    @app.delete("/api/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["jobs"])
    def delete_job(job_id: str, session: Session = Depends(db.get_session)):
        job = session.get(Job, job_id)
        if not job:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "job not found")
        session.delete(job)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/api/stats", response_model=Stats, tags=["jobs"])
    def stats(session: Session = Depends(db.get_session)):
        by_status = dict(session.execute(select(Job.status, func.count()).group_by(Job.status)).all())
        by_type = dict(session.execute(select(Job.type, func.count()).group_by(Job.type)).all())
        return {"total": sum(by_status.values()), "by_status": by_status, "by_type": by_type}

    return app


app = create_app()
