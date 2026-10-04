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

Supported initial inputs are first Shopify orders with source-stated line amounts
and no credit policy, normalized customer payments with job profile
`customer_payment.v1`, and normalized synthetic payment payloads. Unsupported
inputs refuse; an approval does not broaden existing domain support. Missing
Shopify line amounts are not computed from quantity and price. Source bytes and
payloads survive preparation failures.

Legacy automatic import processing is not yet switched over. Shopify changes,
refunds and credit holds, invoice/bank-file adapters, master/stock application,
bulk continuation, mandates, demo cutover remain
pending. This initial explicit path must not be represented as completed admission
coverage or deployed as the full cutover.

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
commit refuses. An executed proposal replays its retained receipt without effects
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
