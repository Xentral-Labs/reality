# Tasks: Customer Item Numbers

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/customer-item-numbers.md](contracts/customer-item-numbers.md)

Tests come first in each phase where practical.

## Phase 1: Setup

- [x] T001 Clarify the spec with the owner (Clarifications 2026-10-02)
- [x] T002 Plan, research, data model, contract, quickstart
- [x] T003 Tasks

## Phase 2: Mapping (FR-001)

- [x] T004 Tests:
  - schema checks and the migration downgrade;
  - set and restate as versions, remove;
  - resolution by customer, case and spaces;
  - the same number at another customer;
  - refusals;
  - tenant isolation.
- [x] T005 Migration `0114`, the model, `services/customer_item_numbers.py`, the events, the refusals with translations

## Phase 3: Order entry and import (FR-002, FR-005)

- [x] T006 Tests:
  - manual entry by number, unknown and conflicting refused;
  - the import resolves by number, keeps an unknown line and reports it;
  - assigning with remember-for-customer;
  - the stated number on order, delivery and invoice reads;
  - a changed mapping leaves past lines.
- [x] T007 Order entry, file import, assignment and reads

## Phase 4: Adapters and gates (FR-003)

- [x] T008 Tools, MCP, Web and CLI, with adapter tests
- [x] T009 Catalog gates:
  - data model and docs field rows;
  - reporting graph;
  - command and action catalogs, tool topics;
  - isolation catalog and counts;
  - events;
  - resource catalog and labels;
  - coverage matrix and docs generation.

## Phase 5: Web

- [ ] T010 Kundenartikelnummern on the customer, the number on order and invoice lines, the entry field, remember on assignment, translations, browser fixtures

## Phase 6: Stories and Guide (FR-004)

- [ ] T011 Business story M02 (manual entry and import with an unknown number)
- [ ] T012 Promote M02: Guide catalog, Guide tests, coverage, roadmap, docs

## Phase 7: Verification

- [ ] T013 Full backend suite and web checks
- [ ] T014 Manual check per `quickstart.md`
- [ ] T015 Review of the diff; fix findings
