# Network Addressing Plan

## 1. Docker Compose (local development)

Four user-defined bridge networks keep the tiers apart. `data` is `internal: true`, so it
has no route to the host or the internet.

| Network | Subnet | Gateway | Purpose | Internal |
|---------|--------|---------|---------|----------|
| `app` | 172.28.1.0/24 | 172.28.1.1 | frontend ↔ api, test runners, Selenium Grid | no |
| `data` | 172.28.2.0/24 | 172.28.2.1 | api/worker ↔ postgres/redis/vault | **yes** |
| `observability` | 172.28.3.0/24 | 172.28.3.1 | Prometheus, Grafana, Loki, Promtail | no |
| `ci` | 172.28.4.0/24 | 172.28.4.1 | Jenkins | no |

### Static assignments

| Host | Network(s) | IP | Container port | Host port |
|------|-----------|----|----------------|-----------|
| frontend | app | 172.28.1.10 | 8080 | **8080** |
| api | app / data | 172.28.1.20 / 172.28.2.20 | 8000 | **8000** |
| selenium-hub | app | 172.28.1.100 | 4444 | **4444** |
| worker (×2) | app, data | DHCP (.100+) | 9100 | – |
| postgres | data | 172.28.2.10 | 5432 | – |
| redis | data | 172.28.2.11 | 6379 | – |
| vault | data | 172.28.2.30 | 8200 | **8200** |
| prometheus | observability (+app) | 172.28.3.10 | 9090 | **9090** |
| grafana | observability | 172.28.3.11 | 3000 | **3000** |
| loki | observability | 172.28.3.12 | 3100 | **3100** |
| jenkins | ci | 172.28.4.10 | 8080 / 50000 | **8081** / 50000 |

Range convention inside each /24: `.1` gateway, `.10–.49` static services, `.100–.199`
test infrastructure, `.200–.254` reserved. Docker's DHCP hands out the rest.

Postgres and Redis publish **no** host ports, so they are reachable only from the `data` network.

## 2. Kubernetes (Docker Desktop)

| Range | CIDR | Notes |
|-------|------|-------|
| Pod network | 10.1.0.0/16 | Docker Desktop default |
| Service (ClusterIP) network | 10.96.0.0/12 | Docker Desktop default, `kube-dns` = 10.96.0.10 |
| Node | 192.168.65.0/24 | Docker Desktop VM |
| LoadBalancer | 127.0.0.1 (localhost) | Docker Desktop's built-in LB maps to the host |

### Ingress hostnames

`*.localtest.me` is public DNS that always resolves to 127.0.0.1, so no `/etc/hosts` edits are needed.

| Hostname | Namespace / Service | Purpose |
|----------|--------------------|---------|
| staging.jobs.localtest.me | jobs-staging / frontend:80 | Staging app |
| jobs.localtest.me | jobs-production / frontend:80 | Production (active / blue) |
| preview.jobs.localtest.me | jobs-production / frontend-preview:80 | Production preview (green) |
| argocd.localtest.me | argocd / argocd-server | GitOps UI |
| rollouts.localtest.me | argo-rollouts / dashboard | Canary / blue-green UI |
| grafana.localtest.me | monitoring / grafana | Dashboards + logs |
| prometheus.localtest.me | monitoring / prometheus | Metrics |
| vault.localtest.me | vault / vault | Secrets UI/API |

### In-cluster DNS names

| Name | Port |
|------|------|
| `api.jobs-<env>.svc.cluster.local` | 8000 |
| `frontend.jobs-<env>.svc.cluster.local` | 80 → 8080 |
| `postgres.jobs-<env>.svc.cluster.local` (headless) | 5432 |
| `redis.jobs-<env>.svc.cluster.local` | 6379 |
| `worker-metrics.jobs-<env>.svc.cluster.local` | 9100 |
| `kube-prometheus-stack-prometheus.monitoring.svc` | 9090 |
| `loki-gateway.monitoring.svc` | 80 |
| `vault.vault.svc` | 8200 |

## 3. Allowed traffic flows (NetworkPolicy matrix)

Every app namespace starts with **default-deny** for ingress and egress. Only these flows are allowed:

| From → To | frontend:8080 | api:8000 | worker:9100 | postgres:5432 | redis:6379 | kube-dns:53 |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| ingress-nginx ns | ✅ | ✅ | | | | |
| frontend | | ✅ | | | | ✅ |
| api | | | | ✅ | ✅ | ✅ |
| worker | | | | ✅ | ✅ | ✅ |
| monitoring ns | | ✅ | ✅ | | | |
| analysis Job (prod) | ✅ | | | | | ✅ |
| anything else | ❌ | ❌ | ❌ | ❌ | ❌ | |

> Note: Docker Desktop's default CNI does not enforce NetworkPolicy. The policies are still
> validated and applied, and they are enforced on any CNI that supports them (Calico, Cilium).
