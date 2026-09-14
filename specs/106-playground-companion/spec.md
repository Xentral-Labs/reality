# Feature Specification: Playground Companion

**Created**: 2026-09-07
**Status**: Approved scope
**Language**: English

## Context and Intent
The sandbox owner needs help understanding their own recorded business activity
without leaving the cockpit.

### Non-Goals
No autonomous mutations, proposal approval, live integrations, new business rules,
or durable conversation storage in this increment.

## User Scenarios & Testing
### User Story 1 — Ask about this sandbox (P1)
The owner asks a question in the central chat tab and can switch back to operational views.
Acceptance: a reply uses only this sandbox's records; another owner's run is rejected.
Requests to mutate cannot create proposals or business records.

### User Story 2 — Discover useful questions (P2)
The owner sees up to three questions based on loaded Reality, with more available.
Acceptance: recording activity updates suggestions without clearing the conversation;
changing the center tab preserves messages and the composer stays at the bottom.

### Edge Cases
Unavailable provider, failed request, empty or loading Reality, long conversations,
many exceptions, narrow viewport, archived run, run switching during a response.

## Requirements
- **FR-001**: Show the chat as a central Ask Reality tab alongside operational registers.
  The right column contains attention only, with three findings initially and disclosure.
- **FR-002**: Provide three contextual questions, more questions, a fixed composer,
  loading/error states, and a conversation retained during center-tab changes.
- **FR-003**: Authenticate the run owner for every question; derive the tenant from the
  run, never from submitted messages. Expose read-only capabilities to the assistant
  and reject non-read tool calls server-side. No business or proposal writes.
- **FR-004**: Reuse the configured managed assistant and shared Reality tools. Provider
  unavailability is explicit, never replaced by a fabricated answer.
- **FR-005**: Preserve sandbox boundaries, four-language UI and light/dark styling.
  Operational registers remain reachable alongside answers for verification.
  Business history and Documents are reached through the existing central tabs;
  do not duplicate these navigation links below the chat conversation.
- **FR-006**: Render assistant Markdown as readable paragraphs, headings, lists and
  tables. Distinguish speakers by message alignment and accessible labels, without
  visible repeated You/Reality headings. Wide tables scroll inside their
  message, never widen the companion. Raw HTML, images and external links stay disabled.
  After the first answer, question suggestions collapse behind More questions to
  leave the available space to the conversation.

- **FR-007**: Collapse the timeline into a compact count/latest-event strip by default;
  explicit expansion reveals existing events without automatic opening on updates.
  The central chat uses the available panel without a duplicate heading, introduction
  or focus toggle (superseding the initial focus-mode experiment).
- **FR-008**: Display the submitted question immediately, followed by an accessible
  animated pending reply in the conversation. Success appends the answer; failure
  retains the question with an inline error and explicit retry without duplicate
  questions or failed turns in provider history. Preserve earlier completed turns.
- **FR-009**: Present attention as compact grouped work items, with action-oriented
  labels for common classes and canonical fallbacks for unknown classes. Resolve
  customer/item/document context through the existing tenant-scoped inspector.
  Display server-provided quantities with locale formatting; never infer shortages
  from unreserved quantities. Clicking opens the linked record in the center with
  evidence and operational-register navigation. No dismiss/complete mutation exists.
  Missing context remains explicitly unavailable; catalog access remains live.

## Success Criteria
- SC-001: A question and answer fit the cockpit without adding page-level scroll.
- SC-002: Security tests reject foreign runs and attempted mutation tool calls.
- SC-003: Conversation survives all center-tab changes and resets on sandbox changes.

## Assumptions and Dependencies
The deployment-managed assistant is configured. Clicking Send transmits the question
and tool-selected sandbox context to that existing provider. History is bounded and
held only in the current browser component; reload starts a new conversation.

## Requirement Traceability
| Requirement | Tasks | Proof |
|---|---|---|
| FR-001, FR-002, FR-005 | T004, T005, T006 | Frontend contracts and browser journey |
| FR-003, FR-004 | T002, T003, T006 | Owner and read-only provider regressions |
| FR-006 | T007 | Safe Markdown contract and themed browser answer |
| FR-007 | T008, T009 | Collapsed recorder and absence of redundant focus controls |
| FR-008, FR-009 | T009 | Pending/error/retry browser checks and grouped attention contracts |
