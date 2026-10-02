# Tasks: Consolidate Census Membership

**Input**: spec.md, plan.md, research.md, data-model.md, contracts/membership.md, quickstart.md.
**Gate**: Reviewed bounded owner scope, all eight Constitution rows PASS, no unresolved clarification; analyze must find no critical issue before implementation.
**Language**: English for every artifact. Tasks are checked only where actual evidence exists; complete acceptance is recorded in verification.md.

## Phase 1: Specification and Design Gates

- [x] T001 Confirm requirements review, independent design review, eight Constitution PASS rows and non-destructive analysis in `specs/327-consolidate-census-members/spec.md`, `plan.md`, `research.md`, `tasks.md`; record gate evidence in `verification.md` before implementation.

## Phase 2: Foundational Failing Proof

- [x] T002 Capture actual isolated revision-0118 column/PK/FK/unique/index DDL, header/member trigger and function definitions, two incoming member FKs and non-FK SQL dependencies; recheck migration numbering and freeze `specs/327-consolidate-census-members/evidence/predecessor-schema.json` with commands/results in `verification.md` (FR-003/006/009/010; DR-002/003).
- [x] T003 Add selected dependency-closed metadata fixtures for store-only tests (avoid creating the old consumer FK against a new view before T012), shared two-tenant/four-family/equal-ID fixtures and canonical census/company-input seeding plus full unrelated authority row/schema snapshots in `packages/reality-core/tests/test_cost_census_members.py` and `test_cost_census_member_migration.py`; add representative missing-store/alias/guard and absent-revision proofs and observe red before runtime code changes (FR-001/002/003/004/006/009/011; DR-001/002/003).

## Phase 3: User Story 1 — Explain the Original Captured Observation (P1)

Goal: exact old capture values and original inspection remain explainable after consolidation.
Independent acceptance: compare member/context/hash/page/cursor results and replay after newer knowledge; missing outcome remains absent and corruption refused. This proves history independently; deployment remains atomic with US2/US3.

- [x] T004 [US1] Add exact 6/6/7/7 original columns and row/hash/context/IDs, empty family/capture, NULL source outcome, original page/cursor and replay/later-knowledge assertions in `packages/reality-core/tests/test_cost_census_members.py`; retain existing corruption and capture-bound checks in `tests/test_cost_census_storage.py` (FR-002/005/007/008/011; DR-001). Observe the new storage proof failing before T005.
- [x] T005 [US1] Implement closed four-family physical Table with family-qualified PK, original observations/hash, real subject/parent/outcome/self FKs, selection uniqueness, two stored generated identity aliases and unconditional complete-FK indexes in `packages/reality-core/src/reality/db/cost_census_members.py`; register core-first before shared indexing in `db/core.py` (FR-001/002/003/004/007/011; DR-001/002).
- [x] T006 [US1] Register exact original filtered views with fixed invoker-rights INSERT routing and stored RETURNING, native mutation paths and explicit backing dependencies in `packages/reality-core/src/reality/db/cost_census_members.py`; preserve original mapped class column sets in `db/cost_census.py` (FR-005/007/010; DR-001/003).
- [x] T007 [US1] Review unchanged serializers, capture byte-size inputs and original shared service paths in `services/cost_census_storage.py`, `services/cost_captured_basis.py`, `services/cost_records.py`; record the unchanged serializer/interface review in `specs/327-consolidate-census-members/verification.md` (FR-005/007/008/011; DR-001/003). Run the historical/interface executable proof with T018 after store guard/consumer retarget/migration are available; do not claim migrated guard parity from metadata-only proof.

## Phase 4: User Story 2 — Protected, Correctly Typed Membership (P1)

Goal: maintain typed references, physical admission and immutable history without extra consumer fields.
Independent acceptance: valid original batch writes plus adversarial subject/tenant/type/census/shape cases and both parent admission/seal race orders.

