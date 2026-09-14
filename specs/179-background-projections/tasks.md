# Tasks: Background projections and responsive Inspector

**Input**: spec.md, plan.md, research.md, data-model.md, contracts/projections.md.
**Gate**: Product scope accepted; specific internal-job schema approved by the owner on 2026-09-12. Background implementation starts only after all Constitution rows pass and analysis has no critical finding.

## Phase 1: Specification and design
- [x] T001 Record accepted scope, scenarios and measurable requirements in `specs/179-background-projections/spec.md`.
- [x] T002 Measure catalog and inspect scheduling, projection and read boundaries in `specs/179-background-projections/research.md`.
- [x] T003 Record human schema decision and all-PASS Constitution review in `specs/179-background-projections/plan.md` and `data-model.md`.
- [x] T004 Run cross-artifact analysis and record resolved findings in `specs/179-background-projections/quickstart.md`.

## Phase 2: User Story 1 — Responsive catalog
- [x] T005 [US1] [FR-001] Add failing cache, mutation-isolation, failure-retry and raw-validation tests in `packages/reality-core/tests/test_application_catalog.py` and endpoint coverage in `test_http_boundary.py`.
- [x] T006 [US1] [FR-002] Add collapsed/expanded/search browser assertions in `apps/web/scripts/unified-inspector-browser.mjs`.
- [x] T007 [US1] [FR-001] Add separate runtime cache and startup/HTTP usage in `packages/reality-core/src/reality/catalogs.py`, `web/app.py`, `web/api.py`.
- [x] T008 [US1] [FR-002] Lazily mount disclosure bodies in `apps/web/src/unified/InspectorCatalog.tsx`.
- [x] T009 [US1] [FR-001] [FR-002] Measure warm improvement and run catalog/browser acceptance; record evidence in `specs/179-background-projections/quickstart.md`.

## Phase 3: User Story 2 — Background stored projections
- [x] T010 [US2] [FR-003] [FR-005] Add dependency, coalescing, publication, rollback and tenant proofs in `packages/reality-core/tests/test_projection_jobs.py` before services change.
- [x] T011 [US2] [FR-004] [FR-009] Add internal-job authorization, queue-cap, archive, bootstrap, clock and real-connection retry/concurrency proofs in `packages/reality-core/tests/test_projection_jobs.py`.
- [x] T012 [US2] [FR-004] [FR-011] Add upgrade/downgrade and invalid-actor/index tests in `packages/reality-core/tests/test_projection_job_migration.py`.
- [x] T013 [US2] [FR-004] Implement approved run metadata constraint/index in `packages/reality-core/src/reality/db/scheduled_jobs.py` and `migrations/versions/0057_projection_jobs.py`.
- [x] T014 [US2] [FR-003] [FR-005] Split selected canonical builders and scoped usage, audit event dependencies in `packages/reality-core/src/reality/services/projections.py`, `services/core.py`, `config/business_event_catalog.yaml`.
- [x] T015 [US2] [FR-003] [FR-004] [FR-009] Implement committed-outbox eligibility, internal enqueue and allowlisted handler in `packages/reality-core/src/reality/services/projection_jobs.py`, `services/scheduled_jobs.py`, `jobs/handlers/projections.py`, `jobs/registry.py`.
- [x] T016 [US2] [FR-004] [FR-005] [FR-009] Wire bounded scheduler dispatch and consistent worker transactions in `packages/reality-core/src/reality/jobs/runtime.py`, `jobs/runner.py`; preserve claim fencing and regular-job fairness.
- [x] T017 [US2] [FR-003] [FR-004] [FR-005] [FR-009] Run independent background/recovery stories and record evidence in `specs/179-background-projections/quickstart.md`.

