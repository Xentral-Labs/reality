---
description: "Requirement-traceable Operational Integrity implementation tasks"
---

# Tasks: Operational Integrity

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/operational-actions.md`, and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

Tests precede implementation. All artifacts and evidence are written in English.

## Phase 1: Specification and Design Gates

- [ ] T001 Confirm product approval and review every unchecked requirement-quality item in `specs/250-operational-integrity/checklists/integrity.md`
- [x] T002 Confirm all initial and post-design Constitution Check rows remain PASS in `specs/250-operational-integrity/plan.md`
- [x] T003 Run `$speckit-analyze` over `specs/250-operational-integrity/spec.md`, `plan.md`, and `tasks.md` and resolve all CRITICAL findings before implementation

## Phase 2: Failing Proof and Shared Foundations

- [x] T004 [P] [US1] [FR-001] [FR-002] [FR-003] [FR-004] [DR-001] [DR-002] Add failing lot/serial/handling-unit, split, stale-review, repeated-confirmation, tenant-isolation, and unrelated-location disposition tests in `packages/reality-core/tests/test_returns.py`
- [x] T005 [P] [US2] [FR-005] [FR-006] [FR-007] [FR-008] [DR-003] [DR-004] Add failing homogeneous partial-retention, heterogeneous choice-list/explicit-selection, invalid-selection, fulfilment-boundary, stale-review, and tenant-isolation tests in `packages/reality-core/tests/test_commitment_revisions.py`
- [x] T006 [P] [US3] [FR-009] [FR-010] [FR-011] [FR-012] [DR-003] [DR-004] Add failing unfulfilled/partial/held/ineligible/stale/foreign cancellation service tests in `packages/reality-core/tests/test_commitment_actions.py`
- [x] T007 [P] [US4] [FR-013] [FR-014] [FR-015] [FR-016] [DR-005] Add failing known-refusal, complete-rollback, committed-lost-response, evidence-mismatch, and true-unknown tests in `packages/reality-core/tests/test_application_tools.py`
- [x] T008 [P] [US4] [FR-004] [FR-014] [FR-015] [DR-006] Add real PostgreSQL race tests for disposition/revision/cancellation and proposal reconciliation in `packages/reality-core/tests/test_postgresql_integration.py`

## Phase 3: User Story 1 — Resolve the Exact Returned Stock (P1)

**Independent test**: Dispose tracked returned stock while the same item/lot exists elsewhere and reconcile exact location and identity.

- [x] T009 [US1] [FR-001] [FR-002] [DR-001] [DR-002] Inherit return Movement tracking identity and preserve arrival-source/resolving links in `packages/reality-core/src/reality/services/return_dispositions.py`
- [x] T010 [US1] [FR-003] [FR-004] Add identity-complete state-bound review, exact receipt verification, and concurrent unresolved protection in `packages/reality-core/src/reality/services/return_disposition_actions.py`
- [x] T011 [US1] [FR-003] [FR-018] Expose inherited identities and exact before/effect/after explanation through `packages/reality-core/src/reality/services/delivery_reads.py` and `packages/reality-core/src/reality/services/movement_explanations.py`
- [x] T012 [US1] [FR-001] [FR-004] [DR-006] Run the US1 service and PostgreSQL tests and record commands/results in `specs/250-operational-integrity/quickstart.md`

## Phase 4: User Story 2 — Revise Without Over-Reservation (P1)

**Independent test**: Revise partially fulfilled commitments with homogeneous and heterogeneous active allocations and prove `active reserved ≤ open` or a pre-effect refusal.

- [x] T013 [US2] [FR-005] [FR-007] [FR-008] [DR-003] [DR-004] Implement atomic homogeneous release/retention and ambiguity refusal around append-only revision in `packages/reality-core/src/reality/services/core.py`
- [x] T014 [US2] [FR-006] [FR-007] [FR-008] Create state-bound revise review/detail/receipt behavior including opaque retained-allocation choices and validation in `packages/reality-core/src/reality/services/commitment_actions.py`
- [x] T015 [US2] [FR-006] [FR-017] Route revision through shared review, confirmation, detail, and reconciliation in `packages/reality-core/src/reality/services/delivery_actions.py` and `packages/reality-core/src/reality/tools/application.py`
- [x] T016 [US2] [FR-017] [FR-018] Replace the unconfirmed direct Web revision behavior with the shared reviewed contract in `packages/reality-core/src/reality/web/api.py`, `apps/web/src/api.ts`, and `apps/web/src/unified/ActionCard.tsx`
- [x] T017 [US2] [FR-005] [FR-008] [DR-006] Run US2 service/adapter tests and record evidence in `specs/250-operational-integrity/quickstart.md`

## Phase 5: User Story 3 — Cancel the Open Remainder Truthfully (P1)

**Independent test**: Cancel unfulfilled, partially fulfilled, reserved, and held customer/supplier commitments through shared interfaces and compare exact effects.

- [x] T018 [US3] [FR-010] [FR-011] [DR-003] [DR-004] Extend cancellation with required reason, optional source/action correlation, exact released IDs, and stable event evidence; update every existing internal caller with its explicit business reason in `packages/reality-core/src/reality/services/core.py`, `packages/reality-core/src/reality/services/demo_profile.py`, `packages/reality-core/src/reality/demo/normal_month.py`, and affected tests
- [x] T019 [US3] [FR-009] [FR-010] [FR-012] Create cancel review, stale validation, receipt, detail, and reconciliation in `packages/reality-core/src/reality/services/commitment_actions.py`
- [x] T020 [US3] [FR-009] [FR-012] [FR-017] Register canonical `commitment_cancel` and route it through confirmation/recovery in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/services/delivery_actions.py`
- [x] T021 [P] [US3] [FR-009] [FR-017] Add explicit MCP propose schema and adapter contract tests in `packages/reality-core/src/reality/mcp/catalog.py` and `packages/reality-core/tests/test_return_announcement_adapters.py`
- [x] T022 [P] [US3] [FR-009] [FR-017] Add thin CLI/API cancellation adapters and tests in `packages/reality-core/src/reality/cli/app.py`, `packages/reality-core/src/reality/web/api.py`, and `packages/reality-core/tests/test_commitment_actions.py`
- [x] T023 [US3] [FR-009] [FR-017] [FR-018] Add Web review/confirm/result/reconcile presentation and localization in `apps/web/src/unified/ActionCard.tsx`, `apps/web/src/api.ts`, and `apps/web/src/localization.tsx`
- [x] T024 [US3] [FR-009] [FR-017] Add MCP/Web parity browser evidence in `apps/web/scripts/operational-integrity-browser.mjs`
- [x] T025 [US3] [FR-009] [FR-017] Add Chat tool-discovery/proposal parity and canonical-service tests in `packages/reality-core/tests/test_chat.py` and `packages/reality-core/tests/test_capability_guidance.py`

