# Tasks: Operational Finance Subledgers

**Input**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md), [contracts/commands.md](contracts/commands.md), [contracts/views.md](contracts/views.md), [verification.md](verification.md), [test-plan.md](test-plan.md).

**Status**: Account-catalog slice integrated, verified and running on local port 8080. Full finance roadmap remains open; see [verification-results.md](verification-results.md).

## Local development cutover decision — 2026-09-09

The owner is the only current local tester and has no real account population to migrate. Build a clean new schema and regenerate disposable test fixtures. No old-account-string backfill, unresolved legacy-account state, dual account columns, old-binary compatibility or per-tenant migration rollout is required. Keep the repository Alembic chain coherent; do not rewrite unrelated migration history. A reset/reseed must target an explicitly identified disposable local/test database and must not occur automatically on application startup or against an arbitrary configured database. This planning change does not execute a reset.

This removes local development compatibility work, not business integrity: newly recorded evidence/entries remain immutable and tenant-scoped, with explicit reversals. Customer/supplier opening imports, external historical-source matching and coverage remain product features for customers moving from other systems.

## Format and execution rules

`- [ ] T001 [P?] [USn] [FR/DR references] Action with exact repository path`

Paths are repository-relative; named new files are planned additions. Tests below require meaningful failing proof before the corresponding code. Each test task names its entry test; expand it into independently asserted parametrized cases for the full listed fixture. PostgreSQL race tests use separate sessions/barriers. A test referencing a later story is authored now and completed only after its explicit dependency; never mark that story fully complete while such checks are red.

Every implementation slice includes tenant filters/composite links, events, command/read discovery, shared adapter routing, Inspector provenance and appropriate UI states. No direct ORM writes from adapters. Shared-file tasks execute sequentially. No parallel marker authorizes concurrent edits to the same file.

## Phase 1: Specification and design gates

- [ ] T001 Record the reviewed product scope and actual technical/schema approval evidence in `specs/148-accounting-journal-cost-centers/checklists/requirements.md`; review `specs/148-accounting-journal-cost-centers/data-model.md` against the Constitution. Do not infer schema approval from task-generation authorization.
- [ ] T002 Freeze the actual integration checkout, migration head and web mounting paths in `specs/148-accounting-journal-cost-centers/research.md`; confirm every `specs/148-accounting-journal-cost-centers/plan.md` Constitution row remains PASS. Preserve concurrent workspace changes.
- [ ] T003 Run cross-artifact analysis of `specs/148-accounting-journal-cost-centers/spec.md`, `specs/148-accounting-journal-cost-centers/plan.md` and `specs/148-accounting-journal-cost-centers/tasks.md`; resolve CRITICAL findings through the authorized review workflow before implementation. Record the approved outcome in `specs/148-accounting-journal-cost-centers/checklists/requirements.md`.

## Phase 2: Foundational failing proof and shared boundaries

Goal: establish shared transaction, identity and evidence rules before adding consumers. These tests grow with each later schema slice.

- [ ] T004 [DR-001] Add failing `test_dr_001_acceptance` in `packages/reality-core/tests/finance/test_provenance.py` covering: Source/evidence/Reality and separate receipt provenance. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T005 [DR-002] Add failing `test_dr_002_acceptance` in `packages/reality-core/tests/finance/test_schema.py` covering: Shortest-link schema review; no duplicated line ownership. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T006 [DR-003] Add failing `test_dr_003_acceptance` in `packages/reality-core/tests/finance/test_tenant_isolation.py` covering: Isolation catalog and PostgreSQL cross-tenant/target refusal tests. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T007 [DR-004] Add failing `test_dr_004_acceptance` in `packages/reality-core/tests/finance/test_immutability.py` covering: Immutable source/ledger/package/receipt history and read-only derived state. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T008 [DR-005] Add failing `test_dr_005_acceptance` in `packages/reality-core/tests/finance/test_received_values.py` covering: Decimal balance, no source amount recomputation or silent split residual. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T009 [DR-006] Add failing `test_dr_006_acceptance` in `packages/reality-core/tests/finance/test_adapter_jobs.py` covering: Tool/service/adapter parity, existing worker registry, no direct external-effect handler. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T010 [DR-007] Add failing `test_dr_007_acceptance` in `packages/reality-core/tests/finance/test_migration_catalogs.py` covering: Reviewed clean-schema initialization/reseed, data/event/command/Inspector catalogs and existing regressions. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T011 [FR-021] Add failing `test_fr_021_acceptance` in `packages/reality-core/tests/finance/test_authorization.py` covering: Shared tools, owner configuration, tenant mutation policy and unchanged Chat/MCP confirmation. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T012 [FR-022] Add failing `test_fr_022_acceptance` in `packages/reality-core/tests/finance/test_initialization_reads.py` covering: Clean database initialization, service-generated fixtures and immutable new-model entry/allocation history. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T013 [DR-001, DR-002, DR-005] Implement bounded role/direction/amount validation in `packages/reality-core/src/reality/domain/finance.py`; define exact Decimal rejection, evidence ownership and no-derived-Fact rules.
- [ ] T014 [DR-001, DR-002, DR-003, DR-004, DR-007] Add finance coordination/operation/effect/evidence models in `packages/reality-core/src/reality/db/finance.py` and metadata registration in `packages/reality-core/src/reality/db/core.py`; create the next-head additive foundation revision in `packages/reality-core/migrations/versions/` after T002 resolves its exact identifier. Enforce tenant composite keys and immutable evidence links.
- [ ] T015 [FR-021, FR-022, DR-003, DR-004, DR-005, DR-006] Implement finance lock/revision, idempotency result recovery and bound transaction composition in `packages/reality-core/src/reality/services/finance/transaction.py`; integrate every legacy posting/allocation/refund/reversal/payment-run path in `packages/reality-core/src/reality/services/core.py` without intermediate commits. Count effective allocations at both endpoints exactly once.
- [ ] T016 [FR-021, DR-003, DR-006] Implement atomic confirmed finance execution in `packages/reality-core/src/reality/tools/application.py` and common validated envelopes in `packages/reality-core/src/reality/tools/finance.py`; reject self-approval/stale permission and return authoritative IDs after lost-response recovery.
- [ ] T017 [DR-001, DR-002, DR-003, DR-004, DR-005, DR-006, DR-007] Extend `packages/reality-core/src/reality/catalogs.py` and existing catalog registrations in `packages/reality-core/src/reality/tools/application.py` plus `packages/reality-core/src/reality/web/application_catalog.py` for introduced tables/events/commands; route finance capability dispatch through `packages/reality-core/src/reality/cli/app.py`, `packages/reality-core/src/reality/mcp/server.py` and `packages/reality-core/src/reality/web/api.py`. Document transaction/tenant/provenance contracts in `docs/ARCHITECTURE.md` and `docs/DATA_MODEL.md`.

## Phase 3: User Story 5 — Control permitted subledger accounts (P1)

**Dependencies**: Foundation; account schema is required by every subsequent story.
**Independent acceptance**: Create the minimal set in an empty tenant; reject wrong/blocked roles; retain the original account after changing defaults; initialize clean fixtures using required account IDs. External target mapping belongs to US2; frozen-package assertions finish with US3. Local account setup is independently testable.

