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

No new schema in this package; see data-model.md for reused storage and compatibility.
Historical source/effect/outcome rows are not rewritten. Any new nullable authority
link must preserve unknown historical attribution. Production migration and rollback
tests are required before rollout; migration is never run at worker startup.
