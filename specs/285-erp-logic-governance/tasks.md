---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: Governed ERP Logic Ownership

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/governance-trace.md`, and `quickstart.md`
**Gate**: Constitution Check passed; scope approved; no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be written in
English. Tests precede the implementation they prove. A semantic disagreement discovered in US3
stops that calculation slice and is recorded in `review.md`; no task silently chooses a winner.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [ ] T001 Record reviewer decisions for every open item in `specs/285-erp-logic-governance/checklists/governance.md`; do not treat unchecked requirements-quality items as implementation work
- [ ] T002 Confirm every Constitution Check row remains PASS and record architecture/domain approval in `specs/285-erp-logic-governance/plan.md`
- [ ] T003 Run `$speckit-analyze` against `spec.md`, `plan.md`, and this `tasks.md`; resolve every CRITICAL finding before Phase 2
- [ ] T004 [P] Capture the exact pre-refactor ordered application and MCP registry metadata/bindings fixture in `packages/reality-core/tests/fixtures/erp_registry_baseline.json`
- [ ] T005 [P] Create the bounded audit record structure and list the four approved calculation families in `specs/285-erp-logic-governance/review.md`

## Phase 2: Foundational Failing Proofs

**Goal**: Establish injected, deterministic test seams before production governance code or registry movement.

- [ ] T006 [FR-001] [FR-002] [FR-014] Add failing complete-trace fixtures for a command mutation, command read, public read and explicit exclusion in `packages/reality-core/tests/test_erp_governance.py`
- [ ] T007 [FR-003] [FR-008] [FR-015] Add failing missing-owner, duplicate-owner, conflicting-owner and diagnostic assertions in `packages/reality-core/tests/test_erp_governance.py`
- [ ] T008 [FR-004] [FR-005] [FR-006] Add failing AST fixtures for an adapter business write, local availability calculation and permitted formatting/authorization controls in `packages/reality-core/tests/test_erp_governance.py`
- [ ] T009 [FR-007] [FR-016] Add failing exact, broadened, stale and unused boundary-exception fixtures in `packages/reality-core/tests/test_erp_governance.py`
- [ ] T010 [DR-004] [DR-007] Add failing inward-dependency fixtures for domain, services, tools and automated adapters in `packages/reality-core/tests/test_erp_governance.py`

## Phase 3: User Story 1 — Trace an ERP capability to one authority (P1)

**Goal**: Produce one complete validated trace for every governed ERP command and public ERP read.

**Independent Test**: Select representative reads and mutations from orders, inventory, logistics,
finance and contribution; each resolves to exactly one owner with classifications, entry points,
effects/data basis, verification and executable evidence. Broken references fail by identity.

### Tests first

- [ ] T011 [US1] [FR-001] [FR-002] Add failing trace-shape, deterministic-order and no-sensitive-data contract tests in `packages/reality-core/tests/test_erp_governance.py`
- [ ] T012 [P] [US1] [FR-003] [FR-014] Add failing uniqueness and evidence-resolution cases to `packages/reality-core/tests/test_application_catalog.py`
- [ ] T013 [P] [US1] [FR-010] Add failing generated governance-page and JSON freshness contracts in `apps/docs/scripts/docs-contract.test.mjs`
- [ ] T014 [US1] [DR-001] [DR-002] [DR-003] [DR-005] Add metadata-only/no-business-authority and shortest-link assertions in `packages/reality-core/tests/test_erp_governance.py`

### Implementation

- [ ] T015 [US1] [FR-001] [FR-002] Implement immutable governance metadata models and trace composition in `packages/reality-core/src/reality/governance.py`
- [ ] T016 [US1] [FR-003] [FR-014] [FR-015] Integrate singular owner/evidence/reference validation into `packages/reality-core/src/reality/catalogs.py`
- [ ] T017 [US1] [FR-002] [FR-014] Define and validate the executable-evidence declaration shape in `packages/reality-core/config/command_catalog.yaml` and `packages/reality-core/src/reality/catalogs.py`, with test-node resolution limited to repository CI/docs validation
- [ ] T018 [US1] [FR-002] [FR-014] Add evidence/verification declarations for party, item, location, terms, order, delivery, lot and return resources in `packages/reality-core/config/command_catalog.yaml`
- [ ] T019 [US1] [FR-002] [FR-014] Add evidence/verification declarations for invoice, payment, accounting and contribution resources in `packages/reality-core/config/command_catalog.yaml`
- [ ] T020 [US1] [FR-002] [FR-014] Add evidence/verification declarations for analytics, source, company and governance resources plus public MCP read roots in `packages/reality-core/config/command_catalog.yaml`
- [ ] T021 [US1] [FR-010] Extend `apps/docs/scripts/generate-catalog-reference.py` to generate `apps/docs/content/tool-usage/governance.md` and the matching section of `apps/docs/.vitepress/data/tool-usage.json` from the validated trace
- [ ] T022 [US1] [FR-016] Classify non-business transport/operational helpers with explicit reasons in the existing command/capability coverage blocks of `packages/reality-core/config/command_catalog.yaml`
- [ ] T023 [US1] [DR-001] [DR-002] [DR-003] [DR-005] Document metadata-only authority and unchanged Source → Evidence → Reality links in `docs/features/erp-logic-governance.md`
- [ ] T024 [US1] [FR-018] Record US1 coverage counts, representative lookup timing and unresolved gaps in `specs/285-erp-logic-governance/review.md`

## Phase 4: User Story 2 — Prevent a second business implementation (P1)

**Goal**: Fail before merge when an adapter writes business state, reverses a layer dependency or reconstructs a governed critical calculation.

**Independent Test**: Inject one forbidden and one legitimate example for every rule. Forbidden
fixtures fail with capability, owner and expected boundary; permitted transport behavior passes.

### Tests first

- [ ] T025 [US2] [FR-004] [FR-005] Add production-tree positive controls and planted business-model mutation/Core-DML cases in `packages/reality-core/tests/test_erp_governance.py`
- [ ] T026 [US2] [FR-005] [FR-006] Add owner-specific forbidden-ingredient and allowed presentation-arithmetic fixtures in `packages/reality-core/tests/test_erp_governance.py`
- [ ] T027 [US2] [FR-007] [FR-016] Add path/function/rule/evidence resolution and stale-use tests for the exception catalog in `packages/reality-core/tests/test_erp_governance.py`
- [ ] T028 [US2] [DR-004] [DR-007] Add production import-graph positive controls for domain, services, tools, Web/API, CLI, Chat, MCP, jobs, integrations and demo code in `packages/reality-core/tests/test_erp_governance.py`

### Implementation

- [ ] T029 [US2] [FR-004] [FR-005] [FR-006] Implement AST import, business-write and named-calculation boundary validators in `packages/reality-core/src/reality/governance.py`
- [ ] T030 [US2] [FR-007] [FR-016] Add the exact exception schema and only currently proven exceptions to `packages/reality-core/config/erp_boundary_exceptions.yaml`
- [ ] T031 [US2] [DR-004] [DR-007] Resolve or narrowly classify current reverse dependencies, moving `_opening_movement_evidence` from `packages/reality-core/src/reality/tools/application.py` to its owning service path before it is governed
- [ ] T032 [US2] [FR-004] [FR-005] Run the production-tree validator, record every finding with exact file/function/owner in `specs/285-erp-logic-governance/review.md`, and stop to add reviewed path-specific remediation tasks before changing any newly discovered file
- [ ] T033 [US2] [FR-017] Re-run and preserve tenant, authorization, confirmation and idempotency contracts in `packages/reality-core/tests/tenant_isolation/`, `test_mcp_permission_parity.py`, `test_proposal_review_parity.py`, and `test_demo_entrypoint_parity.py`
- [ ] T034 [US2] [FR-018] Record every resolved violation and remaining reviewed exception in `specs/285-erp-logic-governance/review.md`

## Phase 5: User Story 3 — Verify critical ERP calculations have one meaning (P1)

**Goal**: Give all registered consumers of the four approved calculation families shared semantic evidence without collapsing different grains or authority states.

**Independent Test**: Each family scenario exercises its owner and all registered consumers with the
same cutoff; values and known/unknown/stale/refused states agree. Any mismatch blocks only that
family and is written to `review.md` for domain approval.

### Inventory tests and owner alignment

- [ ] T035 [US3] [FR-011] [FR-012] Add failing inventory parity stories for transfer legs, active/inactive dimensional reservations, incoming revised supply, receipt and correction in `packages/reality-core/tests/scenarios/test_erp_calculation_parity.py`
- [ ] T036 [US3] [DR-006] Assert exact dimensional rows aggregate to operational item/location physical, reserved and available values while incoming/projected remain separately defined in `packages/reality-core/tests/scenarios/test_erp_calculation_parity.py`
- [ ] T037 [US3] [FR-011] [FR-012] Align inventory projection/tool/readiness/exception consumers with the declared per-grain owners in `packages/reality-core/src/reality/services/{core.py,inventory_positions.py,projections.py,fulfillment_readiness.py,exceptions.py}`

### Fulfilment tests and owner alignment

- [ ] T038 [US3] [FR-011] [FR-012] Add failing customer/supplier fulfilment parity stories for revision, partial movement, correction, over-fulfilment clamp, cancellation, hold, reservation and return behavior in `packages/reality-core/tests/scenarios/test_erp_calculation_parity.py`
- [ ] T039 [US3] [DR-006] Compare scalar/batch terms, correlated lists, commitment projection, readiness, exceptions and MCP reads at one cutoff in `packages/reality-core/tests/scenarios/test_erp_calculation_parity.py`
- [ ] T040 [US3] [FR-011] [FR-012] Consolidate effective/fulfilled/open semantics behind admitted primitives in `packages/reality-core/src/reality/services/core.py` and reuse them from `delivery_reads.py`, `fulfillment_readiness.py`, `projections.py`, and `exceptions.py`
- [ ] T041 [US3] [FR-013] If any fulfilment path disagrees, document the exact scenario and competing outputs in `specs/285-erp-logic-governance/review.md` and stop T040 pending approved clarification

### Finance tests and owner alignment

- [ ] T042 [US3] [FR-011] [FR-012] Add failing sales/supplier invoice stories with partial payments, credits, refunds, inactive allocations, reversal, opening position, cutoff and multiple currencies in `packages/reality-core/tests/scenarios/test_erp_calculation_parity.py`
- [ ] T043 [US3] [DR-003] [DR-006] Compare scalar/bulk settlement positions, open-item projection, aging, party balances, dunning/exceptions and public reads without currency netting in `packages/reality-core/tests/scenarios/test_erp_calculation_parity.py`
- [ ] T044 [US3] [FR-011] [FR-012] Reuse `settlement_positions` and `party_balance_rows` from any divergent finance consumer in `packages/reality-core/src/reality/services/{core.py,finance/balances.py,payment_actions.py,payment_intake.py,dunning.py,exceptions.py}` while preserving their distinct questions

### Contribution tests and owner alignment

- [ ] T045 [US3] [FR-011] [FR-012] Add failing exact sale/shipment/inventory review plus direct/allocated selling-cost and stale-correction stories in `packages/reality-core/tests/scenarios/test_erp_calculation_parity.py`
- [ ] T046 [US3] [DR-003] [DR-006] Compare preview known DB1, reviewed DB1/DB2, cost query, generation/captured report and negative-DB1 exception states in `packages/reality-core/tests/scenarios/test_erp_calculation_parity.py`
- [ ] T047 [US3] [FR-011] [FR-012] Route contribution consumers through `domain/contribution.py::aggregate_contribution` and the correct candidate/reviewed state owner in `packages/reality-core/src/reality/services/{contribution.py,contribution_reviews.py,contribution_generations.py,exceptions.py}`

### Cross-family gate

- [ ] T048 [US3] [FR-013] Fail governance coverage when a registered critical consumer lacks a scenario or declares a conflicting owner in `packages/reality-core/src/reality/governance.py` and `packages/reality-core/tests/test_erp_governance.py`
- [ ] T049 [US3] [FR-017] Add two-tenant/non-disclosure and unchanged opaque-ID/provenance assertions to all four matrices in `packages/reality-core/tests/scenarios/test_erp_calculation_parity.py`
- [ ] T050 [US3] [FR-018] Complete the four-family consumer inventory, parity result and any blocking discrepancy in `specs/285-erp-logic-governance/review.md`

## Phase 6: User Story 4 — Extend one business area without destabilizing others (P2)

**Goal**: Compose independently reviewable registration fragments into the exact existing public registries with duplicate refusal and stable facades.

**Independent Test**: A test fragment changes only its business-area input and deterministic assembled
output; duplicate/incomplete registration fails. The complete ordered public metadata, schemas,
bindings, authorization and proposal-review classification equal the captured baseline.

### Tests first

- [ ] T051 [US4] [FR-008] [FR-009] Add failing ordered-fragment composition, duplicate key and stable mutable-facade tests in `packages/reality-core/tests/test_tool_catalog.py`
- [ ] T052 [P] [US4] [FR-009] Add exact before/after MCP name, description, group, access, schema, binding and order assertions in `packages/reality-core/tests/test_agent_command_parity.py`
- [ ] T053 [P] [US4] [FR-009] Add stable import, proposal lifecycle and review-classification compatibility assertions in `packages/reality-core/tests/test_proposal_review_parity.py`

### Implementation

- [ ] T054 [US4] [FR-008] Implement `Tool` contract and ordered duplicate-refusing composition in `packages/reality-core/src/reality/tools/registry.py`, re-exporting compatibility names from `tools/application.py`
- [ ] T055 [US4] [FR-008] Extract existing finance, costing and analytics/graph registration fragments to `packages/reality-core/src/reality/tools/registrations/{finance.py,costing.py,analytics.py}` without moving proposal lifecycle/dispatch
- [ ] T056 [US4] [FR-008] Move dependency-light MCP definition/building primitives to `packages/reality-core/src/reality/mcp/definitions.py` and preserve re-exports from `mcp/catalog.py`
- [ ] T057 [US4] [FR-008] Extract operations, finance, costing and analytics MCP fragments to `packages/reality-core/src/reality/mcp/registrations/{operations.py,finance.py,costing.py,analytics.py}` with deterministic final composition
- [ ] T058 [US4] [FR-009] Compare assembled registries to `packages/reality-core/tests/fixtures/erp_registry_baseline.json` and restore any changed public metadata, order, schema, binding or mutability before proceeding
- [ ] T059 [US4] [FR-010] Regenerate Tool Usage and verify catalog parity through `apps/docs/scripts/generate-catalog-reference.py` and `apps/docs/.vitepress/data/tool-usage.json`
- [ ] T060 [US4] [FR-017] Run application catalog, tool catalog, MCP authorization/permission, proposal review and Chat/CLI adapter suites listed in `specs/285-erp-logic-governance/quickstart.md`

## Final Phase: Cross-Cutting Review and Verification

- [ ] T061 [P] [FR-018] Update ownership/layer rules and audit navigation in `docs/ARCHITECTURE.md` and `docs/features/erp-logic-governance.md`
- [ ] T062 [P] [FR-010] Run `make docs-generate` and commit `apps/docs/content/tool-usage/governance.md` plus `apps/docs/.vitepress/data/tool-usage.json`; then pass `make docs-catalog-check`
- [ ] T063 Run `make spec-check` and audit every FR/DR row against this task coverage table and `specs/285-erp-logic-governance/review.md`
- [ ] T064 Run backend Ruff formatting/checks and the focused governance/critical-calculation suites from `specs/285-erp-logic-governance/quickstart.md`
- [ ] T065 Run the complete PostgreSQL backend test suite and record exact results in `specs/285-erp-logic-governance/review.md`
- [ ] T066 Run applicable Web catalog contracts, localization audit and production build; record exact results in `specs/285-erp-logic-governance/review.md`
- [ ] T067 Review the final diff for migrations/schema changes, public contract drift, tenant leaks, stored derivations and accidental source-payload exposure; record zero findings or blockers in `specs/285-erp-logic-governance/review.md`
- [ ] T068 Obtain final architecture/domain review of all exceptions and four semantic parity results in `specs/285-erp-logic-governance/review.md`
- [ ] T069 Mark tasks/checklists/status complete only after every required check is green; do not change `docs/V0_CHECKLIST.md` unless its own release criterion is newly proven

## Dependencies and Execution Order

```text
Phase 1 gates
    ↓