- [ ] T018 [US5] [FR-024] Add failing `test_fr_024_acceptance` in `packages/reality-core/tests/finance/test_accounts.py` covering: Minimal setup, manual/imported references, unique codes and no number-derived role. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T019 [US5] [FR-025] Add failing `test_fr_025_acceptance` in `packages/reality-core/tests/finance/test_accounts.py` covering: All shared posting paths, role/default resolution, tenant checks and concurrent block/revision race. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T020 [US5] [FR-026] Add failing `test_fr_026_acceptance` in `packages/reality-core/tests/finance/test_accounts.py` covering: Immutable used role, audited rename, blocked exact reversal, replacement refusal and role-wide balances. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T021 [US5] [FR-028] Add failing `test_fr_028_acceptance` in `packages/reality-core/tests/finance/test_accounts.py` covering: Clean account initialization, required IDs, no legacy-string authority and currency-separated reads. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T022 [US5] [FR-024, FR-026, FR-028] Implement account/default models and required account_id directly in `packages/reality-core/src/reality/db/finance.py` and `packages/reality-core/src/reality/db/core.py`; remove the legacy account string and update fixture producers/callers. Test clean-schema initialization; no backfill, unresolved roles or compatibility columns.
- [ ] T023 [US5] [FR-024, FR-025, FR-026, FR-028] Implement create/update/default/import preview and role-wide discovery in `packages/reality-core/src/reality/services/finance/accounts.py`; integrate original-invoice-account precedence, blocked exact inverse and all eight normal posting paths in `packages/reality-core/src/reality/services/core.py`.
- [ ] T024 [US5] [FR-024, FR-025, FR-026, FR-028] Expose account tools in `packages/reality-core/src/reality/tools/finance.py` and V08 empty-tenant setup/settings in `apps/web/src/finance/AccountSettings.tsx`; wire current `apps/web/src/App.tsx`, shared discovery and Inspector links; external mapping UI follows T062.
- [ ] T025 [US5] [FR-024, FR-025, FR-026, FR-028] Run the story-specific tests from `specs/148-accounting-journal-cost-centers/test-plan.md`, its shared tool/adapter contract checks and applicable browser states; record actual results and any deferred integration cases in `specs/148-accounting-journal-cost-centers/verification-results.md`. Complete this story only after its dependent checks pass.

## Phase 4: User Story 7 — Resolve customer payment differences (P1)

**Dependencies**: US5 and foundation.
**Independent acceptance**: 1,020 cash against 1,000 leaves 20 credit; 980 cash leaves 20 open unless a separately approved reduction settles it; race/refund/reversal preserve both histories.

- [ ] T026 [US7] [FR-035] Add failing `test_fr_035_acceptance` in `packages/reality-core/tests/finance/test_settlement.py` covering: Actual receipt 1,020, allocation 1,000, excess 20; strict legacy invoice action preserved. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T027 [US7] [FR-036] Add failing `test_fr_036_acceptance` in `packages/reality-core/tests/finance/test_settlement.py` covering: Unaccepted skonto/withholding stays open; explanatory note has no financial/aging effect. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T028 [US7] [FR-037] Add failing `test_fr_037_acceptance` in `packages/reality-core/tests/finance/test_settlement.py` covering: Stated adjustment 20 or 60, separate evidence/non-cash entries, no fake source or calculation. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T029 [US7] [FR-038] Add failing `test_fr_038_acceptance` in `packages/reality-core/tests/finance/test_settlement.py` covering: Stale/duplicate/source-credit rejection; atomic combined action and independent cash recording. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T030 [US7] [FR-039] Add failing `test_fr_039_acceptance` in `packages/reality-core/tests/finance/test_settlement.py` covering: Reuse/refund existing excess, no duplicate payment; tenant/party/currency and available-credit bounds. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T031 [US7] [FR-040] Add failing `test_fr_040_acceptance` in `packages/reality-core/tests/finance/test_settlement.py` covering: PostgreSQL concurrent allocation/refund/adjustment and independent payment/adjustment/refund reversals. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T032 [US7] [FR-041] Add failing `test_fr_041_acceptance` in `packages/reality-core/tests/finance/test_settlement.py` covering: Catalog/matrix/UI parity, 980 cash plus 20 adjustment wording and external missing-tax readiness. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T033 [US7] [FR-036, FR-037, FR-038] Add settlement-adjustment evidence extension and next-head migration in `packages/reality-core/src/reality/db/finance.py`; implement reason, source/effect and positive received-amount rules in `packages/reality-core/src/reality/domain/finance.py`.
- [ ] T034 [US7] [FR-035, FR-036, FR-037, FR-038, FR-039, FR-040] Implement actual receipt, atomic combined settlement and same-account credit allocation/refund in `packages/reality-core/src/reality/services/finance/settlement.py`; reuse bounded primitives in `packages/reality-core/src/reality/services/core.py`, retain strict legacy invoice actions, and independently reverse cash/reduction/refund effects.
- [ ] T035 [US7] [FR-035, FR-036, FR-037, FR-038, FR-039, FR-040, FR-041] Expose customer commands and result reads in `packages/reality-core/src/reality/tools/finance.py`; implement V03/V09 customer dialogs and V01–V06/V08 integration in `apps/web/src/finance/SettlementActions.tsx`; annotate handoff missing tax rather than deriving it in `packages/reality-core/src/reality/services/finance/handoff.py`.
- [ ] T036 [US7] [FR-035, FR-036, FR-037, FR-038, FR-039, FR-040, FR-041] Run the story-specific tests from `specs/148-accounting-journal-cost-centers/test-plan.md`, its shared tool/adapter contract checks and applicable browser states; record actual results and any deferred integration cases in `specs/148-accounting-journal-cost-centers/verification-results.md`. Complete this story only after its dependent checks pass.

## Phase 5: User Story 8 — Supplier differences and available credits (P1)

**Dependencies**: US7; opening-credit additions finish with US9.
**Independent acceptance**: Supplier agreement is required for reductions; customer/supplier tabs find credits even without open invoices; both endpoint consumption and races prevent excess refund.

- [ ] T037 [US8] [FR-042] Add failing `test_fr_042_acceptance` in `packages/reality-core/tests/finance/test_settlement.py` covering: Supplier cash/control signs, agreement authority, partial/full reduction, excess allocation/refund and PostgreSQL race/reversal parity. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T038 [US8] [FR-043] Add failing `test_fr_043_acceptance` in `packages/reality-core/tests/finance/test_credits.py` covering: Both credit tabs, payment/credit-note origins counted once, same-party/side/currency bounds, no-open-invoice discoverability and V09 UI matrix. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T039 [US8] [FR-042] Implement explicit supplier direction/entitlement validation and transaction-bound supplier payment/reduction/refund wrappers in `packages/reality-core/src/reality/services/finance/settlement.py` and `packages/reality-core/src/reality/services/core.py`; never erase unilateral withholding.
- [ ] T040 [US8] [FR-043] Implement shared eligible-origin availability/totals/explanations in `packages/reality-core/src/reality/services/finance/reads.py`; exclude inverses/reductions/transfer intermediates and separate side/party/currency, extending to opening origins in US9.
- [ ] T041 [US8] [FR-042, FR-043] Expose supplier and shared credit tools in `packages/reality-core/src/reality/tools/finance.py` and both V09 tabs in `apps/web/src/finance/AvailableCredits.tsx`; show exact origin and allocation/refund action, no automatic netting.
- [ ] T042 [US8] [FR-042, FR-043] Run the story-specific tests from `specs/148-accounting-journal-cost-centers/test-plan.md`, its shared tool/adapter contract checks and applicable browser states; record actual results and any deferred integration cases in `specs/148-accounting-journal-cost-centers/verification-results.md`. Complete this story only after its dependent checks pass.

## Phase 6: User Story 9 — Import opening positions (P1)

**Dependencies**: US8; no external accounting connector dependency.
**Independent acceptance**: All four 100 EUR residual directions create only control/neutral effects; replay retains identity; summary/detail overlap refuses duplicate effects; unknown dates remain unknown.

