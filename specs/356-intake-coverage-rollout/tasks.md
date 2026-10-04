# Tasks: Intake decision coverage, demo and safe rollout

**Input**: spec.md, plan.md, research.md, data-model.md and contracts/intake.md.
**Status**: Implementation tasks are intentionally unchecked; design verification
does not prove runtime behavior. Domain → services → tools → adapters.

## Phase 1: Setup and existing contract inventory

- [ ] T001 Re-read dependencies and resolve exact existing regression files in `packages/reality-core/tests/`; confirm planned writer/caller coverage against `specs/351-decision-gated-intake/writer-coverage.md`.
- [ ] T002 Establish isolated PostgreSQL fixtures and the DR-001/DR-002/DR-003 negative matrix in `packages/reality-core/tests/test_intake_rollout_coverage.py`: lossless values, causal links, derived-state and tenant refusal.

## Phase 2: US1 — Prove all governed paths cross the boundary

**Independent acceptance**: Execute US1 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T003 [US1] Add and observe failing proofs for FR-001, FR-002, FR-003 in `packages/reality-core/tests/test_intake_rollout_coverage.py`: `test_writer_inventory_has_no_unowned_path`, `test_all_transports_and_direct_calls_are_guarded`, `test_exceptions_cannot_be_reused_for_business_effects`.
- [ ] T004 [US1] Close remaining canonical-writer and adapter bypasses without putting business rules in transports in `packages/reality-core/src/reality/services/tenant_policy.py`; deliver FR-001, FR-002, FR-003 without weakening their refusal checks.
- [ ] T005 [US1] Complete baseline inventory and catalog/service caller coverage with exact test links in `specs/351-decision-gated-intake/writer-coverage.md`; deliver FR-001, FR-002, FR-003 without weakening their refusal checks.

## Phase 3: US2 — Run demo through the same admission

**Independent acceptance**: Execute US2 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T006 [US2] Add and observe failing proofs for FR-004, FR-005, FR-006 in `packages/reality-core/tests/test_intake_rollout_coverage.py`: `test_live_demo_uses_real_decisions`, `test_bootstrap_scope_is_fixed`, `test_demo_controls_and_retry_markers_survive`.
- [ ] T007 [US2] Test new/existing demo missing-reviewer, explicit enrollment, expiry/revocation and saturation behavior for FR-004/FR-006/FR-010 in `packages/reality-core/tests/test_intake_rollout_coverage.py`; implement actionable awaiting-reviewer status in `packages/reality-core/src/reality/services/demo_data.py` and `apps/web/src/components/DemoDataIntegration.tsx` without implicitly creating a mandate.
- [ ] T008 [US2] Route continuous synthetic source production and interpretation through shared preparation/approved apply in `packages/reality-core/src/reality/services/demo_data.py`; deliver FR-004, FR-005, FR-006 without weakening their refusal checks.
- [ ] T009 [US2] Retain scoped setup and source-controls under canonical handlers in `packages/reality-core/src/reality/services/company_setup.py`; deliver FR-004, FR-005, FR-006 without weakening their refusal checks.

## Phase 4: US3 — Introduce the change without inventing history

**Independent acceptance**: Execute US3 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T010 [US3] Add and observe failing proofs for FR-007, FR-008, FR-009, FR-010 in `packages/reality-core/tests/test_intake_rollout_coverage.py`: `test_historical_provenance_is_honest`, `test_pending_job_cutover_is_safe`, `test_rollback_preserves_decision_boundary`, `test_status_and_documentation_are_truthful`.
- [ ] T011 [US3] Implement pending-job compatibility, worker fencing and retained-source recovery in `packages/reality-core/src/reality/services/intake.py`; deliver FR-007, FR-008, FR-009, FR-010 without weakening their refusal checks.
- [ ] T012 [US3] Update source/import and demo status readers and rollout documentation in `packages/reality-core/src/reality/web/api.py`; deliver FR-007, FR-008, FR-009, FR-010 without weakening their refusal checks.
- [ ] T013 [US3] Complete full regression, migration/restart and browser evidence before release in `docs/V0_CHECKLIST.md`; deliver FR-007, FR-008, FR-009, FR-010 without weakening their refusal checks.

## Final phase: Integration and verification

- [ ] T014 Add concurrent approval, crash-before/after-commit, cross-tenant and scope-reuse integration proof for DR-001–DR-003/SC-001 in `packages/reality-core/tests/test_intake_rollout_coverage.py` and execute the story tests against real PostgreSQL.
- [ ] T015 Update exact source/decision explanation and applicable contracts in `docs/features/company-setup-demo.md` plus the other paths listed in plan.md; include DR-001–DR-003 and register new test families in `docs/SPEC_COVERAGE_MATRIX.md`.
- [ ] T016 Run required gates from `quickstart.md`, review the actual diff and migration/rollback evidence, and record measured results in this feature's `verification.md` before marking any story complete (SC-002).

## Dependencies and execution order

T001 → T002 → each story's failing proof → its domain/service implementation →
tool/adapter integration → final integration tests → contract/catalog updates →
required gates. All stories depend on setup; later stories use the shared unit
contract proven by US1. Feature dependencies are listed in spec.md.

## Parallel opportunities

