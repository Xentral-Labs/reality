# Research: Automatic Credit Hold

Read on 2026-09-30 against `origin/main` at ec6997d5. Paths are under `packages/reality-core/src/reality/`.

## R1. Today

- `_credit_limit_exceeded_exceptions` (`services/exceptions.py`) reads parties with a positive `credit_limit`. It sums the open amount of their `sales_invoice` open items in `default_currency`, and reports the excess with every open invoice id. Order value, credits, payables and overdue items play no part.
- Commitment holds exist with the reason `credit_check` (`HOLD_REASONS`). An active hold blocks readiness (`commitment_hold` blocker) and shipment. `hold_commitment` returns *any* active hold instead of adding one, and `release_commitment_hold` lifts every hold on a promise. The release event records the decision (spec 263 attribution) but no reason.
- Any active member may release (`tenant_policy`); owner-only confirmation exists for finance commands through `confirming_principal` and `require_owner`.
- Sales-order promises are created in `create_manual_order` (the reviewed `order_create`, Web, CLI and chat), the Shopify interpretation (`core.py`, near the `customer_delivery` Commitment), the file `sales_order` import (`file_interpreters.py`), and later by the spec 296 item assignment (`order_line_items.py`). Demo seeding sets no credit limits.

## R2. Exposure (FR-001)

**Decision**: one read-time function `credit_exposure(session, tenant, party_id, *, as_of=None)` in a new `services/credit_exposure.py`. It covers the party's `default_currency` only.

| Part | Source | Sign |
|---|---|---|
| Open invoices | `financial_open_items` rows of type `sales_invoice` and `opening_customer_debt` with open > 0 | + |
| Open orders not yet invoiced | Each line of the party's sales orders. The base is the line's non-cancelled promise quantity (the line quantity when it has no promise), less what is already invoiced (`_order_line_billing`), times the stated unit price | + |
| Available credits | `available_credit_items(side="customer")` for the party: credit notes and unallocated payments | − |
| Payables (named only) | Open `supplier_invoice` items of the same party | 0 |

- Overdue invoices are the open-invoice rows due before `as_of`; each is named with its number and open amount.
- A line without a stated price (spec 314) counts 0 and is named as unpriced.
- Documents in another currency are named as not counted.
- The result carries every part and the named rows, so a hold and the finding explain themselves.

**Alternatives rejected**:
- Commitment `amount` as the order value: it is quantity × price at creation, is not reduced by invoicing, and a revision does not always refresh it.
- Storing an exposure snapshot as an authority, which DR-002 forbids.

## R3. Hold at entry (FR-002, FR-003)

**Decision**: `hold_if_over_credit_limit(session, tenant, order_document, commitments, *, action_id)`, called once per new sales order after its promises exist:
- in `create_manual_order`;
- in the Shopify interpretation;
- in the file `sales_order` import.

It does nothing when the limit is 0 or the order adds no counted value. When the exposure including the order exceeds the limit, each promise of the order gets its own `credit_check` hold:
- `created_by="credit_limit"`;
- a note that summarises the facts;
- one `commitment.held` event per promise whose payload carries the exposure parts and the named rows — the record of what the decision was based on.

A credit hold is added even when another hold is active: readiness already lists every active hold, and a credit decision must not be released with an address hold. It is idempotent per promise.

The spec 296 item assignment holds its new promise when the order already has an unreleased credit hold, so an assigned line cannot slip past the decision.

**Alternatives rejected**:
- A readiness blocker computed live, which the owner declined (it holds nothing at entry and has no release to record).
- A hold on the party, which would block orders under the limit.

## R4. Release (FR-004)

**Decision**: a new reviewed delivery tool `credit_hold_release` with `{document_id, reason}` (the sales order):
- It releases the order's active `credit_check` holds only.
- The reason is mandatory and non-blank (`credit_hold_release_reason_missing`).
- Confirmation requires an owner, through the finance pattern (`confirming_principal` + `require_owner`; refused with `company_owner_access_required`).
- The `commitment.hold_released` event carries `reason_code: credit_check` and the reason. The decision trail links it to the person.

`commitment_hold_release` (any member) now leaves `credit_check` holds in place: its review names them, and it refuses with `credit_hold_owner_release_required` when only credit holds are active. A closure that ends the promise (cancellation, bulk close) still releases every hold, as today.

Surfaces:
- MCP `credit_hold_release_propose`.
- Web through the delivery-action endpoints, with a "Release credit hold" action on a held order for owners.
- CLI propose and confirm.
- Read tool `credit_exposure` (`party_id`) on MCP, Web and CLI, so chat and the party view can answer "why held".

## R5. Finding (FR-005)

`_credit_limit_exceeded_exceptions` calls `credit_exposure` and reports the excess over the limit. Its causal values gain the exposure parts and the overdue invoice ids, and its record links keep the open invoices. The count of open invoices stays. Tests that pinned "open invoices only" are updated on purpose.

## R6. Journeys

- C07: an order over the limit is held at entry and released by an owner with a reason. The refusals for a member and for a blank reason are asserted.
- C08: two overdue invoices are named separately from the invoice not yet due.
- R08: a customer who is also a supplier has an overdue receivable, an open credit note and a payable; a new order over the limit is held, and its facts name all of them, the payable not subtracted.

## R7. Review round (2026-09-30)

- Every generic release path (document release, web, CLI, the chat tool) keeps credit holds: `release_commitment_hold` keeps `credit_check` by default, and only the closures that end a promise (cancellation, revision to fulfilled) release them.
- The order value is the stated line amount prorated for the uninvoiced quantity, never quantity times unit price (Constitution VIII).
- A line without a promise (a service or charge) stops counting once every promise of its order is cancelled.
- A promise revised upwards runs the same credit check as a new order.
- The exposure is read for many customers at once: invoiced quantities, open items, credits and orders in a bounded number of reads, whatever the number of lines or customers; the credit-limit finding reads all limited customers in one pass and links the open orders too.
- Limitations kept: an invoice without links to its order lines counts next to the order; `as_of` moves the aging, not which postings count.
- The owner rule applies to holds the credit check placed (`created_by = credit_limit`). A `credit_check` hold a person places by hand stays theirs to release, as before; the full suite found five tests relying on that.

