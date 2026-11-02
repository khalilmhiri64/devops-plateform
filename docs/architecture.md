# Architecture

## 1. Application

```mermaid
flowchart LR
  user([Browser]) -->|HTTP :8080 / Ingress| fe[frontend<br/>nginx + static JS]
  fe -->|/api/* proxy| api[api<br/>FastAPI]
  api -->|INSERT/SELECT| pg[(PostgreSQL)]
  api -->|LPUSH jobs:queue| rd[(Redis)]
  wk[worker xN] -->|BLMOVE jobs:queue → :processing| rd
  wk -->|UPDATE status/result| pg
```

| Service  | Tech                       | Responsibility | Port | Health |
|----------|----------------------------|----------------|------|--------|
| frontend | nginx-unprivileged, vanilla JS | UI; same-origin reverse proxy to the API | 8080 | `/healthz` |
| api      | Python 3.12, FastAPI, SQLAlchemy | Validate and store jobs, enqueue, query, stats, `/metrics` | 8000 | `/health/live`, `/health/ready` |
| worker   | Python 3.12, redis-py      | Process jobs (wordcount, reverse, fibonacci, prime_check) | 9100 (metrics) | `/metrics` |
| postgres | PostgreSQL 16              | System of record | 5432 | `pg_isready` |
| redis    | Redis 7 (AOF on)           | Job queue | 6379 | `PING` |

**Job lifecycle:** `queued → processing → completed | failed`.
The worker uses the *reliable queue* pattern (`BLMOVE` into a processing list). If a worker
crashes mid-job, the message stays in `jobs:queue:processing`, and the next worker to start
re-queues it (`Worker.recover()`).

**Design choices that matter for operations**
- 12-factor config: everything comes from env vars, and secrets come from Vault.
- JSON logs on stdout, with `service`, `level` and `job_id` fields, so Loki can parse them.
- RED metrics (rate, errors, duration) labelled by *templated* route, which keeps label cardinality bounded.
- Liveness and readiness are separate checks: readiness fails when the DB or Redis is down, so traffic is drained and the pod is not restarted.
- Containers are non-root with a read-only root filesystem, use multi-stage builds, and include a `test` stage that CI runs.

## 2. Delivery pipeline

```mermaid
flowchart LR
  dev([git push]) --> J[Jenkins]
  subgraph CI [Jenkins pipeline]
    direction TB
    L[Lint · Hadolint · OPA/conftest · TF validate · secret scan] --> U[Unit tests + coverage gate ≥80%]
    U --> B[Build images] --> T[Trivy image scan]
    T --> E[Ephemeral compose env:<br/>integration · Selenium Grid E2E · k6 · ZAP]
    E --> P[Push to registry]
  end
  J --> CI
  P -->|main| GS[gitops-bump staging] --> G[(Git: k8s/overlays)]
  P -->|tag v*| AP{Manual approval} --> GP[gitops-bump production] --> G
  G -->|watch| A[ArgoCD]
  A --> S[jobs-staging<br/>RollingUpdate]
  A --> PR[jobs-production<br/>Argo Rollouts]
  PR --> C[api: Canary + Prometheus analysis]
  PR --> BG[frontend: Blue-Green + preview smoke]
```

Jenkins never runs `kubectl apply`. It only commits an image tag to Git, and ArgoCD makes
the cluster match Git. That gives every change an audit trail and makes `git revert` a rollback.

## 3. Platform (Docker Desktop Kubernetes)

```mermaid
flowchart TB
  subgraph k8s [Kubernetes - docker-desktop]
    subgraph ingress-nginx
      IN[ingress-nginx<br/>LoadBalancer → localhost:80]
    end
    subgraph argocd
      ACD[ArgoCD]
    end
    subgraph argo-rollouts
      AR[Rollouts controller + dashboard]
    end
    subgraph monitoring
      PROM[Prometheus] --- GRAF[Grafana]
      LOKI[Loki] --- PT[Promtail DaemonSet]
      AM[Alertmanager]
    end
    subgraph vault
      V[Vault dev] --- VSO[Vault Secrets Operator]
    end
    subgraph gatekeeper-system
      GK[OPA Gatekeeper]
    end
    subgraph jobs-staging
      S1[frontend · api · worker · postgres · redis]
    end
    subgraph jobs-production
      P1[frontend Rollout · api Rollout · worker · postgres · redis]
    end
  end
  IN --> S1 & P1
  VSO -->|K8s Secret jobs-db-credentials| S1 & P1
  PROM -->|ServiceMonitor scrape| S1 & P1
  GK -.admission.-> S1 & P1
  ACD -->|sync| S1 & P1
```

Everything in this diagram is provisioned by **Terraform** (`terraform/`): Helm releases for the
add-ons, the namespaces (with ResourceQuota, LimitRange and Pod Security `restricted`), the Vault
KV secrets, policies and Kubernetes auth roles, and the ArgoCD project and applications.

## 4. Security layers

| Layer | Control | Where |
|-------|---------|-------|
| Code | Ruff lint, secret scanning (Trivy fs) | Jenkins *Static analysis* |
| Dependencies / images | Trivy HIGH/CRITICAL gate, `.trivyignore` with an owner and expiry per entry | Jenkins *Image scan* |
| Running app | OWASP ZAP baseline (DAST) | Jenkins *Ephemeral env* |
| Manifests (shift-left) | conftest + Rego in `security/opa/policies` | Jenkins, `make policy` |
| Admission (runtime) | Gatekeeper ConstraintTemplates (same rules) | `security/gatekeeper`, synced by ArgoCD |
| Secrets | Vault KV v2 → Vault Secrets Operator → K8s Secret; nothing in Git | `terraform/modules/vault-config` |
| Network | default-deny NetworkPolicies, explicit allow per flow | `k8s/base/networkpolicies.yaml` |
| Pods | non-root, read-only rootfs, drop ALL caps, seccomp RuntimeDefault, PSA `restricted` | all manifests |
