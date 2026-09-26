---
description: "Requirement-traceable fulfillment safety parity implementation tasks"
---

# Tasks: Fulfillment Safety Parity

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Gate**: Constitution Check passed and no unresolved `[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Tests precede the implementation they prove.

## Phase 1: Specification and Design Gates

- [X] T001 Confirm owner requirements review of `checklists/safety.md` and record its decision without treating it as implementation completion
- [X] T002 Confirm all Constitution Check rows remain PASS in `plan.md`
- [X] T003 Run `$speckit-analyze` over `spec.md`, `plan.md`, and `tasks.md` and resolve every CRITICAL finding
- [X] T004 Run `make spec-check` and correct feature-artifact structure in `specs/275-fulfillment-safety-parity/`

## Phase 2: Foundational Failing Proof and Migration

- [X] T005 [P] [US1] [FR-001,FR-002] Add failing payment-term policy service tests in `packages/reality-core/tests/test_payment_terms.py`
- [X] T006 [P] [US1] [FR-001,FR-002] Add failing API and tenant-isolation assertions in `packages/reality-core/tests/test_master_data_api.py`
- [X] T007 [US1] [FR-001,FR-002] Add migration `packages/reality-core/migrations/versions/0099_payment_term_prepayment.py` with false default and downgrade proof
- [X] T008 [US1] [FR-001,FR-002] Add `PaymentTerm.requires_prepayment` to `packages/reality-core/src/reality/db/core.py`
- [X] T009 [US1] [FR-001,FR-002] Extend create/update/read events and source fallback in `packages/reality-core/src/reality/services/core.py`
- [X] T010 [P] [US1] [FR-001,FR-002] Extend API, CLI and application-tool arguments in `packages/reality-core/src/reality/web/api.py`, `packages/reality-core/src/reality/cli/app.py`, and `packages/reality-core/src/reality/tools/application.py`
- [X] T011 [P] [US1] [FR-001,FR-002] Extend MCP payment-term schemas in `packages/reality-core/src/reality/mcp/catalog.py`
- [X] T012 [P] [US1] [FR-001,FR-002] Expose the explicit policy in the existing payment-term editor/read model under `apps/web/src/`

## Phase 3: User Story 1 — Unpaid prepayment orders cannot ship

**Independent test**: A stocked and reserved prepayment order refuses every dispatch before
qualifying allocation, counts partial/reversed/unrelated evidence correctly, and ships after full
allocation; an unpaid net-term control remains shippable.

- [X] T013 [P] [US1] [FR-003,FR-004,FR-005,FR-006] Add failing qualifying-allocation and blocker tests in `packages/reality-core/tests/test_fulfillment_readiness.py`
- [X] T014 [P] [US1] [FR-004] Add failing cross-tenant, cross-party, cross-currency, reversed and ambiguous-attribution tests in `packages/reality-core/tests/test_fulfillment_readiness.py`
- [X] T015 [US1] [FR-003,FR-004,FR-005,FR-006] Implement batch-capable derived payment readiness in `packages/reality-core/src/reality/services/fulfillment_readiness.py`
- [X] T016 [US1] [FR-003,FR-004] Return required/received/remaining amounts and opaque evidence links from `packages/reality-core/src/reality/services/fulfillment_readiness.py`
- [X] T017 [US1] [FR-005,FR-006] Enforce payment readiness in shipment preparation and packaged execution in `packages/reality-core/src/reality/services/shipment_actions.py` and the shared shipment execution service
- [X] T018 [US1] [FR-005] Add zero-effect assertions for refused shipment/package/movement creation in `packages/reality-core/tests/test_shipment_actions.py`

## Phase 4: User Story 2 — One explainable fulfillment decision serves every surface

**Independent test**: Application, projection, Web/Chat tool and MCP return equivalent readiness;
relevant payment/hold changes retire review tokens and unrelated events do not.

- [X] T019 [P] [US2] [FR-007,FR-008,FR-009,FR-010] Add failing shared-readiness and multi-blocker tests in `packages/reality-core/tests/test_fulfillment_readiness.py` and `packages/reality-core/tests/test_materialized_projections.py`
- [X] T020 [P] [US2] [FR-011,FR-012] Add failing payment/hold/reversal review-token freshness tests in `packages/reality-core/tests/test_shipment_actions.py`
- [X] T021 [P] [US2] [FR-008,FR-009] Add failing application/MCP normalized parity tests in `packages/reality-core/tests/test_ai_mcp.py` and `packages/reality-core/tests/test_mcp_read_contract.py`
- [X] T022 [US2] [FR-007,FR-008,FR-009] Integrate the shared service into fulfillment queue/blocker projection building in `packages/reality-core/src/reality/services/projections.py`
- [X] T023 [US2] [FR-009] Add a canonical application read/tool result for readiness or extend the existing fulfillment reads in `packages/reality-core/src/reality/tools/application.py`
- [X] T024 [US2] [FR-010,FR-011,FR-012] Include canonical readiness basis in dispatch review and validation in `packages/reality-core/src/reality/services/shipment_actions.py`
- [X] T025 [US2] [FR-008,FR-009] Serialize the shared result without alternate rules in `packages/reality-core/src/reality/web/api.py` and `packages/reality-core/src/reality/mcp/catalog.py`

## Phase 5: User Story 3 — Proposal failures are truthful and recoverable

**Independent test**: Duplicate invoice posting and deterministic shipment refusal become terminal
failed with verified no effect; an injected unexpected/unknown outcome remains executing.

- [X] T026 [P] [US3] [FR-013,FR-014] Add failing deterministic finance, reviewed and unreviewed proposal failure tests in `packages/reality-core/tests/test_application_tools.py`
- [X] T027 [P] [US3] [FR-014] Add an unknown-outcome control that must remain executing in `packages/reality-core/tests/test_application_tools.py`
- [X] T028 [P] [US3] [FR-015] Add failing MCP status and Web proposal-detail parity assertions in `packages/reality-core/tests/test_ai_mcp.py` and `packages/reality-core/tests/test_proposal_review_parity.py`
- [X] T029 [US3] [FR-013,FR-014] Centralize known-no-effect failure finalization around proposal execution in `packages/reality-core/src/reality/tools/application.py`
- [X] T030 [US3] [FR-013,FR-015] Store a structured failure receipt and expose terminal detail/verification in `packages/reality-core/src/reality/tools/application.py`, `packages/reality-core/src/reality/services/delivery_actions.py`, and `packages/reality-core/src/reality/services/shipment_actions.py`
- [X] T031 [US3] [FR-015] Expose equivalent failed lifecycle and safe-next-action fields through existing Web/MCP proposal status adapters in `packages/reality-core/src/reality/web/api.py` and `packages/reality-core/src/reality/mcp/catalog.py`

## Phase 6: User Story 4 — Shipment tools are executable from published contracts

**Independent test**: A client builds every supported shipment request from `tools/list` alone;
invalid fields/enums refuse before review and capability description resolves canonical names.

- [X] T032 [P] [US4] [FR-016,FR-017] Add failing serialized MCP `tools/list` schema tests for all shipment purposes in `packages/reality-core/tests/test_mcp_http_runtime.py` and `packages/reality-core/tests/test_ai_mcp.py`
- [X] T033 [P] [US4] [FR-017] Add failing unknown nested/top-level field and invalid enum preparation tests in `packages/reality-core/tests/test_shipment_tools.py`
- [X] T034 [P] [US4] [FR-018] Add failing canonical `capability_describe` shipment guidance tests in `packages/reality-core/tests/test_tool_catalog.py`
- [X] T035 [US4] [FR-016,FR-017] Share purpose/movement vocabulary between MCP schema and executable validation in `packages/reality-core/src/reality/mcp/catalog.py`, `packages/reality-core/src/reality/domain/shipments.py`, and `packages/reality-core/src/reality/services/shipment_actions.py`
- [X] T036 [US4] [FR-018] Correct capability name resolution and shipment prerequisites/refusals/verifications in `packages/reality-core/src/reality/tool_catalog.py` and `packages/reality-core/config/resource_catalog.yaml`
- [X] T037 [US4] [FR-019] Run `make docs-generate` and commit affected generated pages under `apps/docs/content/tool-usage/` and `apps/docs/.vitepress/data/tool-usage.json`
- [X] T038 [US4] [FR-019] Run `make docs-catalog-check` and fix any executable/catalog drift

## Phase 7: Cross-Surface Acceptance Story

- [X] T039 [P] [US1] [FR-020] Add the failing 30-receive/two-order/prepayment business story in `packages/reality-core/tests/scenarios/test_fulfillment_safety_parity.py`
- [X] T040 [P] [US2] [FR-021] Add Web/application versus MCP normalized result assertions to `packages/reality-core/tests/scenarios/test_fulfillment_safety_parity.py`
- [X] T041 [US1] [FR-020] Prove no unpaid shipment effect, payment-before-shipment ordering, final physical 10, reserved 0 and invoice open 0 in `packages/reality-core/tests/scenarios/test_fulfillment_safety_parity.py`
- [X] T042 [US2] [FR-021] Run the focused proof from `specs/275-fulfillment-safety-parity/quickstart.md` and record exact commands/results there

## Final Phase: Cross-Cutting Review

- [X] T043 Update durable contracts in `docs/features/order_to_cash.md`, `docs/features/shipments.md`, and the applicable payment-term/master-data contract
- [X] T044 Run `make spec-check` and audit every FR-001–FR-021 against tests and implementation
- [X] T045 Run focused Ruff and pytest suites for every changed backend module
- [X] T046 Run the complete PostgreSQL backend test suite required by `make test`
- [X] T047 Run frontend tests/build, `npm run i18n:audit`, and `make web-build`
- [X] T048 Review migration upgrade/downgrade, false-default compatibility and tenant isolation
- [X] T049 Review the final diff against Source → Evidence → Reality, shortest links, no recomputation and transport parity
- [X] T050 Mark tasks complete only for green evidence and record any remaining limitation in `quickstart.md`

## Dependencies

```text
Design gates
  → Payment-term policy foundation
  → US1 prepayment enforcement
      → US2 shared readiness and review freshness
      → US3 proposal lifecycle (independent after foundation, but integrated before story)
      → US4 public contract (parallel after foundation)
  → cross-surface acceptance story
  → full verification and review
