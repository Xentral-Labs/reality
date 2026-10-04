# Data model: Reviewed invoice, payment and allocation intake

## Business entities

FinancialIntakePlan: received statement meaning plus explicit posting operations. AllocationIntent: exact target entries/invoice, amount and current residual/account basis. FinancialReceipt: retained document/posting/allocation identities caused by the decision.

## Persistence decision and proof

No new financial tables or authority sources. Reuse documents, ledger/posting groups, settlement allocations, source/outcome/proposal references and existing revision/lock state. Financial plan and review are non-authoritative proposal JSON. Calculated availability is a review observation; it never becomes a stored source amount.

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
