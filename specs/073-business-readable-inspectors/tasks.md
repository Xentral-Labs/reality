# Tasks: Business-readable Inspectors

## Phase 1: Specification and design gates

- [x] T001 Record approved scope and validated requirements in `specs/073-business-readable-inspectors/spec.md`
- [x] T002 Pass the Constitution Check and document design decisions in `specs/073-business-readable-inspectors/plan.md` and supporting artifacts
- [x] T003 Run Spec Kit analysis and resolve all critical findings across `specs/073-business-readable-inspectors/`

## Phase 2: Foundational contract

- [x] T004 [P] [FR-001] [FR-005] [FR-006] [FR-008] [FR-009] Add failing shared inspector hierarchy contract coverage in `apps/web/scripts/ux-support-trace-contract.test.mjs`
- [x] T005 [P] [FR-002] [FR-003] [FR-004] [FR-007] [DR-001] [DR-002] [DR-003] [DR-004] Add failing Fact and same-titled Exception inspector read-model stories in `packages/reality-core/tests/test_master_data_api.py`
- [x] T006 [FR-002] [FR-003] [FR-004] Define the additive typed inspector explanation fields in `apps/web/src/api.ts`

## Phase 3: User Story 1 — Understand a Fact immediately

- [x] T007 [US1] [FR-002] [FR-003] [FR-005] [FR-006] [FR-007] [DR-001] [DR-002] [DR-003] [DR-004] Produce tenant-scoped Fact meaning, business reference, and exact technical rows through shortest links in `packages/reality-core/src/reality/web/api.py`
- [x] T008 [US1] [FR-001] [FR-002] [FR-003] [FR-005] [FR-006] Render Fact meaning, value, affected subject, and source reference before technical identity in `apps/web/src/App.tsx`

## Phase 4: User Story 2 — Distinguish and act on an Exception

- [x] T009 [US2] [FR-002] [FR-004] [FR-005] [FR-006] [FR-007] [DR-001] [DR-002] [DR-003] [DR-004] Produce Exception impact, affected business reference, causes, and authoritative guidance in `packages/reality-core/src/reality/web/api.py`
- [x] T010 [US2] [FR-001] [FR-002] [FR-004] [FR-005] [FR-006] Render the Exception problem and next review step through the shared hierarchy in `apps/web/src/App.tsx`

## Phase 5: User Story 3 — Use one predictable drill-down

- [x] T011 [US3] [FR-001] [FR-002] [FR-005] [FR-006] [FR-007] [FR-009] Apply Summary → Position → Explanation → Related context → Technical details ordering to every inspector kind in `apps/web/src/App.tsx`
- [x] T012 [US3] [FR-008] Add responsive shared inspector styling using existing product primitives in `apps/web/src/styles.css`
- [x] T013 [US3] [FR-001] [FR-002] [FR-005] [FR-006] [FR-008] Add complete English, German, Dutch, and Spanish inspector copy in `apps/web/src/localization.tsx`

## Phase 6: Verification and review

- [x] T014 [FR-001] [FR-002] [FR-005] [FR-006] [DR-001] [DR-002] [DR-003] [DR-004] [DR-005] Update durable shared inspector behavior in `docs/WEB_SPEC.md`
- [x] T015 [FR-001] [FR-009] Run focused API stories, frontend contracts, localization audit, format, and production build and record results in `specs/073-business-readable-inspectors/quickstart.md`
- [ ] T016 [FR-008] Perform desktop and 390 px visual review for Fact, Exception, loading, error, empty-related-data, and technical disclosure states and record evidence in `specs/073-business-readable-inspectors/quickstart.md`
- [x] T017 [DR-001] [DR-002] [DR-003] [DR-004] [DR-005] Run `make spec-check`, `make lint`, and final diff/Constitution review; mark tasks complete only for green evidence

## Dependencies

- T003 blocks implementation.
- T004-T005 are observed failing before T007-T013.
- US1 and US2 share the foundational contract but are independently testable.
- US3 consolidates the common presentation after the two P1 stories prove its content.

## Parallel opportunities

- T004 and T005 affect separate frontend/backend tests and may run in parallel.
- Documentation T014 may proceed after the hierarchy is stable while focused tests run.

## Implementation strategy

The MVP is US1 plus the common contract. US2 proves the operational decision case. US3
then applies the same hierarchy across every existing inspector kind without adding
separate components or persistence.
