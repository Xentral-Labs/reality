# Feature Specification: Shared Inventory Observations

**Feature Branch**: `codex/journey-consistency`
**Created**: 2026-10-02
**Language**: English
**Status**: Implemented and verified; human PR review pending
**Input**: Fix the reviewed inventory derivation and projection catalog gaps. The owner approved this scope on 2026-10-02.

## Context and Intent

### Problem

The Web inventory register derives inventory independently of the shared inventory service. In particular, it counts original supplier quantities instead of the effective outstanding promises. Projection descriptions also omit blocked stock.

### Non-Goals

- Splitting `services/exceptions.py` or redesigning inventory allocation.
- New tables, commands, projections, scheduling or stock policies.
- Fee receivables, which need their own finance specification.

## User Scenarios & Testing

### User Story 1 - One inventory answer (Priority: P1)

An operator sees the same stock position in Web, tools and projections.

**Independent Test**: Compare all six quantities after a receipt, reservation, block, partial release, supplier receipt, revision and cancellation.

**Acceptance Scenarios**:

1. **Given** physical 20, reserved 4 and blocked 3, **When** inventory is read on each surface, **Then** available is 13 everywhere.
2. **Given** a supplier promise revised from 12 to 10 with 3 received, **When** inventory is read, **Then** incoming is 7, not 12 or 10.
3. **Given** stock at two locations and another tenant, **When** a location is selected, **Then** only that location contributes and the other tenant contributes nothing.
4. **Given** numeric filters, sorting and pagination, **When** the register is read, **Then** filtering and ordering use these same derived quantities before pagination.

### User Story 2 - Accurate executable reference (Priority: P2)

An implementer can identify the inputs and outputs of inventory and fulfillment projections from the executable catalog.

**Independent Test**: Catalog assertions and regenerated reference pages name blocked stock and effective incoming quantities.

**Acceptance Scenarios**:

1. **Given** projections read active stock blocks, **When** the reference is generated, **Then** the relevant inputs and exposed outputs describe them accurately.

### Edge Cases

- Revisions, cancellations, correction movements and over-receipts must not restore incoming demand.
- Internal transfers conserve company stock and change the selected location's stock.
- Zero-stock items and empty pages retain existing membership and pagination behavior.

## Requirements

### Functional Requirements

- **FR-001**: Web, services and inventory projections MUST share the derivation of physical, reserved, blocked, available, incoming and projected quantities.
- **FR-002**: Incoming MUST use effective outstanding supplier promises, including revisions, fulfillment corrections and cancellation.
- **FR-003**: Location and tenant scope MUST constrain every contributing record; existing search, sorting, numeric filters and pagination MUST be preserved.
- **FR-004**: Derivations MUST remain observations, preserve provenance, and introduce no stored authority or new schema.
- **FR-005**: Projection inputs, outputs and calculation descriptions MUST match runtime behavior, and generated references MUST be reproducible.

## Success Criteria

- **SC-001**: All covered inventory stories return identical six-quantity positions on the shared service and Web register; the company-wide projection agrees.
- **SC-002**: Catalog checks describe every changed projection without stale generated output.

## Assumptions and Dependencies

- Existing inventory and fulfillment contracts and specs 301, 303 and 304 remain authoritative.
- The Web register's location membership remains based on recorded movements or active reservations; this change does not expand it.
- Tests are required before implementation, with full backend and applicable Web/documentation gates before completion.

## Requirement Traceability

| Requirement | Acceptance | Test | Implementation |
|---|---|---|---|
| FR-001 | US1 1-2; SC-001 | T004, T006 | T005, T006 |
| FR-002 | US1 2; edge cases | T004 | T005 |
| FR-003 | US1 3-4 | T004 | T005 |
| FR-004 | US1; retained provenance | T004 | T005 |
| FR-005 | US2 1; SC-002 | T007 | T008 |
