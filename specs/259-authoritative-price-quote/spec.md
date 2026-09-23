# Feature Specification: Authoritative Price Quote Read

**Feature Branch**: `259-authoritative-price-quote`  
**Status**: Approved  
**Language**: English  
**GitHub Issue**: #48

## Context and Intent

Expose the existing canonical party-aware price resolution as an MCP read tool. An agent supplies
the full commercial context and receives either the selected tier with provenance or an explicit
no-match answer. The tool never creates an assignment, copies a price, or introduces a second
pricing rule.

## User Scenarios & Testing

### User Story 1 - Quote the price that applies now (P1)

An agent asks which unit price applies to a Party, item, quantity, direction, currency and unit. It
receives the authoritative result selected by the same service used by the API and operational
logic, including the selected price-list entry and assignment path.

**Independent Test**: Create direct, group and default candidates, call the MCP tool, and prove the
same winning entry and provenance as `resolve_price`.

### User Story 2 - Explain why no price applies (P1)

An agent asks with complete context for which no eligible tier exists. It receives a stable
`matched: false` result rather than inventing or silently defaulting a price.

**Independent Test**: Call with a quantity below every tier and assert an explicit no-match result.

## Requirements

- **FR-001**: The public read tool MUST require `party_id`, `item_id`, `quantity`, `direction`,
  `currency`, and `unit`; `at` MAY select a historical effective instant.
- **FR-002**: Resolution MUST delegate to the canonical price service.
- **FR-003**: A match MUST return unit price, currency, unit, price-list ID, entry ID, selection
  source (`party`, `group`, or `default`), assignment ID when applicable, Party-group ID when
  applicable, and the evaluated instant.
- **FR-004**: No match MUST return `matched: false` and the normalized request context.
- **FR-005**: Reads MUST enforce tenant scope and reject foreign opaque IDs without disclosure.
- **FR-006**: The operation MUST remain read-only and MUST NOT require confirmation.
- **FR-007**: Existing priority, effective-date, quantity-tier, direction, currency and unit rules
  MUST remain unchanged.

## Success Criteria

- **SC-001**: MCP and canonical service select identical price entries for all covered paths.
- **SC-002**: Direct, group, default, no-match and cross-tenant cases are executable tests.
- **SC-003**: The generated tool catalog describes all inputs and provenance fields.

## Non-Goals

- Creating or changing prices, assignments, Parties or items.
- Reconstructing the agreed price retained on historical document Evidence.
- Inferring omitted commercial context.

## Assumptions and Dependencies

- Existing `resolve_price` priority and validity semantics remain canonical.
- Callers discover tenant-owned opaque Party and item IDs before quoting.

## Requirement Traceability

Issue #48 → US1/US2 → FR-001..FR-007 → `contracts/price-quote.md` → T001..T008.

## Spec Impact

New observable read capability; no schema expansion.
