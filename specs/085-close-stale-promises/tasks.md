---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Close What Is Never Coming

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

Every negative test carries a positive control in the same test.

One is particular to this feature, and it is the reason the feature is safe: the preview and
the closure must share one selection. They are written as one step so that no revision of this
repository can leave them answering different questions.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the five accepted scope decisions are recorded in `specs/085-close-stale-promises/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/085-close-stale-promises/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/085-close-stale-promises/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: Failing Proof

- [x] T005 [P] [US1] [FR-001] [FR-002] Add failing `tests/test_stale_promises.py::test_the_preview_states_what_would_close` covering the count, the reservation quantity released, a bounded sample, and criteria matching nothing
- [x] T006 [P] [FR-003] Add failing `tests/test_stale_promises.py::test_a_promise_with_movement_is_never_closed`, with the positive control that the same promise without movement does close, and covering a shipment voided by a correction
- [x] T007 [P] [FR-004] [FR-005] Add failing `tests/test_stale_promises.py::test_only_open_dated_promises_match` covering a cancelled promise and a promise with no due date, each with a positive control
- [x] T007a [P] [FR-004a] Add failing `tests/test_stale_promises.py::test_a_held_promise_is_never_closed` covering a held promise and one whose party is under a delivery hold, each with a positive control
- [x] T007b [P] [FR-013] Add failing `tests/test_stale_promises.py::test_closing_nothing_is_not_a_failure` proving a repeated closure succeeds and changes nothing
- [x] T008 [P] [DR-003] Add failing `tests/test_stale_promises.py::test_the_preview_writes_nothing` proving no status, reservation or event changes
- [x] T009 [P] [US2] [FR-006] [FR-012] Add failing `tests/test_stale_promises.py::test_a_stale_count_refuses_the_closure` proving the refusal and that nothing closed
- [x] T010 [P] [US2] [FR-007] Add failing `tests/test_stale_promises.py::test_a_closure_requires_a_reason`, with the positive control that the same call with one succeeds
- [x] T011 [P] [US2] [FR-008] [FR-011] [DR-004] Add failing `tests/test_stale_promises.py::test_closing_clears_the_wall` proving every match is cancelled through the shared operation, reservations are released, the overdue class falls silent, and no Document, LedgerEntry or Movement changed
- [x] T012 [P] [FR-009] [DR-005] Add failing `tests/test_stale_promises.py::test_the_act_is_recorded_once` asserting the criteria, the reason, the count and the actor
- [x] T013 [P] [DR-002] Add failing `tests/test_stale_promises.py::test_a_closure_is_tenant_scoped` proving another tenant's matching promises stay open
- [x] T014 [P] [FR-010] Add failing endpoint tests in `tests/test_master_data_api.py` and failing tool assertions in `tests/test_application_catalog.py`

## Phase 3: The Two Operations

- [x] T015 [FR-001] [FR-002] [FR-003] [FR-004] [FR-004a] [FR-005] [DR-003] **One selection, both callers** — add the shared matcher and `preview_stale_promise_closure` to `packages/reality-core/src/reality/services/core.py`, reading movement through the existing correction-aware quantity and writing nothing
- [x] T016 [US2] [FR-006] [FR-007] [FR-008] [FR-009] [FR-012] [FR-013] [DR-004] Add `close_stale_promises`, refusing a changed count and a missing reason, cancelling each match through `cancel_commitment`, recording the act once, and committing as one transaction
- [x] T017 [FR-010] Add both endpoints in `packages/reality-core/src/reality/web/api.py`, both agent tools in `packages/reality-core/src/reality/mcp/catalog.py` and `tools/application.py` with the closing one confirmation-required, and both commands with their parameter descriptions in `packages/reality-core/config/command_catalog.yaml`
- [x] T018 [DR-002] Classify the new public operations in `packages/reality-core/config/tenant_isolation_catalog.yaml`
- [x] T019 Confirm the whole backend suite passes and no operational exception class was added

## Phase 4: Documentation

- [x] T020 Record in `docs/features/commitments.md` that many promises may be closed at once, what the criteria are, what never matches, and that the act carries a reason
- [x] T021 [P] Add the specification row and the new evidence row to `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T022 Create `specs/085-close-stale-promises/quickstart.md` and record the result of the two independent acceptance stories

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration was added
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`, paying particular attention to the fact that this is the only destructive operation in the product
- [x] T904a Measure the demo month's queue and confirm it is unchanged
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T005 | T015 | Done |
| FR-002 | T005 | T015 | Done |
| FR-003 | T006 | T015 | Done |
| FR-004 | T007 | T015 | Done |
| FR-004a | T007a | T015 | Done |
| FR-005 | T007 | T015 | Done |
| FR-006 | T009 | T016 | Done |
| FR-007 | T010 | T016 | Done |
| FR-008 | T011 | T016 | Done |
| FR-009 | T012 | T016 | Done |
| FR-010 | T014 | T017 | Done |
| FR-011 | T011 | T016 | Done |
| FR-012 | T009 | T016 | Done |
| FR-013 | T007b | T016 | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T013 | T018 | Done |
| DR-003 | T008 | T015 | Done |
| DR-004 | T011 | T016 | Done |
| DR-005 | T012 | T016 | Done |
| DR-006 | T019 | — | Done |
