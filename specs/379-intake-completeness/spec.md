# Feature Specification: Essential intake completeness

**Feature Branch**: `codex/intake-completeness`
**Created**: 2026-10-06
**Status**: Approved for implementation
**Language**: English
**Input**: The owner requested a green pull request implementing the preceding analysis of missing essential import rules, following undated live simulator orders.

## Context and Intent

### Problem

Different intake paths replace absent prices, currencies and financial dates with plausible values. Live simulator and file orders can carry a order timestamp while leaving the displayed document date absent. A valid incomplete order must remain distinguishable from a complete order and from a financially actionable statement.

### Scope

- A shared completeness policy for source-backed orders, monetary statements and physical units.
- Refuse monetary source preparation without a stated currency; refuse bank-file statements without a stated booking time or direction.
- Preserve absent manual document unit prices as unknown, separately from stated zero.
- Expose allowed order gaps in the retained import review and manual-order preview.
- Carry source-backed order dates into evidence consistently; author complete future automatic simulator orders.
- Reject unsupported sales quantity units before creating operational promises.

### Non-Goals

- Rewriting immutable historical sources or silently backfilling existing orders.
- Requiring every order to have a customer-agreed delivery deadline, unit price or stated total.
- Recalculating source totals or inventing dates, prices, addresses or delivery promises.
- New schema, connector configuration, exchange-rate support, transport or scheduling infrastructure.
- Requiring a second confirmation for direct authenticated human operations.

### Existing Contracts

- [Source ingestion](../../docs/features/source_ingestion.md)
- [Decision-gated intake](../../docs/features/decision-gated-intake.md)
- [Company simulator](../../docs/scenarios/company-simulator.md)
- [Purchase unit conversion](../301-unit-conversion/spec.md) — FR-007 supersedes its permissive sales control; purchase conversion remains unchanged.
- [Constitution](../../.specify/memory/constitution.md)

## User Scenarios & Testing

### User Story 1 - Refuse ambiguous money (Priority: P1)

A reviewer receives a source with money whose currency, booking time or direction is absent. It stays available as evidence, but cannot become a financial assertion based on a guessed default.

**Why this priority**: A guessed value can change the meaning of money rather than merely leave a display blank.
**Independent Test**: Prepare an incomplete bank file or monetary order and inspect the retained failure and unchanged business records.

**Acceptance Scenarios**:

1. Missing, null or blank currency in a monetary source refuses preparation with a coded field-specific reason and no accepted effects.
2. A bank row missing booking time or direction refuses; a complete incoming or outgoing row prepares its exact stated date, currency and amount.
3. The original source and artifact remain unchanged after refusal; unrelated valid units retain the existing independent-unit behavior.

### User Story 2 - Preserve and explain incomplete orders (Priority: P1)

A reviewer can accept known quantities while seeing which commercial or timing facts were not stated, without converting absence into a free price or an invented deadline.

**Why this priority**: Incomplete orders are legitimate evidence; the missing facts must stay visible.
**Independent Test**: Compare omitted price and stated zero, then review an undated file/manual/Shopify order.

**Acceptance Scenarios**:

1. An omitted or blank manual unit price remains unknown; explicitly stated zero remains zero. Existing explicit-null validation for direct manual requests remains unchanged.
2. Missing document date, order timestamp, requested delivery date, unit price and amounts are identified in the shared order review. A missing deadline alone does not reject the order.
3. A file order with a stated document date keeps it; otherwise a stated order instant determines the company's local document day. Without either, the date stays unknown with a review issue.
4. Source amounts remain exactly as received even when they disagree; no source total is reconstructed.

### User Story 3 - Complete simulator and physical quantities (Priority: P2)

New live orders state their commercial and timing facts consistently; physical order quantities cannot silently mean a different unit.

**Why this priority**: The simulator should demonstrate the production contract and a quantity must have one meaning.
**Independent Test**: Release a live order, read its original source/evidence and customer-order register; prepare an order in an unsupported quantity unit.

**Acceptance Scenarios**:

1. An automatically released live order states one order instant, its company-local document day and the world's authored unit price; replay returns the same records.
2. Sales order lines naming an existing item inherit its unit when none is stated. A different explicitly stated unit refuses an operational sales promise until supported conversion exists. Purchase-unit conversion remains governed by its existing contract.
3. Unknown external item lines remain evidence without a physical promise, with the existing investigation path; no item or unit is guessed for fulfillment.

### Edge Cases

