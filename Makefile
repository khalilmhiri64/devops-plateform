SHELL := /bin/bash
.DEFAULT_GOAL := help
VERSION ?= dev
COMPOSE := docker compose -f docker-compose.yml -f docker-compose.test.yml
PY_SERVICES := api worker

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n",$$1,$$2}'

# ---------------------------------------------------------------- local dev
venv: ## Create a local virtualenv with all test deps
	python3 -m venv .venv && .venv/bin/pip install -q -r services/api/requirements-dev.txt -r services/worker/requirements-dev.txt

up: ## Start app stack (frontend :8080, api :8000)
	VERSION=$(VERSION) docker compose up -d --build --wait

up-full: ## Start everything: app + observability + vault + jenkins
	VERSION=$(VERSION) docker compose --profile full up -d --build

down: ## Stop all containers and delete volumes
	$(COMPOSE) --profile full --profile test down -v --remove-orphans

logs: ## Tail app logs
	docker compose logs -f api worker frontend

# ---------------------------------------------------------------- quality
lint: ## Ruff lint for Python services
	.venv/bin/ruff check services

unit: ## Unit tests with coverage (no Docker needed)
	cd services/api && ../../.venv/bin/pytest -m unit --cov=app --cov-fail-under=80
	cd services/worker && ../../.venv/bin/pytest --cov=worker --cov-fail-under=80

integration: up ## Integration tests against the running stack
	$(COMPOSE) --profile test run --rm integration

e2e: up ## Selenium Grid E2E tests (BROWSER=chrome,firefox for both)
	$(COMPOSE) --profile test up -d --wait selenium-hub chrome firefox
	$(COMPOSE) --profile test run --rm e2e

perf: up ## k6 smoke performance test
	$(COMPOSE) --profile test run --rm k6

perf-load: up ## k6 5-minute load test
	$(COMPOSE) --profile test run --rm k6 run --summary-export=/reports/load.json /scripts/load.js

scan: ## Trivy scan of all built images + repo (secrets, misconfig)
	trivy fs --config tests/security/trivy.yaml .
	for s in api worker frontend; do trivy image --config tests/security/trivy.yaml jobs/$$s:$(VERSION); done

policy: ## OPA/conftest checks on rendered manifests + policy unit tests
	conftest verify -p security/opa/policies
	for e in staging production; do kustomize build k8s/overlays/$$e | conftest test -p security/opa/policies -; done

test: lint unit policy ## Everything that runs without a cluster

smoke: ## Smoke test a deployed environment (URL=...)
	scripts/smoke-test.sh $${URL:-http://localhost:8080}

# ---------------------------------------------------------------- kubernetes
k8s-render: ## Render staging and production manifests to ./reports
	mkdir -p reports && for e in staging production; do kustomize build k8s/overlays/$$e > reports/$$e.yaml; done

bootstrap: ## Provision the platform on Docker Desktop Kubernetes (needs GITOPS_REPO_URL)
	scripts/bootstrap.sh

tf-check: ## terraform fmt + validate
	terraform -chdir=terraform fmt -check -recursive
	terraform -chdir=terraform init -backend=false -input=false >/dev/null
	terraform -chdir=terraform validate

.PHONY: help venv up up-full down logs lint unit integration e2e perf perf-load scan policy test smoke k8s-render bootstrap tf-check
