# Feature Specification: A Caller Key Makes a Payment or Invoice Proposal Safe to Retry

**Feature Branch**: `387-proposal-idempotency-key`
**Language**: English
**Created**: 2026-10-12
**Status**: Proposal — needs the owner's decision before planning continues
**Input**: An agent driving procure-to-pay over MCP lost the response to `payment_run_propose`
and could not tell whether retrying would prepare a second run.

## Context and Intent

### Problem

`payment_run_propose` and `supplier_invoice_record_propose` take no caller key. Every call
creates a new proposal (`create_change_proposal`), so a client that loses a response and retries
leaves two proposals. Once both are approved:

- a second payment run pays the same invoices again, up to what is still open;
- a second supplier invoice is recorded with the same number until the billable quantity is used
  up. It is reported as `duplicate_supplier_invoice` and withheld from payment runs, but a person
  has to clear it.

Approving one proposal twice is already safe: the execution claim runs it once and a replay
returns the stored receipt. The gap is the proposal step, before any person has looked.

`fact_observe_propose` and `reality_gap_create_propose` already take an `idempotency_key`, but
neither dedupes the proposal. `observe_fact` and `capture_gap` fingerprint
`sha256(tenant_id, key)` when the change **executes**: the same key with the same content returns
the existing Fact or gap, and the same key with other content is refused
(`core.py` `observe_fact`, `reality_gaps.py` `capture_gap`). That pattern cannot simply be
reused here. A payment run records no SourceRecord and no row of its own that could carry a
fingerprint, and an execution-time check would still leave a person two proposals to review.

### Scope

- Both tools accept an optional `idempotency_key` with the format and meaning of
  `fact_observe_propose`'s: a caller-chosen string, trimmed, fingerprinted per company.
- The same key and the same arguments return the existing proposal instead of creating one.
- The same key with different arguments is refused with a coded refusal.

### Non-Goals

- No change to execution, to approval, or to what either tool refuses today.
- No key on any other tool in this increment, and no change to `fact_observe_propose` or
  `reality_gap_create_propose`.
- No refusal of duplicate supplier invoice numbers, no proposal expiry or withdrawal, no owner
  gating of payment runs. These are separate questions.
- No key in the web forms or the CLI in this increment. The shared service accepts it, so they
  can follow without new rules.

## User Scenarios & Testing

### User Story 1 - A lost response is retried safely (Priority: P1)

As an agent, I resend a payment run proposal with the same key after a timeout and get the
proposal I already made, not a second one.

**Independent Test**: Propose a run with key K, propose it again with K and identical arguments;
one proposal exists and both calls return its id.

**Acceptance Scenarios**:

1. **Given** a proposal made with key K, **When** the same tool is called with K and identical
   arguments, **Then** the existing proposal id and its current status are returned and no
   proposal is created.
2. **Given** that proposal was already executed, **When** the call is repeated, **Then** the
   executed proposal is returned and nothing executes again.
3. **Given** a proposal made with key K, **When** the same tool is called with K and a different
   amount, **Then** the call is refused with `proposal_idempotency_key_reused` and no proposal is
   created.
4. **Given** no key, **When** either tool is called twice, **Then** two proposals are created, as
   today.

### User Story 2 - Keys never cross a boundary (Priority: P1)

**Acceptance Scenarios**:

1. **Given** key K used by company A, **When** company B uses K, **Then** B gets its own
   proposal and learns nothing about A's.
2. **Given** key K used for a payment run, **When** a supplier invoice is proposed with K,
   **Then** it gets its own proposal (keys are scoped per tool).

### Edge Cases

- Arguments are compared as stated after the adapter drops absent values: `"100"` and
  `"100.00"` are different arguments.
- A blank or whitespace-only key is refused with `proposal_idempotency_key_blank`.
- Two concurrent calls with the same key create one proposal; the other call returns it.
- A rejected or failed proposal is returned like any other; a new attempt needs a new key
  (see D-3).

## Requirements

### Functional Requirements

- **FR-001**: `payment_run_propose` and `supplier_invoice_record_propose` MUST accept an optional
  `idempotency_key` string, through the shared `create_change_proposal` service.
- **FR-002**: A call with a key already used by the same company for the same tool and with
  identical arguments MUST return the existing proposal and MUST NOT create another.
- **FR-003**: A call with such a key and different arguments MUST be refused with the coded
  refusal `proposal_idempotency_key_reused`, and a blank key with
  `proposal_idempotency_key_blank`, each with German, Dutch and Spanish wording (spec 286).
- **FR-004**: Without a key, both tools MUST behave exactly as today.
- **FR-005**: The tools' capability guidance MUST describe the key (idempotency mode
  `supported`, with how to retry).

### Domain and Architecture Requirements

- **DR-001**: The key MUST be fingerprinted per company and tool; a key MUST NOT be matched
  across companies, and a refusal MUST NOT reveal another company's proposal.
- **DR-002**: Uniqueness MUST be enforced by the database, not by a read before the write, so
  that concurrent calls cannot both create a proposal (see D-2).

### Decisions requested

- **D-1**: Optional or required. Proposal: **optional**. Both tools exist and have callers (the
  web review, chat, external MCP clients); requiring the key would break every current caller
  for a protection only a retrying client needs. `fact_observe_propose` and
  `reality_gap_create_propose` require it because they were designed with it.
- **D-2**: Where the fingerprint lives. Proposal: a nullable `request_fingerprint` column on the
  proposal table (`action`) with a unique index on (tenant_id, type, request_fingerprint) where
  it is set. This is a schema expansion and needs approval (Constitution III). The use is repeated
  and money-bearing: every retried proposal of either tool reads and constrains on it. Rejected
  alternatives: searching the proposal's input JSON (no index, and races allow duplicates);
  dedupe at execution like `observe_fact` (a payment run has no row to carry the fingerprint,
  and a person would still face two proposals).
- **D-3**: What a spent key returns. Proposal: the existing proposal in whatever state it is
  in (proposed, executed, rejected, failed). The caller reconciles from that status, and a new
  attempt uses a new key.

## Success Criteria

### Measurable Outcomes

- **SC-001**: In an executed test, a retried call with the same key and arguments leaves
  exactly one proposal and one payment run.
- **SC-002**: In an executed test, the same key with a different amount is refused with
  `proposal_idempotency_key_reused`.

## Assumptions and Dependencies

- Spec 044 and its 2026-10-12 amendment: capability guidance for both tools.
- Spec 286: coded refusals and their translations.
- Spec 098 (payment run) and the invoice recording contracts are unchanged.
- Key format and fingerprint follow `observe_fact` and `capture_gap`:
  `sha256(tenant_id, tool, trimmed key)`.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 1 | MCP input schema test for both tools |
| FR-002 | US1 1, 2; Edge cases | service test: same key and arguments return one proposal; concurrent calls |
| FR-003 | US1 3; Edge cases | service test: changed amount and blank key refused with codes; localization test |
| FR-004 | US1 4 | the existing proposal tests, unchanged |
| FR-005 | — | capability guidance test |
| DR-001 | US2 1, 2 | cross-company and cross-tool test |
| DR-002 | Edge cases | migration test of the unique index; concurrent-call test |
