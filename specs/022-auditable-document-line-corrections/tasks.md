---
description: "Requirement-traceable auditable DocumentLine correction tasks"
---

# Tasks: Auditable Manual Document-Line Corrections

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/document-line-correction.md`, and `quickstart.md`
**Gate**: Approved specification and plan; Constitution Check passed; no unresolved clarification
**Status**: Approved by the owner on 2026-08-31; cross-artifact analysis passed after remediation.

All task descriptions, paths, review notes, code, tests, and resulting repository
artifacts MUST be written in English. Tests precede the behavior they prove.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm owner approval, `14/14` requirement-checklist completion, and zero unresolved clarification markers in `specs/022-auditable-document-line-corrections/spec.md` and `specs/022-auditable-document-line-corrections/checklists/requirements.md`
- [x] T002 Confirm every Constitution Check row remains PASS and the no-schema decision is consistent across `specs/022-auditable-document-line-corrections/plan.md`, `research.md`, and `data-model.md`
- [x] T003 Run `speckit-analyze` and resolve every CRITICAL or HIGH cross-artifact finding in `specs/022-auditable-document-line-corrections/`

## Phase 2: Foundational Failing Proof

- [x] T004 [P] [FR-002] [FR-008] Add failing normalization and complete-snapshot contract tests for retained, added, removed, duplicate, unknown, and cross-Document line IDs in `packages/reality-core/tests/test_document_corrections.py`
- [x] T005 [P] [FR-009] [FR-010] Add failing deterministic revision, stale divergent request, identical current-state no-op, and rejected lost-response ID-less-addition retry tests in `packages/reality-core/tests/test_document_corrections.py`
- [x] T006 [DR-001] [DR-002] Refactor manual line normalization into a private shared helper without changing creation behavior in `packages/reality-core/src/reality/services/core.py`

**Foundation exit**: Existing manual creation remains green; correction tests fail only because the snapshot/correction operations do not yet exist.

## Phase 3: User Story 1 — Correct Manual Line Evidence (P1)

**Goal**: An operator atomically adds, changes, or removes manual line Evidence and receives an exact audit trail.

**Independent Test**: Create a manual Document with lines, submit a valid complete snapshot, and verify current Evidence, stable retained IDs, one exact event, and unchanged unrelated state.

- [x] T007 [P] [US1] [FR-001] [FR-003] [FR-004] Add failing PostgreSQL stories for atomic add/update/remove, stable retained IDs, exact before/after audit with present/absent actor context, rollback on invalid input, and full rollback when event emission is forced to fail in `packages/reality-core/tests/test_document_corrections.py`
- [x] T008 [P] [US1] [FR-005] Add failing external-Evidence rejection and source-version guidance tests in `packages/reality-core/tests/test_document_corrections.py`
- [x] T009 [P] [US1] [FR-001] [FR-005] [FR-008] Add failing GET/PUT contract tests for a correctable manual snapshot and a non-correctable external-Evidence read with source-version guidance in `packages/reality-core/tests/test_master_data_api.py`
- [x] T010 [US1] [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [FR-008] Implement tenant-scoped snapshot, canonical revision, full-delta mutation, exact `document.corrected` audit with optional actor context, non-correctable external snapshot, PUT rejection, and one-transaction behavior in `packages/reality-core/src/reality/services/core.py`
- [x] T011 [US1] [FR-001] [FR-008] Implement Pydantic snapshot/replacement models and GET/PUT transport delegation in `packages/reality-core/src/reality/web/api.py`
- [x] T012 [P] [US1] [FR-013] Add failing Inspector/activity assertions for corrected current lines and the correction event in `packages/reality-core/tests/test_master_data_api.py`
- [x] T013 [US1] [FR-013] Extend Document Inspector correction metadata and event visibility without deriving operational state from Evidence in `packages/reality-core/src/reality/web/api.py`
- [x] T014 [P] [US1] [FR-011] Add typed correction snapshot/result contracts and API calls in `apps/web/src/api.ts`
- [x] T015 [US1] [FR-011] Implement the manual-Evidence “Correct lines” entry point and reusable full-snapshot editor in `apps/web/src/App.tsx`
- [x] T016 [US1] [FR-001] Run the User Story 1 focused backend/API acceptance and record observed results in `specs/022-auditable-document-line-corrections/quickstart.md`

## Phase 4: User Story 2 — Preserve Reality Boundaries (P2)

**Goal**: Economic Evidence corrections cannot silently diverge from linked operational or financial Reality.

**Independent Test**: Link Reality at Document and line level, reject each economic delta with unchanged records and useful guidance, then accept a reference-only correction.

- [x] T017 [P] [US2] [FR-006] [FR-007] Add failing Document-linked Commitment, line-linked Commitment, and Document-linked LedgerEntry protection stories in `packages/reality-core/tests/test_document_corrections.py`
- [x] T018 [P] [US2] [FR-007] Add failing economic-field classification, add/remove rejection, and reference-only success cases in `packages/reality-core/tests/test_document_corrections.py`
- [x] T019 [US2] [FR-006] [FR-007] Implement tenant-scoped linked-Reality detection, economic delta classification, rejection, and owning-workflow guidance in `packages/reality-core/src/reality/services/core.py`
- [x] T020 [P] [US2] [FR-006] Add API assertions that rejected economic corrections leave Evidence, BusinessEvents, Commitments, and LedgerEntries unchanged in `packages/reality-core/tests/test_master_data_api.py`
- [x] T021 [US2] [FR-007] Expose correctability flags and safe owning-workflow guidance through the snapshot endpoint in `packages/reality-core/src/reality/web/api.py`
- [x] T022 [US2] [FR-007] Render linked-Reality warnings, disable unsupported economic save outcomes, and preserve server authority in `apps/web/src/App.tsx`
- [x] T023 [US2] [DR-005] Add regression proof that no operational field or alternative Web rule was introduced in `packages/reality-core/tests/test_operational_fields.py`
- [x] T024 [US2] [FR-006] Run the User Story 2 Reality-boundary acceptance and record observed results in `specs/022-auditable-document-line-corrections/quickstart.md`

## Phase 5: User Story 3 — One Tenant-Safe Capability (P3)

**Goal**: Web and API share one service while cross-tenant, stale, retry, and unsupported-agent behavior stays safe.

**Independent Test**: Exercise service/API/Web semantics, attempt foreign identifiers, run stale and identical retries, and verify no unconfirmed chat/agent correction exists.

- [x] T025 [P] [US3] [DR-003] [DR-004] Add failing cross-tenant Document, line, and item correction cases with overlapping human references in `packages/reality-core/tests/tenant_isolation/test_families.py`
- [x] T026 [P] [US3] [FR-009] [FR-010] Add failing API conflict/reload, identical current-state no-op, and rejected repeated ID-less-addition/no-second-effect cases in `packages/reality-core/tests/test_master_data_api.py`
- [x] T027 [P] [US3] [FR-011] [FR-012] Add failing command-catalog assertions for Web/API-only service delegation and absence of a Chat/agent correction adapter in `packages/reality-core/tests/test_application_catalog.py`
- [x] T028 [US3] [FR-009] [FR-010] Implement row locking, stable canonical serialization, stale-conflict handling including repeated ID-less additions, and identical current-state no-op return in `packages/reality-core/src/reality/services/core.py`
- [x] T029 [US3] [DR-003] Register the new service and endpoints in the tenant-isolation evidence catalog under `packages/reality-core/config/tenant_isolation_catalog.yaml`
- [x] T030 [US3] [FR-011] [FR-012] Extend the existing manual Document correction command entry with line service/read/write/adapter evidence in `packages/reality-core/config/command_catalog.yaml`
- [x] T031 [US3] [FR-009] Map stale conflicts to reload guidance and refresh the authoritative snapshot in `packages/reality-core/src/reality/web/api.py` and `apps/web/src/App.tsx`
- [x] T032 [P] [US3] [FR-011] Add English, German, Dutch, and Spanish correction, validation, and guidance strings in `apps/web/src/localization.tsx`
- [x] T033 [US3] [FR-011] Run and record the User Story 3 isolation/adapter/retry acceptance plus manual Web/API parity scenario in `specs/022-auditable-document-line-corrections/quickstart.md`

## Final Phase: Cross-Cutting Review and Baseline Closure

- [x] T034 [P] [FR-001] [FR-013] Update supported correction and explanation behavior in `docs/WEB_SPEC.md` and `docs/features/operational_fields.md`
- [x] T035 Run the focused correction, API, catalog, operational-field, and tenant-isolation tests from `specs/022-auditable-document-line-corrections/quickstart.md`
- [x] T036 Run Ruff and the complete PostgreSQL backend suite from `packages/reality-core/`
- [x] T037 Run `npm run build`, `npm run i18n:audit`, and `npm run test:i18n` from `apps/web/`
- [x] T038 Confirm the Alembic head and repository diff contain no schema change, and verify rollback claims against `specs/022-auditable-document-line-corrections/plan.md`
- [x] T039 Run final FR/DR, Source → Evidence → Reality, tenant-scope, opaque-ID, shared-service, and event-payload review against `specs/022-auditable-document-line-corrections/spec.md`
- [x] T040 [FR-001] [DR-001] Mark only `006/FR-008` verified in `specs/006-documents-evidence/spec.md` and `docs/SPEC_COVERAGE_MATRIX.md` after every required check is green
- [x] T041 Record final review evidence and owner approval in `specs/022-auditable-document-line-corrections/checklists/requirements.md` and `specs/022-auditable-document-line-corrections/quickstart.md`

## Dependencies

```text
Phase 1 gates
  → Phase 2 normalization/revision foundation
    → US1 manual correction MVP
      → US2 linked-Reality protection
        → US3 isolation and adapter equivalence
          → cross-cutting gates and baseline closure
