---
description: "Requirement-traceable Shared Runtime Catalog implementation tasks"
---

# Tasks: Shared Runtime Catalog

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/runtime-catalog.md`,
and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be written in
English. Test tasks precede the implementation they prove.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm requirements review, record the cross-adapter clarification, and close all
  clarification markers in `specs/288-catalog-review-performance/spec.md`
- [x] T002 Confirm every Constitution Check row is PASS and complete Phase 0/1 design artifacts in
  `specs/288-catalog-review-performance/plan.md`, `research.md`, `data-model.md`,
  `contracts/runtime-catalog.md`, and `quickstart.md`
- [x] T003 Run `$speckit-analyze` and resolve all CRITICAL findings across
  `specs/288-catalog-review-performance/`

## Phase 2: Foundational Failing Proof

- [ ] T004 [FR-001, FR-006, FR-007, FR-008, FR-012] Add failing tests for bounded section-copy
  isolation, concurrent single publication, failure retry and explicit clearing in
  `packages/reality-core/tests/test_application_catalog.py`
- [ ] T005 [FR-002, FR-009, FR-010, DR-004] Add a failing production caller-inventory contract that
  distinguishes eligible runtime consumers from intentional fresh-build paths in
  `packages/reality-core/tests/test_application_catalog.py`

## Phase 3: User Story 1 — Prompt Proposal Review (P1)

**Goal**: Proposal Review reuses central immutable metadata while reading current tenant proposal
and attribution state on every call.

**Independent test**: Proposed, decided, malformed, retired and changed proposals retain content
parity; 20 warmed service reads meet the documented p95 target.

- [ ] T006 [US1] [FR-003, FR-004, FR-005, DR-001, DR-002, DR-003] Add failing Proposal Review
  parity, mutable-state, cross-tenant and no-response-cache tests in
  `packages/reality-core/tests/test_proposal_review_parity.py`
- [ ] T007 [US1] [FR-011] Add the initially failing repeatable 20-read service benchmark and output
  contract in `packages/reality-core/src/reality/benchmarks/proposal_review.py` and
  `packages/reality-core/tests/test_proposal_review_benchmark.py`
- [ ] T008 [US1] [FR-001, FR-006, FR-007, FR-008, FR-012] Implement concurrency-safe,
  failure-retryable runtime snapshot publication plus isolated bounded section reads in
  `packages/reality-core/src/reality/catalogs.py`
- [ ] T009 [US1] [FR-003, FR-004, FR-005, DR-001, DR-002, DR-003] Migrate proposal next-step
  guidance to the shared runtime section boundary without changing proposal reads or decisions in
  `packages/reality-core/src/reality/services/proposal_reviews.py`
- [ ] T010 [US1] [FR-011] Run the Proposal Review benchmark and record build count, 20 durations and
  p95 evidence in `specs/288-catalog-review-performance/quickstart.md`

## Phase 4: User Story 2 — Shared Meaning Across Adapters (P1)

**Goal**: Runtime services/tools use one catalog boundary so API, MCP, Web, CLI and other adapters
gain identical behavior without transport caches.

**Independent test**: Representative direct service/tool, HTTP and MCP calls reuse one runtime
snapshot and return unchanged catalog-backed results; fresh validation still rebuilds.

- [ ] T011 [P] [US2] [FR-002, FR-003, DR-004] Add failing HTTP reuse and result-parity assertions in
  `packages/reality-core/tests/test_http_boundary.py`
- [ ] T012 [P] [US2] [FR-002, FR-003, DR-004] Add failing MCP/direct-tool capability parity and
  no-adapter-cache assertions in `packages/reality-core/tests/test_ai_mcp.py` and
  `packages/reality-core/tests/test_capability_guidance.py`
- [ ] T013 [P] [US2] [FR-003, FR-009, FR-010] Add failing fact-contract, storyline-index,
  catalog-code and explicit fresh-build assertions in
  `packages/reality-core/tests/test_application_catalog.py` and
  `packages/reality-core/tests/test_application_tools.py`
- [ ] T014 [US2] [FR-001, FR-003, FR-010, DR-001, DR-002] Migrate runtime fact-contract and catalog
  code inspection reads to bounded shared sections in
  `packages/reality-core/src/reality/services/core.py` and
  `packages/reality-core/src/reality/catalogs.py`
- [ ] T015 [US2] [FR-001, FR-002, FR-003, FR-010, DR-004] Migrate capability description and
  storyline catalog indexing to shared runtime sections in
  `packages/reality-core/src/reality/tools/application.py` and
  `packages/reality-core/src/reality/storyline/package.py`
- [ ] T016 [US2] [FR-009, FR-010] Preserve and document the explicit uncached validation/generation
  boundary in `packages/reality-core/src/reality/catalogs.py` and
  `specs/288-catalog-review-performance/contracts/runtime-catalog.md`
- [ ] T017 [US2] [FR-002, FR-010, DR-004] Update executable-vocabulary ownership and
  transport-independent runtime reuse in `docs/ARCHITECTURE.md`

## Phase 5: User Story 3 — Safe Startup and Recovery (P2)

**Goal**: Concurrent initialization is complete and single-publication; a failed build remains
retryable and explicit clearing starts a fresh lifecycle.

**Independent test**: Concurrent callers observe no partial value, one successful build is
published, a failed first build can succeed later, and clear forces exactly one new build.

- [ ] T018 [US3] [FR-006, FR-007, FR-008] Extend the failing concurrency test to cover waiting
  callers across failure and recovery in `packages/reality-core/tests/test_application_catalog.py`
- [ ] T019 [US3] [FR-006, FR-007, FR-008] Complete synchronized publication, exception cleanup and
  reset behavior in `packages/reality-core/src/reality/catalogs.py`
- [ ] T020 [US3] [FR-006, FR-007, FR-008] Run the isolated concurrency/retry acceptance story and
  record evidence in `specs/288-catalog-review-performance/quickstart.md`

## Final Phase: Cross-Cutting Review

- [ ] T021 Run `make spec-check` and audit every FR/DR mapping in
  `specs/288-catalog-review-performance/spec.md` and this task file
- [ ] T022 Run focused catalog, proposal, HTTP and MCP tests from
  `specs/288-catalog-review-performance/quickstart.md`
- [ ] T023 Run Ruff and the complete required PostgreSQL backend suite with `make lint` and
  `make test`
- [ ] T024 Confirm no migration exists, exercise code-revert rollback, and review the final diff
  against the Constitution and `specs/288-catalog-review-performance/contracts/runtime-catalog.md`
- [ ] T025 Update final benchmark/test evidence and mark tasks complete only after every required
  check is green in `specs/288-catalog-review-performance/quickstart.md` and this file

## Dependencies

```text
Phase 1 gates
  └── Phase 2 failing proof
        └── US1 central boundary + Proposal Review
              ├── US2 remaining consumers/adapters
              └── US3 concurrency/recovery completion
                    └── Cross-cutting verification
