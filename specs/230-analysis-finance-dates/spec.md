# Feature Specification: Analysis finance and calendar dates

**Language**: English

## Context and Intent
### Problem
Analysis cannot execute canonical outstanding amounts, ignores ledger debit/credit
signs, and treats received document dates as arbitrary text.
### Scope
The owner approved finance measures and date handling as the next implementation.
Expose customer and supplier financial positions through existing finance services;
fix signed ledger sums and calendar date filtering/grouping in the shared builder.
### Non-Goals
No historical settlement reconstruction, net party balance after unused credit,
new storage/schema, inventory derivation, arbitrary service execution or writes.
The legacy ambiguous party open_balance remains explicitly unsupported.

## User Scenarios & Testing
### US1 — Correct finance analysis (P1)
Given partially paid, reversed, fully paid and opening debts, when querying customer
or supplier positions, the current outstanding amount/status/due date matches the
canonical aging register. Currencies stay separate; original document identity and
party/evidence paths remain available. Unposted documents are not financial positions.
Given ledger entries and reversals, signed totals match the canonical account balance.
### US2 — Calendar date analysis (P1)
Given valid, empty and malformed received document dates, monthly totals and period
filters use valid calendar dates without aborting or fabricating dates. Date-only
bounds retain the selected calendar day independently of browser timezone.

## Requirements

### Functional Requirements
- **FR-001**: Expose customer/supplier financial-position nodes backed by canonical
  aging, including opening debts, paid/reversed statuses, remaining amount, due date,
  days overdue and overdue remaining amount. Reuse all settlement/reversal logic.
- **FR-002**: Preserve tenant, currency, fanout, timeout and result limits. Bound
  service input to 20,000 debt documents and refuse overflow without partial totals.
  Service-backed traversal reports actual SQL read count; ordinary traversal retains
  its single-statement execution. Snapshot measures refuse time-bucket trends.
- **FR-003**: Ledger totals use debit-positive/credit-negative signs before aggregation.
- **FR-004**: Explicitly declared document calendar dates support date predicates and
  buckets. Invalid/empty values become unknown in analysis, never change the source.
- **FR-005**: Catalog date metadata drives period controls, custom ranges and result
  display; date-only values never pass through UTC instant conversion. Timestamp
  fields retain existing instant behavior. Templates preserve their field semantics.

## Edge Cases
Unknown due dates stay null; overdue amount is zero when not overdue. Service input
bounds are independent of output limits. Neighbor tenants cannot enter derived rows.
Leap days are validated. Unknown dates form an unknown bucket without silent coercion.

## Assumptions and Dependencies
PostgreSQL, existing aging_register, settlement_positions and reporting graph remain
authoritative. As-of aging is today's UTC date, not historical settlement state.
English repository artifacts; localized catalog labels and shared UI controls.

## Success Criteria
Canonical finance parity, signed account parity and calendar boundary regressions
pass. No second settlement arithmetic and no persistence migration.

## Requirement Traceability
| Requirement | Story | Tasks | Validation |
|---|---|---|---|
| FR-001 | US1 | T001,T002,T003 | Finance parity, opening/reversal tests |
| FR-002 | US1 | T001,T002,T003 | Isolation, currency, limit, count, fanout tests |
| FR-003 | US1 | T001,T003 | Signed ledger regression |
| FR-004 | US2 | T001,T004 | Leap/invalid dates and monthly sums |
| FR-005 | US2 | T001,T004,T005 | Web period contracts, build, Chrome |