```

- US1 depends only on the foundational helper and failing snapshot/revision proof.
- US2 depends on US1's delta model but is independently verified with linked Reality.
- US3 depends on the stable service/API contract from US1 and conflict semantics from US2.
- Documentation and baseline closure must be last; they may not claim green evidence early.

## Parallel Opportunities

- T004 and T005 can run in parallel before T006.
- In US1, T007–T009 and T012 can be authored in parallel; T014 can proceed after the API contract is fixed while T010–T011 are implemented.
- In US2, T017, T018, and T020 can be authored in parallel; T021 and T022 follow the shared guard.
- In US3, T025–T027 can be authored in parallel; T032 is independent after final user-facing strings are known.
- T034 may run alongside final test gates T035–T038, but T040–T041 remain strictly last.

## Implementation Strategy

### MVP first

Complete Phases 1–3 to prove the P1 service, API, Web path, atomic audit, and external-
Source boundary. Do not ship the MVP until US2 protection is complete because economic
correction without the Reality guard would violate the Constitution.

### Incremental delivery

1. Establish shared normalization and deterministic snapshots with failing proof.
2. Deliver full manual Evidence correction and exact audit.
3. Add the approved linked-Reality boundary and reference-only exception.
4. Harden tenant isolation, concurrency, retry behavior, adapter catalog, and localization.
5. Run all gates, review the diff, then close only the documented baseline gap.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) |
|---|---|---|
| FR-001–FR-004 | T007, T009 | T010–T013, T034 |
| FR-005 | T008 | T010–T011 |
| FR-006–FR-007 | T017–T018, T020 | T019, T021–T024 |
| FR-008 | T004, T009 | T010–T011 |
| FR-009–FR-010 | T005, T026 | T028, T031 |
| FR-011–FR-012 | T027, T037 | T014–T015, T030–T032 |
| FR-013 | T012 | T013, T034 |
| DR-001–DR-002 | T007, T039 | T006, T010, T040 |
| DR-003–DR-004 | T025 | T029, T039 |
| DR-005 | T023 | T034, T038–T040 |
