# Contract: B2B Operational Application Services

All mutations use the existing propose/confirm contract, authorization policy, tenant scope and
idempotent request identity. Names below describe semantic operations; exact transport paths remain
adapter concerns.

## Record invoice from an order

Input identifies the order/billable lines, stated invoice number/date/party/currency/total and each
stated invoice line. Preview returns exact retained values, billed and remaining quantities,
eligibility warnings and contribution readiness. Confirm revalidates the snapshot, records source,
document and lines, posts through existing finance services and schedules existing projections.

It rejects missing dates, empty required line sets, duplicate source-line identities, incompatible
items/parties/currencies, over-billing and stale previews. A source total/line disagreement is
reported but never silently balanced.

## Assign supplier supply

Input identifies supplier commitment, purpose, positive quantity and customer commitment when the
purpose is customer demand. Preview returns supplier quantity in force, received/open quantity,
existing effective assignments, proposed result and affected customer coverage. Confirm locks and
revalidates both sides and records the statement. Replay returns the existing assignment.

## Reverse supply assignment

Input identifies an effective assignment, positive quantity and stated reason/source. Preview shows
the effective quantity before and after reversal and any resulting customer shortage. Confirm writes
one append-only reversal. It never edits or deletes the original row.

## Resolve customer return

Input identifies an arrived return movement, quantity and one disposition:

- `restock`: destination sellable location;
- `quarantine_repair`: destination non-sellable location;
- `scrap_loss`: stated adjustment reason;
- `return_to_supplier`: supplier context and outbound destination.

Preview returns arrived, already resolved and unresolved quantities plus the physical movement that
will be recorded. Confirm calls the existing movement service with `resolves_movement_id`. Financial
credit is never implicit.

## Read models

- `supply_coverage`: customer and supplier views with exact reconciliations and Inspector targets.
- `return_resolution`: arrived/resolved/unresolved goods beside independent credit state.
- `movement_explanation`: shortest primary explanation, supporting evidence/source and correction
  state.
- `invoice_contribution`: existing contribution shape with stable unavailable reasons and freshness.

All reads return not found for foreign-company opaque IDs and expose no foreign metadata.
