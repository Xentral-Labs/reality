# Data model: Reviewed Shopify orders, changes and refunds

## Business entities

ShopOrderPlan: one source version, resolved parties/location, evidence lines and proposed commitments. ShopChangePlan: current order review basis plus supported revisions/cancellations. ShopRefundPlan: independent refund source, evidence lines and supported operational announcements.

## Persistence decision and proof

Reuse SourceRecord/SourceStream, Document/DocumentLine, Commitment, refund evidence and existing proposal/outcome tables. This package requires no new tables. SourceStream remains the newest accepted source delivery pointer under its existing ingestion contract; it is not a declaration that the business interpretation has been approved. Pending effects exist only in proposal JSON.

## State and identity rules

- Raw source identities and hashes are immutable and tenant-scoped.
- A prepared plan is proposal input, not an accepted Document or operational row.
- Pending proposals can be rejected or explicitly re-reviewed; confirmation never
  changes their intent or auto-renews an offered review.
- Approved database-only execution has no externally visible partial accepted
  state: effects, decision attribution and receipt commit together.
- Applied/rejected outcomes are replayed from retained receipts; uncertain legacy
  execution is reconciled, not blindly rerun.
- Package membership is immutable after review. Independent units can have
  different outcomes; derived aggregate progress is not business authority.
- Opaque IDs identify records. Human numbers, SKU and source labels are values or
  external references, never internal identity.

## Migration and compatibility

No new schema in this package; see data-model.md for reused storage and compatibility.
Historical source/effect/outcome rows are not rewritten. Any new nullable authority
link must preserve unknown historical attribution. Production migration and rollback
tests are required before rollout; migration is never run at worker startup.

## Received line amounts that the shop does not state

Implementation review found that the legacy adapter computes a line total from
quantity and unit price even when the source supplies no total. A received value
cannot be reconstructed as authority (Constitution VIII). Existing
`DocumentLine.gross_amount` and physical `Commitment.amount` therefore become
nullable; null represents a source that stated no amount, just as
`DocumentLine.unit_price` already does. This adds no table or new business field.
Manual entry still requires an explicit amount. Only the source-evidence canonical
service can carry the absence under the approved intake scope.

The additive migration changes nullability without rewriting historical values.
Rollback refuses while null-valued source evidence remains; it must not invent zero
or a computed amount to satisfy the older schema. Credit/billing reads must expose
unknown value and must not treat it as a known zero. Tests cover a price present
without a total, complete absence, stated zero, stated amounts that disagree with
quantity times price, manual refusal, credit safety and migration round-trip.

## Refund statements with several transactions

A refund payload may name several successful refund transactions without stating
an aggregate monetary total. Prepared evidence records each stated transaction's
amount separately in its own sales-refund Document within the same atomic source
unit; it does not store a computed sum as received authority. Refund goods lines
belong to the first transaction document once, so cumulative cancellation readers
never duplicate goods quantities. Review shows the exact transaction membership
and all proposed reductions/return announcements. A refund without a successful
stated monetary transaction remains pending rather than inventing a zero total.
