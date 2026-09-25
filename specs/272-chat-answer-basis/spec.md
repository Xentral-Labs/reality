# Feature Specification: Compact Chat Answer Basis

**Feature Branch**: `current-worktree`

**Created**: 2026-09-25

**Status**: Approved for implementation by owner request

**Language**: English

**Input**: Replace the confusing, usually empty "What happened" disclosure below chat replies with a compact explanation of the actual evidence and Reality records on which each answer is based.

## Context and Intent

### Problem

The current per-reply "What happened" disclosure exposes a Storyline-specific technical call trace. In ordinary company chat it normally has no eligible Storyline run, so it repeatedly says that no calls were recorded even when the answer visibly contains current company data. The heading promises an explanation but the empty state explains neither the answer nor its business basis.

### Scope

Record the exact read calls used while producing every persisted assistant reply, independently of Storyline participation. Present their business-facing result summaries as a compact "Basis for this answer" disclosure. The disclosure leads with the records and values supporting the answer, keeps technical call details out of the primary view, and links supported records into the existing tenant-scoped Inspector or operational detail.

Existing Storyline traces and proposal-decision explanations remain available for eligible Sandboxes. The new answer basis is the ordinary-chat explanation and does not claim that a read caused later business changes.

### Non-Goals

- No model-generated citations, source claims inferred from prose, or parsing of assistant text.
- No new business authority, stored derived operational status, or browser-side business calculation.
- No change to tool answers, confirmation rules, providers, prompts, business records, or original source payloads.
- No retrofit of exact support records for historical replies created before this feature.
- No raw JSON, latency, internal tool names, or implementation terminology in the compact primary presentation.

## User Scenarios & Testing

### User Story 1 - Understand an answer immediately (Priority: P1)

As an operations user, I can expand a concise basis below an assistant reply and see which business records and returned values support its conclusion.

**Why this priority**: An answer about an open or blocked order is not fully explainable when the product cannot show the information it just read.

**Independent Test**: Ask which customer orders remain open in a company with one blocked order, expand the reply basis, and verify that it identifies the order, its requested quantity, its reserved quantity, and the blocked conclusion without exposing technical call vocabulary.

**Acceptance Scenarios**:

1. **Given** a reply produced from an order-read result, **When** the user expands "Basis for this answer", **Then** the disclosure shows the order's business number and supporting quantity/status values in no more than four compact rows.
2. **Given** a returned record has a supported detail destination, **When** the user selects its link, **Then** the existing tenant-scoped detail or Inspector opens for that exact opaque record identity.
3. **Given** an answer used several reads, **When** its basis is expanded, **Then** the evidence is grouped without duplicate records and remains scannable before optional extra detail.

---

### User Story 2 - Distinguish evidence from derivation (Priority: P1)

As an operations user, I can tell which values were read and which concise conclusion follows from them without treating the conclusion as a newly stored authority.

**Why this priority**: Source-stated values, Reality records, and read-time observations have different authority and must not be blurred.

**Independent Test**: For an order of 10 units with 0 reserved, verify that the basis presents both held values and labels the blocked or uncovered conclusion as derived, without creating a Fact, changing the Document, or storing the conclusion as business state.

**Acceptance Scenarios**:

1. **Given** a read result includes demand and reservation quantities, **When** the basis is rendered, **Then** the values are presented as returned and any concise interpretation is explicitly presented as derived.
2. **Given** the user only expands or closes the basis, **When** the interaction completes, **Then** no business record, proposal, event, or source payload changes.

---

### User Story 3 - Avoid false or empty explanations (Priority: P2)

As a user reading old, fallback, refused, or failed replies, I do not see a disclosure that promises unavailable evidence.

**Why this priority**: Hiding an unavailable optional explanation is clearer than repeatedly stating that internal recording did not happen.

**Independent Test**: Open a historical reply without recorded support and verify that no answer-basis disclosure or misleading unavailable message is rendered.

**Acceptance Scenarios**:

1. **Given** a reply has no recorded supporting read, **When** chat history renders, **Then** the basis control is absent.
2. **Given** recorded support has been pruned or cannot be read, **When** the reply renders, **Then** the answer remains intact and the unavailable basis does not replace or weaken it.
3. **Given** evidence recording fails after a reply is produced, **When** the send completes, **Then** the assistant reply is not repeated and remains usable without the optional basis.

### Edge Cases

