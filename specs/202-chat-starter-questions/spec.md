# Feature Specification: Chat starter questions

**Created**: 2026-09-15
**Status**: Scope authorized by the user request
**Input**: Offer two or three good questions when entering a fresh chat.

## Context and Intent

### Problem
An empty conversation gives new users no concrete starting point.

### Scope
Three editable question suggestions beneath the existing chat welcome text.

### Non-Goals
Personalized recommendations, new tools, automatic sending, business calculations and schema changes.

## User Scenarios & Testing

### User Story 1 - Start with a useful question (Priority: P1)
A user entering a fresh conversation can choose a concrete question about orders, stock or money.

**Why this priority**: Makes the first question easier to formulate.
**Independent Test**: Open an empty conversation, select a suggestion, edit and send it through the ordinary composer.

**Acceptance Scenarios**:
1. Given an empty conversation, when it loads, then three question buttons appear beneath the welcome text.
2. Given an empty draft, when a suggestion is selected, then its localized text fills the focused composer without a request being sent.
3. Given a nonempty draft, when suggestions are displayed, then they are disabled to preserve the draft.
4. Given an existing or pending message, when the conversation renders, then starter questions are absent.
5. Given a narrow viewport or another supported language, when entering chat, then all questions remain readable and keyboard accessible.

### Edge Cases
Loading or starting a session disables suggestions. A fresh conversation restores them. Exhausted allowance retains existing sending restrictions. Generic questions do not assert that the company has particular records.

## Requirements

### Functional Requirements
- **FR-001**: Empty conversations MUST show exactly three read-only questions: open customer orders, stock shortages for open orders and overdue customer invoices.
- **FR-002**: Selection MUST fill and focus the composer without sending. Nonempty drafts and loading, sending or session-creation states MUST prevent selection.
- **FR-003**: Suggestions MUST disappear with recorded or pending messages and return for fresh conversations.
- **FR-004**: Questions MUST use the selected English, German, Dutch or Spanish UI language and support keyboard use and narrow screens.

## Success Criteria

### Measurable Outcomes
- **SC-001**: One activation produces an editable question with zero message submissions.
- **SC-002**: Exactly three readable starters appear in empty chat at desktop and 390px widths.

## Assumptions and Dependencies

- The request authorizes this bounded addition; choosing three questions and draft-first interaction are routine implementation decisions.
- Existing chat tools answer questions using current company scope and existing evidence links.
- Browser acceptance covers FR-001–004; existing chat regression, frontend build, localization and spec gates remain applicable.

## Requirement Traceability

**Language**: English. Localized UI strings are intentional product translations.

| Requirement | Acceptance | Test task | Implementation task |
|---|---|---|---|
| FR-001 | Scenario 1 | T003 | T004 |
| FR-002 | Scenarios 2–3 | T003 | T004 |
| FR-003 | Scenario 4 | T003 | T004 |
| FR-004 | Scenario 5 | T003 | T005 |
