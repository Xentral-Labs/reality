# Tasks: Reviewed invoice, payment and allocation intake

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
- [ ] T002 Establish isolated PostgreSQL fixtures and the DR-001/DR-002/DR-003 negative matrix in `packages/reality-core/tests/test_financial_intake_admission.py`: lossless values, causal links, derived-state and tenant refusal.

## Phase 2: US1 — Review financial meaning before posting

**Independent acceptance**: Execute US1 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T003 [US1] Add and observe failing proofs for FR-001, FR-002, FR-003, FR-004 in `packages/reality-core/tests/test_financial_intake_admission.py`: `test_financial_prepare_is_non_posting`, `test_financial_review_exposes_exact_meaning`, `test_finance_authority_and_values_are_preserved`, `test_financial_effect_and_receipt_are_atomic`.
- [ ] T004 [US1] Split invoice/payment normalised models into prepared meaning and transaction-bound apply in `packages/reality-core/src/reality/services/payment_intake.py`; deliver FR-001, FR-002, FR-003, FR-004 without weakening their refusal checks.
- [ ] T005 [US1] Route bank-file financial targets through the shared financial plan and atomic executor in `packages/reality-core/src/reality/services/file_interpreters.py`; deliver FR-001, FR-002, FR-003, FR-004 without weakening their refusal checks.

## Phase 3: US2 — Decide a payment allocation explicitly

**Independent acceptance**: Execute US2 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T006 [US2] Add and observe failing proofs for FR-005, FR-006, FR-007 in `packages/reality-core/tests/test_financial_intake_admission.py`: `test_unambiguous_match_is_still_a_proposal`, `test_changed_allocation_refuses_without_rematch`, `test_unmatched_payment_can_be_accepted_explicitly`.
- [ ] T007 [US2] Freeze reference-resolution and allocation intents with relevant current-state fingerprints in `packages/reality-core/src/reality/services/payment_intake.py`; deliver FR-005, FR-006, FR-007 without weakening their refusal checks.
- [ ] T008 [US2] Use shared finance locks and explicit allocation services in approved apply in `packages/reality-core/src/reality/services/finance/settlement.py`; deliver FR-005, FR-006, FR-007 without weakening their refusal checks.

## Phase 4: US3 — Process independent financial statements safely

**Independent acceptance**: Execute US3 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T009 [US3] Add and observe failing proofs for FR-008, FR-009 in `packages/reality-core/tests/test_financial_intake_admission.py`: `test_financial_batch_preserves_authority_and_units`, `test_intake_is_not_external_payment_execution`.
- [ ] T010 [US3] Register financial intake policy and truthful source/result presentation in `packages/reality-core/src/reality/services/proposal_decisions.py`; deliver FR-008, FR-009 without weakening their refusal checks.
- [ ] T011 [US3] Integrate invoice/payment source adapters without special demo posting authority in `packages/reality-core/src/reality/integrations/demo_data.py`; deliver FR-008, FR-009 without weakening their refusal checks.

## Final phase: Integration and verification

- [ ] T012 Add concurrent approval, crash-before/after-commit, cross-tenant and scope-reuse integration proof for DR-001–DR-003/SC-001 in `packages/reality-core/tests/test_financial_intake_admission.py` and execute the story tests against real PostgreSQL.
- [ ] T013 Update exact source/decision explanation and applicable contracts in `docs/features/company-setup-demo.md` plus the other paths listed in plan.md; include DR-001–DR-003 and register new test families in `docs/SPEC_COVERAGE_MATRIX.md`.
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
