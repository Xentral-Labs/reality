# Feature Specification: Reviewed invoice, payment and allocation intake

## Approved scope clarification (2026-10-04)

This rollout governs external sources, imports and agent-proposed business effects.
They require an exact retained proposal and an authorized confirmation before acceptance.
A direct action by an authenticated human is itself the decision and uses the existing
application authorization and audit trail; it does not require a second proposal or
confirmation cycle. Derived effects of one operation share its transaction and receipt.

The owner retained PRs #333–#346 and withdrew the later universal canonical-writer
rollout. Internal service calls and every manual UI/CLI operation are not additional
admission projects. Existing tenant, domain, Finance and Chat confirmation rules remain.
A static writer inventory is discovery material, not a mandate to guard every writer.
References below to governed writes mean external intake only; broader earlier planning
and universal-writer tasks are superseded by this clarification.

**Created**: 2026-10-03
**Status**: Specified; implementation pending
**Language**: English
**Input**: Owner approved reviewed external intake, including imported master data,
payments, changes and bulk processing. Direct authenticated human actions are decisions
and retain existing audit attribution without another approval cycle.

## Context and Intent

### Problem

The provider-agnostic invoice/payment interpreter records evidence, posts invoices/payments and allocates unambiguous references immediately. Bank-file profiles also create payment records directly. Source facts must be retained while accepted financial meaning waits for exact authorization.

### Scope

Prepare received invoice and payment evidence, planned postings and reference-based allocations. Preserve current finance authority and canonical accounting, settlement and ambiguity rules across bank files and synthetic source adapters.

### Non-Goals

