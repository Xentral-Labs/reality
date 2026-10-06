# Decision-gated source interpretation

## Approved scope clarification (2026-10-04)

This rollout governs external sources, imports and agent-proposed business effects.
They require an exact retained proposal and an authorized confirmation before acceptance.
A direct action by an authenticated human is itself the decision and uses the existing
application authorization and audit trail; it does not require a second proposal or
confirmation cycle. Derived effects of one operation share its transaction and receipt.

The owner retained PRs #333–#346 and withdrew the later universal canonical-writer
rollout. Internal service calls and every manual UI/CLI operation are not additional
admission projects. Existing tenant, domain, Finance and Chat confirmation rules remain.
A static writer inventory is discovery material, not a mandate to guard every writer.
References below to governed writes mean external intake only; broader earlier planning
and universal-writer tasks are superseded by this clarification.

## Implementation status

Specs 356–361 define reviewed external intake across Shopify, supported file/master/
stock profiles, normalized invoice/payment statements and live Demo Data. Import
workers prepare exact proposals; they do not accept business evidence automatically.
Unsupported profiles preserve raw sources and report a review issue.

The shared preparation/review/confirmation services support one coherent unit,
fixed packages and manifests of up to 500 independent units. Web and CLI expose
exact selection, original evidence, retained progress, stopping and renewed review.
Named agents require explicit finite owner mandates; workers never call providers.
Without an authorized reviewer, new demo sources and their prepared proposals wait.

Source-unstated line amounts and order totals remain unknown. Stated zero and
inconsistent received values are preserved. Direct authenticated human operations
retain existing authorization and audit without another intake proposal cycle.
Historical missing attribution remains unknown. Required committed-head CI is the
completion gate; verification links and implementation history live in the specs.

## Acceptance transaction

Preparation retains a content-addressed plan in `ChangeProposal.input`; it creates
no accepted Document, Commitment or posting. The plan freezes source identity and
hash, job mapping, resolved opaque references, planned effects and relevant state.
Financial plans also bind the finance revision and resolved account identities.

Confirmation rechecks current authority and the exact digest. Locks follow Tenant,
finance, proposal, source identity/stream, job, and ordered reference rows. Canonical
no-commit services apply the frozen intent; they never rerun source interpretation
or rematch a payment. Effects, decision attribution, immutable outcome and receipt
commit together. Inner service savepoints remain legal; a premature transaction
commit refuses. Canonical entrypoints also verify the currently authorized
operation and frozen invocation arguments; an approved commitment cannot authorize
an unrelated master write or silently change the reviewed quantity. An executed proposal replays its retained receipt without effects
or another outcome.

Raw admission acquires the Tenant serialization row before source identity locks.
Taking that lock grants no approval. No staging business tables or operational
Document status fields were added, and historical attribution is not fabricated.

## Large-file preparation

`file_intake.package_item_csv` validates a separate raw input ceiling of 5000 rows
and 20 MiB. Whole-file structure and duplicate checks precede package emission.
Packages preserve row order and are bounded by both 500 rows and 2 MiB canonical
UTF-8 content. A single oversized row refuses instead of being split. This pure
preparation helper grants no business acceptance; database conflicts, semantic
issues and explicit exclusions belong to the reviewed master-data adapter.

The existing one-package item CSV path retains its 500-row / 2 MiB limits.

## Verification

Executable initial proofs are in `test_intake_admission.py`,
`test_file_intake_admission.py` and `test_financial_intake_admission.py`.
Full CI and the remaining rollout acceptance proofs are required before completion.

Shop changes and refunds freeze collection membership and relevant current order,
reservation, shipment, revision, hold, announcement and prior-refund state. A new
member or changed row invalidates review. Credit proposals freeze the current
exposure at the reviewed observation time; new exposure requires a fresh review.
The nullable amount migration never rewrites historical records and refuses an
unsafe rollback while source-unstated amounts remain.

The explicit bulk services retain up to 500 exact reviewed child IDs/digests. One
manifest confirmation queues database-only shared-worker continuations of at most
25 units; it grants no permission for future arrivals. Current original reviewer
membership/token and each child's stronger permission/state are checked again.
Known no-effect refusals and stops are retained separately from accepted children;
unknown infrastructure failure rolls back the entire provisional chunk. Paginated
status reads return child receipts without running work. The retained rollout adds finite AgentMandates and selection/recovery UI (spec 360),
plus the external-source runtime cutover (spec 361). Universal writer gating is
outside the approved scope.

## Explicit financial statement profiles

`customer_payment.v1`, `supplier_payment.v1` and `sales_invoice.v1` prepare exact
statement meaning before evidence/posting. Current owner authority is checked at
confirmation and each queued child. A matched payment freezes its selected
invoice settlement position; unrelated postings do not invalidate independent
siblings. Changed availability refuses the combined posting/allocation instead
of rematching or silently dropping the allocation. Account identities, dates,
company currency and inner document linkage remain exact. Outgoing statement
admission records bookkeeping only and never executes a bank transfer.

Canonical business defaults are now part of retained preparation, so a later
canonical default does not silently change approved meaning. Historical reviews
keep their original digests. Legacy/demo and bank-file adapters still require the
tracked cutover before this is described as all-path admission.


## Essential-value admission

Spec 379's [shared completeness rules](intake-completeness.md) apply to new preparation. Currency, bank direction and bank booking time cannot be invented from defaults or source arrival. Allowed order timing/commercial gaps remain visible review observations. Historical retained reviews keep their exact digests and values; raw remains lossless independently of acceptance.
