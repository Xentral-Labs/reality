# Feature Specification: Payment evidence and selection scope
**Feature Branch**: `codex/368-payment-evidence-scope`
**Created**: 2026-10-05
**Language**: English
**Status**: Implemented and verified; external prose/discovery limitations documented
**Input**: The owner approved correcting payment interpretation and shipment sample/count ambiguity after PR 373 merged, followed by an external MCP acceptance round.

## Context and Intent
### Problem
Agents mistake the stated order gross amount in standard fulfillment readiness for an unpaid prepayment, and a bounded discovery page for the full shipment count.
### Scope
Explain payment evaluation and order basis through existing readiness, queue and order explanation reads. Expose a retained selection count only when one response covers it completely.
### Non-Goals
No new tool or daily command, schema, settlement or readiness rule, automatic release, business mutation, additional aggregate query, external scheduler or guarantee of arbitrary prose.
### Existing Contracts
Specs 275, 283, 347 and 367 remain authoritative for readiness, consolidated invoices, owner release and transient evidence boundaries. See [MCP reads](../../docs/features/mcp_reads.md).

## User Scenarios & Testing
### User Story 1 - Interpret payment qualification (Priority: P1)
An agent distinguishes an order basis, qualifying prepayment evidence and a shipment constraint.
**Why this priority**: Misreporting an unpaid balance changes operational advice.
**Independent Test**: Compare standard, unpaid, paid, ambiguous and owner-released orders across existing reads.
**Acceptance Scenarios**:
1. **Given** a standard order with a stated gross amount, **When** readiness is read, **Then** the order basis is identified and payment is explicitly not evaluated; legacy zeroes prove neither payment absence nor settlement.
2. **Given** no linked order or no stated amount, **When** read, **Then** no amount authority is invented.
3. **Given** a prepayment order, **When** read, **Then** qualifying amounts are scoped to this order and existing evidence identities; missing or ambiguous evidence is qualified, not treated as a customer balance.
4. **Given** an owner release with a positive remaining amount, **When** read, **Then** the actual release is visible without representing payment or waiving unrelated blockers.
5. **Given** completed fulfillment, **When** read, **Then** the shipment constraint is not applicable and financial evidence retains its own evaluation boundary.
### User Story 2 - Distinguish a page from its selection (Priority: P1)
An agent distinguishes shown records from the matching retained selection.
**Why this priority**: A sample is not a company shipping total.
**Independent Test**: Read limited first, final cursor, complete and empty pages.
**Acceptance Scenarios**:
1. **Given** omitted earlier or later records, **When** read, **Then** the selection count is unknown, even on a final cursor page.
2. **Given** a complete first page, **When** read, **Then** the selection count equals the shown records only for that retained filter at this read.
3. **Given** movements, **When** counted, **Then** counts describe records, not quantities, orders, customers or Shipment consignments; upstream completeness remains unknown.
### Edge Cases
Consolidated invoice qualification follows its existing all-or-nothing rule. Release does not remove attribution ambiguity or consolidated open blockers. Presentation metadata never changes cached payloads or dispatch review tokens. Tenant/grant boundaries and legacy containers remain intact.

## Requirements
### Functional Requirements
- **FR-001**: Existing readiness reads MUST identify stated order gross versus unstated or unestablished basis and explicitly mark standard payment evaluation not_evaluated with interpreted received/remaining unknown.
- **FR-002**: Existing prepayment interpretation MUST retain canonical amounts, scope to qualifying order evidence, qualify missing/ambiguous/unstated evidence, and expose canonical constraint codes and actual release without claiming payment or unrelated release.
- **FR-003**: Direct readiness, exact order explanation and existing payment readiness in fresh/cached queue reads MUST share interpretation; legacy numbers, persisted payloads, review tokens, tenant scope and grants MUST remain unchanged.
- **FR-004**: Discovery MUST expose selection_record_count only for a complete first page; all partial pages MUST return null and explain unknown selection size. Movement counts MUST distinguish records from consignments and quantities.
- **DR-001**: Existing tool descriptions, agent guidance, generated reference and durable MCP contract MUST document these boundaries; verification MUST separate deterministic contracts from actual external-client prose and scheduling evidence.
### Key Entities
Transient payment interpretation and discovery summary fields. No new stored entities or relationships.

## Success Criteria
### Measurable Outcomes
- **SC-001**: Every covered read distinguishes standard order basis from evaluated prepayment evidence.
- **SC-002**: Every covered partial page reports unknown selection count and every complete first page reports its retained count.
- **SC-003**: Compatibility proofs observe unchanged persisted review/cache payloads and no acceptance-round business mutation.

## Assumptions and Dependencies
Owner acceptance is the explicit “ok mach” following the proposed scope. Shared readiness remains authoritative. External scheduling is inspected in the client separately and never inferred from Reality access. Actual free-form responses are recorded as observations, not guaranteed by these metadata fields.

## Requirement Traceability
| Requirement | Acceptance | Tests | Implementation |
|---|---|---|---|
| FR-001 | US1.1,2 | T003 | T004 |
| FR-002 | US1.3–5, edge cases | T003 | T004 |
| FR-003 | Edge cases | T003,T007 | T004 |
| FR-004 | US2.1–3 | T005 | T006 |
| DR-001 | Both stories | T007,T008 | T007 |
