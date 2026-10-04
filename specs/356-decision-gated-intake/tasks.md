# Tasks: Decision-gated interpretation and admission

## Approved scope clarification (2026-10-04)

This rollout governs external sources, imports and agent-proposed business effects.
They require an exact retained proposal and an authorized confirmation before acceptance.
A direct action by an authenticated human is itself the decision and uses the existing
application authorization and audit trail; it does not require a second proposal or
confirmation cycle. Derived effects of one operation share its transaction and receipt.

The owner retained PRs #333–#346 and withdrew the later universal canonical-writer
rollout. Internal service calls and every manual UI/CLI operation are not additional
admission projects. Existing tenant, domain, Finance and Chat confirmation rules remain.
A static writer inventory is discovery material, not a mandate to guard every writer.
References below to governed writes mean external intake only; broader earlier planning
and universal-writer tasks are superseded by this clarification.

**Input**: spec.md, plan.md, research.md, data-model.md and contracts/intake.md.
**Status**: Implementation tasks are intentionally unchecked; design verification
does not prove runtime behavior. Domain → services → tools → adapters.

## Phase 1: Setup and existing contract inventory

- [ ] T001 Re-read dependencies and resolve exact existing regression files in `packages/reality-core/tests/`; confirm planned writer/caller coverage against `specs/356-decision-gated-intake/writer-coverage.md`.
- [ ] T002 Establish isolated PostgreSQL fixtures and the DR-001/DR-002/DR-003 negative matrix in `packages/reality-core/tests/test_intake_admission.py`: lossless values, causal links, derived-state and tenant refusal.

## Phase 2: US1 — Prepare meaning without accepting it

**Independent acceptance**: Execute US1 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T003 [US1] Add and observe failing proofs for FR-001, FR-002, FR-003 in `packages/reality-core/tests/test_intake_admission.py`: `test_raw_survives_prepare_failure`, `test_preparation_has_no_business_effects`, `test_mapping_and_source_are_frozen`.
- [ ] T004 [US1] Define immutable typed prepared-intake and effect schemas with canonical decimal/date serialization in `packages/reality-core/src/reality/domain/intake.py`; deliver FR-001, FR-002, FR-003 without weakening their refusal checks.
- [ ] T005 [US1] Implement side-effect-free preparation and retained review using existing source/outcome/proposal records in `packages/reality-core/src/reality/services/intake.py`; deliver FR-001, FR-002, FR-003 without weakening their refusal checks.

## Phase 3: US2 — Accept exactly the reviewed interpretation

**Independent acceptance**: Execute US2 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T006 [US2] Add and observe failing proofs for FR-004, FR-005, FR-006, FR-007 in `packages/reality-core/tests/test_intake_admission.py`: `test_stale_or_forged_approval_refused`, `test_effects_and_receipt_are_atomic`, `test_outcomes_and_replay_are_truthful`, `test_direct_writer_and_scope_reuse_refused`.
- [ ] T007 [US2] Add immutable attempt/replay tests for FR-006 and common lock-order concurrency tests for FR-005/FR-007 in `packages/reality-core/tests/test_intake_admission.py`; implement outcome allocation in `packages/reality-core/src/reality/services/intake.py` and Tenant-first raw/event admission with sorted source advisory keys in `packages/reality-core/src/reality/services/core.py` before activating approved intake.
- [ ] T008 [US2] Enforce transaction-bound approved effects and truthful import outcomes; classify non-business writes in `packages/reality-core/src/reality/services/intake.py`; deliver FR-004, FR-005, FR-006, FR-007 without weakening their refusal checks.
- [ ] T009 [US2] Route legacy import processing to preparation and retained replay for migrated kinds in `packages/reality-core/src/reality/services/core.py`; deliver FR-004, FR-005, FR-006, FR-007 without weakening their refusal checks.
- [ ] T010 [US2] Add atomic intake approval and no-commit application without the generic executor's separate durable executing claim in `packages/reality-core/src/reality/tools/application.py`; deliver FR-004, FR-005, FR-006, FR-007 without weakening their refusal checks.

## Phase 4: US3 — Review many fixed units

**Independent acceptance**: Execute US3 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T011 [US3] Add and observe failing proofs for FR-008, FR-009, FR-010 in `packages/reality-core/tests/test_intake_admission.py`: `test_package_and_batch_modes_are_distinct`, `test_mixed_batch_has_exact_results`, `test_batch_resume_does_not_duplicate`.
- [ ] T012 [US3] Define manifest, limits and result contracts for consumers without implementing a second execution engine in `packages/reality-core/src/reality/domain/intake.py`; deliver FR-008, FR-009, FR-010 without weakening their refusal checks.
- [ ] T013 [US3] Add shared tenant-scoped prepare/review/result operations and tool bindings in `packages/reality-core/src/reality/tools/application.py`; deliver FR-008, FR-009, FR-010 without weakening their refusal checks.

## Final phase: Integration and verification

- [ ] T014 Add concurrent approval, crash-before/after-commit, cross-tenant and scope-reuse integration proof for DR-001–DR-003/SC-001 in `packages/reality-core/tests/test_intake_admission.py` and execute the story tests against real PostgreSQL.
- [ ] T015 Update exact source/decision explanation and applicable contracts in `docs/DATA_MODEL.md` plus the other paths listed in plan.md; include DR-001–DR-003 and register new test families in `docs/SPEC_COVERAGE_MATRIX.md`.
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
