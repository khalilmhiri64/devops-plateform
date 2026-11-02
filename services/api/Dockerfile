# syntax=docker/dockerfile:1.7
# ---------- build stage: install deps into a venv ----------
FROM python:3.12-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---------- test stage: used by CI to run unit tests inside the image ----------
FROM build AS test
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt
COPY . .
CMD ["pytest", "-m", "unit", "--cov=app", "--cov-report=xml:/reports/coverage.xml", "--junitxml=/reports/junit.xml"]

# ---------- runtime stage: minimal, non-root ----------
FROM python:3.12-slim AS runtime
ARG VERSION=dev
LABEL org.opencontainers.image.title="jobs-api" org.opencontainers.image.version=$VERSION
ENV PATH=/opt/venv/bin:$PATH PYTHONUNBUFFERED=1 APP_VERSION=$VERSION
RUN groupadd -g 10001 app && useradd -u 10001 -g app -s /sbin/nologin -M app
COPY --from=build /opt/venv /opt/venv
WORKDIR /app
COPY app ./app
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health/live').status==200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
