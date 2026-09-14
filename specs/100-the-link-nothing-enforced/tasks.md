---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: The Link Nothing Enforced

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [x] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

The established rules apply. Two are particular to this feature.

**The gates are written before anything is declared**, exactly as Spec 094's was, so their first
run is evidence rather than decoration and the findings are recorded from that run.

**The measurement comes before the declaration.** The recorded risk said three classes and three
references; the numbers are taken from the mapper and the source first, and the declaration is
written from them.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm the accepted scope decisions are recorded in `specs/100-the-link-nothing-enforced/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and that no Complexity Tracking exception is claimed in `specs/100-the-link-nothing-enforced/plan.md`
- [x] T003 Complete the reviewer-owned domain review in `specs/100-the-link-nothing-enforced/checklists/domain.md`
- [x] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding
- [x] T005 [DR-003] Measure the references from the mapper and the consumers from the source, and record the figures and both directions in `spec.md`

## Phase 2: The Gates, Written First

- [x] T006 [FR-001] [FR-008] Add failing `test_reference_integrity.py::test_every_nullable_reference_is_classified` and record what it names
- [x] T007 [FR-003] Add failing `test_reference_integrity.py::test_declared_consumers_are_the_discovered_consumers`
- [x] T008 [FR-005] Add failing `test_reference_integrity.py::test_every_writer_passes_the_reference_through` and record what it names
- [x] T009 [FR-006] [FR-007] [FR-009] Add failing `test_reference_integrity.py::test_every_adapter_can_carry_the_reference` and `::test_an_mcp_passthrough_is_not_an_exemption`, and record what they name
- [x] T010 [FR-002] [FR-008] [DR-002] Add failing `test_reference_integrity.py::test_the_reference_catalog_fails_in_both_directions` and `::test_the_loader_refuses_a_broken_catalog`

## Phase 3: The Declaration

- [x] T011 [FR-001] [FR-002] [FR-003] [FR-004] [DR-002] Add `config/reference_catalog.yaml` with every nullable reference classified, its consumers and their directions
- [x] T012 [DR-002] Add the loader and its validation to `src/reality/catalogs.py`, refusing an unclassified reference, an empty reason and a stale entry
- [x] T013 [FR-011] Run the complete backend suite and confirm no class, register or projection moved

## Phase 4: What The Gates Found

- [x] T014 [FR-009] Declare the manual document line schema in `src/reality/mcp/catalog.py` so it names `billed_document_line_id` instead of accepting a free-form object
- [x] T015 [FR-010] Add the billed-line field to `apps/web/src/api.ts` and to both the recording and correcting forms in `apps/web/src/App.tsx`
- [x] T016 [FR-006] Re-run the adapter gate and confirm every declared adapter now carries every load-bearing reference

## Phase 5: The Two Directions

- [x] T017 [P] [FR-004] Add failing `test_derivation.py::test_a_missing_billing_reference_makes_the_queue_cry_wolf`
- [x] T018 [P] [FR-004] Add failing `test_derivation.py::test_a_missing_billing_reference_makes_the_queue_go_blind`
- [x] T019 [FR-004] Confirm the declared direction of every consumer matches what those two recordings show
- [x] T020 Create `specs/100-the-link-nothing-enforced/quickstart.md` and record the three independent acceptance stories

## Phase 6: Documentation

- [x] T021 Record the four references, the two directions and the gate in `docs/features/operational_exceptions.md`
- [x] T022 [P] Add the specification row to `docs/SPEC_COVERAGE_MATRIX.md`, recording that the measurement changed three numbers in the risk it came from
- [x] T023 [P] Run `npm run format` in `apps/web` and `apps/docs` and regenerate the catalog reference if any generated page changed

## Final Phase: Cross-Cutting Review

- [x] T900 Run `make spec-check`
- [x] T901 Run `make lint` and the complete backend PostgreSQL suite in CI's invocation and ordering
- [x] T902 Run the `apps/docs` tests and format check, and build the web app
- [x] T903 [DR-001] Confirm no migration was added
- [x] T904 Review the final diff against the Constitution and the review risks in `plan.md`
- [x] T904a Confirm the demo month's pinned queue is unchanged
- [x] T905 Re-derive the feature number with `scripts/next_feature_number.py` immediately before opening the pull request, and take the number it gives

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T006 | T011, T012 | Done |
| FR-002 | T010 | T011, T012 | Done |
| FR-003 | T007 | T011 | Done |
| FR-004 | T017, T018, T019 | T011 | Done |
| FR-005 | T008 | T011 | Done |
| FR-006 | T009, T016 | T014, T015 | Done |
| FR-007 | T009 | T012 | Done |
| FR-008 | T010 | T012 | Done |
| FR-009 | T009, T016 | T014 | Done |
| FR-010 | T902 | T015 | Done |
| FR-011 | T013, T901 | — | Done |
| DR-001 | T903 | — | Done |
| DR-002 | T010 | T012 | Done |
| DR-003 | T006, T007, T008 | T005 | Done |
| DR-004 | T901 | — | Done |
| DR-005 | T904 | — | Done |
| DR-006 | T901 | — | Done |
