# Tasks: Undeliverable, Refused and Lost Parcels

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: Setup

- [x] T001 Clarify the spec (decisions delegated to the recommended options, 2026-10-02)
- [x] T002 Plan
- [x] T003 Tasks

## Phase 2: Failed delivery (FR-001, FR-002, FR-003)

- [x] T004 Tests:
  - undeliverable reopens the promise and brings stock back;
  - a refusal keeps its reason;
  - lost writes the goods off;
  - the claim is settled by a payment;
  - refusals;
  - isolation;
  - review and replay.
- [x] T005 Migration 0125, model, finance role and claim type
- [x] T006 Service, review, tools (application, MCP, CLI, web pass-through)
- [x] T007 Shipment read and web form

## Phase 3: Gates

- [x] T008 Catalogs, refusals, i18n, pinned counts, data model, docs generation

## Phase 4: Stories and Guide (FR-005)

- [x] T009 Business stories D07, D08 and D09
- [x] T010 Promote D07, D08 and D09: Guide catalog, coverage, roadmap, matrix

## Phase 5: Verification

- [ ] T011 Full backend suite and web checks
- [ ] T012 Review of the diff; fix findings
