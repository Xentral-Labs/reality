# Tasks: Ship-Complete and No-Backorder Rules

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/delivery-rules.md](contracts/delivery-rules.md)

Tests come first in each phase where practical.

## Phase 1: Setup

- [x] T001 Clarify the spec with the owner (Clarifications 2026-10-02)
- [x] T002 Plan, research, data model, contract, quickstart
- [x] T003 Tasks

## Phase 2: Rule record (FR-001)

- [x] T004 Tests:
  - schema checks and the migration downgrade;
  - stating a rule for a customer and for an order;
  - the effective rule (order over customer over default);
  - refusals;
  - tenant isolation.
- [x] T005 Migration `0112`, the `DeliveryRule` model, `services/delivery_rules.py`, the event and the refusals with translations

## Phase 3: Readiness and shipments (FR-002)

- [x] T006 Tests:
  - readiness blocker under ship complete, with no rule as control;
  - every shipment path refuses a partial shipment and accepts a complete one;
  - a lifted order ships in parts;
  - importers are not refused;
  - cancelled and fulfilled lines count as complete.
- [x] T007 Readiness blocker, `require_delivery_rule` on every person-facing path, the queue label

## Phase 4: Findings (FR-005)

- [x] T008 Tests: both classes, with positive controls, next steps and invalidation
- [x] T009 `order_waiting_for_completeness` and `backorder_against_rule`, their catalog, reference and resource entries

## Phase 5: Adapters and gates (FR-003)

- [x] T010 Tools, MCP, Web and CLI, with adapter tests and tenant isolation
- [x] T011 Catalog gates:
  - data model and docs field rows;
  - reporting graph;
  - command and action catalogs, tool topics;
  - isolation catalog and counts;
  - events and counts;
  - coverage matrix and docs generation.

## Phase 6: Web

- [x] T012 Lieferregel on the customer and the order, the blocker label, the two findings, translations, browser fixtures

## Phase 7: Stories and Guide (FR-004)

- [x] T013 Business stories B10 and M06
- [x] T014 Promote the journeys: Guide catalog, Guide tests, coverage, roadmap, docs

## Phase 8: Verification

- [ ] T015 Full backend suite and web checks
- [x] T016 Manual check per `quickstart.md` on an isolated stack, in German
  - Komplettlieferung for Müller GmbH: the review listed both open orders, and the customer then showed it "am Kunden festgelegt". SO-P306-1 reported "Auftrag wartet auf Vollständigkeit", readiness named `ship_complete_incomplete`, and a shipment of the ready wheels was refused with the order named.
  - Lifting the rule from the finding ("Teillieferung erlaubt" for the order) cleared the blocker, and the shipment was accepted.
  - Keine Rückstände for Kleinteile AG: after 6 of 10 screws shipped, "Rückstand gegen Kundenregel" offered "Offenen Rest stornieren" with the rule's reason prefilled. The confirmed cancellation cancelled the line.
  - Fixed during the check: the default rule's source label was untranslated.
- [x] T017 Review of the diff; fix findings
  - A line split across movements (two warehouses, serial units) no longer fails per movement: only the shipment as a whole answers to the rule.
  - The fulfillment queue derives the rule's blocker once per order from the lines it already holds, not through readiness per line.
  - A quantity that is no number keeps the movement's own refusal.
  - A corrected shipment does not count for no backorders.
  - Replaying a confirmation is checked before the review comparison.
  - An order kept back by a hold is not waiting for completeness.
  - The order's customer is `document.party_id`.
  - The web cards withdraw on unmount and do not prepare twice.
  - The reference catalog reason for `Commitment.document_id` names the delivery rule.
  - Tests: positive controls for the isolation and single-line cases.
