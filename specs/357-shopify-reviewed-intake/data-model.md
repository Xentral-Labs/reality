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