Phase 2 failing proof
    ↓
US1 trace authority
    ↓
US2 enforce boundaries ─────────┐
    ↓                           │
US3 semantic audit/consolidate  │
    ↓                           │
US4 modularize registries ◀─────┘
    ↓
Final verification/review
```

- US1 is the MVP and establishes the ownership vocabulary required by all later gates.
- US2 depends on US1 for diagnostics and owner identities.
- US3 depends on US1 and US2; its four family test tasks may run in parallel, but owner changes in
  shared service files are sequential. A family can remain blocked without permitting US4 to hide
  the discrepancy.
- US4 depends on singular ownership and architecture gates; modularizing first would distribute an
  unproven registry.

## Parallel Opportunities

- T004 and T005 are independent setup artifacts.
- T006–T010 use one shared test module and therefore execute sequentially even though their fixture
  concerns are independent.
- T012 and T013 touch distinct files and can run in parallel; T014 follows T011 in the shared
  governance test module.
- T025–T028 and T035/T038/T042/T045 execute sequentially within their respective shared test files.
- T052 and T053 are independent compatibility proofs once T051 fixes the composition contract.
- T061 and T062 can proceed in parallel after runtime/catalog outputs stabilize.

## Implementation Strategy

1. **MVP — US1**: complete trace, singular ownership and generated reviewer reference.
2. **Safety — US2**: make prohibited duplicate paths fail with low-noise diagnostics.
3. **Semantic proof — US3**: audit fulfilment first, then inventory, finance and contribution; stop
   any disagreeing family for owner review.
4. **Maintainability — US4**: split registrations only after all authority gates are green.
5. **Release evidence**: complete docs, full suites and independent architecture/domain review.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-002 | T006, T011 | T015, T017–T021 | Pending |
| FR-003 | T007, T012 | T016 | Pending |
| FR-004–FR-006 | T008, T025–T026 | T029, T032 | Pending |
| FR-007 | T009, T027 | T030 | Pending |
| FR-008 | T007, T051 | T054–T057 | Pending |
| FR-009 | T051–T053 | T058 | Pending |
| FR-010 | T013 | T021, T059, T062 | Pending |
| FR-011–FR-012 | T035–T036, T038–T039, T042–T043, T045–T046 | T037, T040, T044, T047 | Pending |
| FR-013 | T038–T046, T048 | T041, T050 | Pending |
| FR-014–FR-015 | T006–T007, T012 | T016–T020 | Pending |
| FR-016 | T009, T027 | T022, T030 | Pending |
| FR-017 | T033, T049, T060 | T032, T058 | Pending |
| FR-018 | T024, T034, T050 | T005, T061, T065–T068 | Pending |
| DR-001–DR-003 | T014, T043, T046 | T023, T037, T044, T047 | Pending |
| DR-004–DR-005 | T010, T014, T028, T049 | T023, T029–T032 | Pending |
| DR-006 | T036, T039, T043, T046 | T037, T040, T044, T047 | Pending |
| DR-007 | T010, T028, T033 | T029–T032 | Pending |
| SC-001–SC-002 | T006–T013, T025–T028 | T015–T032 | Pending |
| SC-003–SC-004 | T035–T050 | T037, T040–T041, T044, T047–T050 | Pending |
| SC-005 | T011 | T021, T024 | Pending |
| SC-006 | T051–T053 | T054–T058 | Pending |
| SC-007–SC-008 | T033, T060, T063–T067 | T061–T069 | Pending |
