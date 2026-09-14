---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Silent Source Detection

**Input**: [`spec.md`](./spec.md), [`plan.md`](./plan.md), [`checklists/`](./checklists/)
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement MUST appear in at least one test task and one
implementation or documentation task. Test tasks precede the code they prove.

## Sequencing Constraints

1. **Evidence must exist before a class is declared.** The catalog loader resolves every
   `path::test_name` and raises when the function is absent.
2. **Activating a class is atomic.** The catalog ids must equal
   `OPERATIONAL_EXCEPTION_CLASS_ORDER` exactly and the catalog derivations must equal the
   `DERIVATION_REGISTRY` keys exactly, so derivation, registry entry, both order constants
   and the catalog entry land together.
3. **The catalog entry now needs its guidance.** Since Spec 071 a class without a
   description, an owner and a clearing path is refused, so the activation step writes all
   three or fails.

## Phase 1: Specification and Design Gates

- [ ] T001 Confirm the four accepted scope decisions and the four constants are recorded in `specs/072-silent-source/spec.md`
- [ ] T002 Confirm every Constitution Check row is PASS and Complexity Tracking is empty in `specs/072-silent-source/plan.md`
- [ ] T003 Complete the reviewer-owned domain review in `specs/072-silent-source/checklists/domain.md`
- [ ] T004 Run `$speckit-analyze` and resolve every CRITICAL consistency or coverage finding

## Phase 2: Failing Proof

All derivation paths are under `packages/reality-core/tests/operational_exceptions/`.

- [ ] T005 [P] [US1] [FR-001] [FR-002] Add failing `test_derivation.py::test_silent_source` asserting the entry, the silence measured from the last receipt, and the learned pause
- [ ] T006 [P] [US1] [FR-003] [DR-002] Add failing `test_derivation.py::test_silent_source_learns_the_rhythm` with a history that pauses every weekend, proving a Monday read is quiet and a genuine stoppage is not
- [ ] T007 [P] [US1] [FR-004] Add failing `test_derivation.py::test_silent_source_floor_protects_fast_sources` proving a minute-rhythm source is not reported for a short interruption, and that a zero-pause history falls back to the floor alone
- [ ] T008 [P] [US2] [FR-005] Add failing `test_derivation.py::test_silent_source_says_nothing_without_history` covering no records, fewer than the minimum, and an inactive capability
- [ ] T008a [P] [US1] [FR-002] Add failing `test_derivation.py::test_silent_source_handles_receipts_after_the_evaluation_instant` proving a receipt in the future of the instant produces no entry rather than an error, and that out-of-order receipts still yield the same rhythm
- [ ] T009 [P] [US1] [FR-006] [FR-007] [DR-004] Add failing `test_derivation.py::test_silent_source_entry_shape` asserting identity, severity, title, impact, record type/id, causal values and an opaque trace
- [ ] T010 [P] [US1] [FR-008] [DR-001] Add failing `test_derivation.py::test_silent_source_clears_when_delivery_resumes` proving a new record removes the entry with nothing persisted
- [ ] T011 [P] [US1] [FR-010] Add failing `test_derivation.py::test_silent_source_orders_longest_silence_first` proving deterministic order across repeated reads
- [ ] T012 [P] [DR-005] Add failing `test_derivation.py::test_silent_source_is_tenant_scoped` proving one tenant's records never feed another tenant's rhythm
- [ ] T013 [P] [DR-003] Add failing `test_derivation.py::test_silent_source_constants_are_product_wide` asserting the four constants exist as module-level values and that no tenant-specific value participates
- [ ] T014 [P] [US1] [FR-009] Add failing `test_explanation.py::test_silent_source_explanation_and_not_found_parity` covering the identity, a resumed identity, a malformed one and a foreign tenant
- [ ] T015 [P] [FR-012] Extend `test_explanation.py::test_shared_consumer_parity_includes_new_classes` so the shared row contract must carry this class too
- [ ] T016 [FR-011] Update the closed registry expectation in `test_coverage.py` and the class list in `tests/test_application_catalog.py`