- [ ] T043 [US9] [FR-044] Add failing `test_fr_044_acceptance` in `packages/reality-core/tests/finance/test_opening.py` covering: Four exact opening directions and no revenue/expense/cash effect. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T044 [US9] [FR-045] Add failing `test_fr_045_acceptance` in `packages/reality-core/tests/finance/test_opening.py` covering: Source-stated residual, summary mode, separate directions/currencies and unknown aging. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T045 [US9] [FR-046] Add failing `test_fr_046_acceptance` in `packages/reality-core/tests/finance/test_opening.py` covering: Bounded atomic import, owner/stale checks, re-upload, changed snapshot and coverage/backfill conflicts. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T046 [US9] [FR-047] Add failing `test_fr_047_acceptance` in `packages/reality-core/tests/finance/test_opening.py` covering: Opening allocation/adjustment/refund parity, V09 origin identity and concurrent reversal/consumption. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T047 [US9] [FR-048] Add failing `test_fr_048_acceptance` in `packages/reality-core/tests/finance/test_opening.py` covering: V10 shared state/visual/catalog proof and no accidental normal-business handoff/activity. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T048 [US9] [FR-044, FR-045, FR-046] Add opening scope/item evidence and next-head migration in `packages/reality-core/src/reality/db/finance.py`; implement direction and coverage identity checks in `packages/reality-core/src/reality/domain/finance.py`.
- [ ] T049 [US9] [FR-044, FR-045, FR-046] Implement owner-bound 200-item/4-MiB atomic preview/import, changed snapshot/backfill review and four-direction posting in `packages/reality-core/src/reality/services/finance/opening.py`; integrate original/summary coverage into financial intake.
- [ ] T050 [US9] [FR-047, FR-048] Extend settlement, credit reads, adjustment and inverse dependency handling in `packages/reality-core/src/reality/services/finance/settlement.py` and `packages/reality-core/src/reality/services/finance/reads.py`; exclude opening evidence from ordinary turnover/cash/new-business handoff in `packages/reality-core/src/reality/services/finance/handoff.py`.
- [ ] T051 [US9] [FR-044, FR-045, FR-046, FR-047, FR-048] Expose opening tools in `packages/reality-core/src/reality/tools/finance.py` and V10 preview/conflict/confirmation in `apps/web/src/finance/OpeningItems.tsx`; connect V03/V09/Inspector provenance.
- [ ] T052 [US9] [FR-044, FR-045, FR-046, FR-047, FR-048] Run the story-specific tests from `specs/148-accounting-journal-cost-centers/test-plan.md`, its shared tool/adapter contract checks and applicable browser states; record actual results and any deferred integration cases in `specs/148-accounting-journal-cost-centers/verification-results.md`. Complete this story only after its dependent checks pass.

## Phase 7: User Story 2 — Received detail and optional attribution (P1)

**Dependencies**: US5; full frozen-package test completion depends on US3.
**Independent acceptance**: Received net 1,000 allows 600/400 assignment without changing gross 1,190; null differs from zero; overassignment and wrong/retired centers fail.

- [ ] T053 [US2] [FR-006] Add failing `test_fr_006_acceptance` in `packages/reality-core/tests/finance/test_components.py` covering: Source fidelity, absent versus zero, coding namespace and no inferred amounts. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T054 [US2] [FR-007] Add failing `test_fr_007_acceptance` in `packages/reality-core/tests/finance/test_components.py` covering: Summary/line roles and no repeated document amount attribution. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T055 [US2] [FR-008] Add failing `test_fr_008_acceptance` in `packages/reality-core/tests/finance/test_components.py` covering: 600/400 and partial assignment, over-allocation, mixed bases/currencies and immutable revision. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T056 [US2] [FR-009] Add failing `test_fr_009_acceptance` in `packages/reality-core/tests/finance/test_components.py` covering: Target-specific references, no tax determination, local posting survives missing mapping. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T057 [US2] [FR-010] Add failing `test_fr_010_acceptance` in `packages/reality-core/tests/finance/test_components.py` covering: Retire/rename and frozen package assignment/mapping history. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T058 [US2] [FR-027] Add failing `test_fr_027_acceptance` in `packages/reality-core/tests/finance/test_accounts.py` covering: Optional per-target mapping revisions, frozen exports and unchanged gross basis. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T059 [US2] [FR-006, FR-007, FR-008, FR-009, FR-010] Add received components, typed references, assignment revisions/parts and target/profile/reference mapping schema with next-head migration in `packages/reality-core/src/reality/db/finance.py`; enforce XOR owner, kind-aware FKs and explicit nullable received amounts.
- [ ] T060 [US2] [FR-027] Implement optional versioned local-account target mapping in `packages/reality-core/src/reality/services/finance/components.py` and `packages/reality-core/src/reality/db/finance.py`; preserve gross basis. Complete immutable prepared-consumer validation with US3. This task depends on target/profile schema from T059; local account setup does not depend on this task.
- [ ] T061 [US2] [FR-006, FR-007, FR-008, FR-009, FR-010] Implement lossless component extraction, explicit assignments and reference history in `packages/reality-core/src/reality/services/finance/components.py`; do not add document summaries twice or derive missing net/tax/center allocations.
- [ ] T062 [US2] [FR-006, FR-007, FR-008, FR-009, FR-010, FR-027] Expose component/reference and optional local-account target-mapping tools and read provenance in `packages/reality-core/src/reality/tools/finance.py`; implement V04/V07/V08 in `apps/web/src/finance/FinancialComponents.tsx` with separate source/internal values and partial/unassigned states.
- [ ] T063 [US2] [FR-006, FR-007, FR-008, FR-009, FR-010] Run the story-specific tests from `specs/148-accounting-journal-cost-centers/test-plan.md`, its shared tool/adapter contract checks and applicable browser states; record actual results and any deferred integration cases in `specs/148-accounting-journal-cost-centers/verification-results.md`. Complete this story only after its dependent checks pass.

## Phase 8: User Story 6 — Resolve declared cases for handoff (P1)

**Dependencies**: US2 service/schema increment; full package revision checks finish with US3.
**Independent acceptance**: Eight ERP directions remain fixed; two explicit cases/groups resolve exactly per target; country-only input does not infer treatment; competing scopes fail.

- [ ] T064 [US6] [FR-029] Add failing `test_fr_029_acceptance` in `packages/reality-core/tests/finance/test_mapping.py` covering: Eight-direction service/adapter matrix, explicit/default accounts and non-posting triggers. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T065 [US6] [FR-030] Add failing `test_fr_030_acceptance` in `packages/reality-core/tests/finance/test_mapping.py` covering: Defined source/internal cases, multi-case scope and no country/rate inference; resolve source codes without a target, reject namespace/kind/tenant collisions and stale/retired mappings, preserve original codes and frozen source revision IDs. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T066 [US6] [FR-031] Add failing `test_fr_031_acceptance` in `packages/reality-core/tests/finance/test_mapping.py` covering: Defined optional groups, no guessed classification and wrong-tenant/retired refusal. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T067 [US6] [FR-032] Add failing `test_fr_032_acceptance` in `packages/reality-core/tests/finance/test_mapping.py` covering: Exact target resolution, group modes, overlap rejection and competing-path refusal. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T068 [US6] [FR-033] Add failing `test_fr_033_acceptance` in `packages/reality-core/tests/finance/test_mapping.py` covering: Immutable revisions, owner activation, stale preview and unchanged prior package/local balances. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T069 [US6] [FR-034] Add failing `test_fr_034_acceptance` in `packages/reality-core/tests/finance/test_mapping.py` covering: V01/V04/V05/V08 additions, shared resolver parity and read-only matrix. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T070 [US6] [FR-029, FR-030, FR-031, FR-032] Implement fixed matrix and exact case/group discrimination in `packages/reality-core/src/reality/domain/finance.py`; add target-independent source_classification_mapping_revision with exact active source-scope uniqueness and typed local-reference FK, plus target mapping shape/active-scope checks in `packages/reality-core/src/reality/db/finance.py` without arbitrary predicates or country rules.
- [ ] T071 [US6] [FR-030, FR-031, FR-032, FR-033] Implement target-independent source classification resolution and owner draft/activate/retire, separate internal overrides, and target mapping draft/test/activate/retire and frozen revision selection in `packages/reality-core/src/reality/services/finance/components.py`; enforce owner activation, retired/stale refusal and non-competing account/case scopes.
- [ ] T072 [US6] [FR-029, FR-030, FR-031, FR-032, FR-033, FR-034] Expose matrix, finance.source_mapping draft/activate/retire/resolve and target mapping tools in `packages/reality-core/src/reality/tools/finance.py`; implement V08 editors and V01/V04/V05 explanation in `apps/web/src/finance/MappingSettings.tsx`; verify existing ERP adapters preserve the eight directions.
- [ ] T073 [US6] [FR-029, FR-030, FR-031, FR-032, FR-033, FR-034] Run the story-specific tests from `specs/148-accounting-journal-cost-centers/test-plan.md`, its shared tool/adapter contract checks and applicable browser states; record actual results and any deferred integration cases in `specs/148-accounting-journal-cost-centers/verification-results.md`. Complete this story only after its dependent checks pass.

