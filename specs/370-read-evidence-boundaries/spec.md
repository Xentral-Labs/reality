# Feature Specification: Evidence boundaries in existing reads

**Feature Branch**: `codex/read-evidence-boundaries`
**Created**: 2026-10-05
**Language**: English
**Status**: Implemented and verified; residual external prose limitations documented
**Input**: Owner approved improving existing tool answers and descriptions after the external PR375 test, with no new command or business logic.

## Context and Intent
### Problem
The external agent found and verified the executed Decision but introduced an unqualified opening count and a conditional inventory-history explanation without reading that history. Existing coverage metadata is correct but separated from the count. Order-linked movements and current stock do not establish complete inventory history.
### Scope
Make existing read results and tool guidance name their evidence limits where the observations are presented. Preserve existing values, discovery selection and follow-up tools.
### Non-Goals
No new tool, inventory-history query, persistence field, permission, business rule, execution, provider-specific prompt patch, historical snapshot or guarantee about arbitrary model prose.

## User Scenarios & Testing
### User Story 1 - Qualify discovered Decision counts (Priority: P1)
As an operator, I need the count to describe the evidence selection rather than all historical actions.
**Independent Test**: Read order-filtered and company-wide executed Decisions, including empty and paginated selections, and inspect count and coverage together.
**Acceptance Scenarios**:
1. Given a complete first selection with one retained order execution, when read, then its summary names retained execution-event coverage alongside the count and historical completeness remains unknown.
2. Given no retained match or a partial/final cursor page, when read, then it does not claim historical absence or a complete selection count.
3. Given no order filter, when read, then the scope is retained executed Decisions with no affected-order association claim.

### User Story 2 - Explain inventory only from inspected evidence (Priority: P1)
As an operator, I need present stock distinguished from the reasons it reached that state.
**Independent Test**: Read an order whose item has an unrelated receipt; its order-linked movement list remains unchanged while the response says inventory history is not established.
**Acceptance Scenarios**:
1. Given current inventory and an order-linked shipment, when explained, then no receipt timing or alternative inventory context is inferred.
2. Given missing or extra inventory history, when explained, then the same interpretation limit applies, and callable movement provenance reads are described without promising a complete stock history.

### Edge Cases
Empty orders, completed orders, same-item movements for another order, company-wide discovery, empty selections, intermediate and final cursor pages, foreign tenants and explicit legacy discovery. Limits are transient observations and must not change business values or persisted records.

## Requirements
### Functional Requirements
- **FR-001**: Executed Decision page summaries MUST place retained selection scope and unknown historical completeness beside their count, including deterministic observation wording that qualifies the count immediately.
- **FR-002**: Existing page count/completeness semantics MUST remain unchanged for complete first, partial and final cursor pages; company-wide and order-filtered scopes MUST differ. Empty results MUST NOT establish historical absence.
- **FR-003**: Order explanation MUST explicitly distinguish current stock and order-linked movement evidence from complete inventory history; it MUST NOT infer receipt timing, stock context or historical stock causes.
- **FR-004**: Existing discovery, order and inventory tool guidance MUST require summaries to preserve evidence scope and state uninspected history as not checked, using existing movement provenance readers only for their actual scope.
- **FR-005**: Shared reads MUST preserve tenant scope, quantities, operational state, read-only behavior, existing discovery/legacy selection and permissions. No database or tool schema expansion.
- **DR-001**: Durable and generated catalog documentation MUST describe these limits. Test evidence and a fresh external read-only acceptance observation MUST be recorded separately; provider prose is not a deterministic contract guarantee.
### Key Entities
Existing transient discovery summary and order interpretation guidance. Existing Documents, Commitments, Reservations, Movements and Decisions retain their identity and meaning.

## Success Criteria
- **SC-001**: All executed-Decision count scenarios name the retained coverage boundary without claiming full history.
- **SC-002**: Order explanations do not present current inventory as proof of its historical causes.
- **SC-003**: Existing read, tenant, quantity and compatibility regressions remain green; no operational effects are introduced during acceptance.

## Assumptions and Dependencies
Owner scope approval is the preceding “Ja, mach das bitte”. Specs 145, 366, 368 and 369 and docs/features/mcp_reads.md remain authoritative. External clients own their prose and may ignore guidance; acceptance must report that honestly. Existing movement_explanation establishes provenance for an exact retained movement, not complete inventory history.


## Requirement Traceability
Repository language: English for code, tests, specifications, documentation, commits and PRs.

| Requirement | Test tasks | Implementation tasks |
|---|---|---|
| FR-001, FR-002 | T004,T009 | T005 |
| FR-003 | T006,T009 | T007 |
| FR-004 | T006,T009 | T008 |
| FR-005 | T004,T006,T009 | T007,T011 |
| DR-001 | T009,T010 | T008,T011 |
