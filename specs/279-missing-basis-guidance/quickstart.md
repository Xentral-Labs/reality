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

## Live results (2026-09-26, isolated stack `reality279`)

### T908 German sweep — PASS

`missing-basis-sweep-live.mjs` against a demo company found no raw code in four invoices'
contribution panels, the Warehouse cost panel, the Exceptions list and detail, or the
Delivery blockers table and guidance. The first runs failed on two real gaps, both fixed:

- eight contribution gaps were missing from the catalog (`ambiguous_fulfilment`,
  `ambiguous_billing`, `customer_scope_mismatch`, `item_scope_mismatch`,
  `revised_fulfilment_unsupported`, `unsupported_fulfilment`,
  `commercial_goods_cost_unresolved`, `commercial_inventory_cost_unknown`). A test now reads
  the gap codes from the service sources.
- the Delivery blockers report carries one `blocker_type` per row, not `blocker_codes`.

The report's `detail` column is still English text from the service ("stock not fully
reserved"); it is data, not a code, and is left for the impact-sentence follow-up.

### T909 walk-through — SC-003 not met

1. **Demo company:** the guidance correctly says cost decisions cannot be confirmed there.
   Demo and practice companies refuse `execute_cost_change` and admit no invited members.
   The first wording, "This company is read-only", was wrong and was changed.
2. **Business company** (item with 40 pcs opening stock): the panel shows "Nobody has
   confirmed the acquisition cost for this item yet" and the step "Prepare the item's cost
   review". "Mit Reality vorbereiten" fills the chat. The person sends it, and the agent
   answers in German.
3. **The agent cannot prepare the review.** It asks for `owner_party_id`, manifest IDs and
   seven other technical parameters. After a plain-language answer (own company, FIFO, EUR,
   pcs, 40 pcs at 12 EUR, no receipts) it still asks for the company party's ID and the
   opening movement's ID, and offers to create the opening stock again. No proposal is
   created, so the owner step is never reached.
4. **An opening stock recorded through the form has no evidence source record.** Even a
   well-prepared request could not name the opening cost evidence that an inventory review
   requires.

**Follow-up (separate spec):** a shared read that drafts a cost review from held records,
covering the company party, the item's movements and the receipt manifests, so neither the
person nor the agent has to supply IDs. Also a way to record evidence-backed opening cost.
Until then the chat handoff is a correct first step, but not a finished path for a clerk.
