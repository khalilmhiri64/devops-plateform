#!/usr/bin/env bash
# Emergency rollback. See docs/runbooks/rollback.md for when to use which option.
#   scripts/rollback.sh production            # abort in-flight rollout / undo last
#   scripts/rollback.sh staging 0.1.41        # pin a known-good version via GitOps
set -euo pipefail
ENV="${1:?environment}"; NS="jobs-${ENV}"; VERSION="${2:-}"

if [[ -n "$VERSION" ]]; then
  exec "$(dirname "$0")/gitops-bump.sh" "$ENV" "$VERSION"
fi

if [[ "$ENV" == production ]]; then
  for r in api frontend; do
    phase=$(kubectl argo rollouts status "$r" -n "$NS" --timeout 1s 2>/dev/null || true)
    if [[ "$phase" =~ Progressing|Paused ]]; then
      kubectl argo rollouts abort "$r" -n "$NS"           # back to stable immediately
    else
      kubectl argo rollouts undo "$r" -n "$NS"            # previous revision
    fi
  done
else
  kubectl -n "$NS" rollout undo deploy/api
  kubectl -n "$NS" rollout undo deploy/frontend
  kubectl -n "$NS" rollout undo deploy/worker
fi
echo "NOTE: ArgoCD selfHeal will re-apply Git on the next sync. Pin the good version in Git:"
echo "  scripts/rollback.sh $ENV <known-good-version>"
