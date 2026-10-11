# Implementation Plan: Invoice Settlement Dates in One Read

**Branch**: `384-invoice-settlement-dates` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Add `due_date` and `allocations[]` to the invoice branch of `settlement_context`. The due date comes
from `core.aging_register` narrowed to the one document, the allocations from
`core.active_settlement_allocations` narrowed to the invoice's control entry, which is the reader
`open_invoice_amount` already uses. No new rule, tool, schema or dependency.

## Research: is `graph_ask` already the answer?

Executed once against a test company before building: a sales invoice dated 2026-09-01 with a
14-day term, fully settled by a payment effective 2026-09-10, read through
`run_read_tool(..., "graph.ask", ...)`, the path the MCP `graph_ask` tool uses.

- `customer_open_item` filtered by `i.id` returned `due_date 2026-09-15`, `open_amount 0`,
  `settlement_status paid`. The paid invoice does appear; the node keeps settled positions.
- `allocation -[settles]-> posting -[posted_from]-> invoice` returned `allocated_amount 100` grouped
  by `allocated_at`, after the client added `a.currency` to the grouping (otherwise refused with
  `unit_mismatch`).
- The two answers cannot be joined in one question (`customer_open_item` reaches `document`, while
  `posted_from` starts at `invoice`; refused with `edge_direction`).
- The paying document's number is null: `posted_from` targets the `invoice` node, which admits only
  sales invoices and credit notes. Only the payment's posting group and effective time are
  reachable. Allocations are aggregated, so two recorded at the same instant collapse into one row.
- After the payment was reversed, the position showed `open_amount 100` while the allocation query
  still returned the 100 allocation. The `allocation` node reads the raw table and does not apply
  the active-allocation rule.

Conclusion: the arguments and the output shape are composed by the client, and the allocation answer
contradicts the open amount after a reversal. It is not a bounded operational read, so the feature
is built.

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| I. Source → Evidence → Reality | Reads allocations and ledger entries (Reality) and documents (Evidence); nothing new is written. | PASS |
| II. Reality owns operational state | No status field is added to documents; settlement is read from allocations. | PASS |
| III. Proven schema only | No table, column or migration. | PASS |
| IV. Tenant + shared service boundaries | Both readers filter by `tenant_id`; the MCP tool keeps routing to the same service. | PASS |
| V. Spec/test traceability | Every FR maps to a test below, written and observed failing first. | PASS |
| VI. Explainable web behavior | Each allocation names the opaque document ID behind the open amount. | PASS |
| VII. Simplicity | Two existing shared readers, one function. | PASS |
| VIII. Received values not recomputed | Amounts and times are returned as recorded; the due date is the existing read-time observation, not stored. | PASS |

## Repository Structure and Layer Changes

```text
packages/reality-core/src/reality/services/finance/settlement_flows.py  # invoice branch
packages/reality-core/config/command_catalog.yaml                       # purpose/proves text
packages/reality-core/tests/finance/test_settlement_flows.py            # new tests
docs/SPEC_COVERAGE_MATRIX.md                                            # spec 384 section
```

## Design

`_invoice_settlement(session, tenant_id, document, control_entry_id)` returns the two fields:

- `due_date`: `aging_register(session, tenant_id, document_ids={id})`; the row's `due_date` as an
  ISO date or null. The aging rule already handles fee claims (null) and opening debts (stated
  original due date).
- `allocations`: `active_settlement_allocations(session, tenant_id, entry_ids={control_entry_id})`;
  the counterpart entry is the side of the allocation that is not the control entry. Ledger entries
  and documents are read in two tenant-scoped `IN` queries. Ordered by the counterpart's
  `effective_at`, then `allocated_at`, then ID.

## Test Strategy

1. Service: dated invoice with term, two dated partial payments → due date, open 0, two allocations
   with payment document IDs, numbers, amounts and both times (FR-001, FR-002, FR-004).
2. Same invoice after reversing one payment → one allocation remains, open equals the reversed
   amount, allocations plus open equal gross (FR-003). Positive control: the unreversed allocation
   is still returned.
3. MCP tool `finance_settlement_context` handler returns the identical answer (FR-005).
4. Unsettled invoice without a term → due date equals its document date, empty allocations.
5. Gates: finance test files, `ruff`, `make spec-check`, `make docs-catalog-check`.

## Rollback

Revert the function and tests. Nothing is stored.

## Risks and Review

- **Risk**: a client reads `allocated_at` as the payment date. **Mitigation**: `effective_at` is
  returned beside it and the catalog text names the difference.
- **Risk**: extra per-call cost. **Mitigation**: both readers are already narrowed to one document
  or one entry.
