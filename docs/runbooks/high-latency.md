# Runbook: API high latency (`ApiHighLatencyP95`)

**Fires when:** p95 latency is above 500 ms for 10 minutes.

## Triage
1. Is it all routes or one? Check the Grafana "Latency percentiles" panel and filter by `path`.
2. CPU throttling? `kubectl top pod -n jobs-production -l app.kubernetes.io/name=api`. Compare with the 500m limit.
3. HPA at max? `kubectl get hpa -n jobs-production`
4. Postgres slow? `kubectl exec -n jobs-production postgres-0 -- psql -U jobs -c "select pid, now()-query_start as age, query from pg_stat_activity where state<>'idle' order by age desc limit 5;"`

## Mitigate
- Scale out: `kubectl argo rollouts scale api --replicas 8 -n jobs-production`. The HPA reconciles later.
- A large `GET /api/jobs` offset scan points to a missing index. The `status` and `type` columns are indexed; check any new filters.

## Resolve
Reproduce in staging with `k6 run tests/performance/load.js`, fix, and confirm the p95 threshold passes before releasing.
