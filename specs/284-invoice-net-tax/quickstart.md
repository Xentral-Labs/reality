# Quickstart: Invoices state net and tax

## Setup

The isolated stack from spec 282 (`specs/282-cost-review-draft/quickstart.md`) runs a local
integration of the 282 and 284 branches. Use a business company with an item whose cost is
confirmed (for example the 282 walk-through item) and the owner signed in with `?lang=de`.

## Checks

1. **US1:** create a sales order for 2 pcs and record the goods issue. Record the invoice
   through the form with gross 59.50, net 50.00 and tax 9.50. The review shows all three.
   Confirm.
2. **FR-004:** a second attempt with gross 60.00, net 50.00 and tax 9.50 is refused with
   "Net plus tax differs from the invoice gross."
3. **SC-001:** open the invoice line in Finance > Open items. The cost explanation offers
   "Deckungsbeitragsprüfung vorbereiten". Propose, have the owner confirm, and DB1 appears.
4. **FR-006:** an invoice with gross only is recorded as before.

## Evidence

| Check | Result | Date |
|---|---|---|
| Check 1, US1: order SO-284-muivoehy (2 pcs), goods issue, invoice through the form with gross 59.50, net 50.00, tax 9.50; the review shows "Netto €50.00 · Steuer €9.50"; confirmed, verified | PASS | 2026-09-26 |
| Check 2, FR-004: gross 60.00 with net 50.00 and tax 9.50 refused in the form with "Net plus tax differs from the invoice gross." | PASS | 2026-09-26 |
| Check 3, SC-001: the order's cost explanation moved from `received_net_missing` to the inventory renewal (432 €), then "Deckungsbeitragsprüfung vorbereiten" → proposed → owner confirmed in Decisions → DB1 €26.00 (net 50.00 − consumed cost 24.00) | PASS after the spec 242 fix below | 2026-09-26 |
| Check 4, FR-006: INV-282 (gross only) still reports `received_net_missing` | PASS | 2026-09-26 |

Stack: the isolated `reality279` stack running `local/stack-282-284` (spec 282 branch with this
branch merged), walk-through script kept outside the repository because it relies on the
unmerged spec 282 draft dialog.

## Live findings (2026-09-26)

- **Confirming a contribution failed for every web invoice (fixed).** The confirmed review's
  trace carried the invoice date as a date object, and storing the result as proposal output
  failed with a 500 for any invoice with a document date. Seeded invoices have none, so the
  tests never saw it. Fixed in `contribution_reviews.py` with a spec 242 regression test
  (`test_invoice_with_a_document_date_can_be_confirmed`).
- **Service refusals are shown in English.** The German form shows "Net plus tax differs from
  the invoice gross." as the server states it. This is the existing pattern for every service
  refusal (for example "Invoice quantity exceeds the remaining billable quantity."), not
  specific to this feature; localizing refusals is a separate follow-up.
- **After DB1 is confirmed, the guidance offers the contribution review again for DB2.** With
  selling costs unknown the headline says DB1 does not depend on them, and the open step is
  the review that would add them. Spec 279/282 guidance, recorded for review.
