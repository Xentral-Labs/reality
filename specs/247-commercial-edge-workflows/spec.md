# Feature Specification: Commercial Edge Workflows

**Feature Branch**: `245-demo-setup-finance-readiness`
**Created**: 2026-09-21
**Status**: Approved
**Language**: English
**Input**: Implement the four urgent sales-demo gaps: dunning with an optional manually stated fee, customer bad-debt write-off, dedicated deposit/final-invoice clearing, and controlled overdelivery; expose each through normal product services and include traceable demo cases.

## Context and Intent

### Problem

Reality can show overdue invoices, prepayments and quantity differences, but an operator cannot yet record the commercial decisions that commonly follow. A sales demonstration therefore stops at exactly the questions buyers ask: whether a reminder and its fee are recorded, how an irrecoverable balance is closed, how a deposit is cleared into the final invoice, and how an agreed extra delivery changes the promise without falsifying the original order.

### Scope

- Record manual customer dunning notices at levels 1–3 for one or more overdue invoices, with an optional source-stated fee.
- Accept a full or partial customer bad-debt write-off as a separately confirmed settlement adjustment.
- Record customer and supplier deposits independently of a final invoice and explicitly clear their available amount into a later final invoice.
- Record a confirmed quantity increase before an overdelivery and preserve both the original and revised promise.
- Surface every result through the shared services, tools, web product and canonical demo profile, with direct evidence and Reality traceability.

### Non-Goals

- Sending email or letters, automatic dunning runs, automatic escalation or automatic fee calculation.
- Tax determination or tax correction for dunning fees, deposits or bad debt.
- Silent tolerance write-offs, guessed deposit allocation or automatic overdelivery acceptance.
- Reopening completed or cancelled commitments.
- A general accounts-receivable collections case-management system.

### Existing Contracts

- [Dunning notices stub](../183-dunning-notices/spec.md), superseded for the first deliverable by this specification.
- [Payment matching](../../docs/features/payment_matching.md)
- [Accounting journal and settlement differences](../148-accounting-journal-cost-centers/spec.md)
- [Commitment quantity revisions](../097-a-promise-can-shrink/spec.md)
- [Company setup and demo](../../docs/features/company-setup-demo.md)

## Clarifications

### Session 2026-09-21

- Q: Must the first dunning version support a fee? → A: Yes. An operator may state an optional fixed fee; Reality does not calculate or collect it automatically.
- Q: How may an overdelivery occur? → A: Only after a confirmed quantity increase; the original quantity remains visible.
- Q: Which deposit directions are required? → A: Both customer and supplier deposits, each cleared explicitly into a final invoice.
- Q: May bad debt be accepted automatically? → A: No. Full and partial write-offs require explicit confirmation, a reason and evidence.

## User Scenarios & Testing

### User Story 1 - Record a Dunning Notice and Fee (Priority: P1)

An operator selects overdue customer invoices, records a dated dunning notice at level 1, 2 or 3, and may state a fixed fee. The notice, invoices, fee and resulting open amount remain mutually traceable.

**Independent Test**: Create an overdue posted invoice, record a level-2 notice with a EUR 5 fee, then read the notice, invoice, open items and event history.

**Acceptance Scenarios**:

1. **Given** one or more overdue invoices for the same customer and currency, **When** a notice is confirmed, **Then** one dated notice links to those invoices and records its level.
2. **Given** a stated positive fee, **When** the notice is posted, **Then** a separate open customer charge increases the receivable by exactly that amount without inventing tax.
3. **Given** no fee, **When** the notice is posted, **Then** no financial posting is created for a zero amount.
4. **Given** an open dunning fee, **When** the notice is reversed, **Then** the fee is reversed and the audit trail remains visible.
5. **Given** invoices belonging to different customers or currencies, **When** one notice is attempted, **Then** it is refused without partial writes.

### User Story 2 - Accept Customer Bad Debt (Priority: P1)

An authorised operator closes all or part of an uncollectible customer invoice with an evidenced bad-debt adjustment while keeping the original invoice and payment history unchanged.

**Independent Test**: Part-pay an invoice, write off part of its residual, and verify the remaining open amount, party balance, journal explanation and reversal behavior.

**Acceptance Scenarios**:

1. **Given** an open customer invoice, **When** a partial bad-debt amount is confirmed, **Then** only that amount stops aging and the rest remains open.
2. **Given** the complete residual is written off, **When** balances are read, **Then** the invoice is settled and no reusable customer credit is created.
3. **Given** a zero, negative or excessive amount, **When** write-off is attempted, **Then** it is refused.
4. **Given** an accepted write-off, **When** it is reversed, **Then** the receivable reopens by the same amount.

### User Story 3 - Clear Deposits into Final Invoices (Priority: P1)

An operator records money paid before the final invoice as a customer or supplier deposit and later clears some or all of its available amount into the matching final invoice.

**Independent Test**: Record a deposit, post a later final invoice, clear a partial amount, then clear the remainder and inspect both documents and balances.

**Acceptance Scenarios**:

