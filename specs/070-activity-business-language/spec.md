# Feature Specification: Business-readable Activity

**Feature Branch**: `[070-activity-business-language]`
**Created**: 2026-09-04
**Status**: Approved
**Language**: English
**Input**: "Place Activity directly below Exceptions and make activity understandable to ERP users before showing technical identifiers."

## Context and Intent

### Problem

Activity is hidden among configurable workspace Views, although it is a primary cross-functional surface. Its expanded rows lead with event types and opaque identifiers, so an ERP operator cannot quickly understand which order, source, customer, item, or business step changed.

### Scope

- Place the single Activity destination directly below Exceptions in the primary company navigation.
- Keep its live unread count and pulse behavior.
- Present business process, reference, source, party, item, quantity, and outcome in plain language when those values exist.
- Preserve event types and opaque identifiers under an explicit technical-details disclosure.

### Non-Goals

- New activity records, schemas, event types, integrations, or notification channels.
- Inventing labels when authoritative business context is absent.
- Removing technical traceability, raw payloads, filters, or the Activity page.

## User Scenarios & Testing

### User Story 1 - Find Activity immediately (Priority: P1)

As an operator, I can open Activity from a stable primary location without looking through workspace Views.

**Independent Test**: Open Company Overview and verify Activity follows Exceptions, carries live state, and is absent from the Views list and launcher.

**Acceptance Scenarios**:

1. **Given** any company workspace, **When** the sidebar is shown, **Then** Activity appears once directly below Exceptions.
2. **Given** unread activity, **When** the sidebar is shown, **Then** the fixed Activity entry shows the existing bounded count and pulse.

### User Story 2 - Understand a business process first (Priority: P1)

As an ERP operator, I can identify what business process happened and inspect technical identifiers only when needed.

**Independent Test**: Process a sourced sales order and verify its activity names the order and meaningful steps while event types and IDs remain in a collapsed technical section.

**Acceptance Scenarios**:

1. **Given** a sourced order process, **When** Activity is opened, **Then** its group identifies the order and shows available source, party, item, quantity, and step count in business language.
2. **Given** an expanded activity, **When** its steps are read, **Then** each step leads with a plain-language action and business context.
3. **Given** support detail is needed, **When** Technical details is expanded, **Then** exact event type, subject ID, source-record ID, and correlation identifiers remain available.

### Edge Cases

- An event has no related document, party, item, or human reference.
- A group contains several commitments or items.
- A referenced record no longer exists in the current tenant.
- An unknown event type is introduced later.

## Requirements

### Functional Requirements

- **FR-001**: Activity MUST appear exactly once in primary navigation directly after Exceptions and MUST not be repeated in workspace Views or its launcher.
- **FR-002**: The fixed Activity entry MUST retain unread count, pulse, selection, and navigation behavior.
- **FR-003**: Activity groups MUST lead with the best available human business reference and MUST fall back to a plain-language event label rather than an opaque ID.
- **FR-004**: Activity steps MUST expose server-produced plain-language labels and available business context.
- **FR-005**: Opaque identifiers and exact event types MUST remain available under a collapsed Technical details disclosure.
- **FR-006**: Missing optional context MUST be omitted without placeholders that imply known business data.

### Domain and Traceability Requirements

- **DR-001**: BusinessEvent remains the activity authority; enrichment MUST create no records and change no business meaning.
- **DR-002**: Related business context MUST be loaded through tenant-scoped reads and shortest true links.
- **DR-003**: Business labels MUST be produced by the shared backend service, not reconstructed as browser business rules.
- **DR-004**: The feature MUST add no schema or migration.

## Success Criteria

- **SC-001**: An operator can identify a sourced order and its outcome from the activity group without reading an opaque identifier.
- **SC-002**: Activity is reachable in one click from the same primary position in every workspace.
- **SC-003**: Every displayed event retains exact technical traceability on demand.
- **SC-004**: Automated backend and frontend contracts cover every requirement.

## Assumptions and Dependencies

- Existing BusinessEvent payloads and shortest links provide the available display context.
- English service labels continue through the existing localization boundary.
- The user explicitly approved fixed navigation and business-first presentation on 2026-09-04.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001-FR-002 | US1.1-US1.2 | Frontend navigation contract |
| FR-003-FR-006, DR-001-DR-004 | US2.1-US2.3 | Timeline service/API and frontend rendering contracts |
| SC-001-SC-004 | All | Focused tests, build, localization audit, and review |
