# Feature Specification: Close External Agent Qualification Gaps

**Feature Branch**: `267-agent-qualification-gaps`
**Language**: English
**Created**: 2026-09-24
**Status**: Draft
**Input**: Close the reproducible gaps found by the fresh-tenant CanisPro final qualification after spec 257 while preserving proposal review, tenant isolation, evidence traceability and no recomputation.

## Context and Intent

### Problem

The fresh-tenant qualification proved that an external agent can operate most of a B2B company
through public tools and owner review. It also reproduced gaps that prevent release closure. Four
deterministic confirmation failures remain permanently `executing`; contribution approval returns
an internal error; physical movements do not inherit the shipment's stated business time; and
several document-producing actions cannot retain stated net and tax values. The same run found
public-contract, read-parity, validation, authorization and explainability gaps.

This feature records those findings as one bounded follow-up backlog. It does not reopen behavior
proved fixed: customer-credit argument retention, unrelated-event receipt-review stability, named
related-event invalidation, exact missing movement IDs, and stated finance detail for order-backed
purchase and sales invoices.

### Scope

Restore terminal and recoverable proposal behavior, contribution review, stated movement time and
complete stated finance evidence first. Then close the public-schema, read-parity, validation,
authorization and explainability gaps reproduced by the same run. Every correction must be
observable through the same public tools and Web product used by an external agent.

### Non-Goals

- No direct-write path for agents and no bypass of proposal review or owner confirmation.
- No recomputation of source-stated money, quantity, price or date values.
- No document-owned operational status.
- No OAuth, connector-installation or token-management redesign.
- No mutation of the retained qualification tenant as an implementation shortcut.
- No implementation in this specification phase; planning follows product/domain review.

## User Scenarios & Testing

### User Story 1 — Failed confirmation reaches a truthful terminal state (Priority: P1)

An agent confirms a reviewed proposal whose execution is deterministically refused. The proposal
ends as failed with no business effect, remains inspectable and does not disappear into an
unrecoverable executing state.

**Why this priority**: A permanent executing state misstates reality and blocks safe recovery.

**Independent Test**: Exercise the four reproduced refusal families—invalid party identity pair,
invalid location identity pair, forbidden external-evidence correction and invalid adjustment
quantity—and verify terminal state, zero effect and public visibility.

**Acceptance Scenarios**:

1. **Given** a reviewed proposal whose validation fails before any effect, **When** it is confirmed,
   **Then** it becomes terminal `failed`, states `business_effect: none`, and exposes the refusal in
   public status and Web history.
2. **Given** a failed proposal, **When** status is read repeatedly, **Then** it stays terminal and no
   business record or event was created or changed.
3. **Given** an execution whose outcome is genuinely unknown, **When** reconciliation cannot prove
   success or failure, **Then** it may remain executing and is distinguished from a deterministic
   refusal.

---

### User Story 2 — Contribution decisions complete without internal errors (Priority: P1)

An owner reviews a contribution candidate, sees the evidence and quantity scope that produced it,
and either approves it or receives a business refusal naming the exact prerequisite.

**Why this priority**: Correct DB1 candidates were calculated but could not be approved.

**Independent Test**: Approve a complete candidate, attempt an incomplete commercial match, and
test a partial-invoice scope; none may produce an internal server error.

**Acceptance Scenarios**:

1. **Given** a complete fresh candidate and matching evidence hash, **When** an active owner
   confirms it, **Then** the decision executes and remains traceable to its inputs.
2. **Given** a missing commercial match or incompatible quantity scope, **When** confirmation is
   attempted, **Then** the proposal stays recoverable and states the affected lines and missing
   prerequisite instead of returning an internal error.
3. **Given** a partial invoice whose inventory portions conserve the stated quantity, **When** it is
   matched, **Then** the documented public contract can express and review the match.

---

### User Story 3 — Physical history uses the stated event time (Priority: P1)

An operator records a receipt, dispatch or return with a stated occurrence time. Every resulting
movement carries that time, and fields outside the published purpose-specific shape are rejected.

**Why this priority**: Posting time in place of event time corrupts inventory history.

**Independent Test**: Record supplier delivery, customer delivery and customer return shipments
with backdated times, plus requests containing unsupported item fields.