## Phase 3: The Class

- [ ] T017 [US1] [FR-003] [FR-004] [DR-003] Add the four constants with their reasoning and a rhythm helper to `packages/reality-core/src/reality/services/exceptions.py`
- [ ] T018 [US1] [FR-001] [FR-002] [FR-005] [DR-001] [DR-005] Add `_silent_source_exceptions` walking active capabilities, resolving each system code, loading its record history tenant-scoped, and applying the rule
- [ ] T019 [US1] [FR-006] [FR-007] [DR-004] Populate impact and causal values with the silence, the learned pause and the last receipt, and build the trace from opaque capability, system and record identities
- [ ] T020 [US1] [FR-010] [FR-011] **Atomic activation** — in one step, register the derivator, place `silent_source` fifth in `CLASS_ORDER` (`services/exceptions.py`) and in `OPERATIONAL_EXCEPTION_CLASS_ORDER` (`catalogs.py`), and declare the class with its severity, record type, `072/FR-001` authority, evidence, description, owner and clearing path in `packages/reality-core/config/operational_exception_catalog.yaml`
- [ ] T020a [US1] [FR-009] Verify the explanation path handles record type `source_capability` and leaves the `import_job` `raw_source` branch unchanged — the seventh record type deserves the check the fifth and sixth got
- [ ] T021 [US1] [FR-012] Confirm no adapter or frontend change is required and record the confirmation in the pull request
- [ ] T022 [US1] Create `specs/072-silent-source/quickstart.md` and record the result of the independent acceptance stories

## Phase 4: The Confusable Pair

- [ ] T023 [FR-011] Write the new class's guidance so it names `source_interpretation_failure` as the case where something did arrive, and amend that class's description to name this one as the case where nothing arrived — the rule Spec 071 established, applied in both directions
- [ ] T024 Re-run the cross-reference review over all nine classes and confirm every confusable pair still names its sibling from both sides

## Phase 5: Documentation

- [ ] T025 [FR-011] Add the taxonomy row to `docs/features/operational_exceptions.md` with the learned-rhythm rule stated
- [ ] T026 [P] Regenerate the catalog reference and run `npm run format` in `apps/docs` — the repository's own command, not a hand-picked glob, because the check covers all of `apps/docs`
- [ ] T027 [P] Add the specification row and the new evidence rows to `docs/SPEC_COVERAGE_MATRIX.md`

## Final Phase: Cross-Cutting Review

- [ ] T900 Run `make spec-check` and confirm the traceability tables match the delivered tests
- [ ] T901 Run `make lint` and the complete backend PostgreSQL suite
- [ ] T902 Run the `apps/docs` tests and format check, both language editions included
- [ ] T903 Confirm no migration was added and `apps/web` and `provider-site` are unchanged
- [ ] T904 Review the final diff against the Constitution and every FR and DR, including the review risks listed in `plan.md`
- [ ] T905 Re-derive the feature number immediately before opening the pull request, because a number derived earlier can be claimed by another specification in the meantime

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001 | T005 | T018, T020 | Pending |
| FR-002 | T005, T008a | T018 | Pending |
| FR-003 | T006 | T017 | Pending |
| FR-004 | T007 | T017 | Pending |
| FR-005 | T008 | T018 | Pending |
| FR-006 | T009 | T019 | Pending |
| FR-007 | T009 | T019 | Pending |
| FR-008 | T010 | T018 | Pending |
| FR-009 | T014 | T018, T020a | Pending |
| FR-010 | T011 | T019, T020 | Pending |
| FR-011 | T016 | T020, T023, T025 | Pending |
| FR-012 | T015 | T021 | Pending |
| DR-001 | T010 | T018 | Pending |
| DR-002 | T006 | T017 | Pending |
| DR-003 | T013 | T017 | Pending |
| DR-004 | T009 | T019 | Pending |
| DR-005 | T012 | T018 | Pending |
| DR-006 | T016 | T020 | Pending, guarded by the existing cause-vocabulary gate |
