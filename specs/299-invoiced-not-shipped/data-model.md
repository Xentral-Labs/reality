# Data Model: Invoiced Not Shipped, Down-Payment and Pro-Forma Invoices

## Changed: `document`

| Field | Type | Why |
|---|---|---|
| `order_document_id` | nullable FK → `document` (same tenant), indexed | The sales order a down-payment or pro-forma invoice is for. Read by readiness, the offset proposal and the order's evidence (R2). |

New document types: `down_payment_invoice` and `proforma_invoice`.

## New: `down_payment_offset`

| Field | Type | Notes |
|---|---|---|
| `id` | text | PK with `tenant_id` |
| `tenant_id` | FK tenant | indexed |
| `final_invoice_document_id` | FK document | the sales invoice that states the offset; indexed |
| `down_payment_document_id` | FK document | the down-payment invoice it offsets; indexed |
| `amount` | numeric(18,4) | > 0, as stated |
| `source_record_id` | FK source_record | the confirmed recording; indexed |
| `created_at` | timestamptz | |

Check: `amount > 0`.

The posting that clears the down payment on the final invoice is an ordinary ledger posting group on the final invoice document.

## Changed: account roles

New role `customer_down_payments` ("Received down payments"). The default account is created with the others. Transaction matrix rows:
- `down_payment_invoice`: `accounts_receivable` / `customer_down_payments`
- `down_payment_offset`: `customer_down_payments` / `accounts_receivable`

## Derived (not stored)

- **Paid down payment**: allocations to a down-payment invoice's receivable, less its reversals.
- **Offsettable**: paid minus the `down_payment_offset` amounts already recorded.
- **`billed_not_shipped`**: invoiced quantity minus shipped quantity per customer order line.
- **Month-end list**: the shipped-not-billed and billed-not-shipped findings at `as_of`.