## Phase 9: User Story 3 — Prepare and track external accounting handoff (P1)

**Dependencies**: US6, US9 and earlier evidence extensions. Re-run deferred frozen-package cases from US5/US2/US6 here.
**Independent acceptance**: Download is byte-identical after mapping changes; accepted-only never means posted; conflicting/version-mismatched receipts remain explicit.

- [ ] T074 [US3] [FR-011] Add failing `test_fr_011_acceptance` in `packages/reality-core/tests/finance/test_handoff.py` covering: Independent readiness axes, reason counts and no Document status fields. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T075 [US3] [FR-012] Add failing `test_fr_012_acceptance` in `packages/reality-core/tests/finance/test_handoff.py` covering: Exact package manifest/components/identities, neutral profile label and explicit omissions. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T076 [US3] [FR-013] Add failing `test_fr_013_acceptance` in `packages/reality-core/tests/finance/test_handoff.py` covering: Stale preview, repeat preparation/download and no remote success inference. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T077 [US3] [FR-014] Add failing `test_fr_014_acceptance` in `packages/reality-core/tests/finance/test_handoff.py` covering: Lossless receipt chain and target/item/version/outcome evidence. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T078 [US3] [FR-015] Add failing `test_fr_015_acceptance` in `packages/reality-core/tests/finance/test_handoff.py` covering: Idempotent, partial, conflicting, unmatched and out-of-order receipts. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T079 [US3] [FR-016] Add failing `test_fr_016_acceptance` in `packages/reality-core/tests/finance/test_handoff.py` covering: Correction/retry identity, unchanged prior packages, no blind resend or remote reversal. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T080 [US3] [FR-012, FR-014, FR-015, FR-016] Add immutable packages/items/revision links and source-backed receipt detail with next-head migration in `packages/reality-core/src/reality/db/finance.py`; define neutral-v1 schemas in `packages/reality-core/src/reality/domain/finance.py`.
- [ ] T081 [US3] [FR-011, FR-012, FR-013, FR-016] Implement two-axis readiness, 200-item/4-MiB exact-selection preparation, serializer/hash/idempotency, immutable download and correction/retry in `packages/reality-core/src/reality/services/finance/handoff.py`.
- [ ] T082 [US3] [FR-014, FR-015, FR-016] Implement lossless receipt interpretation/matching and partial/unmatched/conflicting/out-of-order reads in `packages/reality-core/src/reality/services/finance/handoff.py`; preserve exact target/item/version evidence and never infer remote success.
- [ ] T083 [US3] [FR-011, FR-012, FR-013, FR-014, FR-015, FR-016] Expose handoff/receipt tools in `packages/reality-core/src/reality/tools/finance.py`; implement V05/V06 in `apps/web/src/finance/AccountingHandoff.tsx`, with reviewed exclusions, prior packages and independent remote facts.
- [ ] T084 [US3] [FR-011, FR-012, FR-013, FR-014, FR-015, FR-016] Run the story-specific tests from `specs/148-accounting-journal-cost-centers/test-plan.md`, its shared tool/adapter contract checks and applicable browser states; record actual results and any deferred integration cases in `specs/148-accounting-journal-cost-centers/verification-results.md`. Complete this story only after its dependent checks pass.

## Phase 10: User Story 10 — Trade-finance controls and agent explanation (P1)

**Dependencies**: US3 and prior settlement/opening foundations. Each subsection is independently verified before combined activation.
**Independent acceptance**: 100 capture/3 fee/97 payout and bank receipt balances correctly; advance and hold races refuse invalid use; transfer conserves role balance; partial billing and migrated unknowns stay explainable.

- [ ] T085 [US10] [FR-049] Add failing `test_fr_049_acceptance` in `packages/reality-core/tests/finance/test_money.py` covering: 100 capture / 3 stated fee / 97 payout-bank receipt; pending events, reserves and disputed funds distinct. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T086 [US10] [FR-050] Add failing `test_fr_050_acceptance` in `packages/reality-core/tests/finance/test_money.py` covering: Capture/statement/bank economic identity, partial batch coverage, refund/fee duplication and unsupported FX; one provider account with two event currencies cannot match or consume across currencies. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T087 [US10] [FR-051] Add failing `test_fr_051_acceptance` in `packages/reality-core/tests/finance/test_advances.py` covering: Both advance directions, partial orders/invoices, cancellation and PostgreSQL earmark-versus-consumption race. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T088 [US10] [FR-052] Add failing `test_fr_052_acceptance` in `packages/reality-core/tests/finance/test_holds.py` covering: Hold-after-preview refusal across individual/run paths, explicit release and evidenced during-hold reconciliation. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T089 [US10] [FR-053] Add failing `test_fr_053_acceptance` in `packages/reality-core/tests/finance/test_transfers.py` covering: Both control-side transfer directions, atomic paired allocations, unchanged role balance and reversal/blocked checks. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T090 [US10] [FR-054] Add failing `test_fr_054_acceptance` in `packages/reality-core/tests/finance/test_trade.py` covering: Partial/consolidated order-goods-invoice-credit-settlement trace and source-stated unallocated charges. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T091 [US10] [FR-055] Add failing `test_fr_055_acceptance` in `packages/reality-core/tests/finance/test_trade.py` covering: Linked/not-applicable/unknown, scoped coverage invalidation and migrated-history false-positive refusal. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T092 [US10] [FR-056] Add failing `test_fr_056_acceptance` in `packages/reality-core/tests/finance/test_agent_contract.py` covering: Complete/paginated structured explanation, cutoff change/restart, exact provenance and no financial Fact writes. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T093 [US10] [FR-057] Add failing `test_fr_057_acceptance` in `packages/reality-core/tests/finance/test_agent_contract.py` covering: Public capability parity, stale/permission refusal, authoritative result re-read and no invented external success. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T094 [US10] [FR-058] Add failing `test_fr_058_acceptance` in `packages/reality-core/tests/finance/test_web_contract.py` covering: V11/V12/V13 and existing-screen shared read/UI/isolation/locale/visual proof. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T095 [US10] [FR-049, FR-050, FR-051, FR-052, FR-053, FR-054, FR-055] Add multi-currency money-account purpose/source detail without an account currency restriction, money-event, advance/change, payable-hold/release, transfer and relationship/coverage models with next-head migration in `packages/reality-core/src/reality/db/finance.py`; implement bounded event/owner/direction rules in `packages/reality-core/src/reality/domain/finance.py`.
- [ ] T096 [US10] [FR-049, FR-050] Implement source-backed provider legs, stable cross-source matching, mutually exclusive payout representation and unsupported FX review in `packages/reality-core/src/reality/services/finance/money.py`; no pending-as-cash or inferred fee/dispute loss.
- [ ] T097 [US10] [FR-051, FR-052] Implement advance assign/release/apply, whole-item holds and separately evidenced during-hold reconciliation in `packages/reality-core/src/reality/services/finance/controls.py`; enforce in all allocation/individual/payment-run paths in `packages/reality-core/src/reality/services/core.py`.
- [ ] T098 [US10] [FR-053] Implement atomic same-role cross-account transfer and paired allocations in `packages/reality-core/src/reality/services/finance/settlement.py`; preserve same-concrete-account primitive, blocked-account and independent inverse rules.
- [ ] T099 [US10] [FR-054, FR-055] Replace duplicate-line billing rejection with explicitly attributed partial/consolidated evidence in `packages/reality-core/src/reality/services/core.py`; implement scoped coverage and goods/order/credit/settlement control in `packages/reality-core/src/reality/services/finance/controls.py` without inventing source totals.
- [ ] T100 [US10] [FR-056, FR-057] Implement full-scope read-only structured finance explanation and revision-bound continuation in `packages/reality-core/src/reality/services/finance/reads.py`; expose eligible capabilities and authoritative post-action verification through `packages/reality-core/src/reality/tools/finance.py` and `packages/reality-core/src/reality/tools/application.py`.
- [ ] T101 [US10] [FR-049, FR-050, FR-051, FR-052, FR-053, FR-054, FR-055, FR-056, FR-057, FR-058] Implement V11/V12/V13 and existing-view/Inspector integration in `apps/web/src/finance/TradeFinance.tsx`; expose money/advance/hold/transfer/coverage commands through `packages/reality-core/src/reality/tools/finance.py` and extend shared catalogs for every action.
- [ ] T102 [US10] [FR-049, FR-050, FR-051, FR-052, FR-053, FR-054, FR-055, FR-056, FR-057, FR-058] Run the story-specific tests from `specs/148-accounting-journal-cost-centers/test-plan.md`, its shared tool/adapter contract checks and applicable browser states; record actual results and any deferred integration cases in `specs/148-accounting-journal-cost-centers/verification-results.md`. Complete this story only after its dependent checks pass.

