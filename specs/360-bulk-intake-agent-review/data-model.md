# Data model: Bulk intake settlement and delegated agent review

## Business entities

IntakeBatch: fixed child identities/digests, confirmation and durable progress/results. IntakeReviewMandate: current scoped authority linked to the granting decision and named token. AgentReviewEvidence: exact source/plan digest, deterministic results, reviewer verdict and mandate revision. ChildDecision: own effects, attribution and receipt.

## Persistence decision and proof

A new tenant-scoped IntakeReviewMandate is justified by repeated authority checks: opaque id, grant_decision_id, agent_token_id, scope/limits JSON, expires_at, revoked_at and revision. Composite FKs enforce same-tenant proposal/token links; grantor is derived from the grant decision rather than duplicated. Reviewer evidence and mandate version live in the exact child proposal review/receipt. Batch manifest, continuation identity and progress use existing proposal/run records. Review/effect amounts stay strings validated as Decimal; no authority is inferred from free text. Add additive migration and keep unknown old attribution unchanged.

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

Additive mandate migration in `packages/reality-core/migrations/versions/` plus metadata import in `db/core.py`; exact revision is allocated from Alembic head at implementation, never guessed.
Historical source/effect/outcome rows are not rewritten. Any new nullable authority
link must preserve unknown historical attribution. Production migration and rollback
tests are required before rollout; migration is never run at worker startup.

## Mandate scope and limits

Mandate `scope` is a strict versioned object, not free text: exact source-system
and capability IDs, allowed profile codes, enumerated effect kinds, maximum rows
per unit, maximum units per UTC day, and an optional amount rule containing one
currency, maximum source-stated amount per unit and maximum source-stated amount
per UTC day. All limits are finite and positive. Owner must choose explicit
amount limits for any financial effect; defaults grant no financial authority.
Membership/role changes, unrelated sources, payout execution and unknown effect
kinds are not in the initial mandate vocabulary.

Amount exposure is the received statement's amount (for Shopify, source-stated
order total; for payments/invoices, source-stated amount), never a recomputed sum
or converted currency. Missing required amount, currency mismatch, unprovided
conversion or a non-finite/negative limit blocks delegated acceptance. Master-item
packages use row/unit quotas without inventing monetary exposure. Source/profile
IDs and token IDs must resolve within the same tenant and remain active.

Daily quota covers units accepted under the mandate version across all concurrent
batches, not just one run. Lock the mandate row while checking retained completed
child receipts and deciding the next unit. Count accepted source-stated exposures
from those authoritative decision receipts; do not store a second commercial total.
Retries of the same executed child consume no extra quota. Quota exhaustion yields
human-review-required, never implicit next-day approval. New review is required
if the operator later selects such pending work again.

Review submission includes mandate ID and immutable revision, both exact source
and prepared-plan digests, the fixed list of source/line references reviewed,
deterministic check codes/results and a structured approve/reject/uncertain verdict.
The server checks binding and required coverage, not whether a model cognitively
understood the source; token attribution is not proof of independent human review.

### Implemented mandate storage and raw review coverage

Revision 0141 follows 0140. Mandate JSON is a strict closed finite scope; no token
permission list, source field, model output or actor argument creates authority.
The token's issuer must equal the actual owner who granted the mandate, and remain
an active owner with an active account. Composite grant/token FKs preserve tenant
binding. Revocation advances revision; prior receipts remain unchanged. Downgrade
refuses when delegation history exists.

Coverage references bind complete 64 KiB original payload/artifact byte ranges,
SHA-256 hashes and relevant original row/line positions. They are declaration and
binding evidence, never a cognitive-understanding claim. Source pages are read
adapters outside workers. Uncertain verdicts remain pending with bounded retained
evidence; accepted/rejected receipts retain exact agent evidence and actual token.

### Delegated batch authority

`AgentBatchReviewEvidence` binds one exact manifest identity/revision/digest to
one same-mandate/revision verdict per child in manifest order. Evidence is closed,
limited to 500 children and at most 2 MiB of canonical UTF-8 JSON. It is retained
inside the existing parent decision authorization; no additional table or queue
payload is introduced. The actual token settles the parent, with no invented
human approval. The retained owner identity names the grant authority and who may
stop further processing, not a claim that they reviewed this source selection.

Every worker child independently rechecks current delegation, exact evidence,
source/capability and prepared state, global UTC-day unit/stated-amount limits and
current token tool restrictions. Each accepted receipt binds its original external
verdict to the actual token and mandate revision. Quota aggregation is a read-only
derivation from receipts; it is not a stored commercial authority.
