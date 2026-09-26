# Quickstart: Drafted cost reviews

Acceptance walk-through for a reviewer. Record results below once verified.

## Setup

An isolated stack as in spec 279 (`specs/279-missing-basis-guidance/quickstart.md`, "Live
results"), a **business** company (not demo or practice, which refuse cost decisions), and
the owner signed in with `?lang=de`.

## Checks

1. **US3 opening cost:** record opening stock of 40 pcs with the total value "480.00 EUR per
   Inventurliste 31.12.2025". The item's cost panel shows "Kostenprüfung des Artikels
   vorbereiten" as the open step.
2. **US2 inventory draft:** choose the step. The dialog shows:
   - owner: your company;
   - FIFO preselected;
   - EUR, pcs;
   - one opening of 480.00 EUR.

   No ID is visible outside System details. Submit. The panel now shows "Ein Inhaber
   bestätigt den Vorschlag".
3. **Owner:** follow "In Entscheidungen prüfen" and confirm. The panel shows an acquisition
   value of 480.00 EUR.
4. **US1 contribution draft:** record a sales order, shipment and invoice for 2 pcs. Open the
   invoice line and choose "Deckungsbeitragsprüfung vorbereiten". The dialog shows revenue,
   goods cost and DB1. Submit and confirm. DB1 appears.
5. **US4 chat:** for another item, write "Bereite die Kostenprüfung für <Artikel> vor". The
   agent asks at most for the valuation method and proposes.

## Evidence

| Check | Result | Date |
|---|---|---|
| Checks 1–5 (T905) | — | — |