## Phase 11: User Story 1 — Record translated financial events once (P1)

**Dependencies**: US10 and all supported evidence kinds; enables automation only after the corresponding service contracts pass. Existing manual ERP posting remains usable earlier.
**Independent acceptance**: Source evidence survives a posting failure; authorized retry records once after a crash/lost response; revoked authority cannot execute; 119 less 50 is 69 and reversal restores 119.

- [ ] T103 [US1] [FR-001] Add failing `test_fr_001_acceptance` in `packages/reality-core/tests/finance/test_recording.py` covering: Existing balanced-role services, no full external chart prerequisite, gross labels. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T104 [US1] [FR-002] Add failing `test_fr_002_acceptance` in `packages/reality-core/tests/finance/test_recording.py` covering: Owner activation, source/type/revision scope, pause/revoke and no intake authority inheritance. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T105 [US1] [FR-003] Add failing `test_fr_003_acceptance` in `packages/reality-core/tests/finance/test_recording.py` covering: Evidence survives posting error; durable handoff crash/retry proof. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T106 [US1] [FR-004] Add failing `test_fr_004_acceptance` in `packages/reality-core/tests/finance/test_recording.py` covering: PostgreSQL replay/concurrency, lost response, changed version and cross-source ambiguity. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T107 [US1] [FR-005] Add failing `test_fr_005_acceptance` in `packages/reality-core/tests/finance/test_recording.py` covering: Existing settlement/reversal regression plus remote outcome independence. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T108 [US1] [FR-001, FR-002, FR-003, FR-004] Add narrowly scoped authority/outbox schema with next-head migration in `packages/reality-core/src/reality/db/finance.py`; inventory supported financial interpretation contracts and versioned activation in `packages/reality-core/src/reality/services/finance/recording.py`.
- [ ] T109 [US1] [FR-001, FR-003, FR-004, FR-005] Implement transaction-bound financial interpretation plus evidence/outbox commit in `packages/reality-core/src/reality/services/finance/recording.py` and current import owner `packages/reality-core/src/reality/services/core.py`; reuse posting/effect identity and preserve zero-effect/changed-source review.
- [ ] T110 [US1] [FR-002, FR-003, FR-004] Implement owner authority configuration and registered bounded recurring drain in `packages/reality-core/src/reality/jobs/handlers/finance.py` and `packages/reality-core/src/reality/jobs/registry.py`; update `docs/features/scheduled-jobs.md`; recheck revoke/pause under lock and honor worker no-root-commit rules.
- [ ] T111 [US1] [FR-001, FR-002, FR-003, FR-004, FR-005] Expose authority/retry tools in `packages/reality-core/src/reality/tools/finance.py`; implement recording review/settings in `apps/web/src/finance/RecordingReview.tsx`, showing unchanged source and recoverable issues separately from remote outcomes.
- [ ] T112 [US1] [FR-001, FR-002, FR-003, FR-004, FR-005] Run the story-specific tests from `specs/148-accounting-journal-cost-centers/test-plan.md`, its shared tool/adapter contract checks and applicable browser states; record actual results and any deferred integration cases in `specs/148-accounting-journal-cost-centers/verification-results.md`. Complete this story only after its dependent checks pass.

## Phase 12: User Story 4 — Control and explain all subledgers (P2)

**Dependencies**: All P1 stories; P2 integrated read/UI completion.
**Independent acceptance**: Full totals span pages/currencies without mixing bases; source/local/remote dates remain distinct; all thirteen views trace to source and work in the required state/locale/viewport matrix.

- [ ] T113 [US4] [FR-017] Add failing `test_fr_017_acceptance` in `packages/reality-core/tests/finance/test_reads.py` covering: Filter-before-total/pagination, operational role balance, currencies and exact provenance. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T114 [US4] [FR-018] Add failing `test_fr_018_acceptance` in `packages/reality-core/tests/finance/test_reads.py` covering: Assigned/unassigned/missing basis, no recognized expense or profit labels. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T115 [US4] [FR-019] Add failing `test_fr_019_acceptance` in `packages/reality-core/tests/finance/test_reads.py` covering: Local/prepared/remote facts independent; compare only like-for-like evidence. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T116 [US4] [FR-020] Add failing `test_fr_020_acceptance` in `packages/reality-core/tests/finance/test_web_contract.py` covering: V01–V13 route/state/keyboard/localization/visual matrix. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T117 [US4] [FR-023] Add failing `test_fr_023_acceptance` in `packages/reality-core/tests/finance/test_initialization_reads.py` covering: Source/local/remote date distinction, timezone boundaries and tied pagination. Use independent expectations from `specs/148-accounting-journal-cost-centers/verification.md`; run and record the failing case before the implementation it proves.
- [ ] T118 [US4] [FR-017, FR-018, FR-019, FR-023] Complete all shared finance list/explain projections in `packages/reality-core/src/reality/services/finance/reads.py` with read-only REPEATABLE READ, stable tied-date pagination, scope/revision invalidation and no refresh writes; preserve distinct amount/date authority.
- [ ] T119 [US4] [FR-017, FR-018, FR-019, FR-020, FR-023] Expose every read in `packages/reality-core/src/reality/tools/finance.py` and existing capability/projection/Inspector catalogs via `packages/reality-core/src/reality/catalogs.py`; wire integrated review/journal/cost/handoff filters in `apps/web/src/finance/FinanceViews.tsx` and `apps/web/src/App.tsx`.
- [ ] T120 [US4] [FR-020] Implement shared read/action states, keyboard semantics and all en/de/nl/es labels in existing locale resources located during T002; maintain `apps/web/src/finance/FinanceViews.tsx` and `apps/web/scripts/finance-contract.test.mjs`; validate 390/1024 Safari/1440, light/dark for V01–V13.
- [ ] T121 [US4] [FR-017, FR-018, FR-019, FR-020, FR-023] Run the story-specific tests from `specs/148-accounting-journal-cost-centers/test-plan.md`, its shared tool/adapter contract checks and applicable browser states; record actual results and any deferred integration cases in `specs/148-accounting-journal-cost-centers/verification-results.md`. Complete this story only after its dependent checks pass.

