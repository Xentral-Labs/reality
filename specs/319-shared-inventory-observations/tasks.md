# Tasks: Shared Inventory Observations

## Phase 1: Specification and Design Gates

- [x] T001 Confirm owner-approved scope and requirement quality in `spec.md`.
- [x] T002 Check all Constitution rows in `plan.md`.
- [x] T003 Analyze `spec.md`, `plan.md` and `tasks.md` for critical findings (5/5 requirements covered; no critical or high findings).

## Phase 2: User Story 1

- [x] T004 [US1] [FR-001] [FR-002] [FR-003] [FR-004] Add failing comparison, revision, correction, location, filter and tenant tests in `packages/reality-core/tests/test_shared_inventory_observations.py`.
- [x] T005 [US1] [FR-001] [FR-002] [FR-003] [FR-004] Implement a shared position query in `packages/reality-core/src/reality/services/inventory_reads.py`; delegate from `services/core.py` and `web/read_models.py`.
- [x] T006 [US1] [FR-001] Verify projection equivalence in `packages/reality-core/tests/test_shared_inventory_observations.py` and document shared derivation in `docs/features/inventory.md`.

## Phase 3: User Story 2

- [x] T007 [US2] [FR-005] Add projection metadata regression in `packages/reality-core/tests/test_shared_inventory_observations.py`.
- [x] T008 [US2] [FR-005] Correct `packages/reality-core/config/projection_catalog.yaml` and regenerate `apps/docs/content/tool-usage/`, German references and `apps/docs/.vitepress/data/tool-usage.json`.

## Final Phase: Verification and Review

- [x] T009 Run focused and full backend tests, lint and spec policy; record evidence in `quickstart.md`.
- [x] T010 Run required Web and documentation gates; record evidence in `quickstart.md`.
- [x] T011 Review final diff for scope, SQL boundaries, provenance and compatibility; record in `quickstart.md`. Human PR review and merge approval remain separate.

## Dependencies and Parallel Work

- [x] T012 Restore verification feasibility: add a failing retained-inventory input query-count/scope regression in `tests/test_inventory_costing_services.py`, then batch immutable input reads in `services/inventory_costing.py:_inputs` without changing validations or setup deadlines (spec impact none; existing specs 146 FR-033 and 234). T012 precedes T009; acceptance output and all integrity/tenant regression tests must remain green.

Remediation analysis: T012 is behavior-preserving, maps to the existing setup/inventory contracts and does not broaden FR-001–FR-005. No unresolved clarification or critical/high consistency finding.

T001 → T002 → T003 → T004 → T005 → T006; T007 can run alongside T004; T008 follows T007. T009-T011 follow all implementation. Deliver US1 first, then US2. No schema or migration work.

## Requirement Coverage

| Requirement | Test tasks | Implementation tasks |
|---|---|---|
| FR-001 | T004, T006 | T005, T006 |
| FR-002 | T004 | T005 |
| FR-003 | T004 | T005 |
| FR-004 | T004 | T005 |
| FR-005 | T007 | T008 |
