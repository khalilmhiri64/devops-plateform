# Deployment Strategies

| Environment | Workload | Strategy | Controller | Promotion | Rollback |
|-------------|----------|----------|-----------|-----------|----------|
| staging | api, frontend, worker | RollingUpdate (`maxSurge 1`, `maxUnavailable 0`) | Deployment | automatic on merge to `main` | `git revert` / `rollout undo` |
| production | **api** | **Canary** 20 → 40 → 60 → 80 → 100% | Argo Rollouts | automatic if analysis passes | automatic on failed analysis |
| production | **frontend** | **Blue-Green** | Argo Rollouts | **manual** after preview smoke test | instant (`abort`), blue kept 120 s |
| production | worker | RollingUpdate | Deployment | automatic | `rollout undo` |

## Canary (API)

`k8s/components/rollouts/api-rollout.yaml`

1. ArgoCD applies the new image tag, and Argo Rollouts creates the canary ReplicaSet.
2. `setWeight: 20` runs 1 of 5 pods on the new version. Without a service mesh, traffic splits by pod ratio through the `api` Service.
3. **Background analysis** (`api-success-rate`) runs every minute for the whole rollout. It fails if the success rate of the *canary pods* drops below 95% twice.
4. After a 2-minute pause, an **inline analysis** (`api-latency`) checks that canary p95 latency is below 500 ms.
5. Weight steps up through 40, 60 and 80, then reaches 100%.
6. Any failed analysis aborts the rollout: traffic returns to the stable ReplicaSet within seconds, and the Rollout is marked `Degraded`.

Watch it:
```bash
kubectl argo rollouts get rollout api -n jobs-production --watch
```

## Blue-Green (frontend)

`k8s/components/rollouts/frontend-rollout.yaml`

1. The new ReplicaSet (green) comes up behind `frontend-preview` (http://preview.jobs.localtest.me).
2. `prePromotionAnalysis` runs a Kubernetes Job that curls the preview 3 times.
3. `autoPromotionEnabled: false`: the pipeline (or a human) runs `scripts/smoke-test.sh` against the preview, then runs
   `kubectl argo rollouts promote frontend -n jobs-production`.
4. The `frontend` Service selector switches atomically to green. Blue stays up for 120 s (`scaleDownDelaySeconds`) so rollback is instant.

## Why different strategies?

- The **API** is stateless and serves many small requests, so error rate and latency are meaningful as soon as a few percent of traffic hits it. Canary limits the blast radius and decides automatically.
- The **frontend** is a static bundle, and mixing two versions can break a user's session (old HTML loading new JS). Blue-green guarantees every user sees exactly one version and allows a human visual check.
- **Schema changes** follow expand/contract: add columns in release N (both versions work), stop using old columns in N+1, drop them in N+2. That keeps rollback safe under every strategy.
