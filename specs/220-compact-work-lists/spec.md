# Feature Specification: Compact Daily Work Lists

**Created**: 2026-09-17
**Status**: Scoped by the user request for more compact, clearer Commitments, Exceptions and Decisions lists.

## Context and Intent

### Problem
Two-line rows leave substantial unused horizontal space and limit visible work.

### Scope
Apply one compact presentation to the three existing daily-work queues.

### Non-Goals
No changes to business rules, data, ordering, filters, proposal confirmation or navigation.
No new density settings or dependencies.

## User Scenarios & Testing

### User Story 1 - Scan more work (Priority: P1)
An operator compares entries quickly using aligned title, context and metadata.

**Independent Test**: Render all three queues in the existing browser fixture.

**Acceptance Scenarios**:
1. Given a list at least 720 CSS pixels wide, when rows render, title and context share one line and ordinary rows are 44 pixels high.
2. Given a narrower list, when rows render, title and context occupy two lines, metadata remains visible and the page does not overflow horizontally.
3. Given any queue, when a row is activated by keyboard, its existing inline preview opens; activation never executes a business change.
4. Given a wide list, search and filters share a toolbar; on narrow lists they wrap without losing controls.

### Edge Cases
Long business names and context truncate within their columns while the full text remains in the accessible button name. Existing previews retain available detail. Missing context does not create an empty text line. Large metadata may wrap. Expanded previews are exempt from row-height targets.

## Requirements

### Functional Requirements
- **FR-001**: All three queues MUST use a shared compact row presentation with aligned title, context and right-aligned metadata at sufficient available width.
- **FR-002**: Narrow layouts MUST retain readable two-line content, at least 44-pixel row targets and no horizontal page overflow.
- **FR-003**: Existing grouping, localized text, search, filters, paging, selection, keyboard activation and inline previews MUST remain available; reading MUST NOT mutate business data.
- **FR-004**: Toolbar and group spacing MUST be reduced, with search and filters alongside each other when available width permits.

## Success Criteria
- **SC-001**: Ordinary wide-list rows measure 44 CSS pixels, compared with the previous approximately 68 pixels.
- **SC-002**: All three queues pass browser interaction and overflow checks on desktop and mobile in English and German, light and dark themes.

## Assumptions and Dependencies
The user's request authorizes this shared presentation refinement. Existing services and list semantics remain authoritative. Layout responds to available content width, including the space left by side chat, rather than screen width alone. See docs/WEB_SPEC.md.

## Requirement Traceability

**Language**: English

| Requirement | Story | Tasks | Verification |
|---|---|---|---|
| FR-001 | US1 | T002, T003, T004 | daily-work-browser.mjs geometry and screenshots |
| FR-002 | US1 | T002, T003, T004 | daily-work-browser.mjs mobile geometry and overflow |
| FR-003 | US1 | T002, T003, T004 | daily-work-browser.mjs keyboard, previews, filters, paging and zero writes |
| FR-004 | US1 | T002, T003, T004 | Desktop/mobile screenshots and shared-toolbar contract |
