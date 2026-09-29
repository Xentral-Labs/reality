# Research: Shop Order Changes and Refunds

Code reading on 2026-09-29 against `origin/main` (`458ac1f3`). Paths are relative to
`packages/reality-core/`.

## R1. What happens today (spec 081)

- `enqueue_shopify_order` → `enqueue_source("shopify", "order", payload["id"], …, source_version_at=updated_at, context=…)`
  (`services/core.py` ~12342). Versions are stored by `store_source_record` with a payload hash
  (duplicates are recognised), an arrival `version`, `supersedes_source_record_id`, and a
  stale/conflict disposition when `updated_at` is present.
- `_shopify_interpretation` (~12371) interprets version 1 into one `sales_order` Document, one
  `DocumentLine` per `line_item` (`source_line_id = str(line_item.id)`, raw line in `payload`) and one
  `customer_delivery` Commitment per line (`document_line_id`). Every version > 1 raises
  `ShopifyUpdateNeedsReview`; `process_import_job` rolls back, completes the job and writes a
  `needs_review` outcome with reason `shopify_update_requires_review`.
- An unknown SKU raises `InvalidOperation("Unknown SKU")`: the job fails, nothing is interpreted,
  and `source_interpretation_failure` reports it.
- Nothing interprets refunds: `connector_catalog.yaml` declares `refund: sales_refund`, but
  `SOURCE_INTERPRETERS` has only `("shopify", "order")`.
- Shopify orders get no invoice, payment or credit note in Reality.

## R2. Comparing a version with current Reality, not with the previous payload

**Decision**: A later version is compared with the order's current Reality: per line, the
commitment's effective quantity (`commitment_quantity`, latest revision), its fulfilled quantity and
status; the order's lines by `source_line_id`; for price and address, the payload of the source the
order was interpreted from.

**Rationale**: Comparing payloads would re-apply or miss changes after a held version or a
person's manual revision. Comparing with Reality makes replay and out-of-order arrival safe
(FR-009): a version that asks for what already holds applies nothing.

The order is found from the version's identity: the `sales_order` Document whose source record has
the same `source_system`, `source_type` and `external_id`. The interpretation context of a later
version comes from its own job input (callers supply it, as `enqueue_shopify_order` does); if it is
missing, the original job's input is reused, as `record_corrected_document_source` does.

## R3. The stated quantity of a line

**Decision**: `current_quantity` when the line carries it (Shopify Admin API since 2023-01; edits and
cancelling refunds lower it), otherwise `quantity`. A line absent from `line_items` states zero.

## R4. Classifying a version

| Change against current Reality | Result | Code when held |
|---|---|---|
| Only uninterpreted fields changed (note, tags, timestamps) | interpreted, no effect | — |
| Open line lowered, not below fulfilled | `revise_commitment(quantity=…)` | — |
| Open line lowered to exactly fulfilled | revision closes the open rest | — |
| Open line with nothing fulfilled lowered to zero or removed | `cancel_commitment(reason=…)` | — |
| `cancelled_at` set, nothing fulfilled on any line | cancel every open line | — |
| `cancelled_at` set, something fulfilled | held | `cancelled_after_shipment` |
| Lowered below fulfilled | held | `reduces_shipped_quantity` |
| Quantity raised | held | `quantity_increased` |
| New line | held | `line_added` |
| Unit price changed | held | `price_changed` |
| Shipping address changed | held | `address_changed` |
| Currency changed | held | `currency_changed` |
| Line on a closed (fulfilled or cancelled) promise changed | held | `closed_line_changed` |
| Lowering needs a choice between several reservations | held | `reservation_choice_required` |
| Line without an item (R6) changed | held | `unassigned_line_changed` |

A version with any held code applies nothing (all or nothing, FR-004). Its outcome is
`needs_review`; the reason code is the single code, or `shopify_changes_require_review` when several
apply, and the summary names every code with its line. `ShopifyUpdateNeedsReview` gains the codes.

