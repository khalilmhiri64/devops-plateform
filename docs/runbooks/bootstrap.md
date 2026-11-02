# Runbook: Bootstrap a fresh machine

## Prerequisites
- Docker Desktop ≥ 4.30 with **Kubernetes enabled** (Settings → Kubernetes), at least 6 CPU / 10 GB RAM allocated
- `kubectl`, `terraform` ≥ 1.6, `kustomize`, `conftest`, `trivy`, `make`, Python 3.12
- A Git repository (GitHub etc.) holding this project. ArgoCD needs a URL to watch.

## Steps
```bash
# 1. Local stack only (no Kubernetes needed)
cp .env.example .env
make up                 # http://localhost:8080
make up-full            # + Grafana :3000, Prometheus :9090, Vault :8200, Jenkins :8081

# 2. Kubernetes platform
GITOPS_REPO_URL=https://github.com/<you>/devops-platform.git make bootstrap
```
`scripts/bootstrap.sh` will:
1. Start a registry on `localhost:5000`.
2. Run `terraform apply` phase 1: ingress-nginx, ArgoCD, Argo Rollouts, kube-prometheus-stack, Loki, Promtail, Vault, the Vault Secrets Operator, Gatekeeper, and the namespaces.
3. Wait for Vault, then run phase 2: Vault secrets, policies and auth, plus the ArgoCD applications.
4. Build and push the `0.1.0` images. ArgoCD then deploys staging and production.

## Verify
```bash
kubectl get applications -n argocd            # all Synced / Healthy
scripts/smoke-test.sh http://staging.jobs.localtest.me
scripts/smoke-test.sh http://jobs.localtest.me
```

## Teardown
```bash
terraform -chdir=terraform destroy -var gitops_repo_url=...
make down
```
