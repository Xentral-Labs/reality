# Tasks: Bulk intake settlement and delegated agent review

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
- [ ] T002 Establish isolated PostgreSQL fixtures and the DR-001/DR-002/DR-003 negative matrix in `packages/reality-core/tests/test_bulk_intake_review.py`: lossless values, causal links, derived-state and tenant refusal.

## Phase 2: US1 — Review and approve a fixed batch

**Independent acceptance**: Execute US1 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T003 [US1] Add and observe failing proofs for FR-001, FR-002, FR-003, FR-004, FR-005 in `packages/reality-core/tests/test_bulk_intake_review.py`: `test_manifest_is_fixed_and_tenant_scoped`, `test_review_covers_every_member`, `test_bulk_settlement_preserves_child_authority`, `test_bounded_runs_resume_exactly`, `test_stop_and_revocation_affect_remaining_units`.
- [ ] T004 [US1] Test original-reviewer handoff, owner demotion/token revocation, small 500-member queue payloads, middle-child domain refusal, late infrastructure rollback and stop-after-current-chunk for FR-003–FR-005 in `packages/reality-core/tests/test_bulk_intake_review.py`; implement the corresponding continuation contract in `packages/reality-core/src/reality/services/intake_batches.py`.
- [ ] T005 [US1] Implement exact manifest review, durable continuation and per-unit result reconciliation in `packages/reality-core/src/reality/services/intake_batches.py`; deliver FR-001, FR-002, FR-003, FR-004, FR-005 without weakening their refusal checks.
- [ ] T006 [US1] Register transaction-bound bounded continuation handlers and catalog definitions in `packages/reality-core/src/reality/jobs/handlers/intake.py`; deliver FR-001, FR-002, FR-003, FR-004, FR-005 without weakening their refusal checks.
- [ ] T007 [US1] Expose canonical bulk operations in API/MCP/CLI and review/result components in `packages/reality-core/src/reality/web/api.py`; deliver FR-001, FR-002, FR-003, FR-004, FR-005 without weakening their refusal checks.

## Phase 3: US2 — Delegate review with a narrow mandate

**Independent acceptance**: Execute US2 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T008 [US2] Add and observe failing proofs for FR-006, FR-007, FR-008, FR-009, FR-010 in `packages/reality-core/tests/test_bulk_intake_review.py`: `test_mandate_scope_is_enforced`, `test_reviewer_checks_source_not_only_summary`, `test_agent_attribution_and_injection_boundaries`, `test_authority_revocation_and_chat_limits`, `test_scheduled_handler_remains_database_only`.
- [ ] T009 [US2] Define mandate and structured reviewer-result schemas and owner-governed create/revoke policy in `packages/reality-core/src/reality/domain/intake_review.py`; deliver FR-006, FR-007, FR-008, FR-009, FR-010 without weakening their refusal checks.
- [ ] T010 [US2] Add the mandate model in `packages/reality-core/src/reality/db/intake_review.py`, metadata registration in `packages/reality-core/src/reality/db/core.py` and the additive revision in `packages/reality-core/migrations/versions/`; prove tenant FK, upgrade/compatible rollback, strict scope, currency/missing amount and concurrent daily quotas for FR-006–FR-010 in `packages/reality-core/tests/test_bulk_intake_review.py` before enabling delegated review.
- [ ] T011 [US2] Persist minimal tenant-scoped delegation, enforce current grant/token/owner authority and review evidence in `packages/reality-core/src/reality/services/intake_review.py`; deliver FR-006, FR-007, FR-008, FR-009, FR-010 without weakening their refusal checks.
- [ ] T012 [US2] Expose truthful parent/mandate context in `packages/reality-core/src/reality/services/decision_attribution.py` and shared review metadata; prove actual token attribution without personal-issuer invention for FR-008 in `packages/reality-core/tests/test_bulk_intake_review.py`.
- [ ] T013 [US2] Expose scoped review fetch/submit tools to explicitly delegated MCP agents in `packages/reality-core/src/reality/mcp/catalog.py`; deliver FR-006, FR-007, FR-008, FR-009, FR-010 without weakening their refusal checks.

## Phase 4: US3 — Recover and measure large intakes

**Independent acceptance**: Execute US3 scenarios; require exact retained-result counts and zero unapproved effects. Write/observe failing tests before their corresponding implementation.

- [ ] T014 [US3] Add and observe failing proofs for FR-011, FR-012, FR-013 in `packages/reality-core/tests/test_bulk_intake_review.py`: `test_surfaces_share_bulk_semantics`, `test_volume_workloads_and_resource_bounds`, `test_bulk_has_measured_nonregression`.
- [ ] T015 [US3] Add bulk/mandate review and recovery to the existing decision/import components with full localization in `apps/web/src/unified/DecisionsPage.tsx`; deliver FR-011, FR-012, FR-013 without weakening their refusal checks.
- [ ] T016 [US3] Implement correctness and resource benchmark harness with controlled agent verdicts in `packages/reality-core/src/reality/benchmarks/intake.py`; deliver FR-011, FR-012, FR-013 without weakening their refusal checks.

## Final phase: Integration and verification

- [ ] T017 Add concurrent approval, crash-before/after-commit, cross-tenant and scope-reuse integration proof for DR-001–DR-003/SC-001 in `packages/reality-core/tests/test_bulk_intake_review.py` and execute the story tests against real PostgreSQL.
- [ ] T018 Update exact source/decision explanation and applicable contracts in `docs/features/scheduled-jobs.md` plus the other paths listed in plan.md; include DR-001–DR-003 and register new test families in `docs/SPEC_COVERAGE_MATRIX.md`.
- [ ] T019 Run required gates from `quickstart.md`, review the actual diff and migration/rollback evidence, and record measured results in this feature's `verification.md` before marking any story complete (SC-002, SC-003).

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


- [ ] T020 Add failure-first owner-scope, genuine-token, complete original-byte coverage, finite quota, expiry/revocation and migration proofs in `test_intake_agent_review.py`; implement the current mandate and structured evidence services (FR-006–FR-010/FR-007a).
- [ ] T021 Prove retained delegated batches with exact complete evidence, current token/source authority, shared quotas, replay, private-scope refusal and late chunk rollback in `test_intake_agent_bulk.py`; expose `submit_agent_batch_review` through a mutating MCP confirmation tool and the canonical shared queue (FR-006–FR-010).

- [ ] T022 Prove bounded explicit Web/API/CLI source selection, exact confirmation, complete source download, truthful child progress/receipts, stop and renewed review in `test_bulk_intake_transports.py` and the real-stack `tests/browser/unified_bulk_intake.py`; expose shared services in Decisions and trusted local CLI (FR-011).

- [ ] T023 Bind current mandate scope/token/expiry/revision to its original owner grant; prove refusal after retained-row alteration and genuine approved commercial limits in `tests/test_intake_agent_review.py`.
- [ ] T024 Prove simultaneous competing quota claims and exact-review replay using independent PostgreSQL connections in `tests/test_intake_agent_concurrency.py`.