## Phase 6: User Story 4 — Recover Proposal State Without Guessing (P1)

**Independent test**: Distinguish known no-effect, recorded effect, and genuine uncertainty without duplicate execution.

- [x] T026 [US4] [FR-013] [FR-014] Move eligible authorization/review/validation refusals before the execution claim and define proven rollback restoration in `packages/reality-core/src/reality/tools/application.py`
- [x] T027 [US4] [FR-014] [FR-015] [DR-005] Extend delivery detail/reconciliation to settle only exact correlated intent/evidence and preserve insufficient-evidence uncertainty in `packages/reality-core/src/reality/services/delivery_actions.py`
- [x] T028 [US4] [FR-016] [FR-018] Normalize stable receipts to distinguish lifecycle, recorded effect, current observation, and remaining work in `packages/reality-core/src/reality/services/commitment_actions.py` and `packages/reality-core/src/reality/services/return_disposition_actions.py`
- [x] T029 [US4] [FR-013] [FR-014] [FR-015] [FR-016] [DR-006] Run application and PostgreSQL recovery tests and record evidence in `specs/250-operational-integrity/quickstart.md`

## Phase 7: Cross-Story Business Proof, Contracts, and Documentation

- [x] T030 [P] [US1] [US2] [US3] [US4] [SC-001] [SC-002] [SC-003] [SC-005] [SC-006] [SC-007] Add an independent CanisPro-style exact-location/identity business story in `packages/reality-core/tests/scenarios/test_b2b_operational_integrity.py`
- [x] T031 [P] [FR-019] [DR-006] [DR-008] Add historical-inconsistency read/no-silent-repair and schema-stability assertions in `packages/reality-core/tests/scenarios/test_b2b_operational_integrity.py`
- [x] T032 [P] [FR-005] [FR-009] [FR-019] Update durable revision, reservation, movement, cancellation, and recovery contracts in `docs/features/commitments.md`, `docs/features/reservations.md`, and `docs/features/movements.md`
- [x] T033 [P] [FR-017] [FR-018] [SC-004] Update unified review/result/Inspect behavior in `docs/WEB_SPEC.md`
- [x] T034 [FR-017] Update business-resource membership and German ERP labels in `packages/reality-core/config/resource_catalog.yaml`, run `make docs-generate`, and commit generated `apps/docs/content/tool-usage/` plus `apps/docs/.vitepress/data/tool-usage.json`

