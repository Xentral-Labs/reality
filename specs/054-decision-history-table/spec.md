# Feature Specification: Decision History Register

**Feature Branch**: `[054-decision-history-table]`
**Created**: 2026-09-03
**Status**: Approved
**Language**: English
**Input**: "History should definitely be a table. I have customers with 50-500 orders a day."

## Context and Intent

### Problem

Decision history is the one queue that never shrinks. Every approval and every rejection stays in it forever, and at 50 to 500 business events a day it reaches thousands of entries within a month.

Today it is read whole. The endpoint returns every historical decision for the company in one response with no count, no page and no filter, and the browser renders each one as a full card with all its arguments unfolded. The response grows without bound, the page grows with it, and finding one decision means scrolling past all of them.

That presentation was inherited from the Copilot conversation, where one card in a message thread is right. In a register it is not: history is looked up, not decided, so the row matters more than the card.

### Scope

- Read decision history as a register: one row per decision, details on request.
- Count, filter and slice that history in the database rather than in the browser.
- Give the register a search, a stable order and page controls.
- Share one argument presentation between an approval card and a history row.

### Non-Goals

- Rebuilding the pending approvals queue; it keeps its card list until it is known how many approvals realistically arrive at once.
- Bulk decisions, grouping, or risk-based ordering; those belong with a pending-queue rework.
- Adding `decided_at` or `decided_by` columns to the audit record, which would require a migration.
- Changing approval permissions, the execution boundary, or any audit record.

### Existing Contracts

