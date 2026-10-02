# Tasks: Integrate account defaults

Input: approved spec and Constitution-PASS plan. Language: English.

## Design gates

- [x] T001 Record approved concrete scope in `specs/332-integrate-account-defaults/spec.md`.
- [x] T002 Research identity/role/lock/view/migration decisions in `specs/332-integrate-account-defaults/plan.md` and `research.md`.
- [x] T003 Review requirements checklist and analyze spec/plan/task consistency before implementation.

## Tests first

- [x] T004 [US1] [FR-001, FR-002, FR-003, FR-004, FR-005, FR-007, FR-008] Add schema, service switch/repeat, revision/stale, tenant/role, uniqueness, view-write rejection and read-only tests in `packages/reality-core/tests/test_account_defaults.py`; observe red before implementation. Reuse `tests/finance/test_accounts.py` provenance tests.
- [x] T005 [US2] [FR-001, FR-002, FR-005, FR-006, FR-007, FR-008] Add populated migration/rollback and mismatched-role refusal tests in `packages/reality-core/tests/test_account_default_migration.py` with exact account/authority/schema comparisons and cross-tenant equal IDs.

## Implementation

- [x] T006 [US1] [FR-001, FR-002, FR-007, FR-008] Add typed marker/constraints and readonly logical view registration in `packages/reality-core/src/reality/db/core.py`; share existing view DDL support in `db/schema_views.py`, `db/cost_projections.py` and `migrations/env.py`.
- [x] T007 [US1] [FR-002, FR-003, FR-004, FR-005, FR-008] Switch production writes/bootstrap to marked accounts, retaining canonical read-only logical view readers in `packages/reality-core/src/reality/services/finance/accounts.py`, transferring IDs atomically under unchanged finance locks/revisions.
- [x] T008 [US2] [FR-001, FR-005, FR-006, FR-007, FR-008] Implement frozen locked copy/parity/retirement/rollback in `packages/reality-core/migrations/versions/0118_account_defaults.py`.
- [x] T009 [US1/US2] [FR-003, FR-005, FR-007] Adapt cleanup/missing-default fixtures in `packages/reality-core/tests/test_postgresql_integration.py`, `tests/finance/test_settlement_flows.py` and historical schema/index expectations (including the pinned 0075/0076 cache job specimens) where needed; adapt shared company deletion/counting to skip compatibility views and verify existing deletion regressions; retain original refusal/provenance assertions.

## Verification and review

- [x] T010 [US1] [FR-002, FR-004, FR-008] Prove competing selections and stale revisions with separate connections in `packages/reality-core/tests/test_account_defaults.py`.
- [x] T011 [US2] [FR-001, FR-005, FR-006, FR-007] Run populated migration, old-revision rollback and shared cost-view regressions; record results in `specs/332-integrate-account-defaults/verification.md`.
- [x] T012 [FR-001–FR-008] Update `docs/DATA_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/SPEC_COVERAGE_MATRIX.md` and the settings audit disposition; run documentation catalog generation/check without new vocabulary.
- [x] T013 Run complete backend, lint, spec and diff gates; record exact failures/rechecks, keeping this task open while its required gate is red.
- [x] T014 Run web/i18n/docs gates and final independent Constitution/migration/service review; record review and evidence before completion.

## Ordering and traceability

T001–T003 gate T004. T004/T005 precede T006/T007/T008. Domain/storage before services,
then migration and compatibility adapters; no new tool/adapter behavior. T009–T011
prove original contracts, then T012–T014 establish documentation and final evidence.

| Requirement | Planned tests | Implementation |
| --- | --- | --- |
| FR-001 | T004, T005, T011 | T006, T008 |
| FR-002 | T004, T005, T010 | T006, T007 |
| FR-003 | T004, T009 | T007, T009 |
| FR-004 | T004, T010 | T007 |
| FR-005 | T004, T005, T009, T011 | T007, T008 |
| FR-006 | T005, T011 | T008 |
| FR-007 | T004, T005, T009, T011 | T006, T008 |
| FR-008 | T004, T005, T010 | T006, T007, T008 |

SC-001/002 map to T005/T011; SC-003 maps T004/T009; SC-004 maps T010.
