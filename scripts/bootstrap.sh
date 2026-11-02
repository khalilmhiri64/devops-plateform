#!/usr/bin/env bash
# One-shot setup of the Kubernetes platform on Docker Desktop.
#   GITOPS_REPO_URL=https://github.com/you/devops-platform.git scripts/bootstrap.sh
set -euo pipefail
cd "$(dirname "$0")/.."

: "${GITOPS_REPO_URL:?set GITOPS_REPO_URL to the git repo ArgoCD should watch}"
CONTEXT="${KUBE_CONTEXT:-docker-desktop}"
log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

for bin in docker kubectl terraform; do
  command -v "$bin" >/dev/null || { echo "missing required tool: $bin" >&2; exit 1; }
done

log "Checking Kubernetes context '$CONTEXT'"
kubectl config use-context "$CONTEXT" >/dev/null
kubectl cluster-info >/dev/null

log "Starting local image registry on localhost:5000"
docker inspect registry >/dev/null 2>&1 || docker run -d --restart=always -p 5000:5000 --name registry registry:2

cd terraform
terraform init -input=false
TF_VARS=(-var "gitops_repo_url=${GITOPS_REPO_URL}" -var "kube_context=${CONTEXT}")

log "Phase 1/2: cluster add-ons and namespaces (Vault not reachable yet)"
terraform apply -input=false -auto-approve "${TF_VARS[@]}" -var enable_vault_config=false \
  -target=module.addons -target=module.namespaces

log "Waiting for Vault to answer through the ingress"
for _ in $(seq 1 60); do
  curl -fsS http://vault.localtest.me/v1/sys/health >/dev/null 2>&1 && break
  sleep 5
done

log "Phase 2/2: Vault secrets/auth and ArgoCD applications"
terraform apply -input=false -auto-approve "${TF_VARS[@]}"
cd ..

log "Building and pushing initial images (tag 0.1.0)"
for svc in api worker frontend; do
  target=$([ "$svc" = frontend ] && echo "" || echo "--target runtime")
  # shellcheck disable=SC2086
  docker build $target --build-arg VERSION=0.1.0 -t "localhost:5000/jobs-$svc:0.1.0" "services/$svc"
  docker push "localhost:5000/jobs-$svc:0.1.0"
done

log "Done."
terraform -chdir=terraform output urls
echo
echo "ArgoCD admin password: $(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d)"
