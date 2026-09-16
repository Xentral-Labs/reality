# Feature Specification: Visible integration actions

**Language**: English for all repository artifacts.

**Created**: 2026-09-16
**Status**: Implemented and verified
**Input**: The user approved visible, distinct action labels for registered sources and received data after reviewing both pairs of identical arrows.

## Context and Intent

### Problem
Two different internal actions in each integration row appear as identical external-link arrows. Their destinations cannot be understood without hovering.

### Scope
Show readable action labels in both integration registers using the shared table presentation. Keep compact preview controls in operational registers.

### Non-Goals
No new routes, business rules, source controls, schema, clickable identifiers/counts, or redesign of other registers. No migration of operational preview actions.

## User Scenarios & Testing

### User Story 1 - Choose the intended integration action (Priority: P1)
As an operator, I can read which action opens settings, received data, details or observations before activating it.

**Independent Test**: Browser fixtures render both registers, inspect visible labels and activate all four actions.

**Acceptance Scenarios**:
1. Given a registered source, its row visibly offers Settings and Received data; they open the existing source configuration dialog and source-filtered received-data view respectively.
2. Given a received source version, its row visibly offers Open details and View observations; they open its Inspector and exact-source Facts view respectively.
3. Given German, English, Dutch or Spanish presentation, each action has a localized visible label matching its accessible name.
4. Given a narrow viewport or compact density, actions remain readable and reachable through the existing table scroll region without page overflow. Keyboard activation retains the destination and Inspector focus return.
5. Given an ordinary operational preview register, its existing compact disclosure presentation remains unchanged.

### Edge Cases
Empty/error states retain existing recovery. Long translations must not be clipped within buttons. Saved column widths must not shrink the action column below its readable width. Opening any of these actions must not write business data.

## Requirements

### Functional Requirements
- **FR-001**: Registered-source rows MUST visibly label their existing configuration and received-data actions Settings and Received data (localized).
- **FR-002**: Received-data rows MUST visibly label their existing Inspector and exact-source observation actions Open details and View observations (localized).
- **FR-003**: Both registers MUST retain visible labels without hover, external-link icons or an overflow menu in normal and compact density at desktop and mobile widths. Labels MUST remain keyboard accessible and untruncated, with table-local scrolling permitted.
- **FR-004**: Routes, exact-source filters, company scope, focus return and read-only activation MUST remain unchanged. Other registers MUST retain their compact preview controls.

## Success Criteria
- **SC-001**: All four actions show their outcome before hover in all four supported languages at 390px and 1440px widths.
- **SC-002**: All four actions reach their original destination and opening them produces zero write requests.
- **SC-003**: No page-level horizontal overflow or clipped action label appears in either density.

## Assumptions and Dependencies
The user's confirmation approves the two-table change and reusable shared presentation support. Existing source configuration, Inspector, Facts routing and localization remain authoritative. Spec 164's compact operational preview contract remains in force; this feature overrides the fixed 80px icon-action convention of spec 115 only for these integration registers. Browser regression tests are required before implementation.

## Requirement Traceability

| Requirement | Scenario | Tasks | Test |
|---|---|---|---|
| FR-001 | US1.1 | T002, T004, T005 | unified-sources-browser.mjs source actions |
| FR-002 | US1.2 | T002, T004, T005 | unified-sources-browser.mjs record actions |
| FR-003 | US1.3–4 | T002, T003, T005 | unified-sources-browser.mjs language/density/viewport matrix |
| FR-004 | US1.1–5 | T003, T005, T006 | sources/source-configuration/tables browser regressions |
