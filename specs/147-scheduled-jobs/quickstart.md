# Quickstart Validation: Scheduler and Worker

**Status**: Implemented; local verification results below. Use disposable PostgreSQL and synthetic tenant data. This document is not live deployment evidence.

## Preconditions

- Architecture/schema review is recorded in review.md; build both images from the same core revision.
- Apply migrations using the existing one-off release command. Neither runtime performs them.
- Create synthetic tenants A/B and existing active owner accounts through normal test/application setup. Use their actual opaque IDs in the placeholders below; never real invitation data.
- Prepare eligible old terminal and non-terminal invitation fixtures through the test harness. Cleanup must keep the non-terminal and tenant-B records.

## Register, preview and activate

```bash
reality-worker jobs list --json
reality-scheduler schedules create invitations.cleanup --tenant TENANT_A --actor OWNER_A --config-json '{}' --cron '0 3 * * *' --request-id CREATE_KEY --json
reality-scheduler schedules preview SCHEDULE_ID --tenant TENANT_A --actor OWNER_A --json
reality-scheduler schedules resume SCHEDULE_ID --tenant TENANT_A --actor OWNER_A --revision 1 --request-id RESUME_KEY --json
```

Expected: disabled schedule on create, five UTC hypothetical occurrences, no cleanup before explicit activation and due time. Reusing CREATE_KEY with identical input returns the same schedule; changed input conflicts. Use the actual returned revision for subsequent controls.

## Prove process separation

In tests, advance the clock to a due occurrence. Run:

```bash
reality-scheduler tick --tenant TENANT_A --max-runs 100 --max-seconds 25 --json
reality-worker runs list --tenant TENANT_A --actor OWNER_A --json
reality-worker once --tenant TENANT_A --max-runs 10 --max-seconds 25 --json
```

Expected: scheduler creates one pending run but deletes nothing. Worker consumes it and deletes at most 100 eligible tenant-A terminal invitations older than the existing 90-day boundary. No mail is sent. Scheduler never calls the handler and worker never creates a timed occurrence.

Then run the two continuous commands as separate services:

```bash
reality-scheduler work --poll-seconds 5
reality-worker work --poll-seconds 5
```

Close browser; work continues. Stop scheduler: existing queue can drain. Stop worker: scheduler leaves at most one unfinished run per schedule. Restart worker: no duplicate effect. Do not expect cron host polling to provide a shorter cadence than its wakeups.

## Manual execution and recovery

```bash
reality-worker jobs run invitations.cleanup --tenant TENANT_A --actor OWNER_A --config-json '{}' --request-id MANUAL_KEY --json
reality-worker once --tenant TENANT_A --json
reality-worker runs show RUN_ID --tenant TENANT_A --actor OWNER_A --json
```

Manual command enqueues only; repeat with the same key returns the same run and does not change schedule timing. No automatic retry with a new request key. Tests exercise claim-before-effect crash, effect-before-commit crash, committed-success/lost-response, stale token, child kill, disabled actor and pause/retry. Observe atomic database effect/run completion. Foreign-tenant lookup must be not found; status reads must perform no writes.

## Required checks after implementation

- Focused pytest paths from plan.md, then `make lint`, `make test`, `make spec-check`.
- Disposable migration upgrade/downgrade and constraint tests.
- Build both Dockerfiles; help/metadata need no database, startup never invokes Alembic, tick/once exit and neither image exposes an HTTP port.
- `make site-build`, `make web-build`, `make docs-build`, and `cd apps/web && npm run i18n:audit` for repository release gates.
- Record measured results here or in final review evidence; do not mark tasks or release checklist complete with required failures.

## Evidence status

Local acceptance on 2026-09-09 used disposable PostgreSQL databases and synthetic invitations only. No live Railway service was deployed and no schedule was activated in an existing company.

| Gate | Measured result |
|---|---|
| Complete backend suite (`make test` target, invoked as `pytest -q`) | 1,500 passed, 8 skipped in 348.47s. Seven skips cover retired server-rendered UI; the opt-in Docker skip was executed separately. |
| Final focused scheduling, invitation-delivery and catalog regressions | 59 passed, 1 skipped in 17.38s. The skipped test is the opt-in Docker smoke test executed separately below. Includes the added explicit ten-interval proof. |
| Ten controlled intervals with two competing workers | Ten distinct runs and exactly ten committed database effects; explicit acceptance test passed. |
| Migration | Upgrade from 0044 to head, downgrade and re-upgrade passed in disposable PostgreSQL; unique occurrence/manual request, unfinished-run and tenant/composite-FK refusal proofs passed. |
| Both final images | Built `reality-scheduler:spec147` and `reality-worker:spec147` from the same source. |
| Container acceptance | 1 passed in 16.96s with `REALITY_CONTAINER_SMOKE=1`; both help commands, registry metadata, idle worker, scheduler-to-worker queue handoff and both continuous services' heartbeat/SIGTERM exit 0 verified. |
| Compose | Base and development `background` profile configurations validated with `config --quiet`. |
| Lint / specification | `make lint`, `make spec-check`, `git diff --check` passed; 15 feature/canonical Markdown documents checked with no missing local links. |
| Frontend / documentation | `make site-build`, `make web-build`, `make docs-build` passed, including format checks, contract tests and bundled i18n audits. Web en/de/nl/es each cover 1,230/1,230 strings; site each covers 437/437. |
| Final Spec Kit analysis | 17 FR/DR, 32 tasks, 100% requirement-to-task coverage, no critical findings; review.md records findings and resolution. |

Run the optional container test only after building both tagged images:

```bash
cd packages/reality-core
REALITY_CONTAINER_SMOKE=1 ../../.venv/bin/pytest -q tests/test_scheduled_worker_deployment.py::test_built_images_share_queue_and_stop_cleanly
```

Recovery evidence includes expired-claim fencing, rollback before completion, durable success after lost acknowledgement, finite retry backoff, unknown-version failure isolation, unresolved suspension, a forcibly killed subprocess and pause after claim. Scoped cleanup preserves the other tenant, pending invitations and recent terminal records, and drains 101 eligible records as batches of 100 then 1.

The full-suite invocation began before the final additional ten-interval test and formatting/type-annotation cleanup; the final focused run covers those changes including migration and handler execution. No behavior-changing code was added after those final focused checks. These local checks do not certify production throughput or a live Railway installation.
