# Research: Journey Proof Stories, Round Three

Read on 2026-09-30 against `origin/main` at 6fb71d2e. Paths are under `packages/reality-core/`.

## R1. F04 — unannounced return, linked later

**Route**: `record_movement(..., "return", ...)` without `commitment_id` or `return_announcement_id`, as the F03 story does. The reviewed `movement_correct` tool links it later with a replacement `return` that names the delivery (`core.correct_movement`, allowed replacement fields in `services/core.py` near 5489). The replacement keeps the original `occurred_at`.

**Expected**: before the link, `unexplained_movement` is reported and `returned_not_credited` is not; after it, `unexplained_movement` clears (a corrected original is excluded) and `returned_not_credited` is reported for 2, the positive control. A credit of 2 settles it.

**Limitation kept**: `return_announcement_id` is not a replacement field, so a correction cannot fulfil an announcement.

## R2. F08 — refund before the return arrives

**Route**: return announcement (`announce_customer_return`, with `announced_at` stated so the clock is the story's), credit note through `document_create` with lines billed to the order line, `credit_note_post`, reviewed `customer_refund_post`, later returns against the announcement.

**Expected**: the credit is settled; the announcement is open with 2 outstanding and nothing is reported before `expected_by`; after it, `announced_return_not_arrived` is reported; one unit back makes `credited_not_returned` report 1; the second fulfils the announcement and clears both.

**Decision (owner)**: a credit through the invoice (`sales_credit_record`) references the invoice line, which `credited_not_returned` ignores by design of its direct-reference filter (`services/exceptions.py` near 2178). It stays as it is and becomes a limitation, because a price credit on the invoice would otherwise read as a quantity credit.

## R3. H09 — receipt without purchase order

**Findings**:
1. `record_movement` accepts `reason`, but `_append_movement` keeps it only for `adjustment`, as an `inventory_adjusted` change record keyed by `movement_id` (`services/core.py` near 5191). A receipt's reason survives only in the delivery review's input; `movement_explanation` says `unexplained`, and `unexplained_movement` reports it.
2. `_movement_exceptions` treats any `shipment_package_id` as explained. `shipment_receive` with `supplier_delivery` needs no commitment (`services/shipments.py` near 268), so a misdelivery recorded that way is never reported.

**Decision**: a stated, non-blank reason on a receipt without a commitment is kept the way an adjustment's is: a change record `movement_reason_stated` with the reason as input and the movement as output. The reason belongs to the decision that recorded the movement, so no movement or document field is added (DR-003).
- `movement_explanation` reads it as `explicit_reason`, like an adjustment.
- `_movement_exceptions` excludes movements with such a record.
- A package no longer explains a *receipt* without a commitment; shipments always have a commitment (customer delivery requires one), and returns keep today's rule to stay in scope.
- Only receipts: goods leaving or coming back without an order stay reported whatever reason is typed, because billing and crediting follow from the order (review round).
- A correction of a receipt keeps the original's stated reason unless it states another.

**Alternatives rejected**: a `reason` column on `movement` (a second home for what the decision already holds); the review input (not every recording path is reviewed).

## R4. P02 — events out of order

**Findings**: a Shopify refund before its order fails with `shop_refund_order_missing` and is retried by the worker's backoff (`services/shop_refunds.py` near 85; retry in `process_pending_import_jobs`), which the story drives with the scenario clock. A payment before its order is recorded unallocated with a named reason (`resolve_references`). Once the order is invoiced, `payment_candidates` names the stated reference only when it matches *several* invoices (`len(ambiguous) > 1`); a unique match gives no reason, so a short payment gets no candidate at all.

**Decision**: a stated reference that resolves to exactly one open invoice adds the reason "stated reference names this invoice". Allocation stays a person's decision (`finance.settlement.apply`, `allocate_credit`).

## R5. P05 — incomplete payload

**Findings** (`services/core.py` Shopify order interpretation, near 12470):
1. `price = decimal(raw_line.get("price", 0))`: a missing price is recorded as a stated 0; `"price": null` raises a non-Reality `InvalidOperation` from `decimal`.
2. `quantity = positive(raw_line["quantity"])`: a missing quantity raises `KeyError`.
3. Both escape `process_pending_import_jobs`, which handles only `RealityError`, so the job and its batch stop outside the reported path.

**Decision (owner)**:
- A line without a stated price is kept with no price: `document_line.unit_price` becomes nullable, and null states "the source gave none". Its promise is created as for any line; line and promise amounts are 0 because nothing can be billed from a price nobody stated (they are derived, not stated, today as well).
- A new exception class `order_line_price_missing` reports such a line while it has no stated price. Shop evidence cannot be corrected in place (`correct_manual_document_lines` refuses external evidence); a later shop version that states the price is a change of what the order states and is held for review as `price_changed` under spec 296, whose comparison must then read a missing price as "none" rather than fail.
- A line with a missing or null quantity refuses the order with the coded failure `source_line_quantity_missing` (a non-positive one keeps `master_data_field_not_positive`), recorded as the source's failed outcome and reported by `source_interpretation_failure`; the batch continues.
- Every reader of `DocumentLine.unit_price` (28 references in 12 files) handles null: comparisons skip it, serialisers emit null, displays say no price was stated, and billing offers the position without a price. The file `sales_order` import keeps a row without a price the same way.

**Alternatives rejected**: keeping 0 with a flag (a typed field would still state a price nobody stated); holding the whole order (the journey asks for acceptance).

## R6. P08 — open orders at go-live

**Route**: the file `sales_order` import (`services/file_interpreters.py` near 418) records the legacy row as its source record, the order evidence with the original quantity of 10 and a promise of 10. A reviewed `commitment_revise` then states the open 6, citing the same source record, with the note that 4 were delivered before go-live; the legacy payload keeps the delivered 4 losslessly.

**Expected**: open quantity 6; reserve, ship and invoice 6; no `shipped_not_billed` or overdue finding for the 4, with the open rest reported as unbilled after shipment as the positive control; the promise and its revision trace to the legacy source record.

**Limitation kept**: the delivered-before-go-live quantity is not a typed value.

**Risk**: the `sales_order` interpreter commits part-way (near 463, 531). The story uses one valid row and does not depend on rollback; the commit is recorded as a follow-up.

## R7. B09 — not provable

`SupplyAssignment` is read only by `supply_assignments.py` and its actions; receipts, reservations, readiness and findings never consume it. After a receipt of 4 against assignments of 3 + 3 + 3, each customer's `protecting_supply` stays 3. "Which promises remain uncovered" is answered only by reservations a person makes. **Decision (owner)**: B09 stays partial; the finding is added to spec 305.

## R8. Migration order

Spec 297 (PR #267) adds `0103_payment_returns`. The nullable price migration is numbered at implementation after rebasing onto `main`, so there is one Alembic head.

## R9. Review round (2026-09-30)

- A stated reason explains receipts only (FR-003); shipments and returns without an order stay reported.
- An explicit null price is accepted only where it is carried over from a source line (invoice or credit from an order or invoice line). A person entering a line through a form, the web or chat is refused with `manual_line_unit_price_missing`; 0 states a free line.
- Assigning an item to an unknown line without a price promises an amount of 0 instead of failing.
- `order_line_price_missing` clears when an invoice bills the line, stating the amount, or the line's promise is cancelled; a later shop version stating the price is held for review under spec 296 and does not write the price.
- The file import reads a stated 0 as a free line, not a missing price; a blank or whitespace quantity or price in a shop line counts as missing.
- A correction of a receipt with a stated reason keeps the reason on its replacement.
- Follow-ups: a later shop version that omits `quantity` is read as 0 by the spec 296 comparison (`shop_order_changes.stated_lines`), which reduces the promise; stated reasons are read with one query per call and filtered in Python, fine for single-record callers.

