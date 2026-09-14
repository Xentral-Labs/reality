---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: A Document's Total Is Received, Not Computed

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

Making a parameter required breaks every caller at once, so the parameter and its callers
change together or the suite cannot run at all. Phase 3 is one step for that reason.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the three accepted scope decisions are recorded in `specs/077-received-document-total/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS, including the row this feature exists to make true, in `specs/077-received-document-total/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/077-received-document-total/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: Failing Proof

- [x] T005 [P] [US1] [FR-001] [FR-003] Add failing `tests/test_documents.py::test_recording_requires_a_stated_total` asserting the refusal and that its message names the total
- [x] T006 [P] [US1] [FR-002] [DR-001] Add failing `tests/test_documents.py::test_stated_total_is_stored_verbatim` asserting the stored total equals the stated one
- [x] T007 [P] [US1] [FR-004] Add failing `tests/test_documents.py::test_total_may_differ_from_the_lines` proving a difference is kept rather than corrected or refused
- [x] T008 [P] [FR-005] Add failing `tests/test_documents.py::test_zero_total_is_a_statement` proving zero is accepted as given
- [x] T009 [P] [US2] [FR-007] Add a failing assertion in `tests/test_application_catalog.py` that the order tool requires the total

## Phase 3: The Required Total

- [x] T010 [FR-001] [FR-002] **Parameters and callers together** — require the amount on every line in `_normalize_manual_line_input`, make `gross_amount` a required keyword on `create_manual_document_with_lines` and on `create_manual_order` in `packages/reality-core/src/reality/services/core.py`, delete both branches that fall back to a computed figure, and update both callers of the order operation
- [x] T011 [FR-001] Make the total required on both write models in `packages/reality-core/src/reality/web/api.py`
- [x] T012 [US2] [FR-007] Add `gross_amount` to the `order_create` schema and its required list in `packages/reality-core/src/reality/mcp/catalog.py`
- [x] T013 [FR-001] State a total at the existing call sites in `tests/test_pricing.py`, `tests/test_document_corrections.py` and `tests/test_master_data_api.py`, and at any order-creating call site the change breaks
- [x] T014 [DR-002] [DR-003] Confirm the whole backend suite passes, proving no derivation and no posting changed

## Phase 4: The Interface

- [x] T015 [US1] [FR-006] Prefill every line amount with quantity times unit price and the header total with the sum of the lines in the manual document form in `apps/web/src/App.tsx`, leaving each editable, and send them
- [x] T016 [US1] [FR-006] Do the same in the manual order form, which sends through `createManualOrder`
- [x] T017 [FR-006] Send the total from both forms through `apps/web/src/api.ts` and confirm the frontend builds

## Phase 5: Documentation

- [x] T018 Record the rule in the handbook data-model chapter, English and German, since no `docs/features/documents.md` exists
- [x] T019 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite
- [x] T902 Run the frontend build
- [x] T903 Confirm no migration was added and no stored value changed
- [x] T904 Review the final diff against the Constitution, including the row this feature makes true, and the review risks in `plan.md`
- [x] T905 Re-derive the feature number immediately before opening the pull request

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T005 | T010, T011, T013 | Done |
| FR-002 | T006 | T010 | Done |
| FR-003 | T005 | T010 | Done |
| FR-004 | T007 | T010 | Done |
| FR-005 | T008 | T010 | Done |
| FR-006 | T017 | T015, T016 | Done |
| FR-007 | T009 | T012 | Done |
| DR-001 | T006 | T010 | Done |
| DR-002 | T014 | T010 | Done |
| DR-003 | T014 | T010 | Done |