## Final Phase: Cross-cutting verification and review

- [ ] T122 [FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-028, FR-029, FR-030, FR-031, FR-032, FR-033, FR-034, FR-035, FR-036, FR-037, FR-038, FR-039, FR-040, FR-041, FR-042, FR-043, FR-044, FR-045, FR-046, FR-047, FR-048, FR-049, FR-050, FR-051, FR-052, FR-053, FR-054, FR-055, FR-056, FR-057, FR-058, DR-001, DR-002, DR-003, DR-004, DR-005, DR-006, DR-007] Add and run the integrated customer/supplier story in `packages/reality-core/tests/scenarios/test_operational_finance_trade.py`, including 119/50/reversal, 600/400, source/remote independence, PSP/advance/hold/transfer and partial-billing coverage; record SC-001 through SC-006 in `specs/148-accounting-journal-cost-centers/verification-results.md`.
- [ ] T123 [DR-003, DR-007] Run PostgreSQL race tests and empty-database migration/minimal-account initialization in `packages/reality-core/tests/finance/test_migration_catalogs.py`; verify explicitly targeted disposable reseed, new-model history and tenant isolation; benchmark serialization/drain duration and record results in `specs/148-accounting-journal-cost-centers/verification-results.md`.
- [ ] T124 Run `make spec-check`, `make lint`, `make test`, `make web-build` and applicable web contract/browser checks defined in `docs/TEST_STRATEGY.md`; record failures honestly in `specs/148-accounting-journal-cost-centers/verification-results.md`. No deployment or active database migration is authorized by this checklist.
- [ ] T125 [FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-028, FR-029, FR-030, FR-031, FR-032, FR-033, FR-034, FR-035, FR-036, FR-037, FR-038, FR-039, FR-040, FR-041, FR-042, FR-043, FR-044, FR-045, FR-046, FR-047, FR-048, FR-049, FR-050, FR-051, FR-052, FR-053, FR-054, FR-055, FR-056, FR-057, FR-058, DR-001, DR-002, DR-003, DR-004, DR-005, DR-006, DR-007] Review every new model/catalog/shortest link and completed task against `specs/148-accounting-journal-cost-centers/spec.md`; update `docs/DATA_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/WEB_SPEC.md` and `docs/features/scheduled-jobs.md`; update `docs/V0_CHECKLIST.md` and `specs/148-accounting-journal-cost-centers/checklists/requirements.md` only with green evidence.

## Dependencies and parallel opportunities

```text
Design gates → shared transaction/identity foundation → US5 accounts
US5 → US7 customer → US8 supplier/credits → US9 opening
US5 → US2 components → US6 mappings
US9 + US6 → US3 handoff → US10 trade controls → US1 automatic recording
All P1 stories → US4 integrated reads/UI → full verification and review
```

Dependency arrows refer to the completed prerequisite service/schema increment, not deferred cross-story acceptance. Deferred checks run in US3 and remain pending until then; they do not create a circular implementation prerequisite.

Within every story: failing tests → domain/schema → services → tools → adapters/views → independent verification. US1 is P1 but scheduled late because safely enabling automation depends on the posting contracts it can execute. Manual eight-direction finance is usable after US5; automation is not silently active in that first increment.

Parallel examples are optional opportunities after prerequisite tests/interfaces are stable, not instructions to spawn agents. No task is marked [P] because the current implementation touches shared finance models/tool registries and requires sequential integration.

| Story | Safe independent work after service contracts stabilize |
|---|---|
| US5 | Browser acceptance fixture preparation for its views can proceed alongside review of the story’s PostgreSQL fixtures; integrate shared source files sequentially. |
| US7 | Browser acceptance fixture preparation for its views can proceed alongside review of the story’s PostgreSQL fixtures; integrate shared source files sequentially. |
| US8 | Browser acceptance fixture preparation for its views can proceed alongside review of the story’s PostgreSQL fixtures; integrate shared source files sequentially. |
| US9 | Browser acceptance fixture preparation for its views can proceed alongside review of the story’s PostgreSQL fixtures; integrate shared source files sequentially. |
| US2 | Browser acceptance fixture preparation for its views can proceed alongside review of the story’s PostgreSQL fixtures; integrate shared source files sequentially. |
| US6 | Browser acceptance fixture preparation for its views can proceed alongside review of the story’s PostgreSQL fixtures; integrate shared source files sequentially. |
| US3 | Browser acceptance fixture preparation for its views can proceed alongside review of the story’s PostgreSQL fixtures; integrate shared source files sequentially. |
| US10 | Browser acceptance fixture preparation for its views can proceed alongside review of the story’s PostgreSQL fixtures; integrate shared source files sequentially. |
| US1 | Browser acceptance fixture preparation for its views can proceed alongside review of the story’s PostgreSQL fixtures; integrate shared source files sequentially. |
| US4 | Browser acceptance fixture preparation for its views can proceed alongside review of the story’s PostgreSQL fixtures; integrate shared source files sequentially. |

## Implementation strategy

First usable increment: foundations plus US5 with existing manual ERP posting, managed accounts and preserved history. Add customer/supplier settlement and opening positions next. Received components/mappings form a second branch of work; handoff joins both. Trade controls and narrow automated recording follow proven financial services. This sequence is deliberately dependency-led within P1, with the P2 whole-product read/UI acceptance last.

Story phases include their own screens; the final UI phase is not permission to defer basic usability. Deferred cross-story package assertions remain visibly pending until US3. Schema/technical approval and the analysis gate must be satisfied before running implementation tasks.

