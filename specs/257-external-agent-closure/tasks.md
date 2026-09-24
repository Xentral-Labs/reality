---
description: "Requirement-traceable Business Reality implementation tasks"
---

# Tasks: External Agent Audit Closure

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

Every functional/domain requirement appears in at least one test task and one implementation
or documentation task. Test tasks precede the code they prove.

## Phase 1: Specification and Design Gates

- [X] T001 Confirm product/domain approval, retained F1–F13 dispositions, and absence of clarification markers in `specs/257-external-agent-closure/spec.md`
- [X] T002 Confirm every Constitution Check and post-design row remains PASS and approve the no-schema decision in `specs/257-external-agent-closure/plan.md`
- [X] T003 Cross-check dependencies and already implemented behavior in `specs/249-web-mcp-review-parity/`, `specs/250-operational-integrity/`, and `specs/251-live-demo-cost-readiness/`; record reuse decisions in `specs/257-external-agent-closure/research.md`
- [X] T004 Run `$speckit-analyze` and resolve every CRITICAL or HIGH requirement, contract, plan, or task inconsistency in `specs/257-external-agent-closure/`

## Phase 2: Foundational Contracts and Failing Proofs

**Goal**: Establish shared catalog, proposal, tenant, provenance, and release-proof boundaries
before story-specific implementation.

- [X] T005 [P] [FR-001] [FR-002] [FR-030] Add failing canonical MCP schema/reference parity assertions for required fields, enums and nested shapes in `packages/reality-core/tests/test_ai_mcp.py` and `apps/docs/scripts/docs-contract.test.mjs`
- [X] T006 [P] [FR-028] [FR-029] Add the redacted F1–F13 terminal-result schema and expected evidence fields to `specs/257-external-agent-closure/quickstart.md`
- [X] T007 [P] [DR-001] [DR-002] [DR-003] Add failing Source → Evidence → Reality and no-recomputation assertions for free invoices, credits, returns and costing in `packages/reality-core/tests/scenarios/test_external_agent_audit_closure.py`
- [X] T008 [P] [DR-004] [DR-006] Add failing opaque-identity and cross-tenant refusal cases for every new read/action in `packages/reality-core/tests/test_ai_mcp.py`
- [X] T009 [P] [DR-005] Add a failing registry contract proving Web, MCP and application bindings resolve to shared tools/services in `packages/reality-core/tests/test_application_catalog.py` and `apps/web/scripts/external-agent-closure-contract.test.mjs`
- [X] T010 [P] [DR-007] Add failing principal-boundary cases for agent preparation, agent confirmation refusal and authenticated-owner confirmation in `packages/reality-core/tests/test_application_tools.py`
- [X] T011 [P] [DR-008] Add a schema-diff assertion proving this feature introduces no business table/column in `packages/reality-core/tests/test_migrations.py`
- [X] T012 [FR-028] [FR-029] Create the executable fresh-tenant audit harness skeleton and redacted evidence writer in `packages/reality-core/tests/scenarios/test_external_agent_audit_closure.py`

**Checkpoint**: Shared failing proofs exist; no production behavior has changed.

## Phase 3: User Story 1 — Discover and Verify the Supported MCP Path (P1)

**Goal**: A clean client discovers valid inputs, review handoff and authoritative verification
without production probing.

**Independent test**: From only public MCP contracts, prepare receipt, dispatch, reservation,
supply assignment, return disposition, settlement and invoice credit; identify review and
verification steps with zero invalid-value probes.

### Tests

- [X] T013 [P] [US1] [FR-003] Add failing structured proposal-next-step tests for ordinary, state-bound and owner-governed proposals in `packages/reality-core/tests/test_ai_mcp.py`
- [X] T014 [P] [US1] [FR-004] Add failing exact-public-name, unique-application-name, ambiguity and unknown capability tests in `packages/reality-core/tests/test_capability_guidance.py`
- [X] T015 [P] [US1] [FR-005] [FR-006] Add failing zero, partial and complete exact-location reservation receipt tests in `packages/reality-core/tests/test_application_tools.py`
- [X] T016 [P] [US1] [FR-001] [FR-002] Add failing closed-value and conditional/nested-schema tests for shipment, supply, return, settlement and credit tools in `packages/reality-core/tests/test_ai_mcp.py`
- [X] T017 [US1] [FR-030] Add a failing deployed-`tools/list` versus generated-reference comparison command/test in `apps/docs/scripts/verify-live-mcp-catalog.py` and `apps/docs/scripts/docs-contract.test.mjs`

