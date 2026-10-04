# Tasks: Reviewed Shopify orders, changes and refunds

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
- [ ] T002 Establish isolated PostgreSQL fixtures and the DR-001/DR-002/DR-003 negative matrix in `packages/reality-core/tests/test_shopify_intake_admission.py`: lossless values, causal links, derived-state and tenant refusal.

## Phase 2: US1 — Review a newly received shop order

**Independent acceptance**: Execute US1 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T003 [US1] Add and observe failing proofs for FR-001, FR-002, FR-003, FR-004 in `packages/reality-core/tests/test_shopify_intake_admission.py`: `test_first_order_waits_for_decision`, `test_review_preserves_received_values`, `test_unknown_and_unstated_lines_are_visible`, `test_approved_order_is_atomic_and_replay_safe`.
- [ ] T004 [US1] Extract pure first-order planning from the legacy interpreter in `packages/reality-core/src/reality/services/shopify_intake.py`; deliver FR-001, FR-002, FR-003, FR-004 without weakening their refusal checks.
- [ ] T005 [US1] Apply approved first-order plans through canonical transaction-bound evidence/commitment services and route the helper to preparation in `packages/reality-core/src/reality/services/core.py`; deliver FR-001, FR-002, FR-003, FR-004 without weakening their refusal checks.

## Phase 3: US2 — Review an upstream change

**Independent acceptance**: Execute US2 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T006 [US2] Add and observe failing proofs for FR-005, FR-006, FR-007, FR-008 in `packages/reality-core/tests/test_shopify_intake_admission.py`: `test_reductions_are_proposed_not_applied`, `test_older_version_cannot_replace_newer`, `test_unsupported_edits_still_refuse`, `test_changed_order_uses_canonical_services`.
- [ ] T007 [US2] Separate classified change plans from application while preserving guard codes in `packages/reality-core/src/reality/services/shop_order_changes.py`; deliver FR-005, FR-006, FR-007, FR-008 without weakening their refusal checks.
- [ ] T008 [US2] Integrate later versions with shared admission and retained job coverage in `packages/reality-core/src/reality/services/shopify_intake.py`; deliver FR-005, FR-006, FR-007, FR-008 without weakening their refusal checks.

## Phase 4: US3 — Review refunds and return announcements

**Independent acceptance**: Execute US3 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T009 [US3] Add and observe failing proofs for FR-009, FR-010 in `packages/reality-core/tests/test_shopify_intake_admission.py`: `test_refund_interpretation_waits_for_decision`, `test_refund_is_not_payment_authority`.
- [ ] T010 [US3] Split refund evidence/effect planning and no-commit apply; integrate child source handling in `packages/reality-core/src/reality/services/shop_refunds.py`; deliver FR-009, FR-010 without weakening their refusal checks.
- [ ] T011 [US3] Expose pending source/proposal results honestly in synchronous helpers and import coverage in `packages/reality-core/src/reality/services/core.py`; deliver FR-009, FR-010 without weakening their refusal checks.

## Final phase: Integration and verification

- [ ] T012 Add concurrent approval, crash-before/after-commit, cross-tenant and scope-reuse integration proof for DR-001–DR-003/SC-001 in `packages/reality-core/tests/test_shopify_intake_admission.py` and execute the story tests against real PostgreSQL.
- [ ] T013 Update exact source/decision explanation and applicable contracts in `docs/features/shopify_ingestion.md` plus the other paths listed in plan.md; include DR-001–DR-003 and register new test families in `docs/SPEC_COVERAGE_MATRIX.md`.
- [ ] T014 Run required gates from `quickstart.md`, review the actual diff and migration/rollback evidence, and record measured results in this feature's `verification.md` before marking any story complete (SC-002).

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

## Implementation refinement: absent source amounts

- [ ] T015 Add failure-first proofs for DR-001/FR-002/FR-003 when source line totals are absent, zero or inconsistent; retain manual entry refusal.
- [ ] T016 Make existing evidence/promise amount columns nullable, add the additive migration and safe rollback test, and preserve source-only absence through canonical no-commit services.
- [ ] T017 Update credit/billing/inspection consumers so unknown received amounts remain unknown and cannot pass a monetary safety check as zero.