Applied reductions go through `revise_commitment` and `cancel_commitment` with
`source_record_id = the version` and `_commit=False` (DR-003), so reservations are released and
`commitment.revised` / `commitment.cancelled` events cite the source. The intake policy
(`tenant_policy._INTAKE_OPERATIONS`) admits these operations for interpretation.

**Alternatives rejected**: applying the reducible part of a mixed version (a half-applied order
would be harder to review than a held one); comparing with the previous payload (R2).

## R5. Refunds as their own source records

**Decision**: When a Shopify order version is stored, each entry of `refunds[]` is also stored as
its own source record `("shopify", "refund", refund.id)`, whose payload is the refund object plus
the order id. It is interpreted by a new `("shopify", "refund")` interpreter, which is also what a
Shopify `refunds/create` webhook would feed.

**Rationale**: `process_import_job` rolls back a held version, so a refund interpreted inside the
order version would be lost whenever the order change is held. As its own source, a refund is
recorded independently, deduplicated by its identity (the same refund in later versions is a
duplicate), and retried if its order is not interpreted yet (the job fails and backs off; the
refund "waits with the order").

**Interpretation of one refund**:
- Evidence: one Document of type `sales_refund` (the connector capability's target type) with the
  refunded amount as stated (sum of the successful `transactions[].amount` of kind `refund`), currency, and one DocumentLine per `refund_line_items[]` entry naming the Shopify line
  through `source_line_id` (not `billed_document_line_id`, which billing readers count), with
  quantity and stated subtotal. No ledger posting
  (Non-Goal); a `sales_refund` has no settlement control, so it is no open item.
- Reality: for a refund line with `restock_type == "return"` on shipped quantity, a return
  announcement (`announce_customer_return`, `source_record_id` = refund source, reference
  `Refund <id>`) for `min(refunded, announceable)`. The existing class
  `announced_return_not_arrived` reports it until goods arrive; a person withdraws it with the
  existing reviewed tool if they never will (FR-007).
- A refund line with `restock_type` `cancel` needs no action here: Shopify lowers the line's
  `current_quantity`, and the order version applies it (R3, R4). `no_restock` records no
  expectation.

**Alternatives rejected**: a credit note (it would enter `credited_not_returned` and the open items
without an invoice to credit; owner chose evidence); a new exception class for refunded-not-returned
(the announcement already has arrival, threshold, withdrawal and a reviewed tool).

## R6. Unknown items

**Decision**: Version 1 with an unknown SKU is interpreted: known lines as today; an unknown line
becomes a DocumentLine with `item_id = None`, `line_type = "item"`, its stated SKU, quantity and
price, and no commitment. A new exception class `order_line_item_unknown` reports sales-order
item lines without an item. A reviewed tool `order_line_item_assign` (document line, item) sets the
line's item and creates its delivery promise, citing the decision.

**Rationale**: `DocumentLine.item_id` and `Commitment.item_id` are already nullable; the exception
derivations start from commitments, so an item-less line cannot distort them. Assigning an item is
the missing interpretation of the source's SKU, decided by a person.

`test_source_survives_interpretation_failure` pinned the old behaviour and is rewritten.

The order's promises are reached through their lines (`Commitment.document_line_id` →
`DocumentLine.document_id`), not through `Commitment.document_id`, which the reference catalog
keeps trace-only; the new class is a `reports_absence` consumer of `document_line_id`.

## R7. Surfaces and gates

- Web: held reason codes and their lines on the import-job review; the order inspector lists its
  refunds; the exception row for an unknown item offers "Assign item"; the held
  `cancelled_after_shipment` names the return-announcement action as its next step
  (`resolution_guidance.json`).
- MCP/Chat and CLI: `order_line_item_assign_propose` / confirm and the read of held reasons through
  the existing interpretation-coverage read.
- Gates: new tool (isolation catalog, command catalog, discovery, resource labels), new exception
  class (all pinned lists), new refusal codes, `sales_refund` document type registration, spec 081
  noted as narrowed, docs regeneration.
