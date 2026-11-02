# Runbook: Production release

1. Make sure `main` is green and staging smoke tests passed (Jenkins).
2. Tag: `git tag v1.4.0 && git push origin v1.4.0`
3. Jenkins builds the tag, runs the full test suite, and **pauses at "Approve production"**. A member of `release-managers` approves.
4. Jenkins commits the new tag to `k8s/overlays/production`, and ArgoCD syncs.
5. Watch: http://rollouts.localtest.me (or `kubectl argo rollouts get rollout api -n jobs-production -w`)
   - The API canary progresses automatically if the analysis passes.
   - The frontend green version waits on http://preview.jobs.localtest.me. Jenkins smoke-tests it and promotes.
6. Check Grafana for 15 minutes after reaching 100%.
7. If anything looks wrong, see [rollback.md](rollback.md).