### Implementation

- [X] T018 [US1] [FR-003] Derive structured review, principal and verification next-step metadata in the shared propose binding in `packages/reality-core/src/reality/mcp/catalog.py` using `packages/reality-core/src/reality/services/proposal_reviews.py`
- [X] T019 [US1] [FR-004] Resolve capability descriptions by canonical MCP identity or unique application-tool identity in `packages/reality-core/src/reality/tools/application.py` and document canonical names in `packages/reality-core/config/command_catalog.yaml`
- [X] T020 [US1] [FR-005] [FR-006] Add derived reservation effect classification, remaining work and verification reads to receipts in `packages/reality-core/src/reality/tools/application.py` without changing exact-location allocation in `packages/reality-core/src/reality/services/core.py`
- [X] T021 [P] [US1] [FR-001] [FR-002] Align canonical enums, nested schemas and actionable validation guidance in `packages/reality-core/src/reality/mcp/catalog.py` and `packages/reality-core/config/command_catalog.yaml`
- [X] T022 [P] [US1] [FR-030] Implement the redacted deployed catalog projection/comparison in `apps/docs/scripts/verify-live-mcp-catalog.py`
- [X] T023 [US1] [FR-001] [FR-002] [FR-003] [FR-004] Update English/German Tool Usage source labels and generated pages via `packages/reality-core/config/resource_catalog.yaml`, `apps/docs/content/tool-usage/`, and `apps/docs/.vitepress/data/tool-usage.json`
- [X] T024 [US1] [FR-003] [FR-005] Update proposal and reservation explanation contracts in `docs/WEB_SPEC.md` and `docs/features/reservations.md`
- [X] T025 [US1] [FR-001] [FR-006] Run the clean-client discovery and exact-location reservation cases and record expected/actual evidence in `specs/257-external-agent-closure/quickstart.md`

**Checkpoint**: US1 is independently deployable and verifiable; no finance or cost authority is broadened.

## Phase 4: User Story 2 — Complete Owner-Governed Finance Without Weakening Authority (P1)

**Goal**: Agents prepare supported finance work, authenticated owners decide it, and agents
reconcile results through one proposal identity.

**Independent test**: Prepare discount, accepted small remainder, overpayment, dunning with fee
and free supplier invoice through MCP; decide owner-governed finance in owner Web review and the
free supplier invoice through ordinary authorized-human confirmation; reconcile through MCP.

### Tests

- [X] T026 [P] [US2] [FR-007] [FR-008] Add failing end-to-end agent→owner→agent proposal handoff tests for finance commands in `packages/reality-core/tests/finance/test_owner_handoff.py`
- [X] T027 [P] [US2] [FR-009] [FR-010] Add failing public settlement stories for exact/partial/reduction/small-remainder/overpayment/credit allocation/refund in `packages/reality-core/tests/finance/test_settlement_flows.py`
- [X] T028 [P] [US2] [FR-011] Add failing missing-account and unrelated-reduction-account diagnostic cases in `packages/reality-core/tests/finance/test_settlement_flows.py`
- [X] T029 [P] [US2] [FR-012] Add failing MCP dunning context, record, fee, reversal, owner and tenant tests in `packages/reality-core/tests/finance/test_commercial_edges.py` and `packages/reality-core/tests/test_ai_mcp.py`
- [X] T030 [P] [US2] [FR-013] [DR-001] [DR-003] Add failing free supplier-invoice tests for ordinary/charge lines, stated totals, provenance, ordinary authorized-human confirmation without owner-only authority, atomic rollback, replay and tenant scope in `packages/reality-core/tests/test_free_supplier_invoice.py`
- [X] T031 [P] [US2] [FR-026] Add failing `finance_payments.direction` validation/filter tests and rejection of `side` in `packages/reality-core/tests/finance/test_payment_reads.py`

