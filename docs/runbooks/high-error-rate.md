# Runbook: API high error rate (`ApiHighErrorRate`)

**Fires when:** more than 5% of API responses are 5xx for 5 minutes.

## Triage (≤ 5 min)
1. Grafana → *Jobs Platform Overview* → "Requests by route": which route is failing?
2. Was there a deploy? `kubectl argo rollouts get rollout api -n jobs-production`, or check ArgoCD history.
3. Check the dependencies through the readiness endpoint:
   ```bash
   kubectl -n jobs-production port-forward svc/api 8000:8000 & curl -s localhost:8000/health/ready
   ```
4. Look at the logs in Grafana → Explore → Loki:
   `{namespace="jobs-production", service="jobs-api", level="ERROR"}`

## Mitigate
| Cause | Action |
|-------|--------|
| Canary in progress | `kubectl argo rollouts abort api -n jobs-production` (normally automatic) |
| Recent full release | [rollback.md](rollback.md) |
| `redis: down` in readiness | `kubectl -n jobs-production rollout restart deploy/redis`; API returns 503 on POST until it's back |
| `database: down` | `kubectl -n jobs-production get pod -l app.kubernetes.io/name=postgres`; check PVC/events |

## Follow-up
Write a post-incident review. Add a regression test at the lowest layer of the pyramid that would have caught this.
