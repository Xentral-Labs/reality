# Contract: Chargebacks, Returned Direct Debits and Payment Fees

## Command `finance.payment.return` (finance change proposal, owner confirmation)

Input:

```json
{"expected_revision": 12, "payment_document_id": "doc_...", "kind": "direct_debit_return",
 "returned_on": "2026-10-02", "reason": "MD06 – refund on customer request",
 "reference": "RTN-4711", "fee_amount": "3.50", "fee_bearer": "customer"}
```

The preview names the payment, the invoices it reopens with their open amount after the return,
the reversal and the fee postings. Receipt: the return detail.

Refusals: `payment_return_not_customer_payment`, `payment_return_already_reversed`,
`payment_return_already_returned`, `payment_return_fee_adjusted`, `payment_return_reason_missing`,
`payment_return_kind_invalid`, `payment_return_fee_invalid` (negative or more than four decimals),
`payment_return_fee_bearer_invalid` (a bearer for a zero fee, or none for a positive one),
`finance_account_default_missing` (no `payment_fee_expense` default), `dunning_preview_stale`-style
`finance_preview_stale` on a stale revision.

## Reads `finance.payment_returns` / `finance.payment_return`

```json
{"id": "prt_...", "payment_document_id": "doc_...", "payment_number": "PAY-1", "kind": "chargeback",
 "reason": "...", "reference": "...", "returned_on": "2026-10-02", "fee_amount": "15.0000",
 "fee_bearer": "company", "reopened": [{"invoice_id": "doc_...", "number": "RE-1", "open": "100.00"}],
 "ledger_reversal_id": "lrv_...", "fee_document_id": "doc_...", "fee_charge_document_id": null,
 "source_record_id": "src_..."}
```

## Settlement reduction category `payment_fee`

`finance.settlement.apply` with `reduction.reason_category = "payment_fee"` books the reduction
against `payment_fee_expense`; everything else is unchanged.

## Exception class `payment_returned`

One finding per invoice reopened by a return and still open; causal values kind, reason,
reference, returned_on, open; clears when the invoice's open amount is zero.