- [Web UI Specification](../../docs/WEB_SPEC.md)
- [Approval Queue Clarity](../052-approval-queue-clarity/spec.md)
- [Agent Interaction](../014-agent-interaction/spec.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Look up one decision among thousands (Priority: P1)

As an operator, I can find a past decision by what it did, without scrolling through every decision before it.

**Why this priority**: History that cannot be searched is an archive nobody opens, and at these volumes it is unreadable within weeks.

**Independent Test**: With more decisions than fit on one page, open the history tab, search for an action, and page through the results.

**Acceptance Scenarios**:

1. **Given** a company has more decisions than one page holds, **When** the history tab opens, **Then** one page of rows is shown with the total page count and working page controls.
2. **Given** a search term is entered, **When** results return, **Then** filtering happened in the service before paging and the view returned to the first page.
3. **Given** a search matches nothing, **When** results return, **Then** a no-results state offers to change or clear the search.
4. **Given** the requested page is beyond the last one, **When** the read is handled, **Then** it clamps to the last page instead of failing or returning nothing.

### User Story 2 - Judge a row without opening it (Priority: P1)

As an operator, I can tell from one row what was decided, how much it covered, who asked for it and how it ended.

**Why this priority**: A register whose rows say too little forces the reader to open every one, which is the state it replaces.

**Independent Test**: Read a page of history covering single-record and batch decisions, approved and rejected, and confirm each row answers those four questions unopened.

**Acceptance Scenarios**:

1. **Given** a decision covered a batch, **When** its row renders, **Then** the row states how many records it covered without being opened.
2. **Given** a decision was executed or rejected, **When** its row renders, **Then** the outcome is distinguishable at a glance and not by color alone.
3. **Given** a row is opened, **When** its detail appears, **Then** the arguments read exactly as they do on an approval card, in the same view, without navigation.
4. **Given** the reader uses a keyboard, **When** the detail control is reached, **Then** it can be operated and announces whether the row is open.

### Edge Cases

- Two decisions share a timestamp at a page boundary.
- A decision's arguments are a batch, a single record, or empty.
- The company has no history at all, or none matching the search.
- A search term matches every decision.
- History is read for a company the member does not belong to.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Decision history MUST be presented as a register with one row per decision, not one card per decision.
- **FR-002**: A row MUST state when the change was requested, which action it was, how much it covered, who requested it, and how it ended.
- **FR-003**: A row covering a batch MUST state its record count without being opened.
- **FR-004**: A row MUST reveal its full arguments on request within the same view, without navigation or a page reload.
- **FR-005**: The detail control MUST be reachable and operable by keyboard and MUST announce the row's open state.
- **FR-006**: History MUST be read one page at a time, at most 25 rows per page, with a total, a page count and previous/next controls.
- **FR-007**: Counting and slicing MUST happen in the database; the browser MUST NOT receive rows it does not display.
- **FR-008**: The order MUST be deterministic beyond the timestamp, so a page boundary can neither repeat nor skip a decision.
- **FR-009**: Search MUST filter in the service before paging and MUST return the reader to the first page.
- **FR-010**: A page number beyond the last page MUST clamp to the last page rather than fail or return an empty result.
- **FR-011**: The argument presentation MUST be shared between the approval card and the history row and MUST render identically in both, independent of the surrounding table styling; only the enclosing card may carry a status colour.
- **FR-012**: The pending approvals count MUST come from the server's total rather than from the number of cards rendered, and the queue MUST say when more approvals wait than it shows.
- **FR-013**: A queue tab MUST report its count as a badge beside its label and MUST report nothing at all when the count is zero or not yet known.
- **FR-014**: Every English string added by this feature MUST carry a German, Dutch, and Spanish translation.

### Domain and Traceability Requirements

- **DR-001**: This feature is read-only; it MUST NOT change the Proposal → Approval → Execution lifecycle, approval permissions, the execution boundary, or any audit record.
- **DR-002**: The paged reader MUST be tenant-scoped and MUST be discoverable by the tenant isolation catalog, so its isolation is proven rather than assumed.
- **DR-003**: It MUST add no table, column, or domain mutation.
- **DR-004**: The browser MUST NOT compute totals, filter rows, or derive business meaning from a decision's arguments beyond their shape.

### Key Entities *(when data is involved)*

- **Decision history page**: A bounded, tenant-scoped, deterministically ordered slice of settled change proposals with its total.
- **Decision row**: One settled change proposal reduced to time, action, scope, requester and outcome, with its arguments available on request.

## Success Criteria *(mandatory)*

- **SC-001**: The history response stays a fixed size as the company's history grows from tens to thousands of decisions.
- **SC-002**: A named past decision can be found within 10 seconds without scrolling past unrelated decisions.
- **SC-003**: Paging across a boundary provably repeats no decision and skips none, including when timestamps collide.
- **SC-004**: The localization audit reports zero missing and zero invalid entries across English, German, Dutch, and Spanish.
- **SC-005**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The audit record stores when a change was requested and by which kind of actor, but not when or by whom it was decided. The register therefore reports the request, and a decided-at column would need a migration this feature excludes.
- Search over the action name is sufficient for lookup at these volumes; searching inside arguments is not required yet.
- 25 rows per page balances a readable register against paging effort; the pending queue keeps a larger bound because its cards are the exception, not the rule.
- Existing tenant authentication and the shared page contract remain available.

## Open Questions

None blocking. The missing decided-at and decided-by attribution is recorded above as a known limit rather than an open question, because closing it requires a schema change that is explicitly out of scope.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001-FR-005 | US2 scenarios 1-4 | Frontend register contracts, including the shared argument renderer and the announced detail control |
| FR-006-FR-010 | US1 scenarios 1-4 | Backend paging tests: page contract, boundary disjointness, service-side search, out-of-range clamping |
| FR-011-FR-012 | US2 scenario 3, US1 scenario 1 | Shared-renderer contract and server-derived pending total |
| FR-013 | US1 scenario 1 | Tab badge contract: no bracketed count, no rendered zero |
| FR-014 | US1-US2 | Localization audit across English, German, Dutch, and Spanish |
| DR-001-DR-004 | US1-US2 | Tenant isolation catalog coverage, tenant-scoped history test, diff review for absent schema change |
| SC-001-SC-005 | All scenarios | Full required quality gates |
