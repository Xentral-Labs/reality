**Language**: English

# Feature Specification: Reliable Shipping Discovery and Decision Catalog

**Feature Branch**: `codex/chat-round-review-discovery`
**Created**: 2026-10-04
**Status**: Scope accepted by the owner on 2026-10-04
**Input**: Correct the remaining daily-round shipping defect and generic confirmation discovery, then qualify client-owned repeated MCP rounds.

## Context and Intent

### Problem

PR370 completed the external reservation cycle, but its full daily Chat mission still
claimed no retained shipping. The actual movement page labeled query=shipment
contained opening stock, receipt and return rows: the shared discovery selection
silently ignored queries for Movement because no configured searchable column exists.
The small provider fixture could not expose a shipment outside the first five IDs.
The generic confirmation tool is also hidden under an intake-specific capability.

### Scope

Restore movement-type discovery, retain honest bounded evidence in Chat, make generic
decision confirmation directly discoverable under review with current caller rights,
and record what repeated read-only external-agent operation actually supports.

### Non-Goals

No new database fields, scheduling infrastructure, internal provider-job handler,
autonomous approval, wider third-party access, Finance semantics, cancellation model,
storage feature, deployment or merge. No general guarantee that a provider writes
truthful prose. Do not replace canonical services with adapter business rules.

## User Scenarios & Testing

### User Story 1 - Read actual shipment evidence (Priority: P1)

The operator runs the published read-first daily mission in a populated demo.
Shipping evidence must select shipment Movements even when other records precede them.

**Independent Test**: Put more than five earlier non-shipment Movements before a
shipment; discover shipment through cursor and legacy reads and both provider loops.
Then run the complete daily mission with the real configured provider.

**Acceptance Scenarios**:
1. Given earlier opening stock/receipt/return records, when movement query shipment
   is read with limit five, then every returned record is a matching Movement and
   the existing shipment is included independently of unrelated IDs.
2. Given query ship or SHIPMENT, then case-insensitive movement-type search returns
   matching records; a nonmatching term returns an honest empty matching selection.
3. Given another tenant's movement or another filter's cursor, then scoped discovery
   and cursor refusal remain unchanged. Legacy and paged reads select the same IDs.
4. Given the complete German or English daily mission, then both providers receive
   bounded matching shipping evidence even across later rounds; reads create no
   proposals. The real daily mission must be assessed against retained shipping,
   rather than declaring prompt injection alone sufficient live validation.
5. Given a sample or refused read, then supplied context preserves scope, has_more
   and unknown coverage; it does not claim totals, exact-order absence or delivery.

### User Story 2 - Find the generic confirmation boundary (Priority: P2)

An external agent inspecting review capabilities finds the tool that confirms a
reservation and learns whether its credential can call it without trying a mutation.

**Independent Test**: Read review with read-only and confirmation-capable principals;
find the generic tool once in that topic with unchanged permission reasons.

**Acceptance Scenarios**:
1. A read-only caller finds proposal_approve_and_execute under review with access
   confirm, callable false and not_in_token; inspection creates no proposal or effect.
2. An appropriately scoped caller sees callable true, while the actual action still
   requires the existing explicit human decision and retained review.
3. Intake-specific capabilities remain discoverable, existing tool bindings are
   retained, and topic counts deduplicate repeated tool representations.

### User Story 3 - Qualify repeated external MCP rounds (Priority: P2)

The owner can distinguish an actual external-agent schedule and saved mission from
an invented claim that Reality runs provider rounds itself.

**Independent Test**: Inspect actual client controls, run a bounded read-only repeated
mission where supported, check saved mission/state, next run and pause, and report
unsupported capabilities explicitly. Preserve unrelated routines.

**Acceptance Scenarios**:
1. Scheduled client reads target only the named synthetic company and continue
   inspecting other work while a Decision is pending; no approval is delegated.
2. Time zone/workdays, saved mission, prior result and next-run/pause state are
   verified through actual client capabilities; a manual run is labeled manual.
3. Missing clock/task/checkpoint controls are recorded as qualification gaps. No
   Reality MCP scheduling tool or activated routine is invented.

### Edge Cases

Mixed movement types and units, an older movement outside the first page, omitted
query, opaque identity precedence, empty/nonmatching results, query changes across
cursor pages, source instructions, current read-first versus historical restrictions,
unknown client outcomes, locked Mac, and revoked test credentials.

## Requirements

### Functional Requirements

- **FR-001**: Movement discovery queries MUST match the held movement type using the existing case-insensitive search contract before paging/limiting, in legacy and paged reads.
- **FR-002**: Shipment context MUST retain matching same-company IDs and coverage across provider rounds, with no writes or inference of whole-company totals or exact-order absence.
- **FR-003**: Generic confirmation MUST be independently discoverable in review with its executable description, confirmation access class and actual caller permission, preserving intake bindings and authorization.
- **FR-004**: Client-owned recurring qualification MUST record actual repeat/mission/time/next-run/pause evidence or explicit unsupported/blocked outcomes, without adding a Reality timer or granting business approval.

- **FR-005**: Canonical MCP dispatch MUST refuse undeclared top-level arguments for flat object schemas whose executable input schema forbids additional properties, before calling the handler. Both internal provider loops MUST receive that refusal and be able to retry the declared read without ending the daily round. Genuine handler failures MUST remain errors.

### Documentation Requirements

- **DR-001**: Executable catalog documentation and German/English demo guidance MUST explain movement-type search, generic decision discovery and the external scheduling boundary.

### Key Entities

Existing Movement, Commitment, Proposal/Action, credential and ephemeral discovery
page. Client-owned mission/checkpoint/schedule remain external observations, not new
Reality authority.

## Assumptions and Dependencies

The accepted order is shipping and catalog correction first, repeated-agent
qualification second. Existing shared PostgreSQL services and MCP transport remain
unchanged. Movement query is substring search, not a new structured business filter.
A provider's exact prose requires live verification; deterministic adapter proofs
establish evidence selection and read-only boundaries only. Recurring tests use
synthetic evidence and preserve unrelated client connections/routines.

## Success Criteria

- **SC-001**: All padded-fixture movement reads return matching same-company IDs; unrelated earlier records never displace the held shipment.
- **SC-002**: Both provider-loop tests preserve the correct bounded evidence through multiple rounds; live full-mission results are reported against the actual retained shipping.
- **SC-003**: Review discovery reports the generic confirmation tool and correct permission for both credential classes without mutation.
- **SC-004**: The owner receives an evidence-based recurring qualification, with manual, scheduled, unsupported and blocked outcomes distinguished.


## Requirement Traceability

| Requirement | Acceptance | Planned proof |
| --- | --- | --- |
| FR-001 | US1, SC-001 | Padded shared selection, cursor, legacy, identity and tenant tests |
| FR-002 | US1, SC-002 | Both provider loops, multiple rounds and real daily mission |
| FR-003 | US2, SC-003 | Standalone metadata and exact principal permission tests |
| FR-004 | US3, SC-004 | Actual external capability or explicit blocked qualification |
| FR-005 | Daily-round recovery | Closed flat-schema refusal, retry, access and union compatibility |
| DR-001 | All stories | Generated catalog and executable EN/DE guidance |