- Null, omitted, whitespace and explicitly zero values; malformed dates; non-finite quantities/amounts.
- A stated document date that differs from the order date, and instants near local midnight.
- Multiple rows of one order with contradictory stated header dates; equivalent timezone representations of one instant are consistent.
- Cross-company references, duplicate release/import, stale review, independent bulk units and rollback.
- Historical reviews keep their digest and no existing source is rewritten.

## Requirements

### Functional Requirements

- **FR-001**: Monetary external source preparation MUST require a nonblank stated currency and MUST NOT assume EUR. Direct human form defaults remain visible and unchanged.
- **FR-002**: Bank-file payment preparation MUST require explicit incoming/outgoing direction and a stated booking instant; received time MUST NOT substitute for booking time.
- **FR-003**: Omitted/blank manual document unit prices MUST remain unknown; explicit zero MUST remain zero; direct explicit-null validation remains unchanged.
- **FR-004**: Shared order completeness observations MUST identify missing document date, order instant, agreed delivery date, unit prices, line amounts and order total in retained reviews/previews without inventing values or refusing legitimate incompleteness.
- **FR-005**: File orders MUST preserve a stated document date, or derive the company-local day from a stated order instant when the profile defines that meaning; contradictory header dates in one coherent order MUST refuse after parsing; equivalent representations of one instant MUST remain admissible. No timing evidence MUST remain unknown.
- **FR-006**: Future simulator orders MUST state their document date and one consistent release/order instant; automatic orders MUST also state the authored unit price through normal services; the source payload MUST retain them.
- **FR-007**: Known-item sales promises MUST use the stock unit, refusing explicitly different unsupported units. Existing known-item profile inheritance, unknown-item evidence and purchase conversion MUST remain intact.
- **FR-008**: Missing-essential refusals MUST identify the field through the existing localized refusal mechanism and retain a safe preparation-phase failure without accepted effects.
- **FR-009**: The durable contract MUST provide a rule/behavior matrix for orders, statements and units, with tests demonstrating both refusal and allowed incompleteness across paths.

### Domain and Traceability Requirements

- **DR-001**: Original Sources/artifacts remain lossless and immutable; accepted effects follow Source → Evidence → Reality and preserve stated values.
- **DR-002**: No operational state or completeness flag is persisted on Documents; issues are review/read-time observations using shortest existing links.
- **DR-003**: Shared services enforce tenant scope, authorization, exact-review integrity, atomic acceptance and replay. No adapter implements alternate business rules.

### Key Entities

- **Source**: The original statement, including omissions.
- **Order evidence**: Received commercial and timing facts, including legitimate unknowns.
- **Prepared review**: Exact intended effects with completeness observations.
- **Payment statement**: Stated money, currency, direction and booking time.

## Success Criteria

- **SC-001**: Every newly prepared incomplete monetary statement names its missing essential field and creates zero accepted financial effects.
- **SC-002**: New simulator orders have a displayed source-backed date and no guessed zero unit price.
- **SC-003**: Every FR and DR maps to acceptance evidence; all required CI gates pass before the PR is reported green.

## Assumptions and Dependencies

- The owner's 2026-10-06 request approves implementing the preceding analysis; this bounded design adds no schema or new authority.
- File and Shopify order profiles use existing recorded item stock units when the source does not state a separate unit. This is a documented profile meaning, not a blanket pieces default.
- Direct manual invoice amounts can be stated without an individual unit price; no source arithmetic is introduced.
- Existing incomplete/historical records remain unchanged. Remediation of historical evidence requires a separate reviewed request.
- Existing source-revision, admission and scheduling contracts remain authoritative.

## Requirement Traceability

| Requirement | Scenario | Planned test/evidence |
|---|---|---|
| FR-001, FR-002, FR-008 | US1.1–3 | tests/test_intake_completeness.py: missing-essential matrix, retained failure and complete bank statement |
| FR-003, FR-004 | US2.1–2 | tests/test_intake_completeness.py: price/zero and review-gap matrix |
| FR-005 | US2.3; header edge cases | tests/test_intake_completeness.py: stated date, company midnight and conflicting headers |
| FR-006 | US3.1 | tests/scenarios/test_live_company.py: source/date/register/replay |
| FR-007 | US3.2–3 | tests/test_intake_completeness.py: units, existing purchase and unknown-item regression |
| FR-009 | All | docs/features/intake-completeness.md; rule matrix and full required gates |
| DR-001–003 | US1.3; US2.4; edge cases | tests/test_intake_completeness.py plus existing intake admission/isolation/replay suites |