## Final Phase: Verification and Review

- [x] T035 [SC-001] [SC-002] [SC-003] [SC-004] [SC-005] [SC-006] [SC-007] Run the complete end-to-end quickstart and record exact outcomes in `specs/250-operational-integrity/quickstart.md`
- [x] T036 [FR-017] [SC-004] Execute and record one contract matrix comparing normalized intent, review, receipt, derived state, and explanation for Web, MCP, Chat, CLI, and API in `specs/250-operational-integrity/quickstart.md`
- [x] T037 [SC-008] Run `make spec-check`, `make lint`, the complete backend/PostgreSQL suite, and `make docs-catalog-check`; record green evidence in `specs/250-operational-integrity/quickstart.md`
- [x] T038 [SC-008] Run `make web-build`, `cd apps/web && npm run i18n:audit`, and the focused browser test; record evidence in `specs/250-operational-integrity/quickstart.md`
- [ ] T039 [DR-001] [DR-002] [DR-003] [DR-004] [DR-005] [DR-006] [DR-007] [DR-008] Review the final diff for shortest links, tenant scope, no Document authority, no human-number identity, no schema expansion, and no blind replay; record decision in `specs/250-operational-integrity/checklists/integrity.md`
- [x] T040 [FR-019] Review migration/rollback and confirm no automatic historical mutation in `specs/250-operational-integrity/plan.md` and the final pull request

## Dependencies and Parallel Opportunities

- Phase 2 tests can be authored in parallel; they block their corresponding story implementation.
- US1 and US3 are independently implementable after Phase 2. US2 and US3 share `commitment_actions.py` and should integrate sequentially there.
- US4 depends on receipts/details from US1–US3 for full reconciliation coverage, though generic failing tests start in Phase 2.
- Documentation tasks T031–T032 can run in parallel after behavior stabilizes; catalog generation T033 follows tool/schema changes.
- Final verification begins only after all story phases and cross-story proof are complete.

## Implementation Strategy

The first independently useful increment is US1 because it prevents wrong physical identity. Follow with US2 to restore availability truth, US3 to expose truthful cancellation, and US4 to harden recovery across them. Do not merge a story while its focused tests or explanation contract are red. The feature is complete only as the four-story integrity boundary; US1 alone is not release-complete for the audited findings.

## Requirement Coverage

| Requirement group | Test tasks | Implementation/documentation tasks |
|---|---|---|
| FR-001–FR-004, DR-001–DR-002 | T004, T008, T012, T030 | T009–T011, T039 |
| FR-005–FR-008, DR-003–DR-004 | T005, T017, T030 | T013–T016, T032, T039 |
| FR-009–FR-012 | T006, T021–T025, T030 | T018–T025, T032–T034 |
| FR-013–FR-016, DR-005 | T007–T008, T029–T030 | T026–T028, T039 |
| FR-017–FR-018 | T021–T025, T033, T035–T036 | T015–T016, T020–T025, T033–T034 |
| FR-019, DR-006–DR-008 | T031, T039–T040 | T032, T039–T040 |
| SC-001–SC-008 | T030–T031, T035–T038 | T034, T039–T040 |
