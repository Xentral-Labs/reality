# Feature Specification: An Invoice Somebody Can Actually Book

**Feature Branch**: `091-invoices-can-be-booked`
**Created**: 2026-09-06
**Status**: Draft
**Language**: English
**Input**: "Posting a sales or supplier invoice is called by the demo and the test suite and by nothing else. No endpoint, no agent tool, no command. Every money class in the queue waits for a posted invoice, so on a real tenant none of them can ever fire."

## Context and Intent

### Problem

A credit note can be recorded, booked, netted and refunded from the API, the agent tools and the
chat surface. Specs 084 and 089 built all of that.

**The invoice — the document both chains actually hang on — has no way to be booked at all.**
`post_sales_invoice` and `post_supplier_invoice` are called by `demo/normal_month.py` and by the
test suite. There is no endpoint, no agent tool, no MCP schema and no entry in the command
catalog. Recording an invoice with its lines is only slightly better off: one HTTP endpoint,
undeclared and unreachable from any agent.

The consequence is not cosmetic. The aging register skips a document with no posted control
entry, so on a tenant that never ran the demo:

- `overdue_receivable` and `overdue_payable` can never fire.
- Neither can `credit_limit_exceeded`, `purchase_discount_available`, or the early-payment
  discount reason.
- A credit note cannot be netted against an invoice, because netting needs the invoice's control
  entry.
- A supplier credit cannot reduce a payable, for the same reason.

The goods half of both chains works — `shipped_not_billed`, `billed_not_received`,
`receipt_unbilled` and the return classes read document lines, not the ledger. So the position
today is precise and uncomfortable: **the goods half of order-to-cash and procure-to-pay is
complete, and the money half is reachable only from the demo.**

This was not found by asking what the queue cannot see. It was found by asking what a person
cannot do.

### Scope

- Book a sales invoice and a supplier invoice from every surface that already books a credit
  note.
- Record a document with its lines as a declared command, reachable from an agent, as recording
  an order already is.
- Declare all three in every catalog that governs operations.

### Non-Goals

- **Booking automatically when a document is recorded.** Recording evidence and booking it are
  two acts, which is the whole reason `credit_note_unposted` exists. Collapsing them here would
  contradict that and would post figures nobody asked to post.
- **A class for an invoice recorded and never booked.** It is the obvious next thing and it is
  the next specification, not this one: the operation has to exist before a class can report its
  absence, and this specification is what makes the condition reachable at all.
- **Closing the wider declaration gap.** Measured rather than guessed: the 85 mutating endpoints
  reach 72 distinct core services, 64 services are declared as commands, and **18 are reached by
  a mutating endpoint without being declared**. Half of those are reads used to shape a response,
  and most of the rest are tenant administration and chat rather than business operations.
  `create_manual_document_with_lines` is the business one, and it is in scope here. So the gap is
  smaller than it first looked — but nothing gates it, because the command catalog is
  hand-maintained while the tenant isolation catalog is complete by discovery. A gate is
  therefore both cheap and absent, and it is the next structural item rather than a rider on
  this one.
- **A CLI command.** Credit note posting has no CLI command either, and matching the credit note
  is the yardstick this specification uses throughout.
- **Changing what posting does.** The postings themselves are unchanged and were correct all
  along; only their reachability was missing.

### Existing Contracts

- [`specs/084-credit-note-posts/spec.md`](../084-credit-note-posts/spec.md)
- [`docs/features/ledger.md`](../../docs/features/ledger.md)
- [`docs/features/order_to_cash.md`](../../docs/features/order_to_cash.md)
- [`docs/features/procure_to_pay.md`](../../docs/features/procure_to_pay.md)
- [Constitution](../../.specify/memory/constitution.md), principles III and IV

## Clarifications

### Session 2026-09-06

- Q: Is this a feature or a defect? → A: A defect, and the same shape as the last one: a contract
  nothing enforced. Every money class was specified, tested and shipped against a posted invoice
  that no surface could produce. The tests passed because the tests post invoices themselves.
- Q: Should recording an invoice post it? → A: No. Two acts, deliberately, exactly as for a
  credit note. Collapsing them would make the recorded-but-unbooked condition unrepresentable,
  and that condition is real.
- Q: Which surfaces? → A: The ones a credit note posting reaches — the API, the agent tools, the
  MCP schema and the command catalog. Matching the credit note is the yardstick, so the two
  cannot drift apart again.
- Q: Why not add the missing class in the same specification? → A: Because the operation has to
  exist first. A class reporting invoices nobody booked, on a product where nobody *can* book
  one, would report every invoice in the tenant.
- Q: Does the demo change? → A: No. It already calls the service directly and will keep doing so;
  what changes is that everybody else can too.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Book a Sales Invoice (Priority: P1)

An operator books a recorded sales invoice, and what the customer owes becomes visible.

**Why this priority**: Nothing on the receivable side of the product works until this exists.

**Independent Test**: Record a sales invoice through the API, book it through the API, and read
the aging register.

**Acceptance Scenarios**:

1. **Given** a recorded sales invoice, **When** it is booked, **Then** the ledger entries exist
   and what it still owes equals its gross amount.
2. **Given** the same invoice, **When** it is booked a second time, **Then** it is refused.
3. **Given** a document that is not a sales invoice, **When** booking is attempted, **Then** it
   is refused.
4. **Given** a booked and overdue sales invoice, **When** the queue is read, **Then** it is
   reported as an overdue receivable — a class that could not fire from any surface before.
