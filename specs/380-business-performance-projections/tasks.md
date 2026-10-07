# Tasks: Incremental Business performance
## Specification and design
- [x] T001 Review explicit user scope and dependencies in `spec.md`.
- [x] T002 Record Constitution PASS and design in `plan.md`, `research.md`, `data-model.md`, `contracts/business.md`.
- [x] T003 Analyze requirement coverage and consistency before implementation.
## US1 - Orders
- [x] T004 [US1] [FR-001] [FR-002] [FR-003] [FR-008] [DR-001] [DR-003] Add failing oracle, replay, amendments, correction and clock tests in `packages/reality-core/tests/test_business_projection.py`.
- [x] T005 [US1] [FR-001] [FR-002] [FR-003] [DR-001] [DR-003] Implement disposable rows, canonical-reader derivation, contribution deltas and clock transitions in `db/business_projection.py`, `services/business_projection_derivation.py`, `services/business_projection.py`; integrate `services/projections.py`, `services/projection_jobs.py`.
## US2 - Mail
- [x] T006 [US2] [FR-004] [FR-008] Add acknowledgement/reply/lineage oracle tests in `tests/test_business_projection.py`.
- [x] T007 [US2] [FR-004] Derive exact correspondence and contribution deltas in `services/business_projection_derivation.py`, `services/business_projection.py`.
## US3 - Recover and read
- [x] T008 [US3] [FR-005] [FR-006] [FR-007] [DR-002] Add paging/isolation/read-only/restart/concurrent rebuild and API tests in `tests/test_business_projection.py`.
- [x] T009 [US3] [FR-005] [FR-006] [FR-007] [DR-002] Implement bounded builds/events, indexed detail pagination and processing visibility in `services/business_projection.py`, additive migration, `web/interactions_api.py`, `apps/web/src/api.ts`, `apps/web/src/unified/BusinessLive.tsx`.
## Verification
- [x] T010 [FR-009] Add reproducible synthetic load runner in `scripts/benchmark_business_projection.py` and million-order multi-tenant/100-viewer plan/results in `benchmark.md`.
- [x] T011 [FR-008] [FR-009] Measure actual oracle/load evidence and remaining limits in `quickstart.md`, `benchmark.md`.
- [x] T012 Run required backend/migration/spec/lint/web/i18n/docs/browser checks; update `quickstart.md` truthfully.
- [x] T013 Review final diff and update `docs/features/business-performance.md`, `docs/features/scheduled-jobs.md`, `docs/DATA_MODEL.md`, `docs/WEB_SPEC.md`; create follow-up PR.

Capacity acceptance SC-004 remains open: successful smoke API latency does not satisfy the unverified million-order/sustained-load trial or the measured shared-worker lag above ten seconds. T010/T011 record implemented measurement work, not a production release approval.

Execution and review tasks above record completed implementation work and gate invocations. Full regression success is determined by the current-head PR checks and recorded in its verification section; pending/red checks are not completion or release approval. The acceptance checklist stays open for SC-004.
