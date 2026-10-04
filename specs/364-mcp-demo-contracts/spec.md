# Feature Specification: Complete Live Demo Agent Contracts

**Feature Branch**: `codex/364-mcp-demo-contracts`
**Created**: 2026-10-04
**Language**: English for repository artifacts
**Status**: Owner approved the five proposed corrections on 2026-10-04
**Input**: Complete the clear post-merge MCP/Chat corrections and deliver a green PR.

## Context and Intent

### Problem

The fresh October 4 walkthrough of merged spec 363 completed a two-unit reservation
entirely through MCP, but the real HTTP schema lost enum choices. Playground proposals
had only a generic review until the first confirmation call prepared retained state.
The external agent omitted required confirmation arguments, and execution receipts
still named internal projections. Internal Chat reached operations but claimed no
shipping despite recorded shipment Movements and proposed a timezone change during a
read-first turn.

### Scope

Deliver the five owner-approved corrections: grounded shipping context and enforced
read-first Chat turns; authoritative HTTP input choices; complete fresh demo review;
explicit executable confirmation instructions; callable execution follow-up guidance.
Use existing shared services and retain original decision evidence.

### Non-Goals

No new schema, scheduling infrastructure, transport, credential expansion, deployment
or merge. No full Finance allocation explanation, demo-number redesign, disk cleanup
feature, external connector administration or general guarantee of third-party model
wording. Do not reinterpret financial allocations as stock reservations. No direct
business writes from an adapter and no autonomous approval.

## User Scenarios & Testing

### User Story 1 - Read current operations without unintended proposals (Priority: P1)

A user gives the published operational mission and asks to read first. The internal
agent receives current retained shipping evidence and cannot create proposals during
that turn. Absence of consignment objects is not presented as absence of shipment
Movements.

**Independent Test**: Both model providers receive bounded real shipment evidence for
a shipping request, even when no consignment exists; attempted mutations during an
explicit read-first turn are refused without proposal creation.

**Acceptance Scenarios**:
1. Given a shipment Movement and no Shipment object, when current shipping is asked
   about, then the model receives that held Movement with IDs, quantities and coverage.
2. Given an explicit English or German read-first request, when a provider requests a
   timezone or reservation proposal, then no proposal is persisted and read tools remain
   usable. An unrelated business request without that restriction retains proposal access.
3. Given incomplete evidence pages, then context states the bounded scope and never
   turns a sample into a total or a guarantee. Embedded tool/source instructions do not
   grant mutation authority.

### User Story 2 - Inspect and confirm a fresh demo decision (Priority: P1)

The agent proposes two units in a fresh demo and receives the same exact retained
business review as an ordinary company. A separate authorized human client can copy
the stated confirmation arguments and verify the real effect without a browser.

**Independent Test**: Fresh Playground HTTP MCP proposes, reviews and executes a
reservation with unchanged stock before confirmation, separate credentials, exact
fingerprint, stale refusal and replay behavior.

**Acceptance Scenarios**:
1. Given a fresh Playground reservation, when proposed and read, then the initial
   retained review includes current stock, intended effect, named records and its
   fingerprint; read-only inspection never refreshes or writes it.
2. Given a retained review, then handoff explicitly names the tool and arguments
   `proposal_id`, `approved=true` and applicable `review_token`, while preserving human
   authority. Required approval is not inferred from the availability of that template.
3. Given an older generic proposal, then handoff states that preparation is required,
   the first call does not execute, and the client must reread and confirm exact updated
   evidence. Unreadable private details remain protected.
4. Given successful execution, then current MCP follow-up guidance names callable
   registered reads, while the original receipt retains its recorded values and basis.

### User Story 3 - Discover real input choices (Priority: P1)

An external client receives the executable tool schema rather than a lossy translation.

**Independent Test**: Authenticated HTTP `tools/list` preserves the registered enums,
nullable choices, nested fields and existing union contracts; calls retain shared
validation and typed adapter behavior.

**Acceptance Scenarios**:
1. Discovery family includes `document_line`; inventory view exposes `aggregate` and
   `location`; nested/nullable enum constraints survive the actual wire response.
2. Existing required fields, defaults, integer/boolean handling and discriminated
   unions remain compatible. Invalid business inputs still receive canonical refusals.

### Edge Cases

Legacy generic delivery proposals; executed/rejected proposals; private review carriers;
foreign IDs; unchanged or changed retained stock; optional review fingerprint; nullable
and nested schema choices; quoted historical user instructions; repeated calls; models
that attempt tools omitted from the advertised read-only set.

## Requirements

### Functional Requirements

- **FR-001**: Shipping requests in internal Chat MUST receive bounded retained shipment
  Movement evidence independently of Shipment object existence, with scope/completeness.
- **FR-002**: An explicit current-turn read-first/read-only instruction MUST constrain
  both provider schemas and execution to reads; it MUST NOT create business proposals.
  Refused mutation attempts MUST return controlled evidence to the provider rather than
  aborting the explanation, including the existing read-only lesson companion.
- **FR-003**: HTTP MCP schemas MUST preserve executable enum/nested/nullable contracts.
- **FR-004**: Fresh demo reservation proposals MUST retain full state-bound review before
  confirmation, using the same shared review/lock boundary as ordinary companies.
- **FR-005**: MCP review MUST provide a complete confirmation argument template and
  distinguish retained-review execution from legacy review preparation.
- **FR-006**: Execution/reconciliation MUST expose callable verification guidance outside
  the immutable recorded receipt; never overwrite recorded projection basis.

### Domain and Architecture Requirements

- **DR-001**: Shared services, Source → Evidence → Reality and tenant scope remain intact.
- **DR-002**: Reads remain non-persisting; explicit human authority, credential limits,
  privacy, stale state, confirmation attribution and replay remain enforced.
- **DR-003**: No schema or domain relationship expansion. External model output remains
  generative; source-grounded context and execution guards are deterministic.

### Key Entities

Existing ChangeProposal with retained review; shipment Movement and Shipment object;
MCP tool definition and principal; current Chat turn and provider access set; immutable
execution receipt and derived adapter follow-up guidance. No new stored entity.

## Success Criteria

- **SC-001**: The fresh demo review shows zero currently reserved and two proposed before
  confirmation; one authorized execution reserves exactly two, without shipping goods.
- **SC-002**: Every tested read-only provider turn creates zero proposals even when the
  model asks for a mutation; current shipping evidence is available with truthful bounds.
- **SC-003**: All affected published choices match the actual client-visible choices.
- **SC-004**: The final PR head passes all required backend, browser, frontend, docs and
  specification checks without weakening gates.

## Assumptions and Dependencies

The latest owner authorization accepts the previously recommended five-item scope;
no clarification remains. Spec 363 provides company identity and safe bounded reads.
Existing specs 145/249/263/270/286/323/325 govern evidence, decision rights and errors.
The recorded retest is diagnostic evidence, not a deterministic model-output guarantee.
Tests are required before implementation where practical, including actual HTTP schema
and Playground coverage missing from the previous regression slice. Wider Finance,
connector isolation, repeated demo numbers and storage diagnostics remain follow-ups.

## Requirement Traceability

| Requirement | Acceptance | Planned proof |
|---|---|---|
| FR-001/FR-002 | US1.1–3 | Two-provider retained evidence and actual dispatch refusal |
| FR-003 | US3.1–2 | Authenticated HTTP tools/list and typed calls |
| FR-004/FR-005/FR-006 | US2.1–4 | Playground initial review, legacy handoff, execution/status and receipt preservation |
| DR-001/DR-002/DR-003 | All stories | Tenant/privacy/stale/replay/lesson suites and no-schema review |
