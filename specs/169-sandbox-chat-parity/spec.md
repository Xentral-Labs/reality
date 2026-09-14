# Feature Specification: The Copilot works the same in Sandbox companies

**Feature Branch**: `169-sandbox-chat-parity`
**Created**: 2026-09-11
**Status**: Draft
**Language**: English
**Input**: "The App copilot behaves identically in Sandbox practice companies and business companies: reads, proposals and confirmed execution. There must be no difference."

## Context and Intent

### Problem

In a Sandbox practice company the App copilot answers every question with "The managed
Copilot could not answer right now. Please try again later (PlaygroundOperationDenied)". The
cause is not an outage: the provider call is guarded by `require_business_operation(...,
"generic_provider_call")`, and the reviewed list of operations a practice company may run
(`_PRACTICE_APP_OPERATIONS`, spec 155) does not contain it. Only the read-only Playground
companion (spec 106) may call the provider inside its own scope.

Spec 155 opened the business reads and the reviewed mutations of the App to practice
companies so that a Sandbox behaves like a real company. The copilot is the one surface that
still differs, and it is the surface a demo viewer tries first. The owner decided that there
must be no difference: the copilot reads, prepares proposals and, after confirmation,
executes them in a practice company exactly as in a business company.

### Scope

- The App copilot's provider call is admitted for active practice companies under the same
  rules as every other reviewed practice operation: persisted eligibility (active practice
  run, verified active owner, unarchived tenant), never a cached label.
- In a practice company the copilot receives the same tool access as in a business company:
  read and propose tools; execution stays behind `proposal_approve_and_execute` and the
  existing decision boundary.
- When the copilot is refused for a company, the chat says why in plain words instead of
  suggesting a transient failure.
- Two finance reads the copilot lacked become public agent tools: available customer or
  supplier credit (payments and credit notes with an unused remainder) and recorded payments
  with allocated and unallocated amounts, so "who paid too much" and "which payments are not
  matched" are answered from records instead of guessed.

### Non-Goals

- No change to the read-only Playground companion of lesson runs (spec 106): outside an
  active practice company the provider call stays refused, and inside the companion scope the
  tool access stays read-only.
- No change to which mutations a practice company may run; the reviewed list of spec 155
  stands, and every copilot mutation still passes it through the proposal boundary.
- No change to AI provider configuration, tokens or the managed key.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md), [workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md).
- [Chat](../../docs/features/chat.md), [chat sessions](../../docs/features/chat_sessions.md).
- Spec 155 (Sandbox business read parity), spec 106 (Playground companion), spec 042 (chat
  and MCP command parity).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask and act in a Sandbox company (Priority: P1)

A demo owner opens a Sandbox practice company, asks the copilot about customer credit, gets an
answer, asks it to prepare a settlement, and confirms the proposal under Decisions.

**Why this priority**: It is the whole feature; a demo that cannot talk is a demo that fails.

**Independent Test**: With a stubbed provider, send a chat message in a practice company and
assert the reply is the provider's text; assert the provider loop receives read and propose
tools; assert a proposal created through the loop appears in `proposals_awaiting_approval`.

**Acceptance Scenarios**:

1. **Given** an active practice company owned by a verified user, **When** the owner sends a
   chat message, **Then** the provider call is admitted and the reply is the provider's text,
   not a denial.
2. **Given** the same company, **When** the copilot loop starts, **Then** its tool access is
   read and propose, identical to a business company.
3. **Given** the same company, **When** the copilot prepares a mutation, **Then** a proposal is
   stored and nothing changes until a person approves it.

---

### User Story 2 - Lesson runs and foreign scopes stay closed (Priority: P1)

A lesson run's companion stays read-only, a playground tenant without an active practice run
gets no provider call, and refusals explain themselves.

**Independent Test**: Existing companion and security tests keep passing; a refused chat
returns a sentence naming the company kind, not "try again later".

**Acceptance Scenarios**:

1. **Given** a lesson run, **When** the companion asks the provider, **Then** only read tools
   are offered, and outside the companion scope the provider call is refused.
2. **Given** a playground tenant without an active practice run, **When** the App chat is
   used, **Then** the chat session itself is refused by the practice policy; **and Given** the
   provider loop refuses an operation for a company, **When** the reply is built, **Then** it
   says the copilot is not available for this company and why.

