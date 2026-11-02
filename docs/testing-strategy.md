# Testing Strategy

The test pyramid, plus non-functional layers. Each layer runs where it gives the fastest useful feedback.

```
                ▲  E2E (Selenium Grid: Chrome + Firefox)       ~10    minutes   ephemeral env / staging
               ▲▲  Performance (k6 smoke / load / stress)      3      minutes   ephemeral env / staging
              ▲▲▲  Integration (real Postgres+Redis+worker)    ~6     seconds   ephemeral env
            ▲▲▲▲▲  Unit (pytest, fakeredis, SQLite)            ~55    seconds   every commit
  ─────────────────────────────────────────────────────────────────────────────────────────
   Static: ruff · hadolint · conftest/OPA · terraform validate · Trivy (fs, image) · ZAP baseline
```

| Layer | Location | Tooling | Runs in | Gate |
|-------|----------|---------|---------|------|
| Unit: API | `services/api/tests/unit` | pytest, FastAPI TestClient, fakeredis | Docker `test` stage | 100% pass, line coverage ≥ 80% |
| Unit: worker | `services/worker/tests` | pytest, fakeredis, SQLite | Docker `test` stage | same |
| Integration | `services/api/tests/integration` | pytest + requests against compose stack | Jenkins ephemeral env | 100% pass |
| E2E | `tests/e2e` | Selenium 4 Remote → Grid, Page Object Model, pytest-html, screenshot on failure | Jenkins ephemeral env | 100% pass (1 rerun allowed) |
| Performance | `tests/performance` | k6 | ephemeral env (smoke), staging (load, nightly) | p95 < 300 ms, errors < 1% |
| Security: SAST/secrets | repo | Trivy fs | every build | 0 secrets |
| Security: images | built images | Trivy image | every build | 0 fixable HIGH/CRITICAL |
| Security: DAST | running frontend | OWASP ZAP baseline | ephemeral env | rules in `zap-rules.tsv` |
| Policy | rendered manifests | conftest (Rego) + `conftest verify` policy unit tests | every build | 0 deny |
| Post-deploy | staging / preview | `scripts/smoke-test.sh`, k6 smoke, Argo analysis | after each deploy | blocks promotion |

## Practices

- **Hermetic unit tests.** No network or containers: Redis is replaced by `fakeredis` and Postgres by a temp SQLite file. The app factory `create_app(settings, redis_client)` exists so tests can inject dependencies.
- **Same image tested and shipped.** The `test` and `runtime` stages share the `build` stage, so the dependencies under test are byte-identical to what ships.
- **Ephemeral environments.** Every build gets its own compose project (`ci-<BUILD_NUMBER>`) and tears it down in `post { always }`, so builds can't interfere with each other.
- **Stable selectors.** The UI exposes `data-testid` attributes, and the Page Object (`tests/e2e/pages/home_page.py`) is the only place that knows them.
- **Flake handling.** The table re-renders every 2 s, so the page object re-queries on every poll and ignores `StaleElementReferenceException`. A single `--reruns 1` is a safety net, not a fix. Any test that needs it gets investigated.
- **Testing in production, safely.** Canary analysis queries Prometheus for the *new* ReplicaSet only (`rollouts_pod_template_hash`). That makes production metrics an automated test that can roll back.

## Running locally

```bash
make venv unit          # unit tests, no Docker
make up integration     # real stack
make e2e                # Selenium Grid (BROWSER=chrome,firefox make e2e)
make perf               # k6 smoke
make policy             # OPA (needs conftest + kustomize)
```
