# Data model: Reviewed file, master-data and stock imports

## Business entities

FileIntakeManifest: artifact/source identity, parser version, mapped profile, complete row membership and excluded issues. MasterPackage: at most 500 reviewed rows. FileOrderPlan: all rows belonging to one order. StockStatementPlan and StockCorrectionPlan: different accepted meanings and effects.

## Persistence decision and proof

Reuse SourceArtifact, SourceRecord, ChangeProposal and existing business tables. New package/file manifest schemas live in proposal JSON, not business staging tables. Raw file SourceRecord uses artifact identity/hash and received metadata, with bytes in SourceArtifact; normalized proposed rows are separately identified as interpretation. No new table is required. Any master-data update continues its existing expected revision contract.

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

Migration 0140 changes only Document.gross_amount nullability. An external order
may state its quantities and unit prices without stating a total. This scenario
requires null to remain distinguishable from a received zero in review, accepted
evidence, lists and the inspector (FR-008a). Existing document amounts are not
rewritten. The downgrade checks for null values and refuses rather than inserting
synthetic amounts. Invoices and payment writers continue to require stated money.

ArtifactSelection is retained proposal JSON: original source/artifact IDs, mapped
target, exact column mapping and original row count. Each child freezes its
original row numbers and source reference. Validation requires their exact union
to cover every original row once. Complete orders are indivisible. No new business
table, fulfilment status or derived commercial amount is introduced.
Historical source/effect/outcome rows are not rewritten. Any new nullable authority
link must preserve unknown historical attribution. Production migration and rollback
tests are required before rollout; migration is never run at worker startup.
