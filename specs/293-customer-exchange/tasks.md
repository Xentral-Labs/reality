# Tasks: Customer Exchange

**Input**: Design documents from `/specs/293-customer-exchange/`

**Tests**: Written before their implementation task and observed failing where practical. Every "no finding" assertion has a positive control; every refusal asserts its code. Paths are relative to the repository root; `core/` means `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Record the approved scope and both clarifications in `specs/293-customer-exchange/spec.md`
- [x] T002 Record design decisions R1–R7 in `specs/293-customer-exchange/research.md`
- [x] T003 Define `customer_exchange` in `specs/293-customer-exchange/data-model.md` and the tool contract in `specs/293-customer-exchange/contracts/customer-exchange.md`
- [x] T004 Complete the Constitution Check in `specs/293-customer-exchange/plan.md`

## Phase 2: Foundational — Schema and Record

- [x] T005 [FR-001] [DR-002] Add a failing migration and model parity test for `customer_exchange` (checks, uniques, FK indexes) in `core/tests/test_customer_exchanges.py`
- [x] T006 [DR-002] Add the `CustomerExchange` model in `core/src/reality/db/core.py` and migration `core/migrations/versions/0101_customer_exchanges.py`
- [x] T007 [DR-004] Register the table in `core/config/data_model.yaml`, the `operational_edge_workflows` deferral in `core/tests/test_reporting_graph_coverage.py` (as `supply_assignment`; analytics grain needs its own design), `core/tests/test_schema_indexes.py` `later_tables` and the stage pattern in `core/src/reality/services/interactions.py`

## Phase 3: User Story 1 — Exchange a returned unit (P1)

**Goal**: A received return is exchanged for the same or another item; nothing is owed a credit or an invoice.

**Independent Test**: `pytest core/tests/test_customer_exchanges.py core/tests/operational_exceptions/test_derivation.py -k "exchange and not announcement"`

- [x] T008 [P] [US1] [FR-001–FR-004] [FR-009] Failing service tests: exchange recorded after a return, other-variant replacement, replacement promise to the same customer at amount 0 without a document, no ledger entry, and each coded refusal from the contract, in `core/tests/test_customer_exchanges.py`
- [x] T009 [P] [US1] [FR-005] [FR-006] Failing derivation tests: return owed a credit before the exchange (positive control), not after; shipped replacement not unbilled; partial exchange plus partial credit; later credit reported as credited and not returned, in `core/tests/operational_exceptions/test_derivation.py`
- [x] T010 [US1] [FR-001–FR-004] [FR-009] Implement `preview_customer_exchange`, `record_customer_exchange` and `customer_exchange_detail` in `core/src/reality/services/customer_exchanges.py`
- [x] T011 [US1] [FR-005] Read exchanges once per evaluation through the shared `_cached` evaluation cache (no change to `core/src/reality/services/exception_inputs.py` needed) and subtract exchanged-and-arrived quantities on the customer side of `_return_exceptions` in `core/src/reality/services/exceptions.py`
- [x] T012 [US1] [FR-010] Failing review tests (effect states delivery, quantities, replacement and `money_moves: false`; stale review refused; replay idempotent), then implement `core/src/reality/services/customer_exchange_actions.py` and wire it into `core/src/reality/services/delivery_actions.py`
- [x] T013 [US1] [FR-008] Failing test and implementation: a replacement cancelled before shipping ends the settlement; a partly shipped then cancelled replacement settles its shipped share, in `core/tests/test_customer_exchanges.py` and `core/src/reality/services/customer_exchanges.py`

## Phase 4: User Story 2 — Advance exchange (P1)

**Goal**: A replacement leaves against an announcement; a missing return stays visible.

**Independent Test**: `pytest core/tests/test_customer_exchanges.py core/tests/operational_exceptions/test_derivation.py -k announcement`

- [x] T014 [P] [US2] [FR-007] Failing derivation tests: advance exchange before arrival (announcement outstanding and naming the replacement, no credit finding), after arrival (nothing open), overdue (announced return not arrived names the exchange), in `core/tests/operational_exceptions/test_derivation.py`
- [x] T015 [P] [US2] [FR-007] Failing test: withdrawn announcement after a shipped advance replacement reports `exchange_without_return`, with a positive control, in `core/tests/operational_exceptions/test_derivation.py`
- [x] T016 [US2] [FR-007] Name exchanges in `_announced_return_not_arrived_exceptions` and add `exchange_without_return` (derivation, `CLASS_ORDER`, `DERIVATION_REGISTRY`) in `core/src/reality/services/exceptions.py` and `core/config/operational_exception_catalog.yaml`

## Phase 5: User Story 3 — Explain an exchange (P2)

**Goal**: Both sides and the decision link to each other.

**Independent Test**: `pytest core/tests/test_customer_exchanges.py -k explain`

- [x] T017 [P] [US3] [FR-012] Failing tests: return movement explanation names exchange and replacement; replacement shipment and delivery case name exchange and returned delivery; decision history shows actor, time and reason, in `core/tests/test_customer_exchanges.py`
- [x] T018 [US3] [FR-012] Implement links in `core/src/reality/services/movement_explanations.py` and `core/src/reality/services/delivery_reads.py`; emit `exchange.recorded` with the proposal as action

## Phase 6: Adapters — Web, MCP/Chat, CLI (US1, US2)

**Goal**: The same reviewed tool on every surface (FR-011).

**Independent Test**: `pytest core/tests/test_customer_exchange_adapters.py`; `node --test apps/web/scripts/action-discovery.test.mjs`

- [ ] T019 [P] [FR-011] Failing adapter tests: Web prepare/review/confirm and read, MCP propose and read with strict schemas, CLI read/propose/confirm and help, cross-tenant refusal, in `core/tests/test_customer_exchange_adapters.py`
- [ ] T020 [FR-011] Register `customer_exchange_record` and `customer_exchange` in `core/src/reality/tools/application.py` (including the `_action_id` set), `core/src/reality/mcp/catalog.py`, `core/src/reality/cli/app.py` and `core/src/reality/web/api.py` (tool literal, read endpoint, sandbox read allowlist)
- [ ] T021 [FR-011] Add the Web exchange form and Warehouse return-row action in `apps/web/src/unified/ExchangeCard.tsx`, `ActionCard.tsx`, `actionDiscovery.ts` and `WarehousePage.tsx`; explanation labels in `MovementExplanation.tsx`; de/nl/es in `apps/web/src/localization.tsx`

## Phase 7: Catalogs and Completeness Gates

- [ ] T022 [DR-004] Declare the command, agent coverage and read capability guidance in `core/config/command_catalog.yaml`; topics in `core/config/tool_catalog.json`; `core/config/action_discovery.json`; mirror in `apps/web/scripts/fixtures/action-reference.json`
- [ ] T023 [DR-004] Register refusals in `core/config/service_refusals.json` (with de/nl/es) and modules in `core/config/refusal_ratchet.json`; tools and service operations in `core/config/tenant_isolation_catalog.yaml`; the event in `core/config/business_event_catalog.yaml`; the service and event modules in `core/src/reality/catalogs.py`; `record_customer_exchange` in `core/src/reality/services/tenant_policy.py` practice operations and `core/src/reality/services/business_locks.py`; the subject in `TIMELINE_SILENT_SUBJECTS` in `core/src/reality/services/projections.py`
- [ ] T024 [DR-004] Add the table and German command label to `core/config/resource_catalog.yaml`; raise the pinned command, event and discovered-operation counts in `core/tests/test_application_catalog.py`
- [ ] T025 Update the exception descriptions for `returned_not_credited`, `credited_not_returned`, `announced_return_not_arrived` and `exchange_without_return` in `core/config/operational_exception_catalog.yaml` and `docs/features/operational_exceptions.md`

## Phase 8: User Story 4 — The Guide states exchanges (P2)

- [ ] T026 [US4] [FR-013] Replace the pinned gap test with the F07 exchange story (recorded exchange, no finding, no money, positive controls) in `core/tests/scenarios/test_catalog_stock_and_returns.py`
- [ ] T027 [US4] [FR-013] Promote F07 in `core/config/business_journey_catalog.yaml` (limitation: price differences go through invoices and credit notes), move F07 into `PROVEN_BY_STORY` in `core/tests/test_business_journey_catalog.py`, update `docs/scenarios/coverage.md`
- [ ] T028 [US4] Run `make docs-generate` and commit the generated Docs, Guide and product advisor knowledge

## Final Phase: Verification and Review

- [ ] T029 Add the new test files and `` `customer_exchange` `` to `docs/SPEC_COVERAGE_MATRIX.md`
- [ ] T030 Run the completeness gates from `specs/293-customer-exchange/quickstart.md`, Ruff (`--no-cache`), `make spec-check`, `make docs-catalog-check`, the Web i18n audit and action-discovery tests
- [ ] T031 Run the complete backend suite (CI shards are the evidence) and the manual Web check in `specs/293-customer-exchange/quickstart.md` on an isolated stack
- [ ] T032 Review the diff against FR-001–FR-013, DR-001–DR-005 and the Constitution; confirm supplier return classes and spec 079 regressions are unchanged

## Dependencies

- T005–T007 precede everything else.
- US1 (T008–T013) precedes US2 (T014–T016), which reuses the service and derivation input.
- T017–T018 need T010. T019–T021 need T012. T022–T025 go with T020 (the gates fail until then).
- T026–T028 need US1, US2 and T020. T029–T032 close.

## Requirement Coverage

| Requirement | Test task(s) | Implementation task(s) | Status |
|---|---|---|---|
| FR-001–FR-004 | T005, T008 | T006, T010 | Pending |
| FR-005, FR-006 | T009 | T011 | Pending |
| FR-007 | T014, T015 | T016 | Pending |
| FR-008 | T013 | T013 | Pending |
| FR-009 | T008 | T010 | Pending |
| FR-010 | T012 | T012 | Pending |
| FR-011 | T019 | T020, T021 | Pending |
| FR-012 | T017 | T018 | Pending |
| FR-013 | T026 | T027, T028 | Pending |
| DR-001–DR-003 | T005, T009 | T006, T011 | Pending |
| DR-004 | T019, T030 | T007, T022–T024 | Pending |
| DR-005 | T032 | — | Pending |

## MVP

Phases 2–3 and T019–T024: a received return exchanged through all surfaces with the two false findings gone.
