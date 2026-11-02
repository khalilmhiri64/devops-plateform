# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM build AS test
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt
COPY . .
CMD ["pytest", "-m", "unit", "--cov=worker", "--cov-report=xml:/reports/coverage.xml", "--junitxml=/reports/junit.xml"]

FROM python:3.12-slim AS runtime
ARG VERSION=dev
LABEL org.opencontainers.image.title="jobs-worker" org.opencontainers.image.version=$VERSION
ENV PATH=/opt/venv/bin:$PATH PYTHONUNBUFFERED=1
RUN groupadd -g 10001 app && useradd -u 10001 -g app -s /sbin/nologin -M app
COPY --from=build /opt/venv /opt/venv
WORKDIR /app
COPY worker ./worker
USER 10001
EXPOSE 9100
CMD ["python", "-m", "worker.main"]