- A read returns a bounded/truncated result: disclose that more support existed without inventing omitted records.
- A result contains business numbers but no supported opaque record identity: show the returned value without a false link.
- A reply uses the same record in multiple tool rounds: present one business record and retain the relevant distinct observations.
- A reply contains only a proposal, refusal, provider error, or deterministic no-provider response: do not fabricate a read basis; existing proposal and error behavior remains authoritative.
- A user attempts to fetch another tenant's message or referenced record: behave as not found and reveal no identity or value.
- A supported record is later changed or removed: the basis describes the bounded result used for that reply and its link may independently become unavailable.

## Requirements

### Functional Requirements

- **FR-001**: Every persisted assistant reply MUST be associated with the exact successful canonical read calls used during that reply, whether or not the company participates in a Storyline.
- **FR-002**: Recorded support MUST retain a bounded snapshot of the returned result sufficient to explain the reply without re-running the read or substituting current values.
- **FR-003**: Support recording and reading MUST enforce tenant scope and assistant-message identity; foreign, user, or unknown messages MUST behave as not found.
- **FR-004**: Evidence-recording failure MUST NOT fail, retry, or duplicate a successfully produced chat reply.
- **FR-005**: The web chat MUST label the disclosure "Basis for this answer" and render business-facing labels, identifiers, values, and explicit derived observations before any optional technical detail.
- **FR-006**: The compact basis MUST show at most four primary rows and MUST collapse duplicate record references; additional support MUST be disclosed as a count or secondary expansion.
- **FR-007**: Supported record references MUST navigate through existing tenant-scoped routes using opaque identity while displaying human-readable business references only as labels.
- **FR-008**: Replies with no available supporting reads MUST render no disclosure and no generic unavailable-recording message.
- **FR-009**: The feature MUST preserve existing Storyline trace behavior and proposal confirmation evidence without representing later changes as causes of the answer.
- **FR-010**: Rendering the answer basis MUST be read-only and MUST NOT store a derived observation as a Fact or other business authority.
- **FR-011**: The answer basis, loading behavior, links, and any disclosed limits MUST work in English, German, Dutch, and Spanish and remain usable on desktop and mobile.
- **FR-012**: Historical replies without new support records MUST remain readable and MUST follow FR-008.
- **FR-013**: The durable web product contract MUST describe the answer-basis behavior and supersede the ordinary-company limitation recorded by spec 195 FR-004.

### Key Entities

- **Chat message**: The existing tenant-scoped persisted user or assistant message; an assistant message owns zero or one bounded answer-basis snapshot.
- **Answer-basis call**: One successful canonical read used for a reply, including its stable operation identity, bounded arguments, bounded returned result, and order within the reply.
- **Record reference**: A tenant-scoped opaque record type and ID extracted from an actual returned result, paired with a human-readable label only when the result supplies one.
- **Derived observation**: A read-time explanatory statement based solely on recorded returned values; it is presentation, not stored business authority.

## Success Criteria

### Measurable Outcomes

- **SC-001**: In the open-order acceptance scenario, a user can identify the supporting order, requested quantity, reserved quantity, and derived blocked conclusion within 10 seconds of expanding one control.
- **SC-002**: The primary basis contains no more than four rows and no internal tool name, raw payload, latency, or JSON block.
- **SC-003**: All tested replies that use at least one successful canonical read expose their recorded support after reload; all tested replies without support expose no disclosure.
- **SC-004**: Cross-tenant, non-assistant, and unknown-message tests reveal no support data.
- **SC-005**: A forced support-recording failure produces exactly one persisted assistant reply and leaves normal chat reading available.
- **SC-006**: Automated checks pass for all four supported languages and for narrow and desktop layouts without horizontal page overflow.

## Assumptions and Dependencies

- Canonical read tools already return the business values used by the model; this feature records and presents those returned values rather than asking the model to cite them.
- Existing shared routing can open common Reality, Evidence, and Source records from opaque type/ID pairs; unsupported result shapes remain unlinked rather than guessed.
- A small tenant-scoped persistence addition is justified because ordinary companies have no eligible Storyline run and exact reply attribution must survive reload.
- Existing bounded trace serialization rules are suitable for limiting stored arguments and results, but the new record is independent of Storyline lifecycle and retention.
- Existing authentication, membership, localization, chat history, and record detail services remain authoritative.

## Requirement Traceability

| Requirements | Acceptance and verification |
|---|---|
| FR-001–004, FR-012 | Ordinary-company capture, bounded persistence, reload, failure isolation, historical-null, and tenant/message authorization tests |
| FR-005–008, FR-010 | Fulfillment basis presenter and web contract tests for four-row business presentation, links, derived labels, and hidden empty state |
| FR-009 | Existing Storyline call/proposal trace regression tests |
| FR-011 | Four-language audit, responsive markup contract, TypeScript build |
| FR-013 | Durable `docs/WEB_SPEC.md` contract and spec policy check |