Independent test-fixture and browser-presentation work can be prepared separately
after the interface contract is fixed. Changes to shared executor, core services,
catalogs and generated outputs remain sequential to avoid conflicting assumptions.
No tasks are labelled parallel when they modify the same file.

## Incremental implementation

Deliver one independently tested story at a time. The first foundation/Shopify slice
proves the mechanism, not all-path coverage. Do not deploy a migrated adapter while
old write-capable workers can still bypass its boundary. Completion remains gated
by all required checks and honest unresolved-outcome reporting.


## Canonical master-data boundary qualification (FR-001–FR-003)

- [x] T019 Prove direct create/update refusal with arbitrary action tags in enabled/disabled authentication, then enforce exact canonical Party/Item/Location invocation authority.
- [x] T020 Prove changed callback arguments, repeat invocation and premature root commit leave no partial source/master records; qualify confirmed ordinary company-partner creation and retained replay.
- [x] T021 Route CLI master create/update through retained catalog proposals and explicit confirmation; migrate legitimate test setup to real named Owner decisions and verify transport/lesson parity.
- [x] T022 Complete master-family source, annotation/catalog, full regression and committed-head CI evidence without claiming remaining writer families are covered.

## Canonical finance configuration boundary qualification (FR-001–FR-003)

- [x] T023 Prove valid direct finance/account calls, action tags and unconfirmed dispatch cannot authorize accepted configuration.
- [x] T024 Bind the existing atomic proposed Finance branch to actual confirmation under its existing delivery/finance/proposal locks, without changing claim state or committing an intermediate decision.
- [x] T025 Freeze exact account calls, recheck the current confirming person/token and reject changed/repeated callbacks and premature root commits; preserve fixed default-account bootstrap and historical migration fixtures explicitly.
- [x] T026 Route legitimate account tests/adapters through confirmed existing commands; complete focused/full regression and committed-head CI evidence, with remaining business writer coverage pending.

## Normalized document boundary qualification (FR-001–FR-003)

- [x] T027 Add meaningful direct/tag and absent-confirmation refusal proofs for normalized Document/DocumentLine creation.
- [x] T028 Enforce current finite command/root authority, frozen single-use child calls and atomic receipt/evidence settlement.
- [x] T029 Route the manual-document Web adapter and legitimate fixtures through actual confirmed existing commands; preserve historical evidence without backfilled consent.
- [x] T030 Qualify document/order/invoice/credit scenarios, browser and full committed-head CI; keep header/correction writer closure pending.

## Atomic order boundary qualification (FR-001–FR-003)

- [x] T031 Observe meaningful changed/repeated/early-commit/post-write-failure proofs on valid orders.
- [x] T032 Freeze and consume the actual canonical order invocation and settle source/evidence/promises with its receipt atomically.
- [x] T033 Qualify both directions, current authority, replay, catalog/browser and committed-head CI.

## Atomic invoice boundary qualification (FR-001–FR-003)

- [x] T034 Observe valid changed/repeated/early-commit/post-write failure proofs for sales, supplier and free supplier invoices.
- [x] T035 Freeze canonical parent calls and settle retained source/evidence/postings/offsets with their actual receipt.
- [x] T036 Qualify invoice variants, fixed setup, adapters and complete committed-head CI.
## Current MCP authority qualification (FR-003)

- [x] T037 Prove real interactive grant/credential revocation, expiry and permission changes after dispatch refuse master/Finance effects.
- [x] T038 Bind the actual verified MCP principal to existing scopes and check its current persisted authority before effects.
- [x] T039 Qualify positive real OAuth confirmation, manual/interactive parity, adapters and full committed-head CI.
## Live source control lock-order regression qualification

- [x] T046 Correct the real production/settlement worker and Pause schedule cycle.
- [x] T047 Qualify shared scheduling/demo semantics, PostgreSQL lock order and real company setup browser.
## Atomic customer credit boundary qualification

- [x] T040 Prove changed/repeated parent and ledger/allocation calls, early commit, post-write failure and unrelated effects.
- [x] T041 Freeze both existing credit recorders and their posting/allocation inside actual retained confirmation.
- [x] T042 Qualify modern/legacy source values, replay, adapters and complete committed-head CI.
## Fixed new-company reference exception qualification

- [ ] T043 Prove existing-company, changed identity, repeat, early commit and post-write failure refusal.
- [ ] T044 Bind actual transient-company insertion and fixed references atomically across ordinary/lesson creation.
- [ ] T045 Qualify fixed reference values, creation, historical migration compatibility and committed-head CI.
## Commercial master data qualification

- [ ] T048 Prove direct/unconfirmed/changed/repeated/early-commit/post-write failure and sibling effects for the ten existing commands.
- [ ] T049 Freeze canonical commercial master services, preserve fixed setup and route REST/CLI through real confirmation.
- [ ] T050 Qualify stated values, tenant/current authority, replay, commercial/setup/adapters and full committed-head CI.
- [ ] T051 Prove changed retained commercial reference state requires renewed review, preserving current authority and exact source values.

## Current fixed application authority qualification

- [ ] T052 Prove real current authority changes after fixed-profile dispatch refuse the canonical write, without fabricated grants or decisions.
- [ ] T053 Share actual current decider validation between fixed and ordinary application scopes.
- [ ] T054 Qualify successful fixed-profile source values/receipt replay, setup compatibility and full committed-head CI.
