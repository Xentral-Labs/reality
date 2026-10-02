# Tasks: Supplier Confirmations, Minimum Quantities and Three-Way Match

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/purchasing-depth.md](contracts/purchasing-depth.md)

Tests come first in each phase where practical.

## Phase 1: Setup

- [x] T001 Clarify the spec with the owner (Clarifications 2026-10-02)
- [x] T002 Plan, research, data model, contract, quickstart
- [x] T003 Tasks

## Phase 2: Confirmed price (FR-001)

- [x] T004 Tests:
  - a revision states a price on a purchase promise, refused on a customer promise;
  - the price in force;
  - the guided invoice takes it;
  - "invoice price differs" compares against it;
  - the review shows both;
  - the migration and downgrade.
- [x] T005 Migration `0117`, `revise_commitment`, `commitment_terms`, the review, the guided invoice and the exception

## Phase 3: Supplier terms (FR-005)

- [x] T006 Tests:
  - set, restate and remove as versions;
  - refusals;
  - the order preview names below-minimum and off-multiple with the suggested quantity;
  - isolation.
- [x] T007 `supplier_item_terms` model and service, preview hints, events, refusals

## Phase 4: Cancellation charge and match (FR-006, FR-002)

- [x] T008 Tests:
  - a charge against a cancelled line raises no finding (with a positive control);
  - the match read: matched, received short, billed at another price, returns and credits, cancelled with charge.
- [x] T009 Exception filters, `services/purchase_match.py`

## Phase 5: Adapters and gates (FR-003)

- [x] T010 Tools, MCP, Web and CLI, with adapter tests
- [x] T011 Catalog gates (data model and field rows, reporting graph, command and action catalogs, tool topics, isolation and counts, events, resource catalog and labels, refusals and translations, coverage matrix, docs generation)

## Phase 6: Web

- [x] T012 Match and confirmed price on the purchase order, the price field in the revision card, terms on the supplier, the hint in purchase entry, translations

## Phase 7: Stories and Guide (FR-004)

- [x] T013 Business stories G09, G06, G12 and I01
- [x] T014 Promote them: Guide catalog, routing check, coverage, roadmap, docs

## Phase 8: Verification

- [ ] T015 Full backend suite and web checks
- [ ] T016 Manual check per `quickstart.md`
- [ ] T017 Review of the diff; fix findings
