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

