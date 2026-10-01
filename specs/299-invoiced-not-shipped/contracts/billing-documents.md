# Contract: Down-Payment, Final and Pro-Forma Invoices; Month-End Billing

## Reviewed tool `down_payment_invoice_record`

- **Arguments**: `order_id` (sales order), `number`, `gross_amount`, optional `net_amount` and `tax_amount` (stated), `effective_at`.
- **Review**: shows the order, its value, the down payments already invoiced and the amount; no billed quantity.
- **Execution**: records the `down_payment_invoice` linked to the order and posts receivable / received down payments.
- **Refusals**:
  - `down_payment_order_required` (not a sales order)
  - `down_payment_currency_mismatch`
  - `down_payment_amount_invalid`
  - `finance_account_default_missing`

## Changed: `sales_invoice_record`

- **New optional argument**: `down_payment_offsets: [{down_payment_document_id, amount}]`.
- **Review**: adds `down_payment_offers`, the order's down-payment invoices with paid, already offset and offsettable amounts. It also shows the stated offsets and the open amount after them.
- **Execution**: posts the invoice, then the offset posting, and records one `down_payment_offset` per stated offset.
- **Refusals**:
  - `down_payment_offset_exceeds_paid`
  - `down_payment_offset_other_order`
  - `down_payment_offset_reversed`
  - `down_payment_offset_exceeds_invoice`

## Reviewed tool `proforma_invoice_record`

- **Arguments**: `order_id`, `number`, `gross_amount`, optional `lines` (description, quantity, stated amounts), `document_date`.
- **Execution**: records the `proforma_invoice` linked to the order; posts nothing.
- **Refusals**: `proforma_order_required`, `proforma_currency_mismatch`.

## Read `month_end_billing`

- **Arguments**: `as_of` (optional).
- **Returns**: `shipped_not_billed` and `billed_not_shipped`. Each row names the order, line, item and quantities, taken from the findings at `as_of`.
- **Surfaces**: MCP `month_end_billing`, Web `GET /finance/month-end-billing`, CLI `month-end-billing`.

## Surfaces for the tools

- MCP: `down_payment_invoice_record_propose`, `proforma_invoice_record_propose`, and the extended sales invoice tool.
- Web: delivery-action pass-through.
- CLI: propose commands.
