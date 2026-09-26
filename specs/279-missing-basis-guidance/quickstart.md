# Quickstart: Guidance for missing basis

Acceptance walk-through for a reviewer. Results are recorded below once implementation
is verified.

## Setup

1. Start the local stack (`make dev-up`) with scheduler and worker, and create a demo
   company.
2. Sign in once as an owner and once as a member (second browser profile). Switch the
   language to German.

## Checks

1. **US1:** Open Lager > Bestand and expand an item with no cost review. Every sentence
   is German, no code such as `uninitialized` or `cost_change_propose` appears, and no
   sentence repeats.
2. **US2:** Open Finanzen > Offene Posten and expand a sales invoice line with DB1
   "Nicht nachgewiesen". The first open step is the item's cost confirmation, not the
   contribution review.
3. **US3:**
   - As the member, choose "Mit Reality vorbereiten". Chat opens with a prepared,
     unsent request.
   - Send it and confirm the preview. The step moves to "Owner confirms", and the member
     sees who must act.
   - As the owner, follow the step to Decisions and confirm. The panel shows the value.
4. **US4:** Stop the worker and trigger a new event. Open Abweichungen: the freshness
   message says background processing is unavailable and links to Home.
5. **US5:**
   - Open an exception "Anschaffungskosten fehlen": the title and guidance are German,
     and the first step matches check 2.
   - In Berichte > Preisfindung, pick a partner and an item.

## Evidence

| Check | Result | Date |
|---|---|---|
| Statement count, current inventory cost query, item not reviewed (T904) | main 4; branch 12 with 1 receipt, 28 with 5 (8 + 4 per receipt, capped by the 20-receipt review bound, so at most about 90) | 2026-09-26 |
| Statement count, current contribution cost query, item not reviewed (T904) | main 4; branch 50 (current preview plus the item's receipt check) | 2026-09-26 |
| Checks 1–5 | — | — |

### Measured risk

The cost panel loads only for an expanded row, but an expanded document shows one
contribution panel per invoice line (`DocumentContributionExplanations`). An unreviewed
30-line invoice therefore costs about 1,500 statements instead of 120. A batch variant of the
receipt check, or deriving steps only for the first line of an item, is the follow-up if that
shows up in practice.
