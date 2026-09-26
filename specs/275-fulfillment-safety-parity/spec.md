# Feature Specification: Fulfillment Safety Parity

**Feature Branch**: `275-fulfillment-safety-parity`

**Created**: 2026-09-26

**Status**: Approved scope

**Language**: English

**Input**: Implement the first prioritized findings from the 2026-09-26 browser and MCP
order-to-cash qualification: native prepayment enforcement, one fulfillment-readiness
decision across surfaces, truthful proposal failure states and review freshness, complete
shipment contracts, and Web/Chat/MCP parity proof.

## Context and Intent

### Problem

Two isolated fresh-company qualifications completed the same procurement and order-to-cash
story through Browser Chat and an external MCP agent. Browser Chat refused an unpaid
prepayment order with the amount required and received. MCP reported the equivalent order
as ship-ready and prepared a dispatch proposal. The agent rejected that proposal before it
could move stock, added a manual hold as a compensating control, posted the payment, released
the hold and then shipped.

The same MCP run found deterministic execution refusals that remained indefinitely
`executing`, previews that accepted already-invalid actions, a dispatch review token that
did not reflect payment or hold changes, and shipment tools whose published schemas omitted
the inputs required to call them. These are one safety problem: an operator or agent cannot
rely on the reviewed fulfillment decision being complete, current and equivalent across
surfaces.

This feature is the bounded first slice selected from the broader qualification backlog in
spec 267. It closes the safety-critical prepayment and proposal-contract gaps before larger
workflow or conversational usability work begins.

### Scope

- Express prepayment as an explicit payment-term policy that fulfillment can act on.
- Derive one explainable fulfillment-readiness result from commitments, stock,
  reservations, active holds, invoiced amount and allocated payment evidence.
- Use that shared decision in Web, Chat and MCP proposal preparation and execution.
- Make deterministic, effect-free execution refusals terminal and inspectable.
- Bind dispatch review freshness to every state that can change readiness.
- Publish complete purpose-specific shipment proposal contracts and enum values.
- Prove equivalent behavior through a deterministic browser/application/MCP business story.

### Non-Goals

- No automatic collection, payment guessing, credit decision or payment allocation.
- No document-owned delivery, reservation, shipment or payment status.
- No rule that infers prepayment from a human-readable term code or label.
- No redesign of every payment term, credit limit, dunning or fulfillment policy.
- No full guided onboarding workflow, conversational entity resolver or general Chat rewrite.
- No repair of every finding in spec 267; contribution, costing, expiry, returns and other
  independent findings remain there.
- No direct database mutation or transport-specific business rule.

## User Scenarios & Testing

### User Story 1 - Unpaid prepayment orders cannot ship (Priority: P1)

An operator creates an order whose agreed payment term requires prepayment. Reality shows
the amount required, the qualifying amount received and a payment blocker until enough
allocated customer payment evidence exists. No supported surface can prepare or execute a
shipment while the blocker remains.

**Why this priority**: Shipping unpaid prepayment orders creates direct financial loss and
the reproduced MCP path could have done so.

**Independent Test**: Create and invoice a ten-unit prepayment order with available and
reserved stock, attempt dispatch through each public surface before payment, fully allocate
payment and then dispatch. Before payment every attempt refuses without a movement; after
payment the same order becomes shippable.

**Acceptance Scenarios**:

1. **Given** a prepayment order with stock and an active reservation but no allocated
   payment, **When** fulfillment readiness is read, **Then** it reports not ship-ready,
   states the required, received and remaining amounts, and names prepayment as the blocker.
2. **Given** that unpaid order, **When** Web, Chat or MCP prepares or executes dispatch,
   **Then** each path refuses through the same business rule and creates no shipment,
   package or movement.
3. **Given** qualifying allocations equal to the required amount, **When** readiness is
   read and dispatch is reviewed, **Then** the payment blocker is absent and dispatch may
   proceed if no other blocker exists.
4. **Given** a partial payment, overpayment, reversed allocation or allocation for another
   party, currency or invoice, **When** readiness is read, **Then** only active allocations
   that settle the relevant order-backed receivable count.
5. **Given** an ordinary net-term order, **When** it is unpaid, **Then** prepayment alone
   does not block its dispatch.

---

### User Story 2 - One explainable fulfillment decision serves every surface (Priority: P1)

An operator or agent sees one current readiness explanation containing stock, reservation,
hold and payment evidence. The proposal preview and execution use the same decision and
cannot disagree merely because they were reached through different transports.

**Why this priority**: A safety rule is ineffective if one adapter can bypass it or display
a different answer.

**Independent Test**: Read and review the same order through application, Web adapter, Chat
tool and MCP tool before and after each relevant state change, and compare the normalized
decision and refusal reason.

**Acceptance Scenarios**:

1. **Given** identical tenant state and intent, **When** readiness is requested through
   supported surfaces, **Then** the ship-ready decision, blocker codes and evidence amounts
   are equivalent.
2. **Given** multiple blockers, **When** readiness is read, **Then** all current blockers are
   returned rather than only the first failure.