- [x] T008 [US2] Extend red-first physical/logical member guard and header protection cases, direct-store admission, building/sealed UPDATE/DELETE refusal, sealed INSERT refusal, no-match zero-row behavior and SQL/ORM bulk INSERT/RETURNING/rowcount in `packages/reality-core/tests/test_cost_census_members.py` (FR-005/006/008; DR-003). Observe backing guard failure before T011; migrated header assertions execute after T017.
- [x] T009 [US2] Add stored-alias NULL semantics, equal IDs, wrong-family/tenant/census document selection, company input naming non-line identities, missing/outcome/duplicate/closed-shape cases in `packages/reality-core/tests/test_cost_census_members.py` and canonical downstream fixtures from `tests/test_company_generation_manifest.py` exercised in `test_cost_census_member_migration.py` (FR-002/003/004/011; DR-002/003). Observe absent consumer retarget before T012; reuse T003 initial absent-store proof for foundational alias constraints.
- [x] T010 [US2] Add bounded two-session READ COMMITTED insertion-versus-sealing tests with synchronization events and observed database lock waits, both race orders, failure cleanup and request/savepoint regression coverage in `packages/reality-core/tests/test_cost_census_members.py` (FR-006/008; DR-003); no timing-only sleeps. Observe admission guard failure before T011.
- [x] T011 [US2] Implement store-owned physical BEFORE guard with original member UPDATE/DELETE refusal and same-tenant building parent FOR UPDATE; add function/trigger create-drop hooks without replacing/removing original header guard/function in `packages/reality-core/src/reality/db/cost_census_members.py` (FR-006/008/010; DR-003).
- [x] T012 [US2] Retarget only the existing `(tenant_id,census_line_id)` composite FK in `packages/reality-core/src/reality/db/company_generations.py` to the backing line identity alias; preserve original public fields and all downstream hashes/values, without ORM private-internal mutation (FR-003/005/011; DR-002).
- [x] T013 [US2] Add repeated/full/selected metadata create/drop/recreate, owned function cleanup, all eight store/consumer complete-key index coverage, Alembic view exclusion and once-only count proofs in `packages/reality-core/tests/test_cost_census_members.py`; adjust only explicit current storage aliases/index/reporting dispositions in `tests/test_cost_records.py`, `tests/test_schema_indexes.py`, `tests/test_reporting_graph_coverage.py` (FR-001/005/010; DR-003). Preserve logical resource coverage; no generic exclusion or lifecycle repair without failing proof.

## Phase 5: User Story 3 — Reversible Storage Transition (P2)

Goal: exact populated migration and rollback with typed downstream references and all original protection.
Independent acceptance: upgrade → supported new captures → downgrade → re-upgrade, complete row/DDL/guard parity; injected failure leaves predecessor intact.

- [x] T014 [US3] Complete populated migration fixture assertions for all four families/two tenants/equal IDs/NULL outcome/empty capture, original cursors and historical digests, downstream company inputs and all unrelated authorities in `packages/reality-core/tests/test_cost_census_member_migration.py`; assert exact -3 physical count and original-DDL/guard restoration (FR-001/002/003/005/007/009/011; DR-001/002). Observe absent-revision proof before T017.
- [x] T015 [US3] Add injected copy/parity abort and supported post-upgrade new captures through canonical services, exact rollback/re-upgrade FKs/indexes/function/trigger behavior and immutable-header/member admission proof in `packages/reality-core/tests/test_cost_census_member_migration.py` (FR-006/008/009/011; DR-001/002/003); observe failure before T017.
- [x] T016 [US3] Prove actual migrated predecessor and consolidated protected-history purge refusal/rollback, eligible purge behavior, no duplicate deletion attempts/counts and another tenant unchanged in `packages/reality-core/tests/test_cost_census_member_migration.py`; reuse unchanged authority in `services/core.py` and `services/account_deletion.py` (FR-010/011; DR-003). No trigger bypass or new retained-history cleanup.
- [x] T017 [US3] Implement frozen `packages/reality-core/migrations/versions/0121_census_members.py` after head recheck: deterministic locks, unguarded document-first exact copy/parity, consumer FK redirect, old line-before-document retirement, views/physical guard/routing before commit; reverse populated restoration with original guards and consumer target before dropping store (FR-001/002/003/004/005/006/007/009/010/011; DR-001/002/003). No current-model import, CASCADE or global constraint disabling.
- [x] T018 [US3] Adapt only demonstrated predecessor/current-schema assumptions and test-only physical corruption trigger target in `packages/reality-core/tests/test_cost_census_storage.py`, `test_cost_census_migration.py`; run full targeted census/captured-basis/company-input/cost-record/schema/lifecycle and previous consolidation migration regressions, recording actual commands/results in `specs/327-consolidate-census-members/verification.md` (FR-003/005/006/007/008/009/010/011; DR-001/002/003). Never weaken retained-history downgrade refusal or other assertions.

