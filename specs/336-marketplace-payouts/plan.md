# Implementation Plan: Marketplace and Payment-Provider Payouts

**Branch**: `336-marketplace-payouts` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

## Summary

- A reviewed finance command, `finance.payout.settle`, takes one stated payout statement.
  - It books every line it can resolve through the existing payment, refund, allocation and return primitives, on a cash account the person names for the provider.
  - It moves the stated net payout to the bank.
  - Lines it cannot resolve stay unbooked and are reported.
- Two reviewed finance commands record an authorization and a capture, as stated records in two new tables. An expired, uncovered authorization is a derived finding.
- Payout lines may state a shipment's tracking number, which is how a cash-on-delivery remittance ties the payment to its shipment.

## Technical Context

**Language/Version**: Python 3.12, SQLAlchemy 2, Alembic, PostgreSQL

**Storage**: migration `0126_payment_authorizations` with `payment_authorization` and `payment_capture`. No new column, and no table for payouts.

**Testing**:
- service tests with positive controls;
- adapter tests (MCP schema, CLI, catalogs);
- stories L03, R04, C09, C10 and C13;
- the finance suites as regression.

**Constraints**:
- tenant-scoped;
- one finance lock per settlement;
- the R04 settlement grows linearly with its lines.

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | The statement and each line are source records. The payout, payment, refund and fee documents carry them, and the ledger entries and allocations follow. |
| II. Reality is the operational authority | PASS | No document status. A line is booked when a document or return carries its source. |
| III. Proven schema only | PASS | Two tables, justified below. Payouts need none. |
| IV. Tenant and service boundaries | PASS | Reviewed finance commands under the finance lock; every read is tenant-scoped. |
| V. Specification and test evidence | PASS | Tests first per phase. |
| VI. Explainable Web product | PASS | The payout read names every line's booking, order, invoice and shipment; the findings name their amounts. |
| VII. Simplicity and storage discipline | PASS | Existing primitives do the booking. |
| VIII. Received values are recorded, never recomputed | PASS | Stated amounts are booked as stated. A statement that does not add up is refused, not corrected. |

### DR-001: the two tables

- `payment_authorization`:
  - Its amount is summed against captures on every read.
  - Its `expires_at` is compared with the reading instant for the finding.
  - It is joined to its order for the finding and the order read.
- `payment_capture`:
  - Its amount is summed per authorization, both to refuse a capture beyond what is left and to derive the remainder.
- Payouts need no table:
  - The statement is a source record, and each line is its own source record.
  - Whether a line is booked is whether a document or a payment return carries that line's source.

## Design

### 1. Settlement (`services/payouts.py`)

**Command** `finance.payout.settle`, with `PayoutSettleRequest` holding:
- `provider_party_id`, `payout_reference`, `paid_on`, `currency`, `amount` (the net payout);
- `clearing_account_id` (cash role, the provider's account) and `bank_account_id` (optional cash account, default the cash destination);
- `lines`, 1 to 2000: `line_id`, `kind` (`charge`, `refund`, `chargeback`, `fee`), `amount`, `references` (payment intake references plus `tracking_number`), and an optional `reason`.

**Preview** (`preview_payout`):
- Validates the accounts and the lines.
- Checks the total: Σcharge − Σrefund − Σchargeback − Σfee equals the amount, or `payout_total_mismatch` with both totals.
- Resolves every line:
  - **charge**: finds the customer from the references across customers, then `resolve_references`. `allocate` for exactly one posted invoice; `record` for a customer without exactly one invoice; `unmatched` otherwise.
  - **refund**: finds the customer the same way. `allocate` to the order's open credit note; `record` otherwise; `unmatched` without a customer.
  - **chargeback**: `return` for the order's unreturned customer payment booked on this provider account, of the same amount (a charge of the same statement counts); `unmatched` otherwise.
  - **fee**: `expense`.
  - A line already booked reads `booked`.
- A statement already settled under this reference with other content is refused (`payout_statement_changed`).

**Execution** (`settle_payout`), under the finance lock:
1. Store the statement source (`payout_statement`, external id `{provider_party_id}/{payout_reference}`).
2. Record the payout document once: bank cash debit, provider cash credit, party the provider.
3. Store each line's source (`payout_line`, external id `{statement source id}/{line_id}`), then book it in the order charge, refund, chargeback, fee.
4. Emit `payout.settled` with the counts and the unbooked line ids.

**Booking primitives**:
- A charge is `record_customer_payment` on the provider account, allocated `min(amount, open)`.
- A refund is `record_customer_refund` on the provider account, allocated to the credit note.
- A chargeback is `payment_returns.record_return`, kind chargeback, with the line's source.
- A fee is a `payout_fee` document: payment-fee expense debit, provider cash credit.

**Core changes**:
- `post_ledger` gains a private `_line_account_ids`, so the deposit can name two cash accounts.
- `record_customer_payment` and `record_customer_refund` gain a private `_cash_account_id`.
- `record_return` gains a private `_source_record`.
- `resolve_references` learns `tracking_number`: package → shipment → movements → promises → order → invoices.

**Reads**:
- `finance.payouts`: newest first, with counts and the unbooked amount.
- `finance.payout`: every line with its outcome, its documents, and its order, invoice and shipment.

### 2. Authorizations (`services/payment_authorizations.py`)

**Commands**:
- `finance.payment.authorization.record`: `order_document_id`, `amount`, `currency`, `authorized_at`, `valid_until` (stored as `expires_at`), `reference`.
- `finance.payment.capture.record`: `authorization_id`, `amount`, `captured_at`, `reference`.

**Refusals**:
- the order is not a sales order;
- the currency differs from the order's;
- the authorization expires before it was authorized;
- the reference was already recorded for this order;
- the capture is beyond the remainder, after the expiry, or before the authorization.

**Read** `finance.payment_authorizations`: per order, each authorization with authorized, captured, remaining, expiry and its state at the instant (`live`, `expired`, `captured`).

### 3. Findings

- `payment_authorization_expired` (record: the order):
  - Uncovered = Σ remainders of the expired authorizations − Σ remainders of the live ones.
  - Reported while it is above 0 and the order has an open customer promise.
- `payout_line_unmatched` (record: the payout document): the unbooked lines, their amount and their kinds. It clears when the statement is settled again once their orders or payments are held.

### 4. Gates

- Commands:
  - `tools/finance.py`, the preview in `tools/application.py`;
  - MCP propose and read tools with `mcp_topics`, and CLI commands;
  - `command_catalog.yaml` with capability guidance for the reads, `action_discovery.json`, the web action-reference fixture;
  - the tenant isolation catalog, `catalogs.py`, the business event catalog, the resource catalog with German labels;
  - `service_refusals.json` and the translations.
- Exception classes:
  - the class order, the registry and the catalog;
  - the reference catalog consumers and pinned counts;
  - the pinned lists, `WITHOUT_A_SCENARIO` and the translations.
- Tables:
  - `data_model.yaml`, the reporting-graph coverage and the foreign-key index list;
  - the transaction matrix rows `payout` and `payout_fee`;
  - `make docs-generate`.

## Rollback

Downgrade 0126 drops the two tables. Payouts leave ordinary documents, ledger entries and allocations, which reverse through the existing ledger reversal.
