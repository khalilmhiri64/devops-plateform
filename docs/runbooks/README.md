# Runbooks

| Alert / situation | Runbook |
|-------------------|---------|
| `ApiHighErrorRate` | [high-error-rate.md](high-error-rate.md) |
| `ApiHighLatencyP95` | [high-latency.md](high-latency.md) |
| `QueueBacklog` | [queue-backlog.md](queue-backlog.md) |
| `TargetDown` | [service-down.md](service-down.md) |
| Bad release / need to undo | [rollback.md](rollback.md) |
| Releasing to production | [release.md](release.md) |
| Fresh machine setup | [bootstrap.md](bootstrap.md) |

Every runbook follows: **Symptoms → Triage (≤5 min) → Mitigate → Resolve → Follow-up**.
Mitigate first (restore service), then find root cause.
