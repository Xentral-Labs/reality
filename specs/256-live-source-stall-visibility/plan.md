# Implementation Plan: Live Source Stall Visibility and Recovery

**Spec**: [spec.md](./spec.md) · **Branch**: `256-live-source-recovery` · **Created**: 2026-09-23

## Constitution Check

- **Source → Evidence → Reality**: untouched. Scheduling is execution metadata, never business authority.
- **No derivation stored as authority**: the stall reason, the overdue state and the live state shown in the integrations overview are derived at read time from the retained schedule and occurrence rows. The only new stored fact is *when a suspended schedule may try again*, which is timing, not an observation.
- **Shortest true relationship**: the recovery moment belongs on the schedule that was suspended. No new table, no duplication onto the connection.
- **Tenant scope**: every new query filters `tenant_id`; the recovery sweep runs inside the existing per-tenant scheduler sweep and its tenant lock.
- **Shared services**: Web, MCP, CLI and API keep reading `services.demo_data.status`; the badge and the overview state are presentation of that same read.
- **Confirmation**: no new mutating control. Automatic recovery applies only to a schedule the owner had left running and that an infrastructure failure interrupted.
- **Storage discipline**: one nullable timestamp column, one Alembic migration, no data backfill.

## Decisions

### D1 — Suspension instead of death (FR-006, FR-007, FR-007a)

`_failed()` classifies the error code. An **infrastructure** code (`database_error`, `handler_timeout`, `child_exited`: the work never reached a business verdict) suspends the schedule: `enabled = False` **and** `resume_after = now + U(4h, 8h)`. Any other code stops it exactly as today, with `resume_after = None`.

`enabled = False` is what keeps a suspended schedule from accumulating occurrences while the database is away, so FR-007a needs no extra mechanism.

`materialize_due()` revives before it selects: a schedule with `resume_after <= now` becomes `enabled = True`, `resume_after = None`, `next_run_at = now`. Production therefore resumes from the moment recovery succeeds. If the failure persists, the next failure suspends it again with a fresh recovery moment, so the source retries every four to eight hours for as long as it takes. The interval is drawn per suspension so that many tenants do not wake up together.

Owner controls (`pause`, `stop`, `disconnect`, `cancel`) clear `resume_after`: what a person stopped stays stopped.

### D2 — Compatibility by what the source uses (FR-011)

`demo_data.preview()` currently requires every entry of the *current* canonical catalog to resolve in the company, and raises otherwise. For a company that already has a connection it now resolves leniently: a catalog entry the company does not have is omitted from the reference map instead of raising.

The captured `config.references` of the running schedule are still compared in `authorize()`/`authorize_settle()`, so a reference the source actually uses that disappeared or became ambiguous still refuses — with `incompatible_references`, which is the truthful code, rather than a blanket `not_authorized`. A **new** connection keeps the strict path: a fresh company is still established against the full current catalog.

### D3 — Reason survives the process boundary (FR-017)

`jobs/runner.py` discards the `SQLAlchemyError` and sends the child's stderr to `DEVNULL`, so the cause of the observed outage exists nowhere. The child now returns a bounded `detail` (exception class plus a truncated message, no parameters, no connection string), the parent logs it with the job outcome and stores it on the run as its failure detail.

### D4 — One place to look (FR-015, FR-016)

The integrations overview already carries the simulation card. It gains the attention badge and the stall line, the `demo_data` row in the systems table shows the live state beside the source's own enabled state, and its **Settings** action opens the simulation page: for a source whose configuration *is* its simulation, two separate places would be a lie about where the settings live.

## Changes

| Area | File | Change |
|---|---|---|
| Schema | `db/scheduled_jobs.py`, `migrations/versions/0091_schedule_recovery.py` | `scheduled_job.resume_after` nullable timestamp, partial index on suspended schedules |
| Schema | `db/scheduled_jobs.py`, same migration | `scheduled_job_run.failure_detail` bounded text |
| Domain/services | `services/scheduled_jobs.py` | `_failed` classification, revive step in `materialize_due`, control clears `resume_after`, `_stall` derivation |
| Services | `services/demo_data.py` | lenient reference resolution for an established connection, `stall`/`overdue` in `status` |
| Jobs | `jobs/runner.py` | bounded failure detail across the child boundary |
| Web | `unified/DataSourcesPage.tsx`, `unified/DemoDataSource.tsx`, `components/DemoDataIntegration.tsx`, `api.ts`, `localization.tsx` | attention badge, live state in the overview, stall line, settings routing |

## Tests

- `tests/test_scheduled_job_recovery.py`: infrastructure failure suspends with a recovery moment in the 4–8 h window; permanent refusal does not; revive resumes without replaying the interval; pause clears the recovery moment; a persisting failure suspends again.
- `tests/test_demo_data_compatibility.py`: a company missing a catalog entry added later still resumes; a captured reference that disappeared still refuses with `incompatible_references`; a fresh connection still requires the full catalog.
- `tests/test_demo_data_status.py`: stall kinds and the overdue state in the status payload; no interface renders attention without a reason.
- `apps/web/scripts/demo-data-stall-browser.mjs`: badge, overview state and settings routing.
- Regression: existing `test_scheduled_jobs*`, `test_demo_data_intake`, `test_home_readiness`.

## Rollback

Revert the code; the column may stay. A suspended schedule then behaves as a disabled one, exactly as before this feature.