```

- US1 is the MVP and creates the central runtime boundary required by US2 and US3.
- US2 consumer tests T011–T013 can be authored in parallel after Phase 2; implementations T014–T017
  depend on T008.
- US3 test T018 may be authored after T004; implementation T019 depends on T008.

## Parallel Execution Examples

- After T005, implementers may author T006, T011, T012, T013 and T018 concurrently because they
  touch distinct focused test modules or independent sections of the catalog test module.
- After T008, T009 can proceed independently from the paired T014 and T015 migrations.
- Documentation T017 may proceed alongside consumer migration once the central contract is stable.

## Implementation Strategy

1. Deliver US1 first: central bounded runtime access plus Proposal Review proves the measured user
   outcome without broad consumer churn.
2. Migrate the remaining inventoried runtime consumers and prove transport parity in US2.
3. Complete adversarial concurrent failure/recovery behavior in US3.
4. Run complete gates and record benchmark evidence before marking any completion task done.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001 | T004, T005, T013 | T008, T014, T015 | Pending |
| FR-002 | T005, T011, T012 | T015, T017 | Pending |
| FR-003 | T006, T011, T012, T013 | T009, T014, T015 | Pending |
| FR-004 | T006 | T009 | Pending |
| FR-005 | T006 | T009 | Pending |
| FR-006 | T004, T018 | T008, T019 | Pending |
| FR-007 | T004, T018 | T008, T019 | Pending |
| FR-008 | T004, T018 | T008, T019 | Pending |
| FR-009 | T005, T013 | T016 | Pending |
| FR-010 | T005, T013 | T014–T017 | Pending |
| FR-011 | T007 | T010 | Pending |
| FR-012 | T004 | T008 | Pending |
| DR-001 | T006, T013 | T009, T014 | Pending |
| DR-002 | T006, T013 | T009, T014 | Pending |
| DR-003 | T006 | T009 | Pending |
| DR-004 | T005, T011, T012 | T015, T017 | Pending |
