# Tasks: Evidence boundaries in existing reads

## Phase 1: Specification and Design
- [x] T001 Record owner-approved scope and review requirements in specs/370-read-evidence-boundaries/spec.md.
- [x] T002 Complete Constitution PASS and evidence-reader research in specs/370-read-evidence-boundaries/plan.md and research.md.
- [x] T003 Analyze spec, plan and tasks; record findings in specs/370-read-evidence-boundaries/verification.md.

## Phase 2: User Story 1 - Scope-qualified counts
- [x] T004 [US1] [FR-001] [FR-002] [FR-005] Add failing scoped/unscoped/empty/page/legacy/no-write regressions in packages/reality-core/tests/test_read_evidence_boundaries.py.
- [x] T005 [US1] [FR-001] [FR-002] Reuse coverage and qualify discovery summary in packages/reality-core/src/reality/services/read_contracts.py.

## Phase 3: User Story 2 - Inventory evidence limit
- [x] T006 [US2] [FR-003] [FR-004] [FR-005] Add failing stock/history/provenance/tenant/description regressions in packages/reality-core/tests/test_read_evidence_boundaries.py and authenticated assertions in test_mcp_http_runtime.py.
- [x] T007 [US2] [FR-003] [FR-005] Add shared transient notice in packages/reality-core/src/reality/services/read_interpretation.py and projections.py without altering values.
- [x] T008 [US2] [FR-004] [DR-001] Sharpen existing descriptions in packages/reality-core/src/reality/mcp/catalog.py and docs/features/mcp_reads.md; run make docs-generate.

## Final Phase: Verification and Review
- [x] T009 [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [DR-001] Run focused PostgreSQL/read/HTTP regressions, Ruff/spec/docs gates and full CI; record evidence in specs/370-read-evidence-boundaries/verification.md.
- [x] T010 [DR-001] Run fresh read-only Claude acceptance, compare unchanged operational state and revoke temporary access; record model observations separately in specs/370-read-evidence-boundaries/verification.md.
- [x] T011 [FR-005] [DR-001] Review final diff/rollback and create a new PR; no merge without owner approval. Record result in specs/370-read-evidence-boundaries/verification.md.

## Dependencies and Implementation Strategy
T001-T003 precede tests/implementation. T004→T005; T006→T007→T008; all then T009-T011. Story tests are independent except shared setup. No parallel implementation is needed for this small change. Deliver US1 first, then US2 and final acceptance.
## Requirement Coverage
| Requirement | Test tasks | Implementation/documentation tasks |
|---|---|---|
| FR-001 | T004,T009 | T005 |
| FR-002 | T004,T009 | T005 |
| FR-003 | T006,T009 | T007 |
| FR-004 | T006,T009 | T008 |
| FR-005 | T004,T006,T009 | T007,T011 |
| DR-001 | T009,T010 | T008,T011 |