```

Parallel opportunities:

- T005–T006 test different adapters before T007–T012.
- T013–T014 are parallel failing proofs before T015.
- T019–T021 cover service, freshness and adapter parity independently.
- T026–T028 cover separate proposal lifecycle surfaces.
- T032–T034 cover serialization, validation and discovery separately.
- T039–T040 can prepare separate halves of the acceptance story before consolidation.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) |
|---|---|---|
| FR-001–FR-002 | T005–T006 | T007–T012 |
| FR-003–FR-004 | T013–T014 | T015–T016 |
| FR-005–FR-006 | T013, T018 | T015, T017 |
| FR-007–FR-009 | T019, T021 | T022–T023, T025 |
| FR-010 | T018–T019 | T017, T024 |
| FR-011–FR-012 | T020 | T024 |
| FR-013–FR-015 | T026–T028 | T029–T031 |
| FR-016–FR-017 | T032–T033 | T035 |
| FR-018 | T034 | T036 |
| FR-019 | T032 | T037–T038 |
| FR-020 | T039, T041 | T015–T17, T022–T24, T029–T31 |
| FR-021 | T040, T042 | T023–T25, T031, T035–T38 |

## Implementation Strategy

The minimum safe slice is US1 plus the payment-term foundation: an unpaid prepayment order is
blocked in shared shipment services. It is not release-complete until US2 proves adapter parity,
US3 makes refusal recovery truthful, US4 makes MCP requests executable from their contract, and the
cross-surface story reconciles the entire flow.