## Requirement coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001 | T103, T122 | T108, T109, T111, T125 | Pending |
| FR-002 | T104, T122 | T108, T110, T111, T125 | Pending |
| FR-003 | T105, T122 | T108, T109, T110, T111, T125 | Pending |
| FR-004 | T106, T122 | T108, T109, T110, T111, T125 | Pending |
| FR-005 | T107, T122 | T109, T111, T125 | Pending |
| FR-006 | T053, T122 | T059, T061, T062, T125 | Pending |
| FR-007 | T054, T122 | T059, T061, T062, T125 | Pending |
| FR-008 | T055, T122 | T059, T061, T062, T125 | Pending |
| FR-009 | T056, T122 | T059, T061, T062, T125 | Pending |
| FR-010 | T057, T122 | T059, T061, T062, T125 | Pending |
| FR-011 | T074, T122 | T081, T083, T125 | Pending |
| FR-012 | T075, T122 | T080, T081, T083, T125 | Pending |
| FR-013 | T076, T122 | T081, T083, T125 | Pending |
| FR-014 | T077, T122 | T080, T082, T083, T125 | Pending |
| FR-015 | T078, T122 | T080, T082, T083, T125 | Pending |
| FR-016 | T079, T122 | T080, T081, T082, T083, T125 | Pending |
| FR-017 | T113, T122 | T118, T119, T125 | Pending |
| FR-018 | T114, T122 | T118, T119, T125 | Pending |
| FR-019 | T115, T122 | T118, T119, T125 | Pending |
| FR-020 | T116, T122 | T119, T120, T125 | Pending |
| FR-021 | T011, T122 | T015, T016, T125 | Pending |
| FR-022 | T012, T122 | T015, T125 | Pending |
| FR-023 | T117, T122 | T118, T119, T125 | Pending |
| FR-024 | T018, T122 | T022, T023, T024, T125 | Pending |
| FR-025 | T019, T122 | T023, T024, T125 | Pending |
| FR-026 | T020, T122 | T022, T023, T024, T125 | Pending |
| FR-027 | T058, T122 | T060, T062, T125 | Pending |
| FR-028 | T021, T122 | T022, T023, T024, T125 | Pending |
| FR-029 | T064, T122 | T070, T072, T125 | Pending |
| FR-030 | T065, T122 | T070, T071, T072, T125 | Pending |
| FR-031 | T066, T122 | T070, T071, T072, T125 | Pending |
| FR-032 | T067, T122 | T070, T071, T072, T125 | Pending |
| FR-033 | T068, T122 | T071, T072, T125 | Pending |
| FR-034 | T069, T122 | T072, T125 | Pending |
| FR-035 | T026, T122 | T034, T035, T125 | Pending |
| FR-036 | T027, T122 | T033, T034, T035, T125 | Pending |
| FR-037 | T028, T122 | T033, T034, T035, T125 | Pending |
| FR-038 | T029, T122 | T033, T034, T035, T125 | Pending |
| FR-039 | T030, T122 | T034, T035, T125 | Pending |
| FR-040 | T031, T122 | T034, T035, T125 | Pending |
| FR-041 | T032, T122 | T035, T125 | Pending |
| FR-042 | T037, T122 | T039, T041, T125 | Pending |
| FR-043 | T038, T122 | T040, T041, T125 | Pending |
| FR-044 | T043, T122 | T048, T049, T051, T125 | Pending |
| FR-045 | T044, T122 | T048, T049, T051, T125 | Pending |
| FR-046 | T045, T122 | T048, T049, T051, T125 | Pending |
| FR-047 | T046, T122 | T050, T051, T125 | Pending |
| FR-048 | T047, T122 | T050, T051, T125 | Pending |
| FR-049 | T085, T122 | T095, T096, T101, T125 | Pending |
| FR-050 | T086, T122 | T095, T096, T101, T125 | Pending |
| FR-051 | T087, T122 | T095, T097, T101, T125 | Pending |
| FR-052 | T088, T122 | T095, T097, T101, T125 | Pending |
| FR-053 | T089, T122 | T095, T098, T101, T125 | Pending |
| FR-054 | T090, T122 | T095, T099, T101, T125 | Pending |
| FR-055 | T091, T122 | T095, T099, T101, T125 | Pending |
| FR-056 | T092, T122 | T100, T101, T125 | Pending |
| FR-057 | T093, T122 | T100, T101, T125 | Pending |
| FR-058 | T094, T122 | T101, T125 | Pending |
| DR-001 | T004, T122 | T013, T014, T017, T125 | Pending |
| DR-002 | T005, T122 | T013, T014, T017, T125 | Pending |
| DR-003 | T006, T122 | T014, T015, T016, T017, T125 | Pending |
| DR-004 | T007, T122 | T014, T015, T017, T125 | Pending |
| DR-005 | T008, T122 | T013, T015, T017, T125 | Pending |
| DR-006 | T009, T122 | T015, T016, T017, T125 | Pending |
| DR-007 | T010, T122 | T014, T017, T125 | Pending |

## Success criteria coverage

| Criterion | Proof |
|---|---|
| SC-001 | US1 replay/reversal plus integrated 119/50 business story |
| SC-002 | US2 600/400 assignment plus unchanged gross balance |
| SC-003 | US3 immutable handoff and exact receipt assertions |
| SC-004 | Foundation/US5 clean initialization plus US4 distinct currency/basis reads |
| SC-005 | Individual test/implementation map, US4 full UI matrix and final required suite |
| SC-006 | US5 all-path account eligibility/block/reversal/default change |

## Generation validation

125 unchecked tasks; 65 FR/DR requirements with test and implementation/documentation coverage. Story counts: US5: 8, US7: 11, US8: 6, US9: 10, US2: 11, US6: 10, US3: 11, US10: 18, US1: 10, US4: 9. All gates and runtime tasks remain unchecked. No implementation completion is implied.

## Active-stack integration tasks

- [x] I001 Transfer the verified account slice and regression tests into the active checkout while preserving newer operational reads.
- [x] I002 Adapt account settings and journal presentation to the unified shell; verify browser confirmation and responsive themes.
- [x] I003 Verify the combined migration chain and full required backend/frontend gates.
- [x] I004 Back up, rehearse and rebuild explicitly selected local test data; deploy matching local images.
- [x] I005 Verify running account setup and sales/purchase settlement stories; record rollout and recovery evidence.

## Available-credit register slice

- [x] C001 Add symmetric availability, allocation/refund/reversal and tenant-isolation service tests (FR-039/FR-040/FR-042).
- [x] C002 Implement shared read-time credit register with origin, account and allocation references; no new schema.
- [x] C003 Expose customer/supplier balance filters through the existing API and unified Finance register, with localized amount labels.
- [x] C004 Verify backend/frontend gates and document exact delivered scope; adjustment and guided refund actions remain pending.

## Separate accepted-adjustment slice

- [x] A001 Add failing symmetric service/proposal tests for stated reductions, authority, source identity, reversal, atomicity and stale/replayed confirmations.
- [x] A002 Add two account roles and additive migration; implement shared adjustment preview/acceptance with existing evidence and settlement records.
- [x] A003 Register confirmed tool and API context/proposal adapters; add invoice action and localized review/confirmation UI.
- [x] A004 Verify all required gates, real browser proof and local rollout; document remaining combined-payment and excess-refund scope.

A001–A004 complete the separately accepted invoice-reduction slice. The dedicated
adjustment-detail table suggestion in T033 is superseded by the implemented
SourceRecord/Document refinement in data-model.md. Broader US7 tasks remain open
for combined payment editing, cross-source reconciliation and excess-refund flows.

## Guided payment and credit lifecycle slice

- [x] P001 Add failing symmetric service/tool tests for combined payments, explicit differences, existing credit reuse/refund and independent reversal (FR-035–FR-043).
- [x] P002 Implement shared contexts, previews and atomic composition; preserve stable evidence identity, tenant/account boundaries and stale/replay safety.
- [x] P003 Expose typed API/CLI/MCP proposals and unified invoice/credit dialogs with localized review, recovery and evidence links.
- [x] P004 Verify complete required gates, isolated browser journeys and local rollout; record precise scope and remaining broader work.


P001–P004 complete the guided actual-payment and existing-credit lifecycle slice.
Opening balances, automated source interpretation, cost centers, posting-case mapping
and accounting handoff remain separate unfinished work. No broad reviewer checklist
markers were changed. See verification-results.md for full-suite and live proof.

## Opening-position delivery slice

- [x] O001 Add failing four-direction, coverage, dates, atomicity, tenant/owner and settlement lifecycle tests (FR-044–FR-048).
- [x] O002 Add the two justified opening evidence tables and neutral role; implement shared import/coverage, consistent finance locking and existing settlement/read integration.
- [x] O003 Expose typed shared API/CLI/MCP proposals and localized unified batch editor/review, origin/date detail and result links.
- [x] O004 Verify complete backend/frontend/migration/browser gates, preserve live data during local rollout and record evidence.

O001–O004 complete the bounded manual opening-position slice. File upload, guided
coverage reconciliation, automatic historical source matching, cost centers, posting
case mapping and external accounting handoff remain separate unfinished roadmap work.
No broad task/checklist completion is implied. See verification-results.md for exact
backend, browser, migration and live preservation evidence.

## Managed-reference catalog slice

- [x] R001 Plan and add regression tests for three reference kinds, immutable identity/history, eligibility, stale/replay/atomicity and tenant/owner boundaries.
- [x] R002 Add the justified reference table/migration, shared services and confirmed tools, catalog registration and API/CLI/MCP adapters.
- [x] R003 Add localized Company settings list/search/history and owner review/confirmation using the current application style.
- [x] R004 Run required backend/frontend/migration/browser gates, preserve live ledger data during local rollout and record exact evidence.

Actual component assignments, cost-center amount allocation and posting-case mapping
remain unfinished roadmap work; these tasks do not complete the broad US2/US6 phases.

