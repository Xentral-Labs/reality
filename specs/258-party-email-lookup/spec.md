# Party email lookup

**Status**: Approved, 2026-09-23  
**Language**: English  
**Input**: GitHub issue #51 plus owner approval to support email only in the first increment.

## Context and Intent

### Problem

Inbound correspondence often identifies a customer or supplier only by sender address. Reality
cannot currently record or exactly match business-party email addresses, so integrations fall back
to unsafe fuzzy name matching.

### Scope

Record zero or more labelled email addresses on a Party through the existing confirmed Party create
and update flows. Expose them on Party discovery and include exact normalized email matches in Party
search. Preserve tenant isolation, proposal review and source provenance.

### Non-Goals

No telephone numbers, postal addresses, individual contact persons, domain-only matching, outbound
email, inferred addresses or automatic Party selection when more than one Party matches.

## User Scenarios & Testing

### US1 — Identify a Party by sender address (P1)

An integration searches Party records with a sender email and receives only Parties whose stored
address matches after safe email normalization.

**Acceptance scenarios**:

1. Given one Party has `orders@example.com`, searching `Orders@Example.com` returns that Party and its emails.
2. Given two Parties share an address, both are returned and the caller must resolve ambiguity.
3. Given another tenant owns the same address, its Party is never returned.

### US2 — Maintain Party email addresses through governed tools (P1)

An agent proposes Party creation or update with labelled email addresses; nothing changes before
human confirmation, and the confirmed Party is discoverable by exact address.

**Acceptance scenarios**:

1. Invalid or blank addresses are refused during proposal preview.
2. Duplicate normalized addresses within one Party are refused.
3. Replacing the email list emits the existing Party update audit with the before/after list.

## Requirements

- **FR-001**: Party create/update records MUST accept an optional bounded list of email addresses with optional labels.
- **FR-002**: Addresses MUST be trimmed and case-normalized for exact matching while retaining one display value.
- **FR-003**: One Party MUST NOT contain duplicate normalized addresses; the same address MAY belong to multiple Parties.
- **FR-004**: Email mutations MUST use existing Party proposal, confirmation, tenant and source-version boundaries.
- **FR-005**: Party discovery MUST expose a deterministic `emails` list and match email addresses exactly after normalization.
- **FR-006**: Cross-tenant email lookup MUST behave as not found and disclose no matching tenant.
- **FR-007**: Lists MUST be limited to 20 addresses per Party; labels MUST be at most 80 characters.
- **DR-001**: Email records MUST point directly to Party and tenant without duplicating Document or Source relationships.

## Edge Cases

- Unicode domains are accepted only in normalized ASCII form in this increment.
- Removing every email leaves an empty list and no searchable address.
- A shared mailbox can intentionally match more than one Party.

## Success Criteria

- **SC-001**: Exact lookup returns all and only tenant-scoped matches within the existing discovery page limit.
- **SC-002**: Create, update, removal, ambiguity and cross-tenant scenarios have executable coverage.
- **SC-003**: Existing clients that omit emails retain unchanged Party behavior.

## Key Entities

- **PartyEmailAddress**: tenant-scoped email address belonging directly to one Party, with display value, normalized value and optional label.

## Assumptions and Dependencies

- The owner approved email-only scope; later contact types require a separate proven use case.
- Existing Party source payload versioning remains the provenance authority for externally supplied changes.

## Requirement Traceability

| Requirement | Stories | Tasks / evidence |
| --- | --- | --- |
| FR-001–FR-004, FR-007, DR-001 | US2 | T003–T006; Party service/proposal tests |
| FR-005–FR-006 | US1 | T002, T007–T009; exact-match and tenant-isolation tests |