1. **Given** a customer or supplier deposit, **When** it is recorded, **Then** it remains available credit and is not presented as payment of a nonexistent final invoice.
2. **Given** a posted final invoice for the same party and currency, **When** a clearing is confirmed, **Then** the lesser stated amount reduces both the deposit's available amount and the invoice's open amount.
3. **Given** a deposit larger than the invoice, **When** the invoice is fully cleared, **Then** the remainder stays available as party credit.
4. **Given** a mismatched tenant, party, currency or unposted invoice, **When** clearing is attempted, **Then** it is refused without partial writes.
5. **Given** a clearing reversal, **When** balances are read, **Then** both the deposit availability and invoice residual are restored.

### User Story 4 - Confirm and Fulfil an Increased Quantity (Priority: P2)

An operator records that a counterparty agreed to a larger quantity and can then receive or ship the additional amount without erasing the original promise.

**Independent Test**: Create a commitment for ten, revise it to twelve, move twelve, and inspect the original quantity, revision, fulfilment and stock.

**Acceptance Scenarios**:

1. **Given** an open commitment for ten, **When** a confirmed revision states twelve, **Then** twelve becomes the quantity in force while ten remains the original quantity.
2. **Given** the increase, **When** twelve are moved, **Then** the movement is accepted and the commitment is fulfilled.
3. **Given** no prior increase, **When** twelve are moved against ten, **Then** the existing overdelivery guard still refuses the movement.
4. **Given** a fulfilled or cancelled commitment, **When** an increase is attempted, **Then** it is refused.

### User Story 5 - Demonstrate Every Workflow (Priority: P2)

A new international demo company contains searchable, consistently numbered examples for every workflow and documentation tells a user exactly where to find them and what to expect.

**Independent Test**: Create a fresh live-demo company and follow the documented paths for all four cases without manually calculating projections.

**Acceptance Scenarios**:

1. **Given** a fresh demo company, **When** setup reports ready, **Then** all four cases and their finance projections are ready to inspect.
2. **Given** the demo-data guide, **When** a user follows each path and searches its reference, **Then** the named documents, amounts, movements and explanations are present.
3. **Given** a seeded invoice with payment terms, **When** its due date or discount window is explained, **Then** the invoice carries the exact `DEMO-14-2` term that produced those dates.
4. **Given** the public demo-data guide, **When** an evaluator looks for master data, live intake, special movements or another demo mode, **Then** the guide names the records and gives a concrete UI or CLI inspection path.

### Edge Cases

- A dunning fee of zero is treated as absent; a negative fee is refused.
- Repeating the same confirmed command or source identity is idempotent.
- A dunning notice cannot include an already settled invoice or mix parties/currencies.
- Bad debt never produces reusable credit and cannot target supplier payables.
- Deposit clearing cannot exceed either available deposit or open final-invoice amount.
- Concurrent clearing attempts serialize so the same available amount is not consumed twice.
- Increasing a commitment does not create a movement, reservation or document-line mutation by itself.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST record a tenant-scoped dunning notice with an opaque identity, human number, notice date, level 1–3, customer, currency, linked overdue invoices, actor, reason and evidence.
- **FR-002**: A dunning notice MAY state one fixed non-negative fee; a positive fee MUST create a separate balanced receivable charge for the exact stated amount, while zero MUST create no posting.
- **FR-003**: Dunning MUST refuse settled, unposted, cross-tenant, mixed-party or mixed-currency invoice sets atomically.
- **FR-004**: Reversing a dunning notice MUST preserve the notice and event history and reverse any still-effective fee exactly once.
- **FR-005**: A confirmed customer settlement adjustment MUST accept `bad_debt` as a reason for a positive amount no greater than the invoice residual, using a dedicated bad-debt expense account and creating no reusable credit.
- **FR-006**: Partial and full bad-debt adjustments MUST affect open items, aging and party balances through the shared ledger/allocation derivation and MUST be reversible.
- **FR-007**: The system MUST record customer and supplier deposits as source-backed money documents and balanced ledger entries whose unconsumed amount is available party credit.
- **FR-008**: A confirmed deposit clearing MUST link a deposit's eligible ledger entry to one posted final invoice of the same tenant, side, party and currency and MUST not exceed either available or open amount.
- **FR-009**: Deposit clearing and reversal MUST be idempotent, concurrency-safe and visible from both documents, the open-items register, party balances and the inspector.
- **FR-010**: An open commitment MAY be revised to a greater positive quantity using the existing immutable commitment-revision history; the original commitment quantity MUST remain unchanged.
- **FR-011**: All fulfilment guards and reads MUST use the quantity in force, while a movement above that quantity MUST still be refused.
- **FR-012**: Every mutation MUST use the shared preview/confirm application path, enforce tenant scope and record actor, effective time and source/evidence links.
- **FR-013**: A fresh canonical demo profile MUST include at least one deterministic normal and one boundary example for each of dunning, bad debt, deposit clearing and overdelivery.
- **FR-014**: Company setup MUST publish all required finance projections before reporting the demo ready.
- **FR-015**: English and German demo documentation MUST provide each example's exact reference, UI path, expected result and explanation path.
- **FR-016**: The canonical profile MUST create or reuse `DEMO-14-2` and attach it to every seeded customer and supplier invoice whose due date or discount window is demonstrated.
- **FR-017**: The English and German operational sales tables MUST enumerate `SO-005` explicitly and MUST NOT use an inclusive range that hides an undocumented case.
- **FR-018**: The English and German guides MUST inventory all seeded items, customers, suppliers and locations, including the supplier-to-item and recurring-customer relationships used by the profile.
- **FR-019**: The guides MUST describe continuous Demo Data intake, its timing and authored settlement mix without presenting probabilistic intake as a fixed seeded case.
- **FR-020**: The guides MUST list each exceptional seeded movement and finance/cost document with its exact reference, purpose and inspection path.
- **FR-021**: The guides MUST distinguish the canonical international profile, the reduced execution profile and the separately invoked `normal-month` scenario, including how each is started.
- **FR-022**: The demo-data guides MUST use a consistent compact table grid at desktop widths, preserve readable horizontal overflow on smaller screens and allow the long master-data inventory to be collapsed.

