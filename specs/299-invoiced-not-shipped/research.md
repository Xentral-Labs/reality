# Research: Invoiced Not Shipped, Down-Payment and Pro-Forma Invoices

Read on 2026-10-01 against `origin/main` at 5d3e4cfa. Paths are under `packages/reality-core/src/reality/`.

## R1. Today

- **Deposits**: a down payment can only be a `customer_deposit` (`services/finance/deposits.py`): cash in, a receivable credit, cleared later against an invoice. It names no order.
- **Prepayment readiness** (`services/fulfillment_readiness.py`) counts payments allocated to posted sales invoices whose lines bill the order's lines, so a deposit before any invoice leaves `prepayment_invoice_missing`.
- **Billed but not delivered**: only the purchase side has it, `billed_not_received` (`services/exceptions.py`). It compares an order line's invoiced quantity with its received quantity.
- **Open amounts**: an invoice's open amount is its own balance on its control account minus allocations (`open_invoice_amount`, `SETTLEMENT_CONTROL`). A second posting on the same document, crediting the receivable, lowers what is open.
- **Missing types**: there is no down-payment or pro-forma document type, and no link from an invoice document to an order other than through billed lines.

## R2. The order link (FR-002, FR-004)

**Decision**: a nullable `document.order_document_id` (same-tenant foreign key to the sales order), set only for `down_payment_invoice` and `proforma_invoice`.

Readiness, the offset proposal and the order's evidence each join on it repeatedly (Constitution III). It is the shortest true relationship: the document is *for* the order, not for any line.

**Rejected**: billing an order line from the down-payment invoice, because every billing reader would count it as invoiced quantity.

## R3. Down-payment invoice (FR-002)

- **Document**: type `down_payment_invoice`, linked to its order. Its lines state what the customer is asked to pay (gross and, optionally, stated net and tax). No line bills an order line.
- **Posting**:
  - receivable debit against a new account role `customer_down_payments` ("Received down payments"), credit;
  - `SETTLEMENT_CONTROL` gains `down_payment_invoice: accounts_receivable, debit`, so ordinary customer payments settle it;
  - it is an open item, so aging and dunning see it.
- **Readiness**: down-payment invoices of the order join the candidate receivables. Their allocated payments count as received, and their existence satisfies the invoice-basis check.
- **Tool**: a reviewed delivery tool `down_payment_invoice_record` (order, number, gross amount, optional stated net and tax, effective time) records and posts it in one confirmation, like `sales_invoice_record`.
- **Refusals**: another currency or party than the order, a non-sales order, a non-positive amount.

## R4. Final invoice offset (FR-003)

- **Proposal**: recording a sales invoice with `sales_invoice_record` previews `down_payment_offers` for the order line's order. These are the order's down-payment invoices with their paid amount, less what earlier final invoices already offset.
- **Confirmation**: the person states `down_payment_offsets: [{down_payment_document_id, amount}]` in the same reviewed recording.
- **Execution**:
  - The final invoice is posted as today.
  - Then a second posting on it: `customer_down_payments` debit, `accounts_receivable` credit, for the stated total. Only the rest is open, and the received down payments are cleared.
  - Each offset is a `down_payment_offset` row (final invoice, down-payment invoice, amount, source record). It is the record a later offset must not exceed (Constitution III: computed against on every proposal).
- **Refusals**:
  - an offset over what is paid and not yet offset: `down_payment_offset_exceeds_paid`
  - another order's down payment: `down_payment_offset_other_order`
  - a reversed down-payment invoice: `down_payment_offset_reversed`

## R5. Pro-forma (FR-004)

Type `proforma_invoice`, linked to its order, with stated lines and gross amount. It is recorded through a reviewed tool `proforma_invoice_record`, is never posted and has no control account. It is not an open item, and no billing or prepayment reader reads it, because they read `sales_invoice` only. The order inspector lists it.

## R6. Invoiced but not shipped (FR-001)

- **Finding**: a class `billed_not_shipped`, the sales mirror of `billed_not_received`, reported per customer order line where the invoiced quantity exceeds the shipped quantity.
  - Invoiced quantity counts sales invoice lines billed to the line; down-payment and pro-forma documents bill no line.
  - Shipped quantity is the raw shipments.
  - Severity normal; it clears when the goods ship.
- **Month-end list**: a read tool `month_end_billing` (`as_of`) returns the shipped-not-billed and billed-not-shipped rows from `operational_exceptions(as_of)`. The list and the findings therefore cannot disagree (SC-003). It is on MCP, Web and CLI.

## R7. Gates

- Migration `0105`:
  - the column and its foreign-key index
  - the `down_payment_offset` table with foreign-key indexes
  - the account-role check
- Class gates for `billed_not_shipped`: CLASS_ORDER, registry, catalogs, test lists, reference catalog (it reads `billed_document_line_id`), labels and the `test:i18n` translations.
- Tool gates: command catalog, coverage, guidance for the read, discovery and its web fixture, labels, isolation catalog and counts, MCP, CLI.
- Refusals with de/nl/es.