**Acceptance Scenarios**:

1. **Given** a shipment with a stated occurrence time, **When** it executes, **Then** every movement
   carries that exact received value.
2. **Given** a field outside the selected shipment purpose, **When** it is proposed, **Then** the
   request is rejected before review and lists the unsupported field.
3. **Given** a return linked to an announcement, **When** that relationship is supported, **Then** it
   is expressed only in its documented location and retained.

---

### User Story 4 — Supported financial documents retain stated components (Priority: P1)

An agent records freight, supplier credits and customer credits with source-stated net, tax and
gross values. Those components remain evidence and let receipt-cost and contribution workflows
finish without recomputation.

**Why this priority**: Missing tax declaration made freight costs, inventory values and DB2
unavailable even though the source stated the values.

**Independent Test**: Record one free supplier invoice, supplier credit and customer credit with
stated components, then read their evidence and affected cost availability.

**Acceptance Scenarios**:

1. **Given** a supported source that states net, tax and gross, **When** it is recorded, **Then** all
   components are retained losslessly on the evidence line.
2. **Given** a source that states gross only, **When** it is recorded, **Then** no net or tax is
   invented and dependent reads name the missing basis.
3. **Given** stated freight or purchase-reduction evidence, **When** it is assigned to receipts,
   **Then** acquisition-cost review can use it without replacing external evidence.

---

### User Story 5 — Public contracts are complete and executable as published (Priority: P2)

An external agent can discover every operation-specific field, enum and example without probing
validation failures, and public status/context reads return structured results.

**Why this priority**: A capability is not safely operable when its contract is empty, silently
ignores fields, or fails with a generic adapter error.

**Independent Test**: Discover cost operations, shipment purposes and credit guidance through the
deployed connector, then exercise proposal status and opening context.

**Acceptance Scenarios**:

1. **Given** the deployed catalog, **When** an agent inspects cost and shipment tools, **Then** each
   operation exposes its complete branch and excludes unrelated fields.
2. **Given** an unknown field, **When** it is submitted, **Then** it is rejected rather than dropped.
3. **Given** a shipment proposal or opening-context read, **When** called, **Then** it returns a
   structured result or a specific refusal, never a generic execution error.
4. **Given** capability guidance, **When** examples and refusals are read, **Then** they are stable
   structured entries rather than sentence fragments used as keys.

---

### User Story 6 — Finance and inventory views explain the complete effect (Priority: P2)

An owner sees dunning fees in open items, inherited payment terms and shipment evidence in invoice
review, and useful return and expiry details in read results.

**Why this priority**: Ledger totals were correct while supporting views omitted parts of the effect.

**Independent Test**: Create a dunning fee, order-backed invoice, expired lot and return
announcement; compare public reads and Web views with their authoritative reality records.

**Acceptance Scenarios**:

1. **Given** a posted dunning fee, **When** balances and open items are read, **Then** the fee appears
   as an explainable open item and totals reconcile.
2. **Given** an inherited payment term, **When** invoice review is shown, **Then** the effective term
   and its source are visible.
3. **Given** a sales invoice backed by dispatch, **When** billing evidence is reviewed, **Then** the
   relevant shipment evidence is present.
4. **Given** an expired lot or return announcement, **When** read, **Then** the result includes status,
   quantity and the relevant date or remaining quantity.
5. **Given** a return restock with a stated reason, **When** its movement is read, **Then** the reason
   is retained.

---

### User Story 7 — Validation, freshness and owner rules are consistent (Priority: P3)

An agent receives specific guidance for price, settlement, expiry, reservation freshness and date
errors, while owner-required decisions enforce the same rule for approval and rejection.

**Why this priority**: These gaps add retries and ambiguity but do not invalidate the working core.

**Independent Test**: Exercise each reproduced boundary with one valid and one invalid request and
compare proposal, approval and rejection behavior.

**Acceptance Scenarios**:

1. **Given** a settlement timestamp, **When** omitted, **Then** contract and runtime agree whether a
   default exists.
2. **Given** a disallowed future date, **When** proposed, **Then** it is rejected with the field and
   accepted range.
3. **Given** an expired lot, **When** reviewed, **Then** preview warns and availability does not
   silently treat it as ordinary stock.
