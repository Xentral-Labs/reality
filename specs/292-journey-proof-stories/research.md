# Research: Journey Proof Stories

Code reading on 2026-09-28 against `origin/main` (`fec842a0`). No story was run yet; each
finding states the expected outcome and the condition it depends on. Paths are relative to
`packages/reality-core/`.

## Shared setup

- Fixtures: `session` and `business` (`tests/conftest.py`) give a tenant, company, customer,
  supplier, item and location; `record_by_id` reads a record back.
- Stories go into the existing catalog files under `tests/scenarios/`, which already hold
  one story per catalog ID and have rows in `docs/SPEC_COVERAGE_MATRIX.md`.
- Orders: `core.create_manual_order` (one commitment per line; every line needs
  `gross_amount`) or the reviewed `order_create` delivery action used by
  `test_catalog_orders_and_shipments.py::_order`.
- Stock and movement: `core.record_movement` (`opening_stock`, `shipment`, `return`);
  a shipment above the open quantity is refused.
- Reservation: `core.reserve`; totals via `core.active_reserved`.
- Open items: `core.open_invoice_amount`, `core.account_balance`,
  `finance.balances.party_balance_rows`; operational signals via
  `services.exceptions.operational_exceptions`.

## Per journey

| ID | Services | Expected | Condition or risk |
|---|---|---|---|
| A04 | `revise_commitment`, `commitment_quantity`, `open_quantity`, `fulfilled_quantity` | pass | Stored `Commitment.quantity` stays the original; read the quantity in force through `commitment_quantity`. |
| A06 | `reserve`, `cancel_commitment` (reason required) | pass | Cancellation releases only that commitment's reservations and hold. |
| A07 | `cancel_commitment` per line | pass | No order-level cancel exists; the story cancels each line. The limitation stays. |
| A19 | `create_manual_order` with a zero-price line, `record_sales_invoice`, exceptions | at risk | Orders accept a zero price. `record_sales_invoice` refuses a zero-amount position (`positive`), and `shipped_not_billed` has no zero-price exemption, so a shipped free line without an invoice line raises a high-severity signal. The story tries a multi-line invoice with the free line at zero through `create_manual_document_with_lines`; if that is refused or the signal remains, A19 stays partial. |
| F01 | shipment, return, `post_sales_invoice`, `post_customer_payment`, credit note with lines citing the order line, `post_sales_credit_note`, `post_customer_refund` | pass | Credit lines must cite the order line; otherwise `returned_not_credited` fires. |
| F05 | return into a returns area, `record_return_disposition`, `return_disposition_summary`, credit note | pass | "Reduced credit" is recorded as a full-quantity credit plus a negative charge line for the damage. Crediting fewer units is deliberately reported as `returned_not_credited` and is not the journey. |
| F07 | return, zero-price replacement order, shipment, exceptions | likely fail | No exchange concept: a linked return raises `returned_not_credited` when the original was invoiced; an unlinked one raises `unexplained_movement`; the shipped zero-price replacement raises `shipped_not_billed`. |
| C04 | prepayment term, `record_sales_invoice` per order, `record_customer_payment`, `allocate_settlement` per invoice, `fulfillment_readiness` | pass | Readiness sums active allocations per order, so one payment split across two invoices releases both. |
| M08 | `finance.settlement.apply` with a customer `reduction` of category `agreed_deduction` | pass | The reason is on the proposal review and the stored adjustment source record, not on the execute receipt. |
| N06 | `party_balance_rows`, `finance.deposit.record`, prepayment invoice and unallocated payment | pass | A prepayment is an ordinary invoice under a prepayment term; unpaid it is an open item, paid but unallocated it is a credit. The story states both. |
| N01 | `create_party(tax_identifier=…)`, `record_sales_invoice` with `reality_finance_v1` net/tax 0/gross, case code via an internal `case_code` reference | pass | A source-declared case code resolves only for a registered source system; the internal reference is the reliable route. The VAT ID lives on the party, not on the invoice. |
| N02 | `record_supplier_invoice` with stated net, tax 0, gross | pass | No reverse-charge concept: stating the self-assessed tax as `tax` is refused by net + tax = gross. The journey question is "stated tax recorded?", so tax 0 as stated is the case; the limitation names the missing self-assessment. |

## Decisions

- **Story placement**: order stories in `test_catalog_orders_and_shipments.py`, return stories
  in `test_catalog_stock_and_returns.py`, finance and tax stories in `test_catalog_finance.py`.
  Rationale: existing catalog convention; no new fixture module.
- **Service route**: stories use the reviewed proposal route where the journey is a person's
  action in the product (cancel, settlement, deposit) and direct shared services otherwise,
  matching the existing catalog stories. No ORM writes.
- **Failure handling**: A19 and F07 are written to the journey's business outcome, not to
  what the code does today. If they fail, the failure is the finding (spec FR-005, FR-006);
  the story is then renamed to pin today's behavior as a named limitation (repository style,
  for example `test_a_return_leaves_the_promise_kept`); the repository uses no `xfail`.
- **Promotion evidence**: each promoted journey's `internal_evidence` names the new story;
  earlier references stay.
