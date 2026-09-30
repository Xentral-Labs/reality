# Implementation Plan: Chargebacks, Returned Direct Debits and Payment Fees

**Branch**: `297-payment-returns-fees` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

## Summary

A person records a returned direct debit or chargeback against a customer payment through one
reviewed finance command. It reverses the payment's posting with the existing reversal, keeps a
`payment_return` record with kind, reason, reference and date, books the stated fee as payment-fee
expense and, where chosen, charges it on to the customer. A `payment_returned` finding follows the
reopened invoice until it is settled again. A provider fee deducted from a payment is a new
settlement reduction category. Freight and surcharges on sales invoices are proven by a story.
C15 and E08 are then promoted.

## Technical Context

**Language/Version**: Python 3.12; TypeScript 5.8 / React 19

**Primary Dependencies**: SQLAlchemy 2, Alembic, Pydantic v2, Typer, FastAPI; existing ledger
reversal, finance change proposal and settlement flow

**Storage**: PostgreSQL; migration `0103_payment_returns` (one table, one role)

**Testing**: pytest on disposable PostgreSQL (service, exception, adapter, isolation, catalog gates,
business stories); i18n audit and Web build

**Target Platform**: Reality core service, Web, MCP/Chat, CLI

**Performance Goals**: the finding reads returns, their payments' allocations and the open amounts
once per evaluation

**Constraints**: no document status field; fees as stated; owner confirmation; tenant-scoped

**Scale/Scope**: 1 table, 1 role, 2 document types, 1 service module, 1 command, 2 reads, 1
exception class, 1 reduction category, 3 adapters

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | The confirmed request is a manual source record; fee documents are Evidence; the return, reversal and postings are Reality citing it. |
| II. Reality is the operational authority | PASS | Which invoices reopened and whether they are settled again is read from allocations and open amounts; no document status. |
| III. Proven schema only | PASS | `payment_return` is read by the finding on every evaluation, joined by the invoice explanation and the payments list, and filtered by kind (research R2). |
| IV. Tenant and service boundaries | PASS | Composite tenant FKs; the command runs through the shared finance change proposal on every surface. |
| V. Specification and test evidence | PASS | Approved spec with clarifications; tests planned first. |
| VI. Explainable Web product | PASS | The invoice names its return; the return links payment, reversal and fee documents. |
| VII. Simplicity and storage discipline | PASS | Reuses `reverse_ledger_posting_group`, `accept_adjustment` and the fee-charge pattern. |
| VIII. Received values are recorded, never recomputed | PASS | Reason, reference, date and fee are stated; nothing is calculated. |

## Design

- `services/payment_returns.py`: `preview_return`, `record_return` (lock finance, reverse the
  payment group with `_commit=False`, fee documents, record, event), `return_detail`, `returns`,
  `returned_invoices` (the finding's reader).
- `tools/finance.py`: `PaymentReturnRequest` and the route; `StatedReduction.reason_category`
  gains `payment_fee`; `settlement.accept_adjustment` maps it to `payment_fee_expense`.
- `domain/finance.py`: role and transaction matrix rows; `core.SETTLEMENT_CONTROL` for the fee
  charge.
- `services/exceptions.py`: class `payment_returned`.
- Web: payments list action and dialog; settlement reduction label; invoice inspector section.

## Risks

- The inherited fee-charge open-item gap (research R3) is visible to the owner; it is documented.
- Returning a payment settled with a payment fee is refused until a follow-up handles the fee
  adjustment.