5. **Given** a booked sales invoice and a booked credit note, **When** the credit is netted
   against it, **Then** what is owed falls.

### User Story 2 - Book a Supplier Invoice (Priority: P1)

The same on the buying side, so what the company owes becomes visible.

**Acceptance Scenarios**:

1. **Given** a recorded supplier invoice, **When** it is booked, **Then** what the company owes
   equals its gross amount.
2. **Given** the same invoice, **When** it is booked a second time, **Then** it is refused.
3. **Given** a document that is not a supplier invoice, **When** booking is attempted, **Then**
   it is refused.
4. **Given** a booked supplier invoice under a term granting an early-payment discount, **When**
   the queue is read, **Then** the discount is reported — another class unreachable before.

### User Story 3 - Record an Invoice Where an Order Can Be Recorded (Priority: P2)

Recording a document with its lines is a declared command reachable from an agent, as recording
an order already is.

**Acceptance Scenarios**:

1. **Given** the agent tools, **When** they are listed, **Then** recording a document is among
   them.
2. **Given** an agent recording an invoice with a line naming an order line, **When** the queue
   is read, **Then** the quantity classes judge it exactly as they judge one recorded over HTTP.

### Edge Cases

- Booking an invoice whose gross amount is zero or negative.
- Booking an invoice belonging to another tenant.
- Booking a document that does not exist.
- Booking a credit note through the invoice operation, and an invoice through the credit note
  operation.
- Booking an invoice whose posting group was reversed.
- Recording a document of a type the model does not settle.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A recorded sales invoice MUST be bookable from the API, and booking it MUST produce
  exactly the postings the service already produces.
- **FR-002**: A recorded supplier invoice MUST be bookable on the same terms.
- **FR-003**: Booking MUST be refused for a document of the wrong type, an unknown document, a
  document of another tenant, and an invoice already booked.
- **FR-004**: Each operation MUST be available as an agent tool and an MCP proposal schema, in
  the same shape as the credit note posting that already exists.
- **FR-005**: Recording a document with its lines MUST be a declared command and MUST be
  available as an agent tool and an MCP proposal schema.
- **FR-006**: Every one of the three operations MUST be declared in the command catalog with its
  mode, adapters, reads, writes and effect, and MUST be classified in the agent coverage map.
- **FR-007**: Every new tool MUST be declared in the tenant isolation catalog, in the family its
  credit-note counterpart sits in.
- **FR-008**: Booking MUST be a separate act from recording; no recording path may book.
- **FR-009**: After booking, what a document still owes MUST be answerable, so that the aging
  register, the overdue classes and settlement all see it.
- **FR-010**: A booked invoice MUST be settleable by a payment and by a credit note through the
  existing settlement relation, with no new path.
- **FR-011**: Every existing operation, class and surface MUST behave exactly as it does today.

### Domain and Traceability Requirements

- **DR-001**: No schema changes and no new service logic. This exposes services that already
  exist and are already proven.
- **DR-002**: No figure may be introduced at any surface; every posted amount MUST be the
  document's own.
- **DR-003**: Every read and mutation MUST be tenant-scoped, and the isolation catalog MUST stay
  complete.
- **DR-004**: No operational exception class is added or changed.
- **DR-005**: The demo MUST keep calling the services directly and MUST produce an unchanged
  queue.

### Key Entities *(when data is involved)*

- **Document**: The sales or supplier invoice being recorded and booked.
- **LedgerEntry**: What booking produces, unchanged.

## Success Criteria *(mandatory)*

- **SC-001**: A tenant that has never run the demo can book an invoice.
- **SC-002**: Five classes that could not fire outside the demo become reachable:
  `overdue_receivable`, `overdue_payable`, `credit_limit_exceeded`,
  `purchase_discount_available`, and the early-payment discount reason.
- **SC-003**: An agent can record an invoice and book it.
- **SC-004**: Every operation the product exposes for a credit note is exposed for an invoice.
- **SC-005**: Nothing that worked before behaves differently.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- The postings themselves are correct and stay untouched; this is a reachability defect, not a
  ledger one.
- The wider declaration gap remains open and is named as the next structural item. Seventeen
  services stay undeclared after this feature, and until a gate exists another operation can be
  shipped tenant-safe and unreachable in exactly this way.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenarios 1, 5 | sales invoice posting endpoint test |
| FR-002 | US2 scenarios 1, 4 | supplier invoice posting endpoint test |
| FR-003 | US1 scenarios 2, 3; US2 scenarios 2, 3; Edge cases | refusal tests |
| FR-004 | US1 scenario 1 | agent tool and MCP schema tests |
| FR-005 | US3 scenarios 1, 2 | document recording tool test |
| FR-006 | US1 scenario 1 | command catalog and coverage gate tests |
| FR-007 | US1 scenario 1 | tenant isolation drift gate |
| FR-008 | US3 scenario 2 | recording does not book test |
| FR-009 | US1 scenario 4; US2 scenario 4 | classes become reachable test |
| FR-010 | US1 scenario 5 | settlement through the existing relation test |
| FR-011 | — | the existing suites, unchanged |
| DR-001 | — | no migration and no service change in the diff |
| DR-002 | US1 scenario 1 | posted amounts equal recorded amounts test |
| DR-003 | Edge cases | tenant isolation test |
| DR-004 | — | the closed registry expectation, unchanged |
| DR-005 | — | the demo month's pinned queue, unchanged |