## Phase 4: User Story 3 — Pure reads and freshness
- [x] T018 [US3] [FR-006] [FR-007] [FR-010] Add read-with-builders/writes-forbidden, snapshot metadata, live MCP and pricing proofs in `packages/reality-core/tests/test_materialized_projections.py`, `test_projection_jobs.py`, `test_http_boundary.py`.
- [x] T019 [US3] [FR-008] Add initial/pending/failed/recovered browser cases and consistent financial totals proofs in `apps/web/scripts/unified-inspector-browser.mjs`, `packages/reality-core/tests/test_payment_projection_performance.py`.
- [x] T020 [US3] [FR-006] [FR-007] [FR-010] Remove implicit refresh, add snapshot/freshness service and live canonical pricing in `packages/reality-core/src/reality/services/projections.py`; preserve explicit live contracts in `services/read_contracts.py`, `tools/application.py`.
- [x] T021 [US3] [FR-006] [FR-007] [FR-008] Adapt stored page/totals/HTTP endpoints and consistent live payments in `packages/reality-core/src/reality/web/read_models.py`, `web/api.py`.
- [x] T022 [US3] [FR-007] [FR-008] [FR-010] Add typed freshness response and shared notice to `apps/web/src/api.ts`, `unified/ProjectionDataDialog.tsx` and affected financial/workspace pages; update `localization.tsx`.
- [x] T023 [US3] [FR-010] Label stored/live/parameterized modes in `packages/reality-core/config/projection_catalog.yaml`, `apps/web/src/unified/CatalogEntryDetails.tsx` and preserve searchable explanations.
- [x] T024 [US3] [FR-006] [FR-008] Update prior refresh-on-read acceptance tests to explicitly complete background work; record real browser/HTTP outcomes in `specs/179-background-projections/quickstart.md`.

## Phase 5: Complete verification and review
- [x] T025 [FR-011] Update `docs/features/scheduled-jobs.md`, `docs/WEB_SPEC.md`, `docs/WORKER_DEPLOYMENT.md` and executable model/catalog documentation with actual behavior and rollback.
- [x] T026 [FR-011] Run spec policy, Ruff and complete PostgreSQL suite; record output in `specs/179-background-projections/quickstart.md`.
- [x] T027 [FR-011] Run frontend build/i18n/contracts and affected browser suites; record output in `specs/179-background-projections/quickstart.md`.
- [x] T028 [FR-011] Run migration checks, regenerate docs and run docs contracts/build; record output in `specs/179-background-projections/quickstart.md`.
- [x] T029 [FR-011] Review final diff against spec/Constitution, update completed task markers only with green evidence in `specs/179-background-projections/tasks.md`.

## Dependencies and implementation strategy
T001–T004 → US1 → US2 → US3 → final gates, sequentially as requested. Tests precede the code they prove. Catalog is an independent deliverable with no business schema dependency; background/read-switch phases are kept together until worker and freshness proofs pass. No deployment or merge is implied. Potential parallel research was restricted to catalog profiling under the plan skill; implementation remains sequential.

## Requirement coverage
| Requirement | Test tasks | Implementation tasks |
|---|---|---|
| FR-001 | T005,T009 | T007 |
| FR-002 | T006,T009 | T008 |
| FR-003 | T010,T017 | T014,T015 |
| FR-004 | T011,T012,T017 | T013,T015,T016 |
| FR-005 | T010,T017 | T014,T016 |
| FR-006 | T018,T024 | T020,T021 |
| FR-007 | T018,T019 | T020,T021,T022 |
| FR-008 | T019,T024 | T021,T022 |
| FR-009 | T011,T017 | T015,T016 |
| FR-010 | T018,T019 | T020,T023 |
| FR-011 | T026,T027,T028 | T025,T029 |

## Public reference follow-up (FR-010, FR-011)

- [x] T030 Add failing documentation contracts for per-read modes, MCP defaults, Web variants and localized explanations.
- [x] T031 Extend the reference generator/model and Markdown renderers with verified read variants and refresh explanations.
- [x] T032 Render mode guidance in the interactive explorer and make it searchable.
- [x] T033 Regenerate documentation, run contracts/build/format/spec checks, verify responsive browser output and review the final diff.
