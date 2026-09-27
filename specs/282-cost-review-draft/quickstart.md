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
| Check 1–3, inventory: opening with value → draft → proposal → owner confirms → 480,00 € (`cost-review-draft-live.mjs`) | PASS | 2026-09-26 |
| Renewal after a goods issue of 2 pcs → 456,00 € (`RENEW=1`) | PASS | 2026-09-26 |
| Check 4, contribution DB1 | BLOCKED: the web invoice form states only gross, so `received_net_missing` | 2026-09-26 |
| Check 5, chat: plain request → one question (method) → proposal linked in the panel | PASS after FR-012 | 2026-09-26 |

## Live findings (2026-09-26, isolated stack)

- **Company party missing.** A new business company has no business partner with role
  `company`. The draft names it, and the clerk records it in master data.
- **Web invoices without a net amount.** Sales invoices recorded through the web form state
  only a gross amount. The contribution preview reports `received_net_missing`, so DB1
  cannot be proven for them. This is a follow-up spec (invoice form states net and tax as
  received).
- **Chat.** Before FR-012 the agent asked for IDs, mistyped copied identifiers and lost them
  between turns. With `cost_review_propose` and item names it drafts, asks only for the
  method and proposes. It still shows opaque IDs in its answer text; that is a chat output
  follow-up, not a draft issue.
- **Demo seed.** The demo seed fixes its opening cost at 6 per unit in code. No source states
  it, so the draft leaves those openings open (SC-003).
