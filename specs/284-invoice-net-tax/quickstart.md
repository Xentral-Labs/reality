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
| Checks 1–4 (T904) | — | — |
