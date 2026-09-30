# Data Model: Chargebacks, Returned Direct Debits and Payment Fees

## payment_return (new)

A confirmed statement that a customer payment came back. Reality, append-only.

| Column | Type | Rule |
|---|---|---|
| `tenant_id` | string | part of the primary key |
| `id` | string | opaque, prefix `prt` |
| `payment_document_id` | string | composite FK `document` (type `customer_payment`); unique |
| `kind` | string | `direct_debit_return` or `chargeback` (check) |
| `reason` | text | stated, not empty |
| `reference` | string | stated bank or provider reference; may be empty |
| `returned_on` | date | stated |
| `fee_amount` | numeric(18,4) | `>= 0`, stated |
| `fee_bearer` | string | `customer`, `company` or `none` (check; `none` iff fee is 0) |
| `ledger_reversal_id` | string | composite FK `ledger_reversal`; unique |
| `fee_document_id` | string, nullable | composite FK `document`: the company's fee cost |
| `fee_charge_document_id` | string, nullable | composite FK `document`: the fee charged on |
| `source_record_id` | string | composite FK `source_record`: the confirmed request |
| `created_at` | UTC timestamp | |

Which invoices it reopened is read from the payment's allocations at read time (DR-002).

## Account role

`payment_fee_expense` — "Payment fees", added to `ACCOUNT_ROLES`, the account-role check and the
demo account plan.

## Document types

| Type | Posting | Meaning |
|---|---|---|
| `payment_return_fee` | `payment_fee_expense` debit / `cash` credit | the fee the bank or provider charged the company |
| `payment_return_fee_charge` | `accounts_receivable` debit / `payment_fee_expense` credit | the fee charged on to the customer; settleable |
| `customer_settlement_adjustment` (existing) | `payment_fee_expense` debit / `accounts_receivable` credit | a fee the provider deducted from a payment (category `payment_fee`) |

## Events

| Event | Subject | Payload |
|---|---|---|
| `payment.returned` | `payment_return` | kind, reason, reference, returned_on, fee, bearer, reopened invoice ids, reversal id |
| `ledger.reversed` | `posting_group` | unchanged, with `payment_return_id` in the actor context |

## Migration

`0103_payment_returns`: the table with composite tenant FKs and FK indexes, and the role check
extended by `payment_fee_expense`.