3. **Given** a blocker changes after review, **When** the old proposal is confirmed, **Then**
   confirmation refuses as stale without executing and directs the operator to a fresh
   review.
4. **Given** a readiness result, **When** an operator inspects it, **Then** each quantity and
   amount is traceable through opaque links to its authoritative Reality and evidence
   records.

---

### User Story 3 - Proposal failures are truthful and recoverable (Priority: P1)

An operator confirms a reviewed action that is deterministically invalid. The proposal
reaches a terminal failed state with no business effect and a specific refusal instead of
remaining indefinitely executing.

**Why this priority**: A stuck proposal hides whether an effect happened and makes safe
recovery impossible.

**Independent Test**: Confirm a duplicate invoice post and a shipment with a deterministic
pre-effect refusal, then read each proposal repeatedly and prove a terminal failure, zero
effect and a stable receipt.

**Acceptance Scenarios**:

1. **Given** validation can prove before an effect that execution must refuse, **When** the
   action is confirmed, **Then** its proposal becomes terminal failed and records
   `business_effect: none` with a structured reason.
2. **Given** a handler transaction is known to have rolled back completely, **When** the
   refusal returns, **Then** the proposal is terminal failed and no effect is reported.
3. **Given** the outcome is genuinely unknown, **When** no authoritative evidence resolves
   it, **Then** the proposal may remain executing and explicitly states that reconciliation
   is required.
4. **Given** a terminal failed proposal, **When** it is opened in Web or read through MCP,
   **Then** both surfaces expose the same lifecycle, refusal and safe next action.

---

### User Story 4 - Shipment tools are executable from their published contracts (Priority: P1)

An external agent can discover every required shipment field, nested movement shape,
purpose value and refusal without probing runtime validation errors.

**Why this priority**: Missing schemas force agents to guess business-critical requests and
undermine safe automation.

**Independent Test**: Generate the public catalog, inspect each shipment proposal schema,
build a valid request from the schema alone and verify that unknown fields and invalid enum
values are rejected before review.

**Acceptance Scenarios**:

1. **Given** shipment receipt or dispatch discovery, **When** its input contract is read,
   **Then** it contains a non-empty purpose-specific shape including required nested
   movements and documented enum values.
2. **Given** a request built from the published contract, **When** it is proposed, **Then**
   it reaches review without schema discovery through errors.
3. **Given** an unknown field, unsupported purpose or invalid hold reason, **When** it is
   proposed, **Then** preparation refuses with the exact field and permitted values.
4. **Given** capability guidance for a shipment mutation, **When** it is requested by its
   canonical public name, **Then** guidance describes prerequisites, expected refusals and
   verification reads.

### Edge Cases

- An order is covered by multiple invoices or one invoice covers multiple orders: only
  unambiguous active allocations attributable to the relevant order count automatically;
  ambiguous coverage blocks and explains the missing attribution.
- An invoice or payment is in another currency: it does not satisfy the prepayment gate.
- An allocation is reversed between review and confirmation: the old dispatch review is
  stale and execution creates no movement.
- Stock, reservation, hold and payment state change together: readiness reports the current
  complete blocker set and the review token changes once for the resulting state.
- A shipment contains multiple movements: the whole confirmed action is refused before
  effect when any movement's commitment is not ready.
- A deterministic refusal occurs after the proposal was claimed for execution but before
  any business effect: failure finalization must still occur.
- An unexpected infrastructure interruption makes effect unknown: the lifecycle must not
  assert failure merely because no receipt was returned.

## Requirements

### Functional Requirements

- **FR-001**: A payment term MUST explicitly state whether fulfillment requires prepayment;
  the policy MUST NOT be inferred from its code, name or due-day value.
- **FR-002**: The prepayment policy MUST be tenant-scoped, visible in payment-term reads and
  retained when an order records that term.
- **FR-003**: Fulfillment readiness MUST derive required, qualifying received and remaining
  amounts at read time from recorded invoice and active settlement-allocation evidence.
- **FR-004**: Prepayment qualification MUST require the same tenant, customer, currency and
  unambiguous order-backed receivable; reversed or inactive allocations MUST not count.
- **FR-005**: A prepayment order MUST remain non-shippable until the qualifying received
  amount is at least the required amount.
- **FR-006**: Net-term orders MUST retain their existing shipping behavior unless another
  independent blocker applies.
- **FR-007**: One shared fulfillment-readiness decision MUST combine commitment status,
  active holds, physical availability, reservation coverage and payment readiness.
- **FR-008**: Web, Chat, MCP and application tools MUST consume the shared decision and MUST
  NOT implement alternative readiness rules.
- **FR-009**: Readiness MUST expose stable blocker codes, human explanations, relevant
  quantities and money amounts, plus opaque links to their authoritative records.
- **FR-010**: Shipment preparation and execution MUST both enforce current readiness and
  MUST create no shipment, package or movement on refusal.
- **FR-011**: A dispatch review token MUST cover every current record or revision whose
  change can alter readiness, including qualifying payment allocations and active holds.
- **FR-012**: A state change that alters readiness MUST retire the previous dispatch review;
  a state change irrelevant to that intent MUST NOT make it stale.
