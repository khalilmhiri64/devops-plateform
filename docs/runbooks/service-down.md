# Runbook: Target down (`TargetDown`)

**Fires when:** Prometheus can't scrape a target for 2 minutes.

```bash
NS=jobs-production
kubectl get pods -n $NS -o wide
kubectl describe pod -n $NS <pod>          # Events: ImagePull? OOMKilled? Probe failures?
kubectl logs -n $NS <pod> --previous       # logs of the crashed container
kubectl get events -n $NS --sort-by=.lastTimestamp | tail -20
```

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `ImagePullBackOff` | tag not pushed to `localhost:5000` | push it, or roll back the tag in Git |
| `OOMKilled` | memory limit too low | raise the limit in Git; check for leaks |
| `CreateContainerConfigError` | `jobs-db-credentials` Secret missing | `kubectl get vaultstaticsecret -n $NS`; check that Vault is up and the VSO logs |
| Readiness failing, liveness OK | dependency down | see [high-error-rate.md](high-error-rate.md) |
| Rejected at admission | Gatekeeper constraint | `kubectl get constraints`; fix the manifest, don't exempt it |
