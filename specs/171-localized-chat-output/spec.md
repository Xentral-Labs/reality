# Feature Specification: Localized Chat Output

**Feature Branch**: `fix/localized-chat-output`
**Created**: 2026-09-11
**Status**: Approved
**Language**: English
**Input**: "Fix chat numbers, monetary amounts, dates, times, and table labels so they follow the signed-in user's profile preferences."

## Context and Intent

### Problem

Ask Reality can return correct records while presenting raw ISO dates, model-selected money formats,
and headings in a language different from the signed-in user's profile.

### Scope

- New answers follow the current authenticated user's language, locale, and display timezone.
- Exact tool values, identities, source content, and historical message bodies remain unchanged.

### Non-Goals

- Rewriting stored messages, source payloads, IDs, or arbitrary Markdown in the browser.
- Adding persistence fields, calculations, schema, or chat authority.

### Existing Contracts

- [Web specification](../../docs/WEB_SPEC.md)
- [Chat contract](../../docs/features/chat.md)
- [Constitution](../../.specify/memory/constitution.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read localized answers (Priority: P1)

An operator receives financial and operational answers in the presentation conventions saved in
their profile.

**Why this priority**: Regional ambiguity can cause money and dates to be misread.

**Independent Test**: Send the same bounded read with German/`de-DE`/`Europe/Berlin` and
English/`en-GB`/`Europe/London`; presentation changes while exact business values do not.

**Acceptance Scenarios**:

1. **Given** a German profile, **When** a user asks about customer overpayments, **Then** prose and
   labels are German and values use `de-DE` plus the selected timezone.
2. **Given** an English profile, **When** the same records are requested, **Then** presentation uses
   English and `en-GB` without changing currencies, values, dates, source text, or IDs.
3. **Given** a saved answer, **When** preferences change, **Then** the old body remains unchanged and
   the next answer receives the new preferences.

### Edge Cases

- Calendar dates do not shift through timezone conversion; instants do.
- Language and locale remain independent.
- Untrusted conversation or source content cannot override server-owned presentation context.
- Existing provider failure and proposal-confirmation behavior remains unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: New answers MUST receive the authenticated user's current language, locale, and timezone.
- **FR-002**: Prose and business labels MUST follow language; numbers, quantities, money, and dates
  MUST follow locale; instants MUST additionally follow timezone.
- **FR-003**: Exact values, currencies, units, source content, technical keys, and opaque IDs MUST
  NOT be translated, recalculated, or replaced.
- **FR-004**: Stored historical message bodies MUST remain unchanged after preference changes.
- **FR-005**: The contract MUST apply to Anthropic and OpenAI-compatible provider paths, including
  admitted practice companies.

### Domain and Traceability Requirements

- **DR-001**: Source → Evidence → Reality and tenant-scoped registered tool paths remain unchanged.
- **DR-002**: No schema, relationship, derived state, or alternate business rule is added.

## Success Criteria *(mandatory)*

- **SC-001**: Provider and authenticated HTTP tests cover 100% of the three profile preferences.
- **SC-002**: Regression tests demonstrate zero changes to historical message bodies and exact values.
- **SC-003**: Existing frontend localization and build gates remain green.

## Assumptions and Dependencies

- Existing profile validation remains authoritative.
- Provider output is stored as the presentation snapshot seen when generated.

## Open Questions

None.

## Requirement Traceability

| Requirement | Scenario | Proof |
|---|---|---|
| FR-001–FR-003, FR-005 | US1.1–US1.2 | Provider and authenticated HTTP tests |
| FR-004 | US1.3 | Service history regression |
| DR-001–DR-002 | US1.1–US1.3 | Existing tenant/tool tests and no-schema review |
