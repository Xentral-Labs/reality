# Feature Specification: A stale review can be renewed

**Feature Branch**: `273-stale-review-refresh`
**Language**: English
**Created**: 2026-09-25
**Status**: Draft (defect found while reproducing an agent-proposed order-to-cash run)
**Input**: An agent was asked which orders are open and to prepare the decisions for shipping and invoicing them. It created the decisions, but approving them fails with "The delivery changed. Prepare a fresh review." and nothing in the product prepares one.

## Context and Intent

### Problem

A delivery-reviewed proposal carries a review token that fingerprints tenant, tool, intent
and the delivery state at the moment the token was made
(`services/delivery_actions.py:381-393`, `services/shipment_actions.py:253-257`). Approval
recomputes that fingerprint and refuses when it differs (`validate_review`,
`services/delivery_actions.py:466-479`). The refusal is correct: a person must confirm
against the reality that is, not the reality that was.

The token is attached when the proposal is **created**
(`tools/application.py:2789-2802`). An agent asked to prepare the decisions for several
open orders therefore mints several tokens against one shared moment. Approving the first
decision moves the very state the others fingerprint — a new reservation, a new movement —
so every remaining decision is stale before the operator reaches it.

The refusal names the remedy, and the remedy does not exist. `review_existing` attaches a
review only when none is stored (`services/delivery_actions.py:515`), so
`POST /delivery-actions/{id}/review` — the "prepare a fresh review" call the Decisions
dialog makes when it opens (`web/api.py:1245-1254`, `unified/ShipmentActions.tsx:60-68`) —
returns the stale token unchanged. `prepare_delivery_action` hands back an existing
proposal untouched for the same reason (`services/delivery_actions.py:427-434`). No path in
the repository rewrites a stored `_delivery_review`. The decision can be rejected; it can
never be approved.

Reproduced on `origin/main` at fdfc62c2 in company `ten_43c9e77e12`: proposal
`act_482c337101` (`shipment_dispatch`) refused approval; a second call to
`review_existing` left its token at `90040a76…`; the recomputed fingerprint was
`e9ac4bce…`, differing only by the reservation created by the decision approved just
before it; writing the recomputed review made the identical decision execute.

### Principle

A refusal may only name a remedy the product can perform. A review is the operator's
window onto current reality: reopening it must show what is true now, and confirmation must
still be measured against exactly what was shown.

### Scope

Renewing a stored review when, and only when, the operator explicitly asks to review a
pending proposal again. The renewed review replaces the stored one, which retires the old
token, and the operator confirms against the review they were shown.

### Non-Goals

No change to what makes a token, to when approval refuses, or to the refusal's wording.
Approval never renews a review — silently re-reviewing inside confirmation would confirm on
the operator's behalf, which is the failure this feature exists to prevent. No automatic,
bulk or deferred approval, no retry of a refused confirmation, no new endpoint, no schema
change, and no change to executed, executing or rejected proposals. The second defect found
in the same run — `movement_create` with `opening_stock` accepts a lot-tracked item at
proposal time and only refuses at approval (`services/opening_stock_actions.py:78-80`) — is
the same shape of problem but a separate intent, and is not addressed here.

## User Scenarios & Testing

### User Story 1 — Approve the second decision of a batch (Priority: P1)

An operator asks an agent to prepare the decisions for the open orders. The agent creates
them together. The operator approves them one after another, and each one presents what is
true at the moment they reach it.

**Independent Test**: create two delivery-reviewed proposals against one item and location,
approve the first, then open and approve the second; the second executes once and its
receipt records the state that existed when it was confirmed.

**Acceptance Scenarios**:

1. **Given** two pending proposals fingerprinting the same delivery state, **When** the
   first is approved and the second is opened for review, **Then** the second shows a
   review computed from the state that now exists and carries a different token.
2. **Given** that renewed review, **When** the operator confirms it, **Then** the proposal
   executes exactly once and stores its receipt.
3. **Given** a stored review that still matches current state, **When** the proposal is
   opened for review again, **Then** its token is unchanged and no write occurs.
4. **Given** a review renewed after an operator held a token from the previous review,
   **When** that previous token is offered for confirmation, **Then** approval refuses and
   nothing executes.

---

### User Story 2 — A refusal that stays honest (Priority: P1)

An operator who is told the delivery changed can act on that sentence, and an operator
whose action is no longer possible at all learns why rather than being told to refresh.