### Implementation

- [X] T032 [US2] [FR-007] [FR-008] Reuse the shared proposal review descriptor and authenticated owner decision route for finance proposals in `packages/reality-core/src/reality/services/proposal_reviews.py` and `packages/reality-core/src/reality/web/api.py`
- [X] T033 [US2] [FR-009] [FR-010] Preserve settlement behavior while adding complete public guidance and receipts in `packages/reality-core/src/reality/tools/finance.py`, `packages/reality-core/src/reality/mcp/catalog.py`, and `packages/reality-core/config/command_catalog.yaml`
- [X] T034 [US2] [FR-011] Make finance context/review diagnostics name the exact missing account role and applicable action in `packages/reality-core/src/reality/services/finance/settlement_flows.py`
- [X] T035 [US2] [FR-012] Bind existing dunning context/detail, record and reverse commands to MCP in `packages/reality-core/src/reality/mcp/catalog.py` and `packages/reality-core/src/reality/tools/application.py`
- [X] T036 [US2] [FR-013] Implement atomic source-backed free supplier-invoice recording and posting in `packages/reality-core/src/reality/services/invoice_actions.py`, reusing existing normalization/posting primitives from `packages/reality-core/src/reality/services/core.py`
- [X] T037 [US2] [FR-013] Expose free supplier invoice through the shared application and MCP catalogs in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/mcp/catalog.py`
- [X] T038 [US2] [FR-026] Enforce the documented payment-direction vocabulary and reject unsupported inputs in `packages/reality-core/src/reality/mcp/catalog.py` and `packages/reality-core/src/reality/tools/application.py`
- [X] T039 [P] [US2] [FR-007] [FR-012] Update Web proposal/dunning handoff labels and localization in `apps/web/src/unified/ProposalReviewCard.tsx`, `apps/web/src/finance/DunningNotice.tsx`, and `apps/web/src/localization.tsx`
- [X] T040 [US2] [FR-007] [FR-008] [FR-009] [FR-012] [FR-013] Run the independent finance-authority story, separating owner-governed decisions from ordinary human confirmation, and record expected/actual evidence in `specs/257-external-agent-closure/quickstart.md`

**Checkpoint**: US2 completes all supported finance cases without turning an agent credential into an owner.

## Phase 5: User Story 3 — Credit and Resolve a Return Through Canonical Records (P1)

**Goal**: Invoice credit and physical return resolution use canonical linked records without
generic-document workarounds.

**Independent test**: Read creditable invoice positions, record a linked partial credit, receive
a tracked return and split it between restock and scrap/loss; verify finance, stock and exceptions.

### Tests

- [X] T041 [P] [US3] [FR-014] [FR-025] Add failing MCP invoice-credit-context read, tenant and blocker tests in `packages/reality-core/tests/test_unified_invoice_credit.py` and `packages/reality-core/tests/test_ai_mcp.py`
- [X] T042 [P] [US3] [FR-015] Add failing schema-regression tests for complete invoice-linked and legacy credit shapes in `packages/reality-core/tests/test_ai_mcp.py`
- [X] T043 [P] [US3] [FR-016] [FR-027] Add failing MCP end-to-end linked-credit and returned-not-credited reconciliation tests in `packages/reality-core/tests/operational_exceptions/test_derivation.py`
- [X] T044 [P] [US3] [FR-017] Add failing precise missing movement/commitment/destination/tracking refusal tests in `packages/reality-core/tests/test_returns.py`
- [X] T045 [P] [US3] [FR-018] Add failing public adapter regression for all four dispositions and exact tracking identity in `packages/reality-core/tests/test_return_announcement_adapters.py`

### Implementation

- [X] T046 [US3] [FR-014] [FR-025] Expose the existing invoice-credit context as a shared application read and MCP tool in `packages/reality-core/src/reality/services/credit_actions.py`, `packages/reality-core/src/reality/tools/application.py`, and `packages/reality-core/src/reality/mcp/catalog.py`
- [X] T047 [US3] [FR-015] Keep the canonical mutually exclusive credit shapes aligned across validation, MCP schema and guidance in `packages/reality-core/src/reality/services/core.py`, `packages/reality-core/src/reality/mcp/catalog.py`, and `packages/reality-core/config/command_catalog.yaml`
- [X] T048 [US3] [FR-016] [FR-027] Preserve invoice-line/order-line relationships and expose their explanation path in `packages/reality-core/src/reality/services/credit_actions.py` and `packages/reality-core/src/reality/services/exceptions.py`
- [X] T049 [US3] [FR-017] Refine return receipt/disposition validation failures at the shared service boundary in `packages/reality-core/src/reality/services/core.py` and `packages/reality-core/src/reality/services/return_dispositions.py`
- [X] T050 [US3] [FR-018] Verify and document canonical dispositions without alternate logic in `packages/reality-core/src/reality/services/return_disposition_actions.py`, `packages/reality-core/src/reality/mcp/catalog.py`, and `packages/reality-core/config/command_catalog.yaml`
- [X] T051 [P] [US3] [FR-014] [FR-017] Update credit/return public documentation and Inspector guidance in `docs/WEB_SPEC.md`, `docs/features/movements.md`, and `apps/docs/content/tool-usage/`
- [X] T052 [US3] [FR-014] [FR-016] [FR-017] [FR-018] [FR-027] Run the independent credit-and-tracked-return story and record expected/actual evidence in `specs/257-external-agent-closure/quickstart.md`

**Checkpoint**: US3 closes the canonical credit/return path and clears linked exceptions without fabricating goods or money effects.

## Phase 6: User Story 4 — Reach Truthful Cost and Contribution Results (P1)

**Goal**: An ordinary company can move from an uninitialized read to supported owner-reviewed
inventory/DB observations, while incomplete evidence remains unavailable.

**Independent test**: Starting with received goods, invoice and freight evidence, follow only
public guidance and owner confirmation to inventory, DB1 and DB2; repeat with missing evidence.

### Tests

- [X] T053 [P] [US4] [FR-020] Add failing stage-aware cost-guidance tests for uninitialized, pending, stale, failed and complete scopes in `packages/reality-core/tests/test_cost_query.py`
- [X] T054 [P] [US4] [FR-021] [DR-007] Add failing agent-prepare/owner-confirm costing-tool journey in `packages/reality-core/tests/test_costing_tools.py`
- [X] T055 [P] [US4] [FR-022] Add failing actual-versus-estimate, missing acquisition, DB1-only and DB2-incomplete cases in `packages/reality-core/tests/test_inventory_costing_services.py`, `packages/reality-core/tests/test_contribution_reviews.py`, and `packages/reality-core/tests/test_selling_costs.py`
- [X] T056 [P] [US4] [FR-023] Add or retain spec-251 calculation-readiness regressions in `packages/reality-core/tests/test_demo_costing_profile.py` and `packages/reality-core/tests/test_demo_data_intake.py`
- [X] T057 [P] [US4] [FR-020] [FR-021] Add failing Web contract/browser checks for actionable guidance and owner handoff in `apps/web/scripts/cost-explanation-contract.test.mjs`

### Implementation

- [X] T058 [US4] [FR-020] Derive bounded cost stages, missing basis, next authorized action and explanation links in `packages/reality-core/src/reality/domain/cost_query.py` and `packages/reality-core/src/reality/services/cost_query.py`
- [X] T059 [US4] [FR-021] Expose the shared guidance through existing cost reads/proposals in `packages/reality-core/src/reality/tools/costing.py`, `packages/reality-core/src/reality/tools/application.py`, and `packages/reality-core/src/reality/mcp/catalog.py`
- [X] T060 [US4] [FR-020] [FR-022] Render the same guidance, independent coverage and unavailable state in `apps/web/src/unified/CostExplanation.tsx`, `apps/web/src/api.ts`, and `apps/web/src/localization.tsx`
- [X] T061 [US4] [FR-023] Verify that canonical demo readiness continues through `packages/reality-core/src/reality/services/demo_profile.py` and `packages/reality-core/src/reality/services/company_setup.py` without an ordinary-company shortcut
- [X] T062 [US4] [FR-020] [FR-021] [FR-022] [FR-023] Run complete/incomplete ordinary-company costing and demo-regression stories and record evidence in `specs/257-external-agent-closure/quickstart.md`

**Checkpoint**: US4 guides users without inventing cost, automatic review or a second demo path.

## Phase 7: User Story 5 — Keep Public Proposals and Reads Clean and Recoverable (P2)

**Goal**: Invalid operational types do not persist, payment filters are strict, and unwanted
pending proposals can be rejected through MCP.

**Independent test**: Reject and replay a proposal, apply valid/invalid filters, and attempt
unsupported operational types; verify queue and persistence remain clean.

### Tests

- [X] T063 [P] [US5] [FR-024] Add failing MCP proposal rejection tests for explicit authorized-human decision, exclusion from default model selection, safe replay, executed/executing refusal and tenant scope in `packages/reality-core/tests/test_application_tools.py` and `packages/reality-core/tests/test_ai_mcp.py`
- [X] T064 [P] [US5] [FR-019] Add failing tests for the exact six-value public manual document vocabulary, unsupported document and movement types, and zero proposal/document persistence in `packages/reality-core/tests/test_application_tools.py` and `packages/reality-core/tests/test_reporting_graph_expansion.py`
- [X] T065 [P] [US5] [FR-025] Add failing invoice-position read independence from creation receipts in `packages/reality-core/tests/test_unified_invoice_credit.py`
- [X] T066 [P] [US5] [FR-026] Add failing supported/unsupported public payment-filter contract tests in `packages/reality-core/tests/finance/test_payment_reads.py`
- [X] T067 [P] [US5] [FR-019] [DR-003] Add lossless unknown-upstream-label versus typed-operational-value tests in `packages/reality-core/tests/test_provenance.py`

### Implementation

- [X] T068 [US5] [FR-024] Expose tenant-scoped proposal rejection and stable replay through a controlled MCP lifecycle tool that requires an explicit authorized-human decision and is excluded from default model selection in `packages/reality-core/src/reality/tools/application.py` and `packages/reality-core/src/reality/mcp/catalog.py`
- [X] T069 [US5] [FR-019] Centralize and enforce the exact public manual operational vocabulary (`sales_order`, `purchase_order`, `sales_invoice`, `supplier_invoice`, `credit_note`, `supplier_credit_note`) during public action preview in `packages/reality-core/src/reality/services/core.py` and derive the enum in `packages/reality-core/src/reality/mcp/catalog.py` without constraining lossless source intake
- [X] T070 [US5] [FR-019] Validate movement types before durable proposal creation in `packages/reality-core/src/reality/services/delivery_actions.py` and `packages/reality-core/src/reality/mcp/catalog.py`
- [X] T071 [US5] [FR-025] [FR-026] Finalize strict invoice-position and payment-filter public read guidance in `packages/reality-core/config/command_catalog.yaml` and `packages/reality-core/config/resource_catalog.yaml`
- [X] T072 [US5] [FR-019] [FR-024] [FR-025] [FR-026] Run the proposal cleanup, invalid-type and filter acceptance story and record evidence in `specs/257-external-agent-closure/quickstart.md`

**Checkpoint**: US5 prevents new audit probes from accumulating as plausible business state.

## Phase 8: Cross-Cutting Qualification and Review

- [X] T073 [P] [FR-030] Run `make docs-generate` and commit the generated English/German Tool Usage pages and `apps/docs/.vitepress/data/tool-usage.json`
- [ ] T074 [P] [FR-030] Run `make docs-catalog-check` and the deployed MCP catalog comparison from `apps/docs/scripts/verify-live-mcp-catalog.py`
- [X] T075 [FR-028] Execute the complete fresh CanisPro public-surface workflow and save a redacted Markdown protocol under `specs/257-external-agent-closure/evidence/`
- [X] T076 [FR-029] Populate the final F1–F13 closure matrix with fixed/guided/regression/accepted/superseded status and exact evidence links in `specs/257-external-agent-closure/evidence/audit-closure.md`
- [X] T077 [DR-001] [DR-002] [DR-003] [DR-004] Review the final story evidence for Source → Evidence → Reality, shortest links, opaque identity and no recomputation in `specs/257-external-agent-closure/evidence/architecture-review.md`
- [X] T078 [DR-005] [DR-006] [DR-007] [DR-008] Review shared-service parity, tenant isolation, owner authority and no-schema evidence in `specs/257-external-agent-closure/evidence/architecture-review.md`
- [X] T079 Run focused tests named in T005–T067, then run Ruff and the complete required backend/PostgreSQL suite; record commands and results in `specs/257-external-agent-closure/evidence/verification.md`
- [X] T080 Run Web contracts, focused browser journeys, `make web-build`, and `cd apps/web && npm run i18n:audit`; record results in `specs/257-external-agent-closure/evidence/verification.md`
- [X] T081 Run `make spec-check`, audit all FR/DR coverage, and rerun `$speckit-analyze`; resolve every CRITICAL finding before marking any completion in `specs/257-external-agent-closure/tasks.md`
- [X] T082 Review the final diff, rollout/rollback and compatibility impact against the Constitution; update durable docs and `docs/V0_CHECKLIST.md` only for evidence-backed completed behavior

## Dependencies

### Phase dependencies

1. Phase 1 is the approval gate.
2. Phase 2 establishes failing shared proofs and blocks all production changes.
3. US1 establishes public discovery/handoff primitives used by US2–US5.
4. US2 and US3 can proceed in parallel after US1 because finance and credit/return use distinct
   services and tests.
5. US4 can proceed after US1 and in parallel with US2/US3; it reuses the handoff but not their
   business services.
6. US5 depends on US1's catalog conventions and US3's invoice-credit read, but proposal rejection
   and type validation can begin independently after Phase 2.
7. Cross-cutting qualification requires all selected story phases complete and green.

### User-story dependency graph

```text
Specification/design gates
          |
