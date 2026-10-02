# Tasks: Consolidate Receipt Manifest Membership

**Input**: spec.md, plan.md, research.md, data-model.md, contracts/membership.md, quickstart.md.
**Gate**: Owner selected the bounded scope; Constitution PASS; analysis must find no critical issue. All repository artifacts remain English. All implementation and verification tasks are complete; see verification.md.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm requirements review, Constitution PASS, independent exact-column routing review and non-destructive analysis for `specs/330-consolidate-manifest-members/spec.md`, `plan.md`, `research.md` and `tasks.md`.
- [x] T002 Capture actual isolated revision-0111 member column/PK/FK/unique/index DDL and all SQL dependencies, confirm no incoming member FKs and recheck migration numbering; record in `specs/330-consolidate-manifest-members/verification.md` and `evidence/predecessor-schema.json` (FR-008/010).

## Phase 2: Foundational Failing Proof

- [x] T003 [US2] Add red-first PostgreSQL physical/logical schema, exact view columns, five-family SQL/ORM CRUD/RETURNING/rowcount, target shape/closed family, PK collisions, all typed parent/target links, duplicate/cross-manifest and tenant refusals in `packages/reality-core/tests/test_cost_manifest_members.py` (FR-001/002/003/004/005; DR-002/003).
- [x] T004 [US3] Add red-first populated predecessor fixture and exact full-row/original-DDL snapshots, all five families/two tenants/equal IDs/empty family, post-upgrade mutations and downgrade/re-upgrade in `packages/reality-core/tests/test_cost_manifest_member_migration.py` (FR-002/008/010; DR-001).

## Phase 3: User Story 1 — Exact Historical Reviews

Independent acceptance: old manifest membership/digest/trace/result survives consolidation and newer knowledge; missing support remains unknown and corruption remains refused.

- [x] T005 [US1] Extend historical manifest migration fixture assertions and reuse late-cost, replacement, correction, unknown received amounts and member-loss regression cases in `packages/reality-core/tests/test_cost_manifest_member_migration.py` and `tests/test_costing_services.py`; observe new storage-specific proof failing before implementation (FR-006/007/010; DR-001).
- [x] T006 [US1] Implement typed shared member store, family checks/partial uniqueness/tenant parent and five target FKs, physical lookup indexes and original mapped-model view registration in `packages/reality-core/src/reality/db/cost_manifest_members.py`; register before FK indexing in `db/core.py` (FR-001/002/003/006/007/010; DR-001/002/003).
- [x] T007 [US1] Run historical receipt regressions and compare untouched `services/costing.py` digest serialization and selected joins; record exact before/after historical values in `specs/330-consolidate-manifest-members/verification.md` (FR-006/007/010; DR-001/002).

## Phase 4: User Story 2 — Existing Interfaces and Isolation

Independent acceptance: every original logical column and mutation contract survives; invalid links fail; detail/paging, counts and purge retain tenant scope.

- [x] T008 [US2] Implement exact-column filtered views, invoker-rights fixed-family INSTEAD OF INSERT routing with stored RETURNING values, native UPDATE/DELETE and metadata hook/dependency cleanup in `packages/reality-core/src/reality/db/cost_manifest_members.py` (FR-004/005/007/009; DR-002/003).
- [x] T009 [US2] Add PostgreSQL metadata full/repeated/selected create-drop, routing function cleanup, original logical columns, FK indexes, Alembic exclusion and once-only tenant count/purge proofs in `packages/reality-core/tests/test_cost_manifest_members.py` before adjusting any lifecycle helper (FR-009; DR-003).
- [x] T010 [US2] Verify existing physical-only helpers in `services/core.py`, `services/account_deletion.py`, `db/schema_views.py` and `migrations/env.py`; adjust only a demonstrated lifecycle defect, preserve original record inspection and explicit reporting disposition in `tests/test_reporting_graph_coverage.py`; run service/tool/record/schema regressions and record results in `specs/330-consolidate-manifest-members/verification.md` (FR-004/005/009; DR-003).

