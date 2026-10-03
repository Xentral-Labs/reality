# Data model: Decision-gated interpretation and admission

## Business entities

PreparedIntake: versioned non-authoritative meaning, immutable source/artifact references, opaque resolved targets, current-state review basis and planned effects. ChangeProposal: exact unit with pending/executed/rejected lifecycle, review and receipt. ImportJob/InterpretationOutcome: retained source-processing history with prepared/review-required/applied classifications. ApprovedEffectScope: ephemeral internal transaction capability, never persisted as business authority.

## Persistence decision and proof

No new business table is required for this foundation. ImportJob.input carries proposal identity; existing status/classification strings distinguish prepared/awaiting decision from applied, and InterpretationRecordReference can reference the proposal using its existing opaque reference shape. ChangeProposal.input/output retain the plan/review and receipt. Add explicit typed validation in domain code. Historical outcome rows remain immutable. Scope guards must not turn source-record/audit writes into business-effect admission.

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

## Immutable outcome numbering

ImportJob.attempts is a monotonic count of newly retained terminal phase outcomes,
not the number of times a client polled. Under the ImportJob row lock allocate
`attempt = attempts + 1` for each new preparation result, explicit rejection,
stale confirmation refusal or successful application. Append an immutable
InterpretationOutcome with that attempt and phase-specific reason/classification;
never overwrite a prepared outcome with an applied outcome. A prepared outcome
may link the proposal, but only applied outcomes link accepted business effects.
Replay/polling returns retained state and allocates no attempt. A phase result is
identified by proposal/review revision plus phase so duplicated requests do not
append it again. Known application failure is recorded only after the effect
transaction has rolled back.

Backoff counts consecutive transient failures for the relevant phase, not the
monotonic outcome sequence; rejected/stale/awaiting-decision results do not enter
automatic failure retry. Test prepare → approve, prepare → reject,
prepare → stale → explicit renewed review → approve, and duplicated phase requests
against the existing unique `(tenant, import_job, attempt)` constraint.

## Integration refinement: company calendar

The reviewed plan retains the company's current IANA zone and its opaque source
statement identity (or the explicit UTC/default absence). Source instants become
business days through the canonical company-calendar service from spec 349. Apply
checks this retained calendar under the shared Tenant lock before canonical effects,
so a timezone change cannot silently move a reviewed order or payment to another
business day. This is review JSON, not a new authority table or derived total.