## Final Phase: Cross-Cutting Review

- [ ] T019 Freeze relevant backend source hashes in `specs/327-consolidate-census-members/evidence/acceptance-source-manifest.json`, run full required PostgreSQL backend and unchanged serial 10,000-source benchmark, lint/spec/diff, docs generation/catalog reproducibility/build and Web format/i18n/tests/build; preserve failed/green raw logs and exact unique counts in `verification.md` (SC-004).
- [ ] T020 Review final implementation/migration diff against every FR/DR and Constitution, exact -3 physical count and four original logical sets, typed alias/incoming link proof, immutable lifecycle, populated rollback and no unrelated authority changes; document review in `specs/327-consolidate-census-members/verification.md` (FR-001/003/005/006/009/010/011; DR-001/002/003; SC-001/002/003).
- [ ] T021 Update `docs/DATA_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/SPEC_COVERAGE_MATRIX.md`, `docs/features/receipt-costing.md`, `docs/ideas/census-storage-consolidation.md`, `docs/ideas/table-storage-overview.md` and feature status/checklists only after every required gate passes; reconcile exact inventory and retain historical audit snapshots in `specs/327-consolidate-census-members/verification.md` (FR-001/002/003/004/005/006/007/008/009/010/011; DR-001/002/003; SC-001/002/003/004).

## Dependencies and Execution Order

T001 → T002 → T003. Before foundational storage implementation, prepare tests from
T004 and the foundational alias cases in T003. Then T005 → T006 → T007 (source review; executable story proof in T018). Prepare T008/
T009/T010 before T011/T012; T011/T012 → T013. Prepare T014/T015/T016 before T017;
T017 → T018 → T019 → T020 → T021. Initial new migration failures can be observed in
T003 and completed again in T014/T015. Migrated assertions only execute after T017.

Tests precede the code they prove; task numbering groups stories and does not permit
skipping those dependency edges. Services/tools/adapters remain unchanged except a
proven bounded compatibility issue. All stories have independently observable proof,
but the storage revision is an atomic release: history alone is the first validation
milestone, never a deployable replacement without guard/link/rollback acceptance.

## Safe Parallel Opportunities

No tasks carry [P]: shared test fixture files, metadata and physical DB fixtures make
mutations sequential. Independent read-only work can be batched: US1 hash/field review
in T007 with source dependency reading; US2 incoming-FK and guard review while preparing
tests in distinct files; US3 immutable predecessor DDL and authority inventory reads.
Full suite/builds and serial benchmark are scheduled to avoid resource interference.
This describes orchestration, not authorization to spawn additional agents.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) |
| --- | --- | --- |
| FR-001 | T003/T013/T014 | T005/T017/T020/T021 |
| FR-002 | T003/T004/T009/T014 | T005/T017/T021 |
| FR-003 | T002/T003/T009/T014/T018 | T005/T012/T017/T020/T021 |
| FR-004 | T003/T009 | T005/T017/T021 |
| FR-005 | T004/T008/T013/T014/T018 | T006/T007/T012/T017/T020/T021 |
| FR-006 | T002/T003/T008/T010/T015/T018 | T011/T017/T020/T021 |
| FR-007 | T004/T014/T018 | T005/T006/T007/T017/T021 |
| FR-008 | T004/T008/T010/T015/T018 | T007/T011/T021 |
| FR-009 | T002/T003/T014/T015/T018 | T017/T020/T021 |
| FR-010 | T002/T013/T016/T018 | T006/T011/T017/T020/T021 |
| FR-011 | T003/T004/T009/T014/T015/T016/T018 | T005/T007/T012/T017/T020/T021 |
| DR-001 | T003/T004/T014/T015/T018 | T005/T006/T007/T017/T020/T021 |
| DR-002 | T002/T003/T009/T014/T015/T018 | T005/T012/T017/T020/T021 |
| DR-003 | T002/T003/T008/T009/T010/T015/T016/T018 | T006/T007/T011/T017/T020/T021 |
| SC-001 | T013/T014 | T020/T021 |
| SC-002 | T014/T015/T016 | T017/T020/T021 |
| SC-003 | T004/T008/T009/T010/T014/T015/T018 | T011/T012/T020/T021 |
| SC-004 | T019 | T001/T019/T021 |

Tasks are planning output, not claims of accepted implementation. No live migration,
commit or deployment follows from task generation.