## Phase 5: User Story 3 — Populated Reversible Transition

Independent acceptance: exact rows and original schema restore after supported post-upgrade changes; interruption/parity failure does not leave partial retirement.

- [x] T011 [US3] Add transaction abort/parity-failure proof and supported post-upgrade insert/update/delete RETURNING checks to `packages/reality-core/tests/test_cost_manifest_member_migration.py`, including all unrelated authority snapshots and current manifest hash refusal semantics (FR-004/006/008/010; DR-001).
- [x] T012 [US3] Implement frozen DDL/index migration `packages/reality-core/migrations/versions/0120_manifest_members.py` after rechecking head: lock, exact copy, per-family bidirectional parity, views/insert routing; lossless exact-schema downgrade/re-upgrade; no current-model import or CASCADE (FR-001/002/003/004/008/010; DR-001/002/003).
- [x] T013 [US3] Run populated roundtrip, older pinned costing fixtures and migration-chain checks through 0109/0110/0111/0112; compare all rows and exact predecessor contracts, recording commands/results in `specs/330-consolidate-manifest-members/verification.md` (FR-008/010; DR-001).

## Final Phase: Cross-Cutting Review

- [x] T014 Run full required PostgreSQL backend suite, unchanged serial existing benchmark, lint/spec, docs generation/catalog reproducibility/build and web build; freeze relevant source hashes and preserve red/green raw evidence in `specs/330-consolidate-manifest-members/verification.md` and `evidence/` (SC-004).
- [x] T015 Review source/migration diff against all FR/DR, exact -4 physical count, no added public columns or history/lifecycle changes; update `docs/DATA_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/SPEC_COVERAGE_MATRIX.md`, `docs/ideas/cost-storage-consolidation.md` and spec status only after required gates pass (FR-001/005/006/007/009/010; DR-001/002/003; SC-001/002/003/004).

## Dependencies and Execution Strategy

T001 → T002 → T003/T004/T005 → T006 → T007/T008 → T009/T010 → T011 → T012 → T013 → T014 → T015. T009 precedes any lifecycle repair inside T010. T011 precedes migration code. Stories provide independently observable proof, but the storage release remains atomic: historical correctness is the first milestone and must not be deployed without interface and rollback acceptance.

Safe parallel examples: prepare schema/interface tests and populated fixture research in different files after T002; read-only service history and DDL review can run independently. Tests that share database fixtures, full builds and performance benchmark run sequentially as needed. No tasks are marked [P] because new test edits and schema changes have shared dependencies; independent orchestration does not authorize extra agents except the plan skill's research/review requirement.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) |
| --- | --- | --- |
| FR-001 | T003/T004/T013 | T006/T012/T015 |
| FR-002 | T003/T004 | T006/T012 |
| FR-003 | T003 | T006/T012 |
| FR-004 | T003/T011 | T008/T010/T012 |
| FR-005 | T003/T010 | T008/T010/T015 |
| FR-006 | T005/T007/T011 | T006/T007/T015 |
| FR-007 | T003/T005/T007 | T006/T008/T015 |
| FR-008 | T004/T011/T013 | T002/T012/T013 |
| FR-009 | T009/T010 | T008/T010/T015 |
| FR-010 | T004/T005/T011/T013 | T002/T006/T012/T015 |
| DR-001 | T004/T005/T007/T011/T013 | T006/T007/T012/T015 |
| DR-002 | T003 | T006/T008/T012/T015 |
| DR-003 | T003/T009/T010 | T006/T008/T010/T012/T015 |
| SC-001 | T003/T013 | T006/T012/T015 |
| SC-002 | T004/T011/T013 | T012/T015 |
| SC-003 | T005/T007 | T006/T007/T015 |
| SC-004 | T014 | T001/T014/T015 |

All tasks are checked against actual implementation and verification evidence in verification.md; planning readiness alone was not treated as backend acceptance.
