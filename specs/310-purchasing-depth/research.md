# Research: Supplier Confirmations, Minimum Quantities and Three-Way Match

## Today

- **Revisions:** `commitment_revision` is append-only with `quantity`, `due_at`, `note` and `source_record_id`. The value in force is the latest stated value per field (`commitment_terms`). The agreed price lives only on `document_line.unit_price`.
- **Price check:** `invoice_price_differs` compares an invoice line with the order line it bills (`billed_document_line_id`). The guided invoice copies the order line's price.
- **Supplier data:** there is no per-supplier item record. `item` has `purchase_unit`, `conversion_factor` and `lead_time_days`, and spec 301 left supplier pack sizes to a later spec.
- **Cancellation:** `cancel_commitment` records the reason and releases holds, but no cost. A free supplier invoice can carry a charge line with `billed_document_line_id`. `_order_line_promises` does not filter cancelled promises.
- **Match:** `billable_positions` gives ordered, delivered and invoiced per line, but skips fully billed lines. No read joins received and billed per purchase line.

## Decisions

- **Price on the revision:** the confirmation already is a revision, so the price joins quantity and date under the same in-force rule. No second confirmation record.
- **Terms per supplier and item** in a small table following the spec 320 pattern, as `customer_item_number` did. They are a warning in review, not a refusal; the person decides.
- **Charge as a free supplier invoice line:** existing posting, payment and evidence apply. The purchase findings only need to skip cancelled promises and charge lines.
- **Match as a read:** every input is a Reality record. Storing the answer would be a second authority (DR-002).

## Alternatives rejected

- A confirmation table separate from revisions: it would duplicate quantity and date.
- Item-level minimums: wrong for two suppliers with different terms.
- A tolerance setting: not asked for, and it adds rules.