4. **Given** a mismatched price tier, **When** an order is proposed, **Then** the refusal names the
   line and applicable entry.
5. **Given** unrelated reservations, **When** one is confirmed, **Then** another becomes stale only
   if its own delivery evidence changed.
6. **Given** an owner-required proposal, **When** approval or rejection is attempted, **Then** the
   same owner requirement applies.

### Edge Cases

- A handler fails after a partial effect: it must not be labelled effect-free and remains
  reconcilable with known and unknown effects named separately.
- A shipment contains different item occurrence times: refuse it unless the selected contract
  explicitly supports per-item times.
- Received finance components disagree: preserve all values and report the discrepancy.
- A fee is settled immediately: history still explains creation and settlement.
- A lot expires exactly on the business date: one documented inclusive/exclusive rule applies in
  preview and availability.
- A proposal becomes stale while open: show the reason and preserve its audit trail.
- A deep link names a failed, stale or executed proposal: open its history/detail state.

## Requirements

### Functional Requirements

- **FR-001**: Every deterministic effect-free execution refusal MUST leave its proposal terminal
  failed with `business_effect: none`, a structured reason and public visibility.
- **FR-002**: A proposal MAY remain executing only when effect is genuinely unknown; status MUST
  expose reconciliation state and known evidence.
- **FR-003**: Execution MUST be atomic for handlers claiming effect-free failure.
- **FR-004**: Complete contribution approval MUST execute for an active owner and MUST never expose
  an internal error for a business refusal.
- **FR-005**: Commercial matching MUST expose a documented quantity-conserving input and identify
  affected lines, movements and missing portions.
- **FR-006**: Partial-invoice contribution scopes MUST produce a candidate or a specific line-scoped
  refusal.
- **FR-007**: A shipment's stated occurrence time MUST be retained unchanged on every movement it
  creates unless a documented purpose accepts a more specific received time.
- **FR-008**: Shipment inputs MUST reject fields outside the selected purpose branch and retain every
  accepted field.
- **FR-009**: Free supplier invoices, supplier credits and customer credits MUST retain source-stated
  net, tax and gross line components under the no-recomputation rule.
- **FR-010**: A gross-only source MUST remain gross-only; dependent reads MUST name missing evidence.
- **FR-011**: The deployed catalog MUST publish the complete discriminated cost-operation union and
  purpose-specific shipment branches, including nested shapes and enums.
- **FR-012**: Unknown public-tool fields MUST be rejected and MUST NOT be silently ignored.
- **FR-013**: Capability guidance MUST expose complete structured examples, refusals and contracts
  for affected cost, shipment and credit actions.
- **FR-014**: Proposal status and finance opening context MUST return structured results for the
  reproduced valid calls and specific refusals for invalid calls.
- **FR-015**: A posted dunning fee MUST appear in party and Web open items, traceable to its fee
  document and ledger entries.
- **FR-016**: Invoice review MUST expose the effective payment term and its source; sales invoice
  review MUST expose relevant dispatch evidence.
- **FR-017**: Return-announcement and expired-lot reads MUST include actionable status, quantity and
  date/remaining quantity; return restock MUST retain its reason.
- **FR-018**: Settlement required/defaulted timestamps MUST agree between published contract and
  runtime validation.
- **FR-019**: Disallowed future finance and operational dates MUST be rejected before review with a
  field-specific explanation.
- **FR-020**: Receipt preview and availability MUST share one documented expiry rule and warn before
  expired stock is treated as ordinary available stock.
- **FR-021**: Price refusals MUST identify the affected order line and applicable price entry.
- **FR-022**: Freshness MUST invalidate only when relevant evidence changes and MUST name the
  invalidating records or events.
- **FR-023**: Approval and rejection MUST enforce the same owner requirement for owner-governed
  proposals.
- **FR-024**: Proposal deep links MUST open the named proposal's current detail/history and show a
  visible loading state while execution evidence catches up.
- **FR-025**: Final verification MUST use a fresh tenant, public tools and authenticated Web owner
  flow and cover F1–F18 from the 2026-09-24 final qualification.
- **FR-026**: Final verification MUST retain a redacted protocol and mark each F1–F18 finding fixed,
  accepted, superseded or still open with exact evidence.

