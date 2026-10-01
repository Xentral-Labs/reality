# Data Model: Multichannel Oversell, Deadlines and Peak Intake

No schema change: no migration, table or column.

## Derived: `item_oversold` (finding)

| Value | Meaning |
|---|---|
| `demand_quantity` | open quantity of open customer-delivery promises for the item, expressed in the item's unit by its stated factor |
| `on_hand_quantity` | item-wide stock from movements |
| `incoming_quantity` | open quantity of open supplier-delivery promises for the item |
| `shortfall_quantity` | demand − on hand − incoming, reported while > 0 |
| `channels` | per stated `sales_channel` (empty shown as "unstated"): quantity and order document ids |
| `not_comparable` | promises in a unit the item states no relation to, named and left out of the sums |

- Record: `item`.
- Trace: the promise and document ids.

## Derived: `outgoing_commitment_due_soon` (finding)

| Value | Meaning |
|---|---|
| `remaining_quantity` | promised in force − shipped |
| `reserved_quantity` | active reservations |
| `due_at` | the date in force |
| `hours_left` | time from the read instant to the date |
| `originally_due_at`, `times_revised` | when the date was revised |

- Record: `commitment`.
- Causes: `insufficient_reservation` and `promise_was_revised`, as for the overdue class.

## Benchmark output: `benchmarks/peak_intake`

The JSON report holds:
- the orders and processes;
- the intake seconds, orders per second and failures;
- the reservation seconds;
- the invariant results: over-reserved items, orders interpreted twice, and whether the shortfall check matched;
- the database and machine notes.

It is a developer artifact, not a stored record.
