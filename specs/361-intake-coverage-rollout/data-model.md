# Data model: Intake decision coverage, demo and safe rollout

## Business entities

WriterCoverageRow: canonical writer, caller families, owning spec, enforcement, test and explicit exception. LegacyIntakeState: retained source/job history without fabricated approval. DemoAdmissionContext: production proposal/apply with the same source controls; fixed setup context remains narrowly distinct.

## Persistence decision and proof

No additional tables beyond package 360's mandate. Pending jobs are transitioned via idempotent tenant-scoped application maintenance, not source mutation or fabricated decisions. Existing setup completion markers and source controls remain authoritative. Deploy additive mandate migration before new clients; reverse runtime automatic review only, not the admission boundary or retained approvals.

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