- **FR-013**: Deterministic pre-effect validation refusals and known complete rollbacks MUST
  transition a claimed proposal to terminal failed with `business_effect: none` and a
  structured refusal receipt.
- **FR-014**: A proposal MAY remain executing only while its business effect is genuinely
  unknown, and its status MUST expose the reconciliation requirement.
- **FR-015**: Proposal detail, history and MCP status MUST expose equivalent terminal failure
  information and a safe next action.
- **FR-016**: Shipment proposal tools MUST publish complete discriminated input contracts
  for every supported purpose, including required nested movement shapes and enum values.
- **FR-017**: Public proposal preparation MUST reject unknown fields, including undeclared
  nested fields, and invalid enum values before review and return permitted values. MCP
  transports MUST enforce the published closed-object contract before permissive SDK argument
  binding can discard undeclared fields or invoke domain dispatch.
- **FR-018**: Capability discovery and description MUST resolve the canonical public names
  of the affected shipment tools and return prerequisites, refusals and verification reads.
- **FR-019**: Generated tool-usage documentation MUST reflect the executable schemas and
  capability catalog after the contract changes.
- **FR-020**: A deterministic acceptance story MUST prove `30 received - 20 shipped = 10`,
  two fully allocated invoices, refusal of the unpaid prepayment shipment with zero effect,
  and shipment only after full allocation.
- **FR-021**: The acceptance story MUST exercise the shared behavior through Web/Chat and
  MCP adapters and compare normalized readiness, lifecycle and effect evidence.

### Key Entities

- **Payment Term**: Tenant-scoped commercial agreement containing stated due-day behavior
  and an explicit prepayment requirement used by fulfillment.
- **Fulfillment Readiness**: A read-time observation for one dispatch intent containing
  stock, reservation, hold and payment evidence, blocker codes and trace links.
- **Dispatch Review**: Persisted review of exact intent plus the readiness-relevant state
  fingerprint that the operator confirms.
- **Change Proposal**: Tenant-scoped reviewed mutation with lifecycle, refusal/effect
  classification, receipt and reconciliation state.
- **Settlement Allocation**: Authoritative active link between received money and the
  relevant receivable; only qualifying allocations satisfy prepayment.
- **Shipment Contract**: Discoverable purpose-specific request shape for a physical
  consignment and its exact movements.

## Success Criteria

### Measurable Outcomes

- **SC-001**: In the acceptance story, 100% of unpaid prepayment dispatch attempts through
  Web/Chat and MCP refuse before effect and create zero shipment, package and movement
  records.
- **SC-002**: After full qualifying allocation, both surfaces report the order ship-ready
  and the confirmed dispatch occurs after the payment evidence timestamp.
- **SC-003**: Equivalent readiness requests across supported surfaces return the same
  decision, blocker codes, required/received/remaining amounts and authoritative IDs.
- **SC-004**: Every tested relevant payment or hold change retires an old dispatch review;
  unrelated events leave it valid.
- **SC-005**: 100% of tested deterministic effect-free refusals reach terminal failed with
  a stable receipt; genuinely unknown controls remain explicitly reconcilable.
- **SC-006**: Every supported shipment purpose exposes a non-empty executable schema with
  all enum and nested fields required to build a valid request without error probing.
- **SC-007**: The full story reconciles exactly to 10 physical and available units, zero
  reserved units, zero open amount on both invoices and zero premature shipment effect.
- **SC-008**: Existing shipment, reservation, hold, invoice, settlement, tenant-isolation
  and review-freshness suites remain green.

## Assumptions and Dependencies

- The 2026-09-26 browser and MCP protocols in
  `docs/ideas/manual-e2e-usability-learnings-2026-09-26.md` are the reproduction evidence.
- Payment remains independent evidence; this feature derives readiness and does not add a
  payment status field to orders or invoices.
- Existing invoice-to-order line links and settlement allocations provide the shortest true
  path from an order commitment to qualifying payment evidence.
- Existing shared shipment, reservation, hold, finance and proposal services remain the
  authorities; adapters stay thin.
- An explicit prepayment policy is a proven typed field because fulfillment repeatedly
  constrains and acts on it. The plan must choose the smallest compatible representation and
  document migration/default behavior.
- Existing payment terms default to not requiring prepayment unless evidence already states
  otherwise; no label- or code-based backfill is permitted.
- Spec 267 remains the broader backlog. This feature supersedes only its overlapping
  deterministic proposal-failure and shipment-contract work when implemented.

## Requirement Traceability

| Qualification finding | User story | Requirements | Success criteria |
|---|---|---|---|
| MCP allowed an unpaid VORKASSE dispatch proposal | US1 | FR-001–FR-006, FR-010 | SC-001–SC-002 |
| Web and MCP disagreed on ship readiness | US2 | FR-007–FR-012 | SC-003–SC-004 |
| Deterministic refusals remained executing | US3 | FR-013–FR-015 | SC-005 |
| Shipment schemas and enums were incomplete | US4 | FR-016–FR-019 | SC-006 |
| End-to-end parity and reconciliation | US1–US4 | FR-020–FR-021 | SC-007–SC-008 |