### Key Entities

- **Proposal**: Reviewed mutation request with principal requirement, freshness evidence, lifecycle,
  receipt and business-effect classification.
- **Contribution Candidate and Review**: Evidence-scoped result, quantity match, hash and decision.
- **Shipment and Movement**: Physical event and authoritative movements it creates.
- **Document Line Evidence**: Lossless received financial components and resulting links.
- **Open Item**: Party claim or obligation, including fee-origin items and settlements.
- **Public Capability Contract**: Discoverable operation branches, fields, enums and guidance.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All four reproduced deterministic failures become terminal failed with zero effect;
  zero remain executing after reconciliation.
- **SC-002**: Three complete contribution candidates are approved with no internal error; incomplete
  candidates return line- or quantity-scoped refusals.
- **SC-003**: Supplier delivery, customer delivery and return samples retain the exact source-stated
  occurrence time on 100% of created movements.
- **SC-004**: Unknown fields in affected shipment and cost branches are rejected in 100% of contract
  tests; no accepted field is dropped.
- **SC-005**: Freight, supplier-credit and customer-credit samples retain all stated components; a
  gross-only control remains explicitly incomplete without derivation.
- **SC-006**: The deployed connector exposes non-empty operation-specific contracts for all supported
  cost operations and shipment purposes.
- **SC-007**: Dunning-fee balances and open items reconcile exactly when open, partially settled and
  settled.
- **SC-008**: Status, opening-context, return and expiry reads complete without generic errors and
  provide every field required by their scenarios.
- **SC-009**: A fresh-tenant qualification finishes with no critical/high finding and records an
  evidence-backed disposition for all F1–F18.
- **SC-010**: Previously fixed credit, freshness, invalidation, movement-ID and invoice-evidence
  regressions remain green.

## Assumptions and Dependencies

- The final-qualification protocol is the evidence source for F1–F18; the repository retains a
  redacted summary rather than depending on its machine-specific path.
- Canonical proposal, costing, shipment, finance, return and inventory services remain the only
  behavior authorities; Web and MCP remain adapters.
- Tenant scoping, owner confirmation, opaque identity and Source → Evidence → Reality remain intact.
- Inconsistent source values are preserved and reported, never normalized.
- P1 stories are release/demo blockers. P2/P3 may ship separately, but final qualification covers
  every F1–F18 disposition.
- Sequencing, migration impact and rollback design are deferred to planning.

## Requirement Traceability

| Qualification finding | User story | Requirements | Success criteria |
|---|---|---|---|
| F1 — deterministic proposals remain executing | US1 | FR-001–FR-003 | SC-001 |
| F2 — contribution confirmation and commercial match | US2 | FR-004–FR-006 | SC-002 |
| F3 — shipment occurrence and unknown fields | US3 | FR-007–FR-008, FR-012 | SC-003–SC-004 |
| F4 — incomplete deployed cost-operation contract | US5 | FR-011–FR-013 | SC-006 |
| F5 — generic proposal-status/opening-context errors | US5 | FR-014 | SC-008 |
| F6 — proposal deep-link and loading behavior | US7 | FR-024 | SC-009 |
| F7 — finance components absent from free/credit documents | US4 | FR-009–FR-010 | SC-005 |
| F8 — dunning fee absent from open items | US6 | FR-015 | SC-007 |
| F9 — payment-term and dispatch evidence omitted | US6 | FR-016 | SC-008 |
| F10 — settlement timestamp contract mismatch | US7 | FR-018 | SC-009 |
| F11 — expired lot warning and availability | US7 | FR-020 | SC-009 |
| F12 — non-actionable price refusal | US7 | FR-021 | SC-009 |
| F13 — over-broad reservation invalidation | US7 | FR-022 | SC-010 |
| F14 — skeletal return/expiry reads | US6 | FR-017 | SC-008 |
| F15 — lost restock reason | US6 | FR-017 | SC-008 |
| F16 — future dates accepted | US7 | FR-019 | SC-009 |
| F17 — malformed capability refusals | US5 | FR-013 | SC-006 |
| F18 — rejection bypasses owner rule | US7 | FR-023 | SC-009 |
| Complete external requalification | US1–US7 | FR-025–FR-026 | SC-009–SC-010 |