## Received-component attribution slice

- [x] D001 Add failing source/summary/line, exact split/partial/zero/missing, tenant/kind/owner, stale/replay/rollback/concurrency and migration regressions.
- [x] D002 Add three justified tables and shared received-detail, immutable assignment and history services with confirmed tools and API/CLI/MCP contracts.
- [x] D003 Add localized Financial detail dialog with source/internal separation, reference search, explicit shares, review/recovery and history.
- [x] D004 Run all required gates and real-browser proof, preserve live data during additive rollout, and record exact delivery evidence.

D001–D004 do not complete source mapping, external handoff, or global cost reporting.

D001–D004 are verified and deployed locally. See verification-results.md for the
complete backend/browser gates, visual fixes, additive migration and live preservation.
Broad US2/US6 and reviewer-owned checklist markers remain unchanged.

## Operational transaction matrix slice

- [x] M001 [FR-025, FR-029, FR-034] Add failing matrix-to-real-posting, missing/blocked/default-change, tenant, no-write and API/CLI/MCP regressions; restore canonical customer-credit attribution.
- [x] M002 [FR-025, FR-029, FR-034] Implement immutable domain descriptions and shared matrix read, register adapters/catalogs without schema or alternative posting logic.
- [x] M003 [FR-025, FR-029, FR-034] Add localized account-settings matrix, configuration link and refresh after changes; verify real browser behavior.
- [x] M004 [FR-025, FR-029, FR-034] Run required full gates, preserve local records and current UI during rollout, and record reviewed evidence.

M001–M004 are verified and running locally. Broad US2/US6 and reviewer-owned checklist markers remain open; source/case/target-account mapping and external handoff are subsequent work.


## Source classification mapping slice

- [x] S001 [FR-030, FR-033, FR-034] Add and observe failing source-scope, lifecycle, provenance, tenant/owner, stale/replay/concurrency and no-write regressions.
- [x] S002 [FR-030, FR-033, FR-034] Implement additive revision schema and shared source mapping list/history/preview/confirmed replacement and component resolution.
- [x] S003 [FR-030, FR-033, FR-034] Register shared tools/API/CLI/MCP/catalogs and localized settings plus component resolution view with recovery/history.
- [x] S004 [FR-030, FR-033, FR-034] Complete full gates, real browser proof, reviewed additive local rollout and preservation evidence.

## Finance workspace settings placement

- [x] U001 [FR-034] Specify and review placement; add failing route/introduction/action-destination regressions before moving UI.
- [x] U002 [FR-034] Compose existing editors in tenant-keyed Finance Settings; keep operational reads/actions out and remove duplicate Company editors.
- [x] U003 [FR-034] Retarget shared management links; verify routing, permissions, reload and the existing real finance journey on desktop/mobile.
- [x] U004 [FR-034] Run proportional backend/catalog and complete frontend gates, rebuild local affected services, and document verified preservation.

S001–S004 and U001–U004 are verified and deployed locally. External target-account
routing, accounting handoff, cost-center source-code translation and broad US2/US6
completion remain separate roadmap work. Reviewer-owned checklist markers are unchanged.

- [x] N001 [FR-034] Specify/review area navigation and add route regression before implementation.
- [x] N002 [FR-034] Implement menu/mobile select, embedded editors, separated reference kinds and shared action destination.
- [x] N003 [FR-034] Verify frontend, catalog and real finance journey; deploy matching local images and record preservation.

- [x] B001 [FR-034] Specify/review compact actions and add browser dimension/footer/menu checks.
- [x] B002 [FR-034] Implement scoped button sizing, footers, account action popover and default badge.
- [x] B003 [FR-034] Verify frontend, responsive and real financial journeys, deploy web and record results.

## External target mapping slice — product and Finance-specific schema approved

- [x] TM001 [FR-009, FR-021, FR-027, FR-032, FR-034] Record human technical approval of the concrete three-table design in `target-mappings.md`; recheck the active checkout/head and complete pre-implementation consistency review. Preserve reviewer-owned checklist markers.
- [x] TM002 [FR-009, FR-021, FR-027, FR-030, FR-031, FR-032, FR-033] Add and observe failing cases in `packages/reality-core/tests/finance/test_target_mappings.py` for the eleven proof groups in `target-mappings.md`, including PostgreSQL constraints/concurrency and no financial write effects.
- [x] TM003 [FR-009, FR-027, FR-032, FR-033] Implement `domain/target_mappings.py`, `db/target_mappings.py`, metadata registration and the next-head additive migration; implement shared lifecycle, matching and consistent preview in `services/finance/target_mappings.py`.
- [x] TM004 [FR-021, FR-033, FR-034] Register typed finance commands/reads, audit and tenant-isolation catalogs and API/CLI/MCP adapters through the existing application tools; verify owner/stale/replay parity.
- [x] TM005 [FR-034] Implement `apps/web/src/finance/TargetMappings.tsx` and `TargetMappingPreview.tsx`; integrate FinanceSettings/FinancialComponents with target-scoped recovery, searchable catalogs, precise review reasons, compact controls and all four locales.
- [x] TM006 [FR-009, FR-021, FR-027, FR-030, FR-031, FR-032, FR-033, FR-034] Verify real customer/supplier evidence preview, browser permission/recovery/responsive states, migration/downgrade, full required backend/frontend gates and final Constitution review; record exact results.
- [x] TM007 [FR-034] After green verification, rehearse and roll out the affected local services with a recoverable backup and preservation checks; update runtime notes and delivered status without claiming export or remote posting.

## Finance settings dialog usability

- [x] UX001 [FR-059] Specify/review all settings editors against existing app patterns; add failing browser checks for absence of permanent forms and explicit create/edit dialogs.
- [x] UX002 [FR-059] Implement shared dialog interaction, contextual titles/help, separate histories, recovery and owner-only maintenance across all Finance settings; maintain all four locales.
- [x] UX003 [FR-059] Verify real confirmed configuration flows, cancellation/focus/error/member/recovery behavior, mobile and dark layouts, frontend gates and spec policy; update local web runtime and verification notes.

## Operational account setup clarity

- [x] AC001 [FR-060] Add browser regression for named account usage dialog, no matrix accordion, and role-scoped default selection; update approved spec/plan.
- [x] AC002 [FR-060] Implement page toolbar/help, readable usage dialog and existing-command default picker; localize all labels.
- [x] AC003 [FR-060] Verify browser default flow, existing financial journey and frontend gates; update local web runtime and evidence.

## External accounting list entry

- [x] EA001 [FR-061] Specify/review and add browser regression for target-list entry and no permanent picker.
- [x] EA002 [FR-061] Implement target navigation, contextual empty states and localized help with existing dialogs.
- [x] EA003 [FR-061] Verify browser/real journey/frontend gates and local web rollout.

## Consistent Finance settings layout

- [x] FL001 [FR-062] Specify/review and add cross-area toolbar geometry regressions.
- [x] FL002 [FR-062] Share toolbar layout and unify card/help/filter/empty/pagination presentation.
- [x] FL003 [FR-062] Verify frontend, browser, real journey and local rollout.

## Empty catalog distinction

- [x] FE001 [FR-063] Specify/review and add empty/filter-reset regression.
- [x] FE002 [FR-063] Implement shared empty state, reset and catalog-presence handling.
- [x] FE003 [FR-063] Verify browser, finance journey, frontend gates and local rollout.

## Finance-only PR preparation

- [x] PR001 Isolate Finance changes from parallel recorder/graph work and integrate current main without regressing page actions or inline previews.
- [x] PR002 Correct duplicate UI requirement identifiers, run full backend/frontend and browser verification, review scope and prepare the Finance-only PR.
- [x] PR003 Publish the Finance-only branch and PR after explicit destination approval required by automatic approval review.