### Domain and Traceability Requirements

- **DR-001**: Source-stated amounts, dates, levels and quantities MUST be recorded exactly and MUST not be recomputed.
- **DR-002**: Dunning status, open amounts, deposit availability, quantities in force and fulfilment MUST be derived from held records rather than duplicated on documents.
- **DR-003**: Dunning invoice membership and deposit clearing MUST use opaque links; human numbers are lookup inputs only.
- **DR-004**: Schema additions are limited to the smallest records needed for dunning identity/membership and explicit deposit meaning; existing settlement allocation and commitment revision structures MUST be reused where their semantics are true.
- **DR-005**: Every repository query and service mutation MUST enforce tenant scope, and cross-tenant targets MUST behave as unavailable.
- **DR-006**: Demo seeding MUST call the same services as normal product actions and MUST NOT write new business records directly through the ORM.

### Key Entities

- **Dunning Notice**: A dated levelled customer reminder with immutable invoice membership and an optional stated fee.
- **Dunning Fee Charge**: The exact optional amount stated on a notice, represented as its own financial evidence and balanced receivable posting.
- **Settlement Adjustment**: Existing confirmed receivable reduction, extended with the `bad_debt` reason and dedicated account semantics.
- **Deposit**: A source-backed customer receipt or supplier payment explicitly classified as money received or paid before a final invoice.
- **Deposit Clearing**: The opaque allocation of available deposit value to one final invoice.
- **Commitment Revision**: Existing immutable restatement whose quantity may be greater or smaller than the original while the commitment is open.

## Success Criteria

- **SC-001**: An operator can complete each of the four workflows from the web product in at most three confirmed actions after locating the target record.
- **SC-002**: Every resulting amount or quantity exposes a path to its Reality record, evidence and source payload in at most three drill-down transitions.
- **SC-003**: Repeating any confirmed request produces no duplicate notice, fee, adjustment, deposit clearing, revision or movement.
- **SC-004**: All four normal cases and their listed boundary cases have executable service and web-adapter tests.
- **SC-005**: A fresh demo company exposes every documented example immediately after the setup dialog reaches its final ready step.
- **SC-006**: Existing payment, settlement, commitment and overdelivery regression suites remain green.
- **SC-007**: A catalog audit can account for every operational case, master-data member, exceptional movement and supported demo mode without an undocumented numeric range.

## Assumptions and Dependencies

- The initial legal/accounting policy is deliberately narrow: no tax is calculated for dunning fees, deposits or bad-debt write-offs. The source amount is recorded and any jurisdiction-specific tax treatment requires a later reviewed feature.
- Dunning levels are user-stated integers 1–3; the system does not infer escalation.
- A dunning fee is a separate receivable charge, not a mutation of the reminded invoice.
- Deposit clearing reuses the proven settlement-allocation invariant where the ledger semantics match; it does not create a second balance table.
- Bad debt is customer-side only in this version. Supplier balance corrections remain `agreed_deduction` or require a separate specified reason.
- Spec 097 already proves that a commitment's quantity in force can differ from its original quantity; this feature removes only the higher-quantity product restriction at the confirmation boundary, not the movement guard.

## Requirement Traceability

| Requirement    | Scenario(s) | Planned evidence                                                                                                 |
| -------------- | ----------- | ---------------------------------------------------------------------------------------------------------------- |
| FR-001..FR-004 | US1         | dunning domain, service, reversal and adapter tests                                                              |
| FR-005..FR-006 | US2         | settlement adjustment and finance projection tests                                                               |
| FR-007..FR-009 | US3         | customer/supplier deposit and concurrency tests                                                                  |
| FR-010..FR-011 | US4         | revision and overdelivery guard tests                                                                            |
| FR-012         | US1..US4    | application tool confirmation and tenant isolation tests                                                         |
| FR-013..FR-015 | US5         | canonical profile, setup and documentation tests                                                                 |
| FR-016..FR-022 | US5         | payment-term binding, catalog completeness, compact responsive layout and bilingual documentation contract tests |
| DR-001..DR-006 | US1..US5    | model, migration, source-chain and repository review                                                             |
