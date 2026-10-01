# Research: Orders Served From Several Warehouses

## R1. Today

- **Reservation** (`services/core.py`, `_preview_reservation` and `reserve`):
  - Availability is judged only at `commitment.location_id`: stock at that location less what is actively reserved there.
  - The reservation is created there, and no caller can name another location.
  - A promise can already hold several active reservations (repeated calls, lots, split remainders). They are all at one location today.
  - `Reservation.location_id` is not null.
- **Readiness** (`services/fulfillment_readiness.py`): reserved quantity is summed over all locations, but physical stock is read at the promise's location only. The fulfilment queue projection (`services/projections.py`) does the same, so `shippable = min(open, reserved, physical at own location)`.
- **Shipping**:
  - `_append_movement` checks stock at the shipment's `from_location_id` and does not require it to equal the promise's location.
  - `_consume_reservations` consumes only reservations at the location the shipment leaves from (fix #202).
  - The packaged dispatch (`services/shipments.py`, `record_packaged_execution`) gates every customer movement on `fulfillment_readiness`, which looks at the own location only.
- **Packages**: `Shipment` and `ShipmentPackage` carry no location. One dispatch creates one shipment with one package, and its movements may leave from different locations.
- **Transfers**: `transfer` is a public movement type with both locations, recorded through `movement_create`. Nothing proposes one.
- **Locations**: `is_active` and `allows_stock`. There is no flag for which locations serve orders.
- **Exceptions**: none judges stock at another location. `reservation_exceeds_stock` compares the whole company. `outgoing_commitment_at_risk` names the unreserved rest without a location.
- **Journeys**:
  - A02 is partial: one order location, two lines proven.
  - B06 is partial: availability per location, but no transfer proposed and no reservation elsewhere.
  - D02 is missing.

## R2. Design (owner decisions, 2026-10-01)

- **Serving locations**: every active location that holds stock. No new field.
- **Reserve elsewhere**:
  - `reserve(..., location_id=None)` and its review take an optional location; empty means the promise's own location, as today.
  - The named location must be active and hold stock, else `reservation_location_not_stock`.
  - Availability is judged there, by the same rule as at home. The reservation records that location.
- **Readiness per location**:
  - Each reservation counts with the stock at its own location: `ready_quantity = Σ_L min(reserved at L, physical at L)`.
  - The readiness read and the fulfilment queue use this one rule.
  - The packaged dispatch and a reviewed shipment check, per movement, what is reserved and on hand at its `from_location_id`.
  - Consumption is unchanged, since it is already per location.
- **"Stock in another warehouse"** (`stock_in_another_location`):
  - It is derived for an open, unheld customer promise when the unreserved rest exceeds what its own location has available while other serving locations have some.
  - It names those locations with their available quantity, and per location the quantity that location could cover.
  - It offers "Reserve there" (`reservation_propose` with `location_id`) and "Prepare transfer" (`movement_create`, type `transfer`, to the promise's location), both reviewed.
- **D02**: two reservations at two locations ship as two packages (two dispatches), each from its own location, against one promise. It is proven by story.

## R3. Alternatives rejected

- **Automatic spreading of a reservation over locations**: the owner wants a person to name the second warehouse.
- **A "serves orders" flag**: no proven need yet (Constitution III).
- **Storing a transfer suggestion**: that would be a derivation stored as authority (DR-002).

## R4. Gates

- The new class goes through `CLASS_ORDER`, `DERIVATION_REGISTRY`, the catalogs tuple, the YAML entry, the test lists, `class_clock`, the reference catalog and its counts, and the resource catalog with its German label.
- Refusal codes need translations.
- The MCP schema of `reservation_propose` and the delivery-action pass-through gain `location_id`, with the command catalog parameter description.
- Every test pinning readiness or queue values for a promise without reservations elsewhere must stay green, because the rule is unchanged when everything is at home.
