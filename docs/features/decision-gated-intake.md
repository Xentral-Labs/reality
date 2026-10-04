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

Specs 356–361 describe the complete rollout. The initial implementation offers an
explicit preparation path through `intake_prepare_propose` / application
`create_change_proposal("intake_apply", {"job_id": ...})`, retained reads through
`intake_review`, and exact confirmation through the existing proposal executor.

Supported explicit inputs are Shopify first orders, supported later reductions and
cancellations, refund transaction evidence and supported return announcements,
normalized customer payments with job profile `customer_payment.v1`, and normalized
synthetic payment payloads. Shopify credit checks appear as exact proposed holds.
Missing source line amounts remain null, and unknown prices stay visible; no line
total is computed from quantity and price. Each stated refund transaction gets its
own evidence amount, with goods lines recorded once. Raw payloads survive failures.

Legacy automatic import processing is not yet switched over. Invoice/bank-file
adapters, master/stock application, bulk continuation, mandates, demo source cutover remain pending. The explicit reviewed services are an
implementation checkpoint, not completed cross-path admission coverage.

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
status reads return child receipts without running work. This checkpoint still
leaves external AgentMandates, selection/recovery UI and the universal adapter
cutover unfinished (spec 360).
