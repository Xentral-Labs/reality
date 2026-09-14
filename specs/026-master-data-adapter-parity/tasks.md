---
description: "Requirement-traceable implementation tasks for master-data adapter parity"
---

# Tasks: Master Data Adapter Parity

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/adapter-parity.md`, and `quickstart.md`
**Gate**: Constitution Check passed, specification and plan approved, and no unresolved
`[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Tests precede any production correction they prove.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [x] T001 Record product-owner specification approval in `specs/026-master-data-adapter-parity/spec.md` and `specs/026-master-data-adapter-parity/checklists/requirements.md`
- [x] T002 Record product-owner plan approval after every Constitution Check row passes in `specs/026-master-data-adapter-parity/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve every CRITICAL cross-artifact finding in `specs/026-master-data-adapter-parity/`

## Phase 2: Foundational Parity Vocabulary

**Goal**: Establish one complete matrix and canonical snapshot language before comparing
interfaces.

- [x] T004 [P] [FR-001] [FR-009] Add the exact 36-cell family/operation/interface declaration and uniqueness/completeness test in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T005 [P] [FR-003] [FR-008] [DR-004] Add family-specific canonical Party, PartyRole, Item, Location, SourceRecord, and historical-link snapshot helpers in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T006 [P] [FR-006] [DR-003] Add isolated two-tenant fixtures with matching visible values and semantic aliases backed by distinct opaque IDs in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T007 [P] [DR-005] Add a model/migration guard proving Spec 026 introduces no business table, field, relationship, or migration in `packages/reality-core/tests/test_migrations.py`
- [x] T008 [FR-004] Add a boundary inventory mapping every declared CLI command and JSON API route to its existing shared Party/Item/Location service in `packages/reality-core/tests/test_master_data_parity.py`

**Checkpoint**: The matrix has 36 unique cells and snapshots compare business meaning
without weakening opaque identity.

## Phase 3: User Story 1 — Choose Any Supported Interface (P1)

**Goal**: Prove equivalent successful master-data lifecycle state across interfaces.

**Independent Test**: Run complete lifecycle sequences for all three families in
isolated tenants through real CLI and JSON API adapters, verify Product Web wiring, and
compare reloaded canonical state after every step.

### Failing proof

- [x] T009 [P] [US1] [FR-002] [FR-003] Add failing Party create/update canonical-state parity stories for real CLI and JSON API paths in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T010 [P] [US1] [FR-002] [FR-003] Add failing Item create/update canonical-state parity stories for real CLI and JSON API paths in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T011 [P] [US1] [FR-002] [FR-003] Add failing Location create/update/parent canonical-state parity stories for real CLI and JSON API paths in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T012 [P] [US1] [FR-007] [DR-001] [DR-002] Add failing deactivate/reactivate identity, source-provenance, Evidence-link, and Reality-link preservation stories for all families in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T013 [P] [US1] [FR-008] Add failing proof that response text/envelopes, timestamps, and generated IDs may differ while canonical business meaning remains equal in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T014 [P] [US1] [FR-010] Add failing executable structural coverage over the actual Party/Item/Location create, edit, deactivate, and reactivate handlers plus their used API-client mappings in `apps/web/scripts/master-data-parity.test.mjs`

### Conditional corrections and acceptance

- [x] T015 [US1] [FR-004] Correct Party/Item/Location shared-service delegation only where T009–T012 prove drift in `packages/reality-core/src/reality/cli/app.py` and `packages/reality-core/src/reality/web/api.py`
- [x] T016 [US1] [FR-010] Correct Product Web Master Data handler or API-client mapping only where T014 proves drift in `apps/web/src/App.tsx` and `apps/web/src/api.ts`
- [x] T017 [US1] [FR-002] [FR-007] Verify all successful matrix cells and lifecycle-preservation snapshots pass in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T018 [US1] Run User Story 1 PostgreSQL and Product Web acceptance and record exact results in `specs/026-master-data-adapter-parity/quickstart.md`

**Checkpoint**: Interface choice produces identical canonical Party, Item, and Location
state throughout the complete lifecycle.

## Phase 4: User Story 2 — Receive the Same Business Protection (P1)

**Goal**: Prove invalid and foreign mutations remain atomic, tenant-safe, and
business-equivalent across adapters.

**Independent Test**: Submit matching invalid and foreign operations through real CLI
and JSON API paths, verify Product Web retains API error ownership, and compare both
tenant graphs before/after.

### Failing proof

- [x] T019 [P] [US2] [FR-005] Add failing blank-name/SKU/unit and invalid typed-value atomicity stories across real CLI and JSON API paths in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T020 [P] [US2] [FR-005] [DR-003] Add failing foreign default/parent Location and hierarchy-cycle before/after stories in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T021 [P] [US2] [FR-006] Add failing foreign Party/Item/Location update and lifecycle non-disclosure stories using matching visible tenant values in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T022 [P] [US2] [FR-005] [FR-006] Add failing local/foreign SourceRecord, role, event, Evidence, and Reality count/digest invariance assertions in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T023 [P] [US2] [FR-005] [FR-010] Add Product Web structural assertions for same-input delegation, actual catch/error rendering, API-owned failures, and absence of browser-local persistence fallback in `apps/web/scripts/master-data-parity.test.mjs`

### Conditional corrections and acceptance

- [x] T024 [US2] [FR-004] [FR-005] [FR-006] Correct only demonstrated adapter translation, error mapping, or transaction drift in `packages/reality-core/src/reality/cli/app.py`, `packages/reality-core/src/reality/web/api.py`, or `packages/reality-core/src/reality/services/core.py`
- [x] T025 [US2] Verify every invalid/foreign story leaves both tenant graphs unchanged and produces the required invalid/not-found classification in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T026 [US2] Run User Story 2 PostgreSQL and Product Web acceptance and record exact results in `specs/026-master-data-adapter-parity/quickstart.md`

**Checkpoint**: No interface weakens shared validation, atomicity, or tenant isolation.

## Phase 5: User Story 3 — Detect Adapter Drift (P2)

**Goal**: Make missing coverage and alternative mutation paths fail deterministically.

**Independent Test**: Validate matrix-to-adapter inventory, service delegation, actual
Web action wiring, and canonicalization sensitivity independently of happy-path stories.

### Failing proof

- [x] T027 [P] [US3] [FR-004] [FR-009] Add drift-detection tests for a missing command/route, wrong service mapping, and direct adapter persistence signature in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T028 [P] [US3] [FR-003] [FR-008] Add canonicalizer mutation tests proving every supported business field/relationship difference fails while transport-only differences pass in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T029 [P] [US3] [FR-009] [FR-010] Add Product Web drift tests for missing used handlers, unused-helper false positives, wrong API-client method, wrong HTTP method/path/body, absent error rendering, and direct/local fallback in `apps/web/scripts/master-data-parity.test.mjs`

### Implementation and acceptance

- [x] T030 [US3] [FR-004] [FR-009] Complete the executable boundary inventory without adding a production parity framework in `packages/reality-core/tests/test_master_data_parity.py`
- [x] T031 [US3] [FR-010] Complete the actual Product Web action-to-route contract without duplicating backend business rules in `apps/web/scripts/master-data-parity.test.mjs`
- [x] T032 [US3] Run independent drift-detection acceptance and record exact results in `specs/026-master-data-adapter-parity/quickstart.md`

**Checkpoint**: Missing or divergent adapter behavior fails by family, operation, and
interface, while presentation-only differences remain allowed.

## Final Phase: Cross-Cutting Review and Baseline Closure

- [x] T033 [DR-001] [DR-002] [DR-004] Clarify canonical-state parity, shared-service ownership, source provenance, and lifecycle preservation in `docs/features/master_data.md` and `docs/CLI_SPEC.md`
- [x] T034 [DR-005] Confirm no model/migration expansion and record the result in `specs/026-master-data-adapter-parity/quickstart.md`
- [x] T035 Run Ruff, focused PostgreSQL parity/API/CLI tests, and the complete parallel PostgreSQL suite; record exact results in `specs/026-master-data-adapter-parity/quickstart.md`
- [x] T036 Run the focused Product Web parity contract, localization contract tests, and production build; record exact results in `specs/026-master-data-adapter-parity/quickstart.md`
- [x] T037 Review the final diff against Constitution, `spec.md`, `plan.md`, all FR/DR mappings, tenant boundaries, shortest links, and unrelated concurrent work in `specs/026-master-data-adapter-parity/checklists/requirements.md`
- [x] T038 [FR-011] Before baseline closure, add a regression expecting `004/FR-016` verified, its coverage row absent, and unrelated gaps retained in `packages/reality-core/tests/test_spec_policy.py`
- [x] T039 [FR-011] After product-owner final approval, mark only `004/FR-016` verified in `specs/004-master-data/spec.md` and remove only its row from `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T040 Run final Spec policy, traceability, checklist, and `git diff --check` gates; record exact results in `specs/026-master-data-adapter-parity/quickstart.md`

## Dependencies

```text
T001–T003 specification/design gates
  → T004–T008 shared vocabulary
    → T009–T018 US1 successful lifecycle parity (MVP)
      → T019–T026 US2 protection parity
        → T027–T032 US3 drift detection
          → T033–T040 final review and baseline closure
```

- US1 is the independently testable MVP and establishes canonical snapshots.
- US2 depends on the snapshot vocabulary but independently proves failure safety.
- US3 depends on the stable matrix and canonicalizer but independently proves drift
  detection.
- Baseline closure cannot precede green complete evidence and final owner approval.

## Parallel Execution Examples

- **Foundation**: T004, T006, and T007 may proceed in parallel; T005 then informs shared
  story assertions.
- **US1**: Party, Item, Location, lifecycle, and Product Web proof tasks T009–T014 touch
  separable fixtures/sections and may be developed in parallel before integration.
- **US2**: Invalid-input, relationship, tenant, graph-invariance, and Web-error tasks
  T019–T023 may proceed in parallel.
- **US3**: Backend inventory/canonicalizer tasks T027–T028 and Web drift task T029 may
  proceed in parallel.

## Implementation Strategy

1. Establish the exact matrix and canonical snapshot rules.
2. Prove successful lifecycle parity as the MVP.
3. Prove invalid and foreign operations cannot mutate or disclose state.
4. Make missing actions and boundary drift fail explicitly.
5. Change production code only for observed drift, then close only `004/FR-016`.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001 | T004 | T030 | Complete |
| FR-002–FR-003 | T009–T013, T028 | T015, T017, T033 | Complete |
| FR-004 | T008, T027 | T015, T024, T030, T033 | Complete |
| FR-005 | T019–T020, T022 | T024 | Complete |
| FR-006 | T006, T021–T022 | T024 | Complete |
| FR-007 | T012 | T017, T033 | Complete |
| FR-008 | T013, T028 | T030, T033 | Complete |
| FR-009 | T004, T027, T029 | T030–T031 | Complete |
| FR-010 | T014, T023, T029 | T016, T031 | Complete |
| FR-011 | T038, T040 | T039 | Complete |
| DR-001–DR-002 | T012 | T033, T037 | Complete |
| DR-003 | T006, T020–T022 | T024, T037 | Complete |
| DR-004 | T005, T028 | T033, T037 | Complete |
| DR-005 | T007 | T034, T037 | Complete |
| SC-001–SC-007 | T004, T009–T032, T034–T036, T038, T040 | T033, T037, T039 | Complete |