**Independent Test**: stale one proposal by a state change that keeps it valid and another
by a state change that makes it impossible; review both again and compare what each says.

**Acceptance Scenarios**:

1. **Given** a proposal refused as stale, **When** the operator opens its review again,
   **Then** the decision becomes confirmable without rejecting and re-creating it.
2. **Given** a proposal whose intent can no longer be reviewed at all, **When** the review
   is renewed, **Then** its stored review is left exactly as it was, the decision stays as
   readable and as rejectable as it was before renewal existed, and confirmation still
   refuses it.
3. **Given** a proposal that is executed, executing or rejected, **When** a review renewal
   is attempted, **Then** its stored review and status are unchanged.

---

### User Story 3 — Confirmation still means what it says (Priority: P1)

Nothing in this feature lets a decision execute against a reality the operator was not
shown.

**Independent Test**: confirm with a token that no review ever issued, and confirm a
proposal whose state moved between its review and its confirmation; both refuse.

**Acceptance Scenarios**:

1. **Given** any proposal, **When** approval is called, **Then** it never renews a review
   and never accepts a token it computed itself.
2. **Given** state that moves between renewal and confirmation, **When** confirmation is
   offered, **Then** it refuses exactly as it does today.

### Edge Cases

- Two operators reviewing the same proposal in two tabs; the later renewal retires the
  earlier token.
- A proposal prepared under a request identity, whose stated request arguments must survive
  renewal so the identity's intent check keeps working.
- A renewal that races an approval of the same proposal under the delivery-state lock.
- Practice companies, where delivery review is not attached at all.
- A proposal whose stored review predates a change to how its review is computed.

## Requirements

- **FR-001**: Reviewing a pending proposal again MUST compute its review from its stored
  intent and current tenant state, and MUST store that review in place of the previous one
  when the two differ.
- **FR-002**: Renewal MUST leave the stored review untouched when the recomputed review is
  identical, and MUST NOT write in that case.
- **FR-003**: Renewal MUST preserve the stated request arguments recorded by a
  request-identity preparation, so that identity's intent comparison keeps its meaning.
- **FR-004**: Renewal MUST apply only to a proposal in `proposed` status, under the same
  decision authorization and delivery-state lock that guard review today.
- **FR-005**: Approval MUST NOT renew a review; it MUST continue to compare the offered
  token against the stored review and refuse on any difference.
- **FR-006**: A token retired by renewal MUST NOT execute the proposal.
- **FR-007**: When a stored review exists and the intent can no longer be reviewed against
  current state, renewal MUST leave that stored review and the proposal status unchanged
  rather than failing the read, so the decision stays readable and rejectable. A proposal
  that has no stored review keeps today's refusal.

## Key Entities

- **Change proposal**: existing tenant-scoped stored intent, review, status and receipt.
- **Delivery review**: the stored, state-bound fingerprint and preview of one intent; it is
  replaced in place by renewal and is never a second proposal.

## Success Criteria

- **SC-001**: A batch of delivery decisions created together can be approved one by one,
  each against the state it meets, with no rejection and re-creation.
- **SC-002**: No proposal reachable in Decisions is permanently unapprovable through a
  stale review.
- **SC-003**: Existing delivery, shipment, opening-stock, hold, invoice and correction
  review suites remain green, including the refusals they assert.
- **SC-004**: No schema migration, no new endpoint and no new business rule.

## Assumptions and Dependencies

The review token remains the authority on whether a confirmation matches current state, and
`validate_review` remains unchanged. The Decisions dialog prepares a review when it opens,
so renewal reaches the operator through the existing call. Spec 249 (FR-007) requires that
reload and revisit restore a pending review without re-preparing the *action*; renewing the
review of an already-identified proposal creates no action and keeps the proposal's opaque
identity, so the two remain compatible. Spec 250 (US4) states that a refusal explains
whether a fresh review is required; this feature makes that explanation actionable.

## Requirement Traceability

| Requirement     | Story    | Planned proof                                                  |
| --------------- | -------- | -------------------------------------------------------------- |
| FR-001, FR-002  | US1      | Service tests on renewal after a state change and on a no-op renewal |
| FR-003          | US1      | Request-identity preparation reused after renewal               |
| FR-004, FR-007  | US2      | Status and refusal tests around renewal                         |
| FR-005, FR-006  | US1, US3 | Approval tests with retired and self-made tokens                |