No external payment execution, accounting engine redesign, automatic write-offs/discounts, invented invoices, changed company currency or new bank connectors.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md)
- [Spec workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md)
- [Owner's roadmap](../../docs/ideas/decision-gated-intake-plan.md)
- [168-demo-order-to-cash](../168-demo-order-to-cash/spec.md)
- [263-decision-trail](../263-decision-trail/spec.md)
- [340-accounting-boundary](../340-accounting-boundary/spec.md)
- [323-proposal-decision-policy](../323-proposal-decision-policy/spec.md)
- [Dependency 356-decision-gated-intake](../356-decision-gated-intake/spec.md)

## User Scenarios & Testing

### User Story 1 - Review financial meaning before posting (Priority: P1)

Inspect received money or invoice statements without allowing a mistaken interpretation to book them.

**Why this priority**: Lossless receipt and accepted ledger authority must remain separate.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** a payment/invoice source, **When** it is interpreted, **Then** a pending evidence/posting proposal exists while documents and ledger remain unchanged.
2. **Given** an exact authorized proposal, **When** approval succeeds, **Then** its evidence and canonical ledger effects commit with the receipt.
3. **Given** a missing amount, currency, account or partner, **When** preparation runs, **Then** the source survives and the missing meaning is surfaced without invented financial values.

### User Story 2 - Decide a payment allocation explicitly (Priority: P1)

See why a received payment would be linked to an invoice and approve that specific allocation.

**Why this priority**: Matching is a separate effect, even when it is obvious.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** one exact posted invoice reference, **When** the payment is prepared, **Then** the candidate and proposed amount are visible but no allocation exists.
2. **Given** multiple candidates, changed residual or blocked account, **When** confirmation runs, **Then** the ambiguous/stale allocation refuses without substituting another invoice.
3. **Given** an unmatched but otherwise valid payment, **When** its evidence/posting-only proposal is approved, **Then** the payment is accepted without inventing an invoice or write-off.

### User Story 3 - Process independent financial statements safely (Priority: P1)

Handle many statements while respecting stronger authority and per-statement atomicity.

**Why this priority**: Bulk must not lower finance permissions or hide failed money records.

**Independent Test**: Exercise this story's scenarios against its own prepared unit and current authorization, including refused execution; verify accepted-record counts and retained receipts.

**Acceptance Scenarios**:

1. **Given** a fixed manifest of valid and invalid statements, **When** it is reviewed and settled, **Then** each permitted independent statement has its own receipt or coded refusal.
2. **Given** owner access is revoked or a posting is already committed, **When** the batch continues or retries, **Then** subsequent units refuse as appropriate and committed ones replay without another booking.

### Edge Cases

- Foreign tenant identities at source, proposal, manifest, target and receipt reads.
- Duplicate source delivery, concurrent review/approval, stale state and token revocation.
- Invalid later content, interruption before/after commit and uncertain execution.
- Changed source versions, mappings, defaults or referenced records after review.
- Rejected/blocked work remains inspectable; read-only recovery never executes it.

## Requirements

### Functional Requirements

- **FR-001**: Invoice and incoming/outgoing payment preparation MUST create no accepted financial document, posting or allocation; the raw source remains retained even when meaning is unresolved.
- **FR-002**: Review MUST show received amount/currency/date/references, resolved party/accounts and each proposed evidence/posting effect, including any explicit defaults.
- **FR-003**: Approved posting MUST use canonical finance services and preserve owner/principal, account, Decimal, source-stated value and tenant constraints.
- **FR-004**: Evidence, posting groups, events, interpretation outcome and decision receipt MUST commit atomically; no internal commit or retry may produce a duplicate posting.
- **FR-005**: An unambiguous reference MUST propose an allocation rather than execute it during interpretation; review MUST name the exact invoice/entries and amount.
- **FR-006**: Allocation MUST recheck open amounts, party, currency and allowed accounts. Ambiguity or changed availability MUST NOT authorize automatic rematching, reductions or residual write-offs.
- **FR-007**: A valid payment MAY be approved without allocation when review explicitly proposes only its evidence/posting. Changing an already prepared combined unit into posting-only MUST require a fresh review.
- **FR-008**: Financial batch execution MUST apply package 356's manifest and replay rules and current finance authority per statement; one bad independent statement MUST NOT cause duplicate or partial other statements.
- **FR-009**: Source interpretation MUST NOT claim bank/provider payment execution; refund payouts, write-offs and other unsupported effects MUST remain outside intake approval.

### Domain and Traceability Requirements

- **DR-001**: Preserve Source → Evidence → Reality wherever applicable, immutable
  lossless source payloads and received values. Review comparisons are observations,
  not replacement source authority. Use opaque IDs and shortest true links.
- **DR-002**: Documents MUST NOT own operational fulfilment, inventory or payment
  status; accepted operational state remains derived from Reality records.
- **DR-003**: All reads/writes MUST be tenant-scoped and all transports MUST use
  shared application services. Cross-tenant identities behave as not found and never
  become authority through caller-supplied actor or scope claims.

### Key Entities

FinancialIntakePlan: received statement meaning plus explicit posting operations. AllocationIntent: exact target entries/invoice, amount and current residual/account basis. FinancialReceipt: retained document/posting/allocation identities caused by the decision.

## Success Criteria

- **SC-001**: Every preparation/refusal scenario produces zero unapproved accepted
  business records; every approved coherent unit has exactly one truthful retained
  result and no duplicates after replay or concurrent settlement.
- **SC-002**: Every FR/DR has acceptance evidence, implementation tasks and executable
  verification; completion requires all required repository checks to pass.

## Assumptions and Dependencies

- The owner authorized this direction and autonomous preparation. These artifacts do not claim implementation, human review of an unseen design, release approval or verified runtime behavior.
- Existing business validation and stronger authorization remain in force; admitting a source does not authorize unsupported new business semantics.
- A coherent order is one unit; an item package is at most 500 rows; a manifest contains at most 500 independent units. These are different bounds, not interchangeable promises.
- Implement after the listed dependency contracts are available; adapter tests may use the shared typed plan contract before all other adapters are delivered.

## Requirement Traceability

| Requirement | Scenario(s) | Planned executable proof | Tasks |
| --- | --- | --- | --- |
| FR-001 | US1 | `packages/reality-core/tests/test_financial_intake_admission.py::test_financial_prepare_is_non_posting` | T003, T004, T005 |
| FR-002 | US1 | `packages/reality-core/tests/test_financial_intake_admission.py::test_financial_review_exposes_exact_meaning` | T003, T004, T005 |
| FR-003 | US1 | `packages/reality-core/tests/test_financial_intake_admission.py::test_finance_authority_and_values_are_preserved` | T003, T004, T005 |
| FR-004 | US1 | `packages/reality-core/tests/test_financial_intake_admission.py::test_financial_effect_and_receipt_are_atomic` | T003, T004, T005 |
| FR-005 | US2 | `packages/reality-core/tests/test_financial_intake_admission.py::test_unambiguous_match_is_still_a_proposal` | T006, T007, T008 |
| FR-006 | US2 | `packages/reality-core/tests/test_financial_intake_admission.py::test_changed_allocation_refuses_without_rematch` | T006, T007, T008 |
| FR-007 | US2 | `packages/reality-core/tests/test_financial_intake_admission.py::test_unmatched_payment_can_be_accepted_explicitly` | T006, T007, T008 |
| FR-008 | US3 | `packages/reality-core/tests/test_financial_intake_admission.py::test_financial_batch_preserves_authority_and_units` | T009, T010, T011 |
| FR-009 | US3 | `packages/reality-core/tests/test_financial_intake_admission.py::test_intake_is_not_external_payment_execution` | T009, T010, T011 |
| DR-001, DR-002, DR-003, SC-001 | US1–US3, edge cases | `packages/reality-core/tests/test_financial_intake_admission.py` source/attribution, derived-state and tenant refusal matrix | T001, T002, T012, T013 |
| SC-002 | All | Required gates and final evidence review | T014 |
