# Feature Specification: Kits, Bundles and Light Assembly

**Feature Branch**: `333-kits-and-bundles`

**Created**: 2026-10-02

**Status**: Draft

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), round 2. Close the capability gap behind the journeys K01, K02, K03, K04, K06 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Kits and bundles do not exist: availability cannot be derived from components, a kit cannot be held back for one missing component, a component return gives no kit credit, assembly does not consume components, and a bundle price is not split.

| Journey | Title | Status today |
|---|---|---|
| K01 | Kit sold, shipped from components | missing |
| K02 | One component missing, no partial kit allowed | missing |
| K03 | Return of a single component from a kit | missing |
| K04 | Light assembly: components consumed, finished item produced | missing |
| K06 | Bundle price split across components (revenue, tax) | missing |

### Scope

- A kit item with a bill of materials of component items and quantities.
- Kit availability derived from component stock; a kit ships whole or not at all.
- Shipping a kit consumes its components; a returned component is credited by the kit's split.
- A light assembly that consumes components and produces the finished item.
- A bundle price split across components for revenue and tax, as stated or by a stated rule.

### Non-Goals

- Multi-level manufacturing, routings and capacity planning.
- Anything that requires a document status field (Constitution II).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Kits, Bundles and Light Assembly (Priority: P1)

As an e-commerce merchant, I sell a set and ship it from its parts.

**Why this priority**: Round 2 of the sales-gap roadmap: a structural gap that several journeys share.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** a kit of 1 frame and 2 wheels with 3 frames and 4 wheels in stock, **When** availability is read, **Then** 2 kits are available.
2. **Given** one wheel missing, **When** the kit order is read, **Then** it is held back whole.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A kit MUST name its components and quantities, stated through the review.
- **FR-002**: Kit availability MUST be derived from component stock at read time.
- **FR-003**: Shipping and returning a kit MUST move its components.
- **FR-004**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-005**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide.

## Assumptions and Dependencies

- Created as a short draft from the sales-gap roadmap; it must be clarified and accepted by the owner before planning.
- Builds on the capabilities and limitations recorded in `docs/scenarios/coverage.md` for the journeys in scope.

## Open Questions

- [NEEDS CLARIFICATION: Is a kit a stored item with its own stock (assembled ahead) or always exploded at shipment?]

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Business stories and service tests (planned) |
| FR-004, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-005, SC-001, SC-002 | US1 | Catalog tests and Guide questions (planned) |
