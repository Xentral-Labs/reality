---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: A Closed Promise Holds Nothing

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

The established rules apply. One is particular to this feature.

**The two legs that make the fulfilled sequence the only one are pinned first**, before anything
is changed. If holding a closed promise or shipping a held one turns out to be possible, the
design has more paths than it thinks.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/108-a-closed-promise-holds-nothing/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and that no Complexity Tracking exception is claimed in `specs/108-a-closed-promise-holds-nothing/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/108-a-closed-promise-holds-nothing/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 Confirm against the code that `require_not_held` guards `reserve` and every movement, that `hold_commitment` refuses a promise that is not open, and that the revision settle path bypasses both

## Phase 2: The Two Legs, First

- [x] T006 [P] [FR-007] Add `test_commitment_holds.py::test_a_closed_promise_cannot_be_held`, with a positive control on an open promise
- [x] T007 [P] [FR-008] Add `test_commitment_holds.py::test_a_held_promise_cannot_be_shipped`, with a positive control after release

## Phase 3: The Release

- [x] T008 [P] [FR-001] [FR-003] [FR-005] Add failing `test_commitment_holds.py::test_cancelling_a_promise_releases_its_hold`, asserting nothing stated is erased and that an unheld cancellation is unchanged
- [x] T009 [P] [FR-002] [FR-006] Add failing `test_commitment_holds.py::test_settling_a_promise_by_revision_releases_its_hold`, including a revision that leaves the promise open
- [x] T010 [P] [FR-004] Add failing `test_commitment_holds.py::test_the_release_is_recorded_by_the_release_operation`
- [x] T011 [P] [DR-002] Add failing `test_commitment_holds.py::test_the_release_joins_the_caller_s_transaction` and `::test_a_closure_never_cancels_a_held_promise`
- [x] T012 [P] [FR-009] Add failing `test_commitment_holds.py::test_no_closed_promise_carries_an_active_hold`
- [x] T013 [P] [US1] [FR-001] Add failing `test_commitment_holds.py::test_goods_can_come_back_against_a_cancelled_held_promise`
- [x] T014 [DR-002] Add `_commit` to `release_commitment_hold` in `src/reality/services/core.py`
- [x] T015 [FR-001] [FR-004] Release the promise's holds in `cancel_commitment` and name them in its event
- [x] T016 [FR-002] Release the promise's holds where `revise_commitment` settles it as fulfilled
- [x] T017 [FR-011] Run the complete backend suite and confirm nothing moved apart from a hold ending sooner
- [x] T018 Create `specs/108-a-closed-promise-holds-nothing/quickstart.md` and record the three independent acceptance stories

## Phase 4: Documentation

- [x] T019 [DR-004] Correct the `commitment_hold_unreleased` guidance in `config/operational_exception_catalog.yaml` so its skip is explained as true by construction and legacy-only
- [x] T020 Record the release in `docs/features/commitment_holds.md`, including the sequence that reaches a fulfilled promise and the legacy limit
- [x] T021 [P] Correct the Spec 107 paragraph in `docs/features/operational_exceptions.md`
- [x] T022 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs`
- [x] T023 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite in CI's invocation and ordering
- [x] T902 Run the `apps/docs` tests and format check
- [x] T903 [DR-001] Confirm no migration and no new command were added
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`, and confirm `require_not_held` is untouched
- [x] T904a Confirm the demo month's pinned queue is unchanged
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T008, T013 | T015 | Done |
| FR-002 | T009 | T016 | Done |
| FR-003 | T008 | T014 | Done |
| FR-004 | T010 | T015 | Done |
| FR-005 | T008 | T015 | Done |
| FR-006 | T009 | T016 | Done |
| FR-007 | T006 | — | Done |
| FR-008 | T007 | — | Done |
| FR-009 | T012 | T015, T016 | Done |
| FR-010 | T904 | — | Done |
| FR-011 | T017, T901 | — | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T011 | T014 | Done |
| DR-003 | T904 | — | Done |
| DR-004 | T902 | T019, T021 | Done |
| DR-005 | T901 | — | Done |
