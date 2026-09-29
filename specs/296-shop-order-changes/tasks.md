# Tasks: Shop Order Changes and Refunds

**Input**: Design documents from `/specs/296-shop-order-changes/`

**Tests**: Written before their implementation task and observed failing where practical. Every "no finding" assertion has a positive control; every refusal and held version asserts its code. Paths are relative to the repository root; `core/` means `packages/reality-core/`.

## Phase 1: Specification and Design Gates

- [x] T001 Record the approved scope and the four clarifications in `specs/296-shop-order-changes/spec.md`
- [x] T002 Record design decisions R1–R7 in `specs/296-shop-order-changes/research.md`
- [x] T003 Record the records used in `specs/296-shop-order-changes/data-model.md` and the contract in `specs/296-shop-order-changes/contracts/shop-order-changes.md`
- [x] T004 Complete the Constitution Check in `specs/296-shop-order-changes/plan.md`

## Phase 2: Foundational

- [x] T005 [FR-001] [FR-004] Failing unit tests for `stated_lines` (current_quantity, quantity, removed line) and for the classification table of research R4, one case per row with its code, in `core/tests/test_shop_order_changes.py`
- [x] T006 [FR-001] [FR-004] Implement `order_for_source`, `stated_lines` and `classify_order_version` in `core/src/reality/services/shop_order_changes.py`; give `ShopifyUpdateNeedsReview` its codes and write them in `process_import_job`
- [x] T007 [DR-003] Check the policy for interpretation: business companies need no admission, practice companies already admit `revise_commitment` and `cancel_commitment` (`_PRACTICE_APP_OPERATIONS`), and demo intake does not use this interpreter; `announce_customer_return` for refunds is checked in T013

## Phase 3: Order changes (A16, L05, A09)

- [x] T008 [P] [FR-001] [FR-009] Failing interpretation tests: a lowered open line revises its promise and releases reservation above it; lowered to what shipped closes the rest; a removed line and a full cancellation with nothing shipped cancel; a note-only change applies nothing (positive control: the same version with a lower quantity does); replay and a stale older version change nothing, in `core/tests/test_shop_order_changes.py`
- [x] T009 [P] [FR-003] [FR-004] Failing hold tests: cancellation after shipment, below shipped, increase, new line, price, address, closed line, several reservations, and a mixed version that also lowers a line (nothing applied), each with its code, in `core/tests/test_shop_order_changes.py`
- [x] T010 [FR-001] [FR-003] [FR-004] [FR-009] Implement `apply_order_version` and call it from `_shopify_interpretation` for version > 1 in `core/src/reality/services/core.py`
- [x] T011 [FR-004] Update `core/tests/test_shopify_update_guard.py`, `core/tests/test_shopify_and_explain.py` and the P04 story in `core/tests/scenarios/test_catalog_sources.py` to the narrowed guard; note in `specs/081-shopify-update-guard/spec.md` that spec 296 narrows FR-002

## Phase 4: Refunds (L04, F12)

- [x] T012 [P] [FR-002] [FR-007] Failing tests: refunds split from an order version into their own sources, deduplicated across versions; a refund records one `sales_refund` document with stated amount and lines linked to the order lines and no ledger entry; a shipped `return` line is announced citing the refund (positive control), `no_restock` announces nothing; a refund before its order fails with `shop_refund_order_missing` and succeeds on retry; an unknown line id waits with `shop_refund_line_unknown`, in `core/tests/test_shop_refunds.py`
- [x] T013 [FR-002] [FR-007] Implement `split_refunds` and `interpret_shop_refund` in `core/src/reality/services/shop_refunds.py`, register `("shopify", "refund")`, admit `announce_customer_return` for practice companies, and add the reference-catalog exemption for refund lines (they name the Shopify line through `source_line_id`, never `billed_document_line_id`; no document-type registry exists)
- [x] T014 [FR-002] The order inspector lists its refunds in `core/src/reality/web/api.py`, with a test

## Phase 5: Unknown items (A17)

- [x] T015 [P] [FR-008] Failing tests: an order with one unknown SKU interprets the known lines and keeps the unknown one without an item or promise; `order_line_item_unknown` reports it (positive control) and clears after assignment; the reviewed assignment creates the promise; each refusal code, in `core/tests/test_order_line_items.py` and `core/tests/operational_exceptions/test_derivation.py`
- [x] T016 [FR-008] Keep unknown lines in `_shopify_interpretation`; implement `preview_item_assignment` and `assign_line_item` in `core/src/reality/services/order_line_items.py`, the review in `core/src/reality/services/delivery_actions.py`, and the exception class in `core/src/reality/services/exceptions.py` with every pinned list; rewrite `test_source_survives_interpretation_failure` (now a non-positive quantity) and the first-version retry test (now a one-time failure), which pinned the old unknown-SKU failure

## Phase 6: Surfaces

- [x] T017 [P] [FR-005] Failing adapter tests: MCP propose/confirm with a strict schema, Web prepare/confirm, CLI propose/confirm/help, tenant isolation, in `core/tests/test_shop_order_change_adapters.py`
- [x] T018 [FR-005] MCP tool, CLI commands, Web pass-through; catalogs (`command_catalog.yaml`, `tool_catalog.json`, `action_discovery.json` and its Web fixture, `resource_catalog.yaml`, `service_refusals.json` with de/nl/es, `refusal_ratchet.json`, `business_event_catalog.yaml`, isolation catalog and pinned counts; `resolution_guidance.json` covers cost and delivery blockers only, so the next step for `cancelled_after_shipment` is named in the held summary)
- [x] T019 [FR-004] [FR-005] Web: a held version's source record names every reason and the next step ("Why it waits"; the Web shows no import-job list); the refunds section on the order; "Assign item" on the `order_line_item_unknown` finding (`apps/web/src/unified/OrderLineItemCard.tsx`); labels in four languages; i18n audit, build and action-discovery contract tests

## Phase 7: Journeys and Verification

- [x] T020 [FR-006] [SC-001] Business stories A16, L05, A09, L04, F12 and A17 through the intake and reviewed tools in `core/tests/scenarios/test_catalog_sources.py`
- [x] T021 [FR-006] [SC-002] Promote the proven journeys in `core/config/business_journey_catalog.yaml` with evidence and specific keywords; check neighbour questions (P04, F07, L01, A01 keep theirs); correct the stale P04 and A10 limitations; update `docs/scenarios/coverage.md` and the roadmap. The L05 story found that a removed line left out again was held as `closed_line_changed`; fixed with a regression test
- [ ] T022 `make docs-generate`, `make docs-catalog-check`, `make spec-check lint`, the full backend suite from a clean worktree and the Web checks
- [ ] T023 Manual check per `quickstart.md` on an isolated stack
- [ ] T024 Review of the diff; fix findings
