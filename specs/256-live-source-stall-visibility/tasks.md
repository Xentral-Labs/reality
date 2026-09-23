# Tasks: Live Source Stall Visibility and Recovery

**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

## Phase 1 — Suspension instead of death (FR-006, FR-007, FR-007a)

- [x] T001 `scheduled_job.resume_after` and `scheduled_job_run.failure_detail` on the models, with the partial recovery index
- [x] T002 Migration `0091_schedule_recovery`
- [x] T003 `_failed` classifies `INFRASTRUCTURE_CODES` and draws a 4–8 h recovery moment
- [x] T004 `_revive_suspended` at the start of the scheduler sweep; production resumes from now, the interval is not replayed
- [x] T005 Owner controls and authorization refusals clear `resume_after`
- [x] T006 `tests/test_live_source_recovery.py` — suspend, stay stopped, revive without backlog, suspend again, owner control settles it

## Phase 2 — The reason survives (FR-017, FR-001–FR-003)

- [x] T007 `jobs/runner.py` returns a bounded failure detail, cut before statement and parameters
- [x] T008 `record_failure`/`_failed` retain it on the run
- [x] T009 `demo_data._stall` and `_overdue_since`; `status` returns `stall` and a derived state per kind
- [x] T010 `tests/test_demo_data_compatibility.py::test_status_states_why_a_source_stopped`

## Phase 3 — Existing companies run again (FR-011, FR-012)

- [x] T011 `preview` resolves leniently for an established connection; items match by name and unit, not by their human number
- [x] T012 Unresolved references never travel on as references
- [x] T013 Compatibility tests including the positive control that they fail without the change

## Phase 4 — Seen without opening it (FR-015, FR-016)

- [x] T014 `stallHeadline`, `stallCause`, `sourceNeedsAttention` in `demoDataSummary.ts`
- [x] T015 Stall line and new badge states on the simulation panel
- [x] T016 Attention badge and stall line on the integrations card; one shared status read (`useDemoDataStatus`)
- [x] T017 Live state in the `demo_data` row of the source table; its Settings action opens the simulation
- [x] T018 `scripts/demo-stall.test.mjs`; dictionary entries for de/nl/es
- [x] T019 Browser proof `scripts/demo-data-stall-browser.mjs`

## Phase 5 — Contracts and verification

- [x] T020 `docs/features/scheduled-jobs.md` and `docs/features/company-setup-demo.md`
- [x] T021 Complete backend suite, web typecheck, i18n audit, ruff
