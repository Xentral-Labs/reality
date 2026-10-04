# Feature Specification: Evidence summaries for operational rounds

**Feature Branch**: `codex/daily-evidence-summary`
**Created**: 2026-10-04
**Language**: English
**Status**: Accepted scope; implementation pending
**Input**: After merging PR 371, continue with the remaining daily-answer inaccuracies.

## Context and Intent

### Problem
The daily round retrieves shipping evidence but reverses four customer returns and
three supplier returns, presents five sampled shipment records without clear coverage,
and invents an outbound-delivery conversion cause for an open order.

### Scope
Make existing read results provide concise, deterministic summaries of their returned
records and distinguish current readiness from an unestablished historical cause.
External agents must obtain these results through MCP without browser access. Update
the operational assignment and native agent guidance to preserve these distinctions.

### Non-Goals
Guaranteeing arbitrary external model prose, rewriting answers with regular expressions,
a second model correctness judge, a new daily scheduler, business mutations, schema
expansion, and full-company or cross-page snapshot totals are excluded.

## User Scenarios & Testing

### User Story 1 - Correct return counts (Priority: P1)
An operational agent receives the count of each returned movement type directly.
**Why this priority**: Reversed customer and supplier counts give incorrect advice.
**Independent Test**: Read seven mixed return records and compare the summary to identities.
**Acceptance Scenarios**:
1. **Given** four return and three supplier_return records, **When** a page is read,
   **Then** its summary reports four customer-return records and three supplier-return records.
2. **Given** a page limit below seven, **When** read, **Then** only shown records are counted;
   the lookahead record is not included and the result states incomplete coverage.

### User Story 2 - Honest coverage (Priority: P1)
The agent can repeat a ready summary without treating a bounded page as a total.
**Why this priority**: Five observed movements are not proof of only five shipments.
**Independent Test**: Traverse two pages and inspect scope for each separately.
**Acceptance Scenarios**:
1. **Given** more matching shipment records than the limit, **When** the first page is read,
   **Then** it states more matching retained records exist.
2. **Given** a final cursor page, **When** read, **Then** it states preceding records were omitted.
3. **Given** an empty first page, **When** read, **Then** no matching retained records is
   distinguished from no external activity; upstream freshness remains unknown.

### User Story 3 - Distinguish blockers and causes (Priority: P1)
The agent explains open quantities and current blockers without inventing past events.
**Why this priority**: A ready open order does not establish why shipping has not happened.
**Independent Test**: Inspect ready, blocked, partially fulfilled and closed orders.
**Acceptance Scenarios**:
1. **Given** a ready open line, **When** explained, **Then** the result states the cause
   of remaining unfulfillment is not established; readiness is not a historical cause.
2. **Given** a blocked line, **When** explained, **Then** current canonical blocker codes
   remain available but are not asserted to explain all past non-shipping.
3. **Given** a completed line, **When** explained, **Then** no remaining-unfulfillment
   cause is requested or invented.

### Edge Cases
- Exact record identity takes precedence over text query; tenant scope remains enforced.
- Type counts count records, not quantities, customers, orders or unique items.
- A last cursor page is not the entire selection, even when has_more is false.
- Live pages can change between reads; summary has the same observation boundary as records.
- Legacy discovery continues returning its existing bounded list, without added envelope.
- A read refusal is unknown evidence, never a zero count.

## Requirements

### Functional Requirements
- **FR-001**: Paged discovery MUST expose exact shown-record count and, for movements,
  counts by retained type, derived solely from returned records with no lookahead inclusion.
- **FR-002**: The summary MUST distinguish shown-page scope, preceding and following
  omitted records, and whether this response covers the complete matching retained selection.
  It MUST NOT claim upstream completeness or snapshot stability.
- **FR-003**: Movement pages MUST provide a deterministic readable observation with
  customer-return and supplier-return counts unambiguously assigned and labelled as records.
- **FR-004**: Order explanations MUST distinguish current canonical blockers/readiness
  from the unknown historical cause of remaining fulfillment; a closed/fully fulfilled
  line MUST mark such a cause not applicable. No missing record establishes a cause.
- **FR-005**: All additions MUST use existing tenant-scoped shared read services, preserve
  legacy output/access/confirmation semantics, and create no persisted business authority.
- **DR-001**: The operational assignment, tool descriptions and native agent instructions
  MUST direct agents to retain exact summaries/coverage and avoid unsupported causes.
  Multi-stage assignments MUST request concise stage findings and avoid unrequested
  quantity totals across different items/units. Generated tool documentation MUST match
  the executable catalog.

### Key Entities
- Movement: retained type and opaque identity; quantities retain their units separately.
- Discovery page: records, cursor, read metadata, transient evidence summary.
- Order fulfillment line: existing canonical readiness/blockers and remaining quantity.

## Success Criteria

### Measurable Outcomes
- **SC-001**: Every regression case assigns four customer and three supplier returns correctly.
- **SC-002**: Every limited or cursor-page summary explicitly distinguishes its coverage.
- **SC-003**: Ready, blocked, partial and closed orders never assert an unsupported conversion cause.
- **SC-004**: The same evidence is available to a read-only external agent without browser access.

## Assumptions and Dependencies

The user accepted this next scope after the documented residual findings and PR 371 merge.
No new approval is needed for preparing these read-only fixes and a reviewable PR.
Existing canonical readiness services establish current blockers, not historical causality.
Deterministic tool output can be proved; external free-form answers require separate
observed acceptance and cannot be guaranteed by a prompt-only test.


## Requirement Traceability

All repository content is English, except intentional German business examples in
existing localized documentation and lossless original source payloads.

| Requirement | Acceptance | Tests | Implementation |
|---|---|---|---|
| FR-001 | US1.1–2 | T004 | T006 |
| FR-002 | US2.1–3 | T005 | T007 |
| FR-003 | US1.1 | T004 | T006 |
| FR-004 | US3.1–3 | T008 | T009 |
| FR-005 | Edge cases, SC-004 | T004 | T006 |
| DR-001 | All stories | T010,T012 | T011,T012 |
