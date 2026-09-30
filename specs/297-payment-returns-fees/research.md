# Research: Chargebacks, Returned Direct Debits and Payment Fees

Code reading on 2026-09-30 against `origin/main` (`6fb71d2e`). Paths are relative to
`packages/reality-core/`.

## R1. What exists

- `core.reverse_ledger_posting_group` (~8855) writes the exact inverse of a posting group, adds a
  `LedgerReversal` (free-text reason, no category, no source) and emits `ledger.reversed`.
  Allocations are never deleted; `active_settlement_allocations` and `_open_amount` ignore those
  whose payment group is reversed, so reversing a customer payment reopens the invoices it paid.
  The reviewed tool is `ledger_reverse` (delivery review, `financial_reversal_actions.py`).
- `dunning.reverse_notice` wraps the reversal with `_commit=False` and emits its own domain event:
  the pattern for a return.
- `finance.settlement.apply` records cash, allocates it and can accept a stated reduction
  (`StatedReduction.reason_category` in early_payment_discount, agreed_deduction,
  accepted_small_remainder, bad_debt); `settlement.accept_adjustment` posts a
  `customer_settlement_adjustment` document against `customer_reduction` or `bad_debt_expense`
  and allocates it. A provider fee is only expressible as `agreed_deduction` today, which books
  it as a sales reduction.
- Account roles live in `domain/finance.py` (`ACCOUNT_ROLES`, `TRANSACTION_MATRIX`), the
  `CreateAccount.role` Literal and the DB check `ck_subledger_account_role`; a new role needs a
  migration (precedent `0089_commercial_edge_workflows`).
- `financial_open_items` reads invoices and opening debts only; a fee charge (`dunning_fee_charge`)
  is a ledger receivable but no open item (known gap, spec 295).
- `document_create` + `sales_invoice_post` accept a sales invoice with lines that have no order
  line and a free `line_type`; `shipped_not_billed`, `invoice_price_differs` and
  `sold_below_purchase_price` ignore such lines.
- No source interprets returns, chargebacks or provider fees.

## R2. The return as its own record

**Decision**: A new table `payment_return` records one returned customer payment: the payment
document, kind (`direct_debit_return` or `chargeback`), stated reason, reference, return date,
stated fee, who bears it, the `LedgerReversal` it caused and the fee documents. It is written by the
reviewed finance command `finance.payment.return`, which reverses the payment's posting group
through `reverse_ledger_posting_group(..., _commit=False)` in the same transaction.

**Rationale**: Constitution III: the finding (R4) reads it on every evaluation, the invoice
explanation and the payments list join on it, and kind is filtered. A `LedgerReversal` column
would put payment semantics on a generic reversal row. One return per payment (unique).

**Alternatives rejected**: a reason category on `LedgerReversal` (every reversal would carry
payment vocabulary); an event only (the finding would have to scan events).

## R3. The fee

**Decision**: A new account role `payment_fee_expense` ("Payment fees").
- Every stated fee is the company's cost first: cash credit / `payment_fee_expense` debit, on a
  `payment_return_fee` document.
- Charged on to the customer (the preselected choice): a second document
  `payment_return_fee_charge` posts `accounts_receivable` debit / `payment_fee_expense` credit, so
  the expense is recovered and the customer owes the fee. It is in `SETTLEMENT_CONTROL`, so it can
  be settled by allocation.
- A zero fee posts nothing.

**Known gap, inherited**: like the dunning fee, the fee charge is a ledger receivable but not an
open item (`financial_open_items` reads invoices only). It is recorded in the spec; widening the
open items is its own follow-up.

## R4. Following up the reopened invoice

**Decision**: A new exception class `payment_returned`: one finding per invoice that a returned
payment had paid and that is still open, naming kind, reason, reference and date. It clears when the
invoice's open amount is zero again (paid, credited or written off). The invoice inspector names the
return.

## R5. Fees deducted from a payment

**Decision**: A new stated-reduction category `payment_fee` in `finance.settlement.apply`, posted by
`accept_adjustment` against `payment_fee_expense` instead of `customer_reduction`. The clerk states
the cash received (97) and the fee (3); the invoice is settled in full.

**Returning such a payment** is refused (`payment_return_reduction_active`) while any reduction
booked with it is still in force: a payment fee, an early-payment discount, an agreed deduction or an
accepted small remainder. It is recognised by the confirmation both source records name
(`confirmation_id`), because the payment and its adjustment have separate source records. Otherwise
the adjustment would stay in force and the invoice would reopen short. The clerk reverses the
adjustment first; a reversed adjustment no longer blocks the return. Recorded as a limitation
(review round, 2026-09-30).

## R6. Freight and surcharges (E08)

**Decision**: No change. A business story records a sales invoice through `document_create` with an
item line billed to its order line plus an unlinked `shipping` and `charge` line, posts it, and
proves that the goods findings do not report the charges (positive control: before the invoice,
the delivery is reported as shipped and not billed).

## R7. Surfaces and gates

- MCP/Chat: `finance_payment_return_propose`, reads `finance_payment_returns` and
  `finance_payment_return`; CLI `finance-payment-return-propose`, `finance-payment-returns`.
- Web: on the Finance page's payments list, "Payment returned" on a recorded customer payment
  opens a dialog (kind, date, reason, reference, fee, bearer) that proposes the command and
  confirms it; the settlement reduction offers "Payment fee".
- Gates: migration `0103_payment_returns` (table and role check), data model, isolation catalog
  and counts, command catalog, discovery, resource labels, refusals in four languages, events
  (`payment.returned`), exception class lists, reference catalog, docs regeneration.

## R9. Review round (2026-09-30)

- A reduction of any category booked with the payment blocks the return until it is reversed (R5).
- The finding reports only what the customer owes as an invoice (sales invoices and opening
  customer debts), newest return per invoice; the preview still lists every document the payment
  paid, with its type, because a refund allocated against the payment is open again too.
- The fee is credited to the cash account the payment was booked on, not the current default.
- A missing or malformed return date has its own refusal, `payment_return_date_invalid`.
- The finding and the invoice inspector read returns with one joined query instead of one
  query per historical return.

