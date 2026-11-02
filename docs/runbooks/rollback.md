# Runbook: Rollback

Choose the fastest option that's safe, then make Git match reality.

| Situation | Command | Time |
|-----------|---------|------|
| Canary/blue-green **in progress** | `kubectl argo rollouts abort api -n jobs-production` (or `frontend`) | seconds |
| Production release **finished** | `kubectl argo rollouts undo api -n jobs-production` | ~1 min |
| Staging | `kubectl -n jobs-staging rollout undo deploy/api` | ~1 min |
| Any env, the GitOps way (preferred) | `scripts/rollback.sh <env> <known-good-version>` | ArgoCD sync ~1 min |

`scripts/rollback.sh production` (with no version) does the right abort or undo automatically.

**Important:** ArgoCD `selfHeal` will re-apply whatever is in Git. After an imperative
abort or undo, always pin the good version in Git (`scripts/rollback.sh <env> <version>`),
or the bad version comes back on the next sync.

Find the previous good version:
```bash
git log --oneline -- k8s/overlays/production/kustomization.yaml | head
```
