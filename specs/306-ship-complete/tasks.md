# Tasks: Ship-Complete and No-Backorder Rules

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/delivery-rules.md](contracts/delivery-rules.md)

Tests come first in each phase where practical.

## Phase 1: Setup

- [x] T001 Clarify the spec with the owner (Clarifications 2026-10-02)
- [x] T002 Plan, research, data model, contract, quickstart
- [x] T003 Tasks

## Phase 2: Rule record (FR-001)

- [ ] T004 Tests:
  - schema checks and the migration downgrade;
  - stating a rule for a customer and for an order;
  - the effective rule (order over customer over default);
  - refusals;
  - tenant isolation.
- [ ] T005 Migration `0112`, the `DeliveryRule` model, `services/delivery_rules.py`, the event and the refusals with translations

## Phase 3: Readiness and shipments (FR-002)

- [ ] T006 Tests:
  - readiness blocker under ship complete, with no rule as control;
  - every shipment path refuses a partial shipment and accepts a complete one;
  - a lifted order ships in parts;
  - importers are not refused;
  - cancelled and fulfilled lines count as complete.
- [ ] T007 Readiness blocker, `require_delivery_rule` on every person-facing path, the queue label

## Phase 4: Findings (FR-005)

- [ ] T008 Tests: both classes, with positive controls, next steps and invalidation
- [ ] T009 `order_waiting_for_completeness` and `backorder_against_rule`, their catalog, reference and resource entries

## Phase 5: Adapters and gates (FR-003)

- [ ] T010 Tools, MCP, Web and CLI, with adapter tests and tenant isolation
- [ ] T011 Catalog gates:
  - data model and docs field rows;
  - reporting graph;
  - command and action catalogs, tool topics;
  - isolation catalog and counts;
  - events and counts;
  - coverage matrix and docs generation.

## Phase 6: Web

- [ ] T012 Lieferregel on the customer and the order, the blocker label, the two findings, translations, browser fixtures

## Phase 7: Stories and Guide (FR-004)

- [ ] T013 Business stories B10 and M06
- [ ] T014 Promote the journeys: Guide catalog, Guide tests, coverage, roadmap, docs

## Phase 8: Verification

- [ ] T015 Full backend suite and web checks
- [ ] T016 Manual check per `quickstart.md`
- [ ] T017 Review of the diff; fix findings
