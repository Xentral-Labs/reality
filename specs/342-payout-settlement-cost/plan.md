# Implementation Plan: Payout Settlement Cost

**Branch**: `342-payout-settlement-cost` | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

`core._batch_reads(session)` opens a scope bound to the session and its root transaction.
`payouts.settle_payout` and `payouts.preview_payout` run inside it. Within the scope:

- `lock_delivery_state`, the tenant lock in `emit_business_event` and `lock_finance` take their
  lock once; `lock_finance` returns the same `FinanceState`, whose revision callers keep raising.
- `_tenant_record` returns parties, proposals, source records and the tenant read once, and any
  record the session already holds without reading it again.
- `company_currency`, `resolve_account`, opening scopes and a posted document's control entry are
  read once; reversal roles are read once per posting group and entered where a group is posted
  or reversed.
- `record_customer_payment` and `record_customer_refund` skip their savepoint.
- `payouts._warm` reads the statement's orders, their lines, the invoices billing them, the orders
  those invoices bill, their control entries and reversal roles with set-based reads; the
  existing `_customers`, `_orders_by`, `_lines_of`, `_invoices_billing` and `_bills_other_orders`
  find them there.

Outside the scope everything reads as before. Two changes apply everywhere and are equivalent:
`allocate_settlement` reads only the allocations touching the payment it checks, and
`core.store_source_records` stores many source records of one type with shared reads (used for
payout lines).

## Constitution Check

- Stated values are never recomputed (VIII); nothing about what is booked changes.
- No schema change (III); tenant scope is part of every memo key.
- Reviewed mutations unchanged; the batch lives inside one confirmed execution.

## Tests

- `tests/finance/test_payout_cost.py`: statement growth per line; batched equals line-by-line.
- R04 story budget tightened from 120 to 20 statements per line.
