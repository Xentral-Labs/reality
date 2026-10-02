# Research: Stock Count Sessions

## What exists

- **Adjustments.** `record_movement("adjustment", ...)` records a reasoned gain (`to_location_id`) or loss (`from_location_id`). Since spec 304 it refuses to take blocked stock (`movement_takes_blocked_stock`).
- **Blocks.** A block is resolved by `scrap_stock_block` (spec 316: one append-only resolution plus one adjustment linked to it).
- **Book quantity.** `stock_by_identity` sums movements per item, location and lot. Every movement has `occurred_at`, so the book at a time is the same sum filtered to `occurred_at <= at`.
- **Reservations.** `reservation_exceeds_stock` already names reservations that exceed stock after a loss, per item. By design, it names no promise to postpone.

## Decisions

- **No freeze.** A line's counting time fixes the book it is compared with. Movements after it are ordinary and keep happening (J03). Counting and posting happen in one confirmation, so the posted adjustment states the difference as it was posted.
- **Statement as source.** The count, with its lines, is kept as one version of `internal_stock_count` / `stock_count` / `<count id>` (spec 320 pattern). The count row names it.
- **Loss order.** Free stock first, then blocks, oldest first, through the shared scrap. The scrap reason cites the count. A loss beyond physical stock now is refused (`stock_count_loss_exceeds_stock`).
- **Lots.** A lot-tracked item needs its lot on each line, and the book is per lot. Pallets and serial units are out of scope; counting a serial-tracked item is refused.
- **Counting time.** It defaults to the review time. A stated time may not lie in the future.
- **Reservations named, not released.** The review lists them; the existing class names them afterwards.
