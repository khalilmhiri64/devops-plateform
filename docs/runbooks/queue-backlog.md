# Runbook: Queue backlog (`QueueBacklog`)

**Fires when:** more than 100 jobs wait in `jobs:queue` for 10 minutes.

## Triage
1. Are workers running? `kubectl get pods -n jobs-production -l app.kubernetes.io/name=worker`
2. Are they processing? Check `rate(worker_jobs_processed_total[5m])` in Prometheus.
3. Are jobs stuck in processing?
   ```bash
   kubectl exec -n jobs-production deploy/redis -- redis-cli LLEN jobs:queue
   kubectl exec -n jobs-production deploy/redis -- redis-cli LLEN jobs:queue:processing
   ```
4. Worker errors: `{service="jobs-worker", level="ERROR"}` in Loki.

## Mitigate
- Scale workers: `kubectl scale deploy/worker -n jobs-production --replicas 6`
- Orphaned messages in `:processing` are re-queued automatically when a worker starts:
  `kubectl rollout restart deploy/worker -n jobs-production`

## Follow-up
If the load is sustained, raise the worker replica count in `k8s/overlays/production` (through Git) or add a KEDA scaler on queue length.
