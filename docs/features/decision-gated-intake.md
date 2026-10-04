# Decision-gated source interpretation

## Implementation status

Specs 351–356 describe the complete rollout. The initial implementation offers an
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
adapters, master/stock application, bulk continuation, mandates, demo cutover and
universal writer coverage remain pending. The explicit reviewed services are an
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
cutover unfinished (spec 355).

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

## Canonical evidence transactions (qualification in progress)

The existing manual normalized-document, manual-order, sales-invoice,
order-linked supplier-invoice and free supplier-invoice commands bind accepted
effects to their actual retained confirmation. An action tag alone grants no
authority. Canonical parent inputs and invoice posting calls are frozen before
callbacks and consumed once; each planned child keeps its own invocation.
Evidence, promises/postings where applicable, and the executed receipt settle
in the application-owned transaction. Premature root commits and unrelated
header/stock effects refuse. Source values remain as stated.

These command families do not establish universal writer coverage. Credits,
header-only evidence, corrections and remaining configuration/operational
writers retain separate spec 356 tasks and require final coverage/CI evidence.
Customer credit qualification now freezes both existing sales_credit_record
variants and their exact credit posting and explicit netting. Receipt settlement
owns the root transaction; a credit confirmation grants no refund or stock effect.
Full committed-head qualification and remaining writer closure are still pending.

Commercial master commands now retain explicit confirmation for payment-term
create/update, price-list create/update, price tiers, party/group price-list
assignments and party-group create/update/membership. REST requires an explicit
confirmed flag and records the actual authenticated person. CLI presents the
exact statement before confirmation; an unauthenticated local CLI decision does
not invent a person or channel attribution. Canonical callbacks are frozen,
consumed once and committed with their receipt. Opaque reference IDs and hashes
of their current stored state require renewed review after another real decision
changes that state. Price, quantity, discount and priority statements are recorded
as received. Fixed declared setup calls retain their existing profile authority.
Lifecycle/source-reference and other operational writers remain separate tasks;
this finite command list is not universal writer certification.

Fixed confirmed `demo_seed` and `normal_month` application profiles recheck their actual current confirming person, manual credential and interactive MCP consent before canonical writes. A fixed authored definition never replaces current consent. Separately bound company and lesson initializers retain their existing narrow authority. Successful settled receipt replay remains unchanged.

The existing master-data lifecycle decision now owns the exact party/item/location/payment-term active flag and a private hash of its actual referenced record. Direct canonical writes and absent confirmation refuse; changed current records require renewed review. REST PATCH and CLI activate/deactivate prepare that same retained decision and explicitly confirm. The browser SDK requires the caller to supply confirmation rather than manufacturing it. The existing confirmed party merge owns its exact duplicate deactivation in the same frozen root transaction; it grants no unrelated business effect. Local family proofs pass; full committed-head CI and remaining writers are still pending.

Manual header and line corrections now prepare a retained review of the current
document, positions and referenced records. Their existing REST endpoints require
explicit `confirmed: true`; an omitted flag creates no proposal or business change.
Changed review context requires renewed review, even when the line revision itself
has not changed. Original stale-revision and downstream Reality restrictions
remain domain rules. Correction effects and their executed receipt share the
application-owned transaction. Appending an immutable upstream source version and
preparing its interpretation records raw evidence only; it does not authorize
canonical document or Reality changes. Header-only creation and other writer
families still require their separate coverage qualification.
