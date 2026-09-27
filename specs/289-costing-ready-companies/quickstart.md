# Quickstart: Every business company knows its own business partner

## Setup

Run an isolated stack (the recipe is in `specs/282-cost-review-draft/quickstart.md`) with an
owner account in German (`?lang=de`).

## Checks

1. **SC-001:** create a business company "Lampenhaus Berg GmbH" through the company setup.
   Master data lists it as a business partner with the role company. Record opening stock with
   its value and open the item's cost review draft: it names the company as the owner and does
   not ask for a company partner.
2. **SC-002:** in a company created before this change, with no company partner, open the draft.
   It offers "Record my company as a business partner" with the company name. Propose it, then
   check that the draft names the waiting proposal. Confirm it in Decisions; the next draft
   uses the partner.
3. **FR-006:** record a company partner in master data while a second proposal waits. Confirming
   the waiting one is refused with "A company business partner already exists."
4. **FR-003:** create an empty sandbox and connect Demo Data; it connects as before.

## Evidence

| Check | Result | Date |
|---|---|---|
| Checks 1–4 (T904) | — | — |
