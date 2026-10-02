# Research: Serving Backorders on Receipt

## What exists

- `SupplyAssignment` states that supplier supply is intended for a customer promise or for stock. It is append-only and reversed by counter-rows.
- `_effective_rows` ignores reversed rows and, since #205, rows whose supplier or customer promise is cancelled. A cancelled customer order therefore already ends its assignment; R02 and G13 lack only a story.
- `supply_coverage` reports per purchase `received`, `open` and `customer_assigned`, and per customer `protecting_supply` as the full assigned total. B09's pinned test shows 3 + 3 + 3 after a receipt of 4.
- `core.reserve` reserves what is available at a location (less reservations and blocks), refuses held promises and accepts a named location since spec 303.
- `outgoing_commitment_at_risk` already treats a reserved promise as covered. It does not read `protecting_supply`, so the split does not change the finding.

## Decisions

- **No new record.** The serving order, the split and available-to-promise are read-time observations. What a person decides becomes ordinary reservations under one confirmed proposal (Constitution VIII).
- **Serving order** (Clarifications): first the assignments of the named purchase, in creation order, then due date, then promise creation. Without a named purchase, assigned promises have no precedence. A purchase is named when the step is opened from its receipt.
- **Scope of waiting promises**: open customer deliveries of the item held at the location, plus the promises assigned to the named purchase wherever they are held (spec 303 lets a promise reserve at another stock location).
- **Tracked items**: refused. A lot or serial reservation names an identity the step would have to choose, and choosing lots is an allocation policy Reality does not have (spec 304 non-goal).
- **Stale review**: re-validated on confirmation; any line that cannot be reserved in full refuses the whole step, so a partial serving never happens silently.
- **Available-to-promise netting**: waiting need that supply still to come covers is not taken from free stock, because that supply is intended for it. A cancelled promise is gone from both sides.