Foundational failing proofs
          |
         US1
      /    |    \
    US2   US3   US4
      \    |    /
          US5
           |
Full CanisPro qualification
```

## Parallel Execution Examples

### User Story 1

- T013, T014, T015 and T016 can run in parallel because they target proposal, capability,
  reservation and schema tests separately.
- After their failures are observed, T019, T020 and T021 can proceed in parallel.

### User Story 2

- T027, T028, T029, T030 and T031 are parallel test streams.
- T035 dunning and T036–T037 free supplier invoice are parallel after shared handoff T032.

### User Story 3

- T041–T045 are parallel failing proofs.
- T046 credit context and T049–T050 return behavior can proceed in parallel.

### User Story 4

- T053–T057 are parallel service, domain, demo and Web proofs.
- T058–T059 must be sequential; T060 and T061 can then proceed in parallel.

### User Story 5

- T063–T067 are parallel failing proofs.
- T068 proposal rejection and T069–T070 type validation can proceed in parallel.

## Implementation Strategy

### MVP

Complete Phases 1–3 (US1). This makes the public contract discoverable, supplies truthful
reservation outcomes and establishes release-level schema parity without changing finance or cost
authority.

### Incremental delivery

1. Deliver US1 discovery and verification.
2. Deliver US2 owner-confirmed finance and missing adapters.
3. Deliver US3 canonical credit and return closure.
4. Deliver US4 ordinary-company cost guidance.
5. Deliver US5 proposal/type/filter hygiene.
6. Run the full fresh CanisPro qualification and close F1–F13 only from evidence.

Each increment must pass its independent acceptance story and relevant docs generation before the
next increment is called ready.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001 | T005, T016 | T021, T023 | Implemented; deployed union parity remains under FR-036 |
| FR-002 | T005, T016 | T021, T023 | Implemented; deployed union parity remains under FR-036 |
| FR-003 | T013 | T018, T024 | Complete |
| FR-004 | T014 | T019 | Complete |
| FR-005 | T015 | T020, T024 | Complete |
| FR-006 | T015 | T020, T025 | Complete |
| FR-007 | T026 | T032, T039, T040 | Complete |
| FR-008 | T026 | T032, T040 | Complete |
| FR-009 | T027 | T033, T040 | Complete |
| FR-010 | T027 | T033, T040 | Complete |
| FR-011 | T028 | T034 | Complete |
| FR-012 | T029 | T035, T039, T040 | Complete; fee read-parity observation remains outside this closure slice |
| FR-013 | T030 | T036, T037, T040 | Complete |
| FR-014 | T041 | T046, T051 | Complete |
| FR-015 | T042 | T047 | Implemented; live adapter defect remains under FR-031 |
| FR-016 | T043 | T048, T052 | Implemented; live adapter defect remains under FR-031 |
| FR-017 | T044 | T049, T051 | Complete |
| FR-018 | T045 | T050, T052 | Complete |
| FR-019 | T064, T067 | T069, T070, T072 | Implemented; relationship/lifecycle gap remains under FR-033–FR-034 |
| FR-020 | T053, T057 | T058, T060, T062 | Implemented; qualification gaps remain under FR-032, FR-035 and FR-037 |
| FR-021 | T054, T057 | T059, T062 | Implemented; SC-007 remains open |
| FR-022 | T055 | T060, T062 | Complete |
| FR-023 | T056 | T061, T062 | Complete |
| FR-024 | T063 | T068, T072 | Complete for pending rejection; failed execution remains under FR-034 |
| FR-025 | T041, T065 | T046, T071, T072 | Complete |
| FR-026 | T031, T066 | T038, T071, T072 | Complete |
| FR-027 | T043 | T048, T052 | Complete |
| FR-028 | T006, T012 | T075 | Qualification executed; success criteria failed and follow-up is pending |
| FR-029 | T006, T012 | T076 | Matrix complete with explicit open findings |
| FR-030 | T005, T017 | T022, T023, T073-T074, T100 | Pending deployed catalog check and follow-up regeneration |
| FR-031 | T089 | T095 | Qualified: complete customer-credit arguments retained |
| FR-032 | T090 | T096 | Qualified: unrelated events remain fresh and related evidence invalidates with IDs |
| FR-033–FR-034 | T093 | T099 | Regression tests pass; external qualification found additional handler families still stuck in `executing`, carried to spec 267 FR-001–FR-003 |
| FR-035 | T091 | T097 | Qualified: exact missing movement IDs returned |
| FR-036 | T094 | T100 | Partially qualified: capability branches exist, but deployed top-level tool schema and strict unknown-field behavior remain open in spec 267 FR-008, FR-011–FR-013 |
| FR-037 | T092 | T098 | Qualified for order-backed invoices; free invoices and credit documents remain open in spec 267 FR-009–FR-010 |
| DR-001 | T007, T030 | T036, T077 | Complete; follow-up must preserve it |
| DR-002 | T007 | T077 | Complete; follow-up must preserve it |
| DR-003 | T007, T067 | T036, T077 | Complete; follow-up must preserve it |
| DR-004 | T008 | T077 | Complete; follow-up must preserve it |
| DR-005 | T009 | T078 | Complete; follow-up must preserve it |
| DR-006 | T008 | T078 | Complete; follow-up must preserve it |
| DR-007 | T010, T054 | T032, T059, T078 | Complete; follow-up must preserve it |
| DR-008 | T011 | T078 | Complete; follow-up uses existing storage |

## Phase 9: Convergence

- [X] T083 CRITICAL: Replace the flattened `cost_change_propose` input contract with an operation-discriminated schema that omits fields from unrelated variants, includes the complete `allocate` contract, and add live-wrapper regression coverage for every supported cost operation per FR-001, FR-002, FR-021, SC-002, and SC-007 (contradicts)
- [X] T084 Repair `capability_describe` so every documented public MCP tool identity resolves deterministically to its canonical capability, and prove it through the deployed MCP transport rather than only direct application calls per FR-004 and SC-001 (contradicts)
- [X] T085 Add actionable descendant-location inventory guidance to zero-effect and shortage reservation previews/receipts while preserving exact-location allocation, with regression coverage for parent commitments and stocked child locations per FR-006 (partial)
- [X] T086 Execute the complete fresh-tenant CanisPro qualification with an authenticated active owner performing the documented Web decisions for account initialization, settlement/overpayment, dunning fee, and costing; retain exact proposal reconciliation evidence and the redacted protocol per FR-028, SC-004, SC-005, and SC-007 (partial; qualification executed, SC-007 failed and is carried by T089–T101)
- [X] T087 Make the Web open-items projection catch up after canonical finance writes or explain its exact outstanding source events and affected business records, then prove parity with the live MCP finance reads per DR-005 (partial)

## Phase 10: Qualification Follow-up — Confirmed Open Findings

- [X] T088 Re-run `$speckit-analyze` for FR-031–FR-037 and resolve every CRITICAL finding before starting T089 in `specs/257-external-agent-closure/spec.md`, `specs/257-external-agent-closure/plan.md` and `specs/257-external-agent-closure/tasks.md`
- [X] T089 [P] [US3] [FR-031] Add failing adapter and business-story regressions for complete `sales_credit_record_propose` argument retention, pre-persistence empty-shape refusal and canonical invoice credit in `packages/reality-core/tests/test_ai_mcp.py` and `packages/reality-core/tests/test_unified_invoice_credit.py`
- [X] T090 [P] [US4] [FR-032] Add failing cost-service regressions for unrelated-event stability and affected-only invalidation with named evidence in `packages/reality-core/tests/test_costing_services.py`
- [X] T091 [P] [US4] [FR-035] Add a failing purchase-transfer-sale valuation story for ownership/acquisition continuity and exact incomplete movement IDs in `packages/reality-core/tests/test_inventory_costing_services.py`
- [X] T092 [P] [US4] [FR-037] Add failing invoice, finance-component and contribution stories for stated net/tax/gross, gross-only unavailability and no recomputation in `packages/reality-core/tests/test_unified_invoice_entry.py`, `packages/reality-core/tests/finance/test_components.py` and `packages/reality-core/tests/test_contribution_services.py`
- [X] T093 [P] [US5] [FR-033] [FR-034] Add failing lifecycle regressions for invalid billed relationships, empty credit shapes, rollback, terminal `failed` with `business_effect: none` and genuinely indeterminate `executing` in `packages/reality-core/tests/test_application_tools.py` and `packages/reality-core/tests/test_unified_invoice_credit.py`
- [X] T094 [P] [US1] [FR-036] Add failing live-schema and capability regressions for the complete `cost_change_propose` operation union and purpose-specific shipment movement values in `packages/reality-core/tests/test_ai_mcp.py` and `packages/reality-core/tests/test_capability_guidance.py`
- [X] T095 [US3] [FR-031] Repair the customer-credit public adapter by retaining union-level MCP arguments in `packages/reality-core/src/reality/mcp/server.py`; existing shared credit services reject invalid/empty input before persistence
- [X] T096 [US4] [FR-032] Replace global-sequence receipt-review freshness with a canonical bounded evidence fingerprint and named invalidation scope in `packages/reality-core/src/reality/services/costing.py`
- [X] T097 [US4] [FR-035] Verify preserved acquisition/ownership continuity through internal transfers and return exact incomplete scopes in `packages/reality-core/src/reality/services/inventory_costing.py`
- [X] T098 [US4] [FR-037] Retain source-stated net/tax/gross invoice evidence without derivation in `packages/reality-core/src/reality/services/core.py` and expose it in the public MCP invoice schema
- [X] T099 [US5] [FR-033] [FR-034] Persist effect-free terminal failure for synchronous reviewed-handler refusals while preserving indeterminate execution in `packages/reality-core/src/reality/tools/application.py`
- [X] T100 [US1] [FR-036] Publish operation-specific MCP schema branches and capability guidance in `packages/reality-core/src/reality/mcp/catalog.py`, then regenerate `apps/docs/content/tool-usage/` and `apps/docs/.vitepress/data/tool-usage.json`
- [X] T101 Run the focused T089–T094 regressions, full backend/Web/docs/spec gates and a new fresh-tenant qualification; record results in `specs/257-external-agent-closure/evidence/verification.md` and update `specs/257-external-agent-closure/evidence/audit-closure.md` only from observed public-surface evidence (qualification completed; confirmed follow-up gaps are specified in spec 267)