### User Story 3 - Ask who paid too much (Priority: P1)

In the Sandbox test company three customers hold 25.00 EUR of credit from duplicate payments.
The owner asks the copilot who paid too much. Without a read for available credit the copilot
looked at credit notes, refunds and returns, found none, and answered that no credit exists.

**Why this priority**: It is the first finance question a demo viewer asks, and the answer was
wrong for want of a read, not for want of data.

**Independent Test**: With an overpaid invoice in a tenant, the read tool for available
credit returns the payment with original, used and available amounts; the payments read
returns it with allocated and unallocated amounts; another tenant sees neither.

**Acceptance Scenarios**:

1. **Given** a payment of 120 allocated 100 to an invoice, **When** `finance_credits` is read
   for the customer side, **Then** it lists the payment with original 120, used 100,
   available 20.
2. **Given** the same payment, **When** `finance_payments` is read with only unallocated
   payments, **Then** it lists the payment with allocated 100 and unallocated 20 and the state
   partially allocated.
3. **Given** another tenant, **When** either read runs there, **Then** it returns nothing.

### Edge Cases

- Archived practice company, revoked owner membership, unverified owner: refused like every
  other practice operation.
- A practice company whose owner lost eligibility mid-conversation: the next provider call is
  refused with the explanatory reply; stored messages remain.
- Provider or transport failure in a practice company: the existing "could not answer right
  now" reply, unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The operation `generic_provider_call` MUST be admitted for active practice
  companies through the same persisted eligibility check as the other reviewed practice
  operations.
- **FR-002**: In a practice company the copilot loop MUST offer read and propose tools, and
  MUST NOT offer execution outside `proposal_approve_and_execute`.
- **FR-003**: Outside an active practice company or the companion scope, the provider call
  MUST remain refused; inside the companion scope tool access MUST remain read-only.
- **FR-004**: When the provider loop is refused by the tenant policy, the chat reply MUST state
  that the copilot is not available for this company and the policy's reason, and MUST NOT
  present it as a transient failure.

- **FR-005**: A public read tool `finance_credits` MUST return available customer or supplier
  credit from the shared credit service: document, party, original, used and available amount,
  currency and state, tenant-scoped, without recording anything.
- **FR-006**: A public read tool `finance_payments` MUST return recorded payments with
  direction, amount, allocated and unallocated amount and a state, filterable to unallocated
  payments, tenant-scoped, without recording anything. Both tools MUST carry capability
  guidance that names when to use them and what they do not prove.

### Domain and Traceability Requirements

- **DR-001**: Source → Evidence → Reality is unchanged; the copilot creates no record outside
  proposals and confirmed execution.
- **DR-002**: No schema change.
- **DR-003**: Eligibility is read from persisted tenant, run, owner and membership state only.

## Success Criteria *(mandatory)*

- **SC-001**: A chat message in a practice company with a stubbed provider returns the
  provider's text; the same message in a lesson-run tenant outside the companion scope returns
  the explanatory refusal.
- **SC-002**: Existing companion, security and practice-company tests pass unchanged.
- **SC-004**: Asked who paid too much in the Sandbox test company, the copilot names the
  payments with available credit from `finance_credits` instead of denying that credit exists.
- **SC-003**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- The managed key or a configured provider exists, as today; this feature changes
  admission, not configuration.
- Spec 155's reviewed operation list remains the authority for what a copilot proposal may
  execute in a practice company.

## Open Questions

None.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | `tests/test_playground_chat.py::test_practice_company_copilot_is_admitted` |
| FR-002 | US1 scenarios 2–3 | same test: captured tool access, proposal stored |
| FR-003 | US2 scenario 1 | existing `test_companion_scope_is_read_only`, `test_generic_provider_egress_cannot_bypass_settings` |
| FR-004 | US2 scenario 2 | `tests/test_playground_chat.py::test_refused_copilot_explains_itself` |
| FR-005, FR-006 | US3 scenarios 1–3 | `tests/finance/test_credit_reads.py`, catalog and guidance tests |
| DR-001–DR-003 | all | no schema diff; eligibility test through `practice_company_runs` |
