# Interface Contract

FR-013: six existing party/item/location create/update tools accept one strict basic
record through Playground prepare_step. Shared update proposal normalization adds
expected_revision. Confirmation rechecks the snapshot before claiming execution;
the master call tree and bulk service both bind exact tool/input/action. Only the
selected family and event are permitted. Ordinary business write routes remain
denied. Receipts expose master record IDs, snapshots and action event IDs.

Reservation listing accepts an optional status filter applied before its existing
bounded limit. Reservation release is an explicitly reviewed Playground operation
using only the shared reservation_release tool. Its narrow authority binds the
reservation ID and action ID; only release_reservation and its reservation.released
event are allowed. State changes invalidate the saved preview before execution.

Document Inspector includes evidence_lines with opaque line ID, received quantity,
gross amount, unit and display label. Independent finance proposals reuse these IDs
and existing reviewed invoice/payment tools; no ordinary tenant write endpoint is
enabled for the sandbox.

Existing commitment-control endpoint retains filters/paging, adding location_id.
Writes use only existing owner-scoped Playground preparation,
revision confirmation and rejection. No new tool or permission. Selected shipment
and reservation previews become stale if remaining fulfillment changes.

Finance open-items accepts optional item_status=outstanding, selecting existing open
and partial states before pagination/count/totals. Existing exact status filters and
empty (all) behavior remain unchanged. Flow separates receivable/payable records.
