# Retained-census review resolution

Status: internal bounded integration of the approved costing services. This is neither a
common financial input manifest nor full-company publication. No schema was added.

## Shared service

`costing.resolve_company_cost_census(session, tenant_id, census_id, max_subjects=10)`
requires REPEATABLE READ, verifies retained capture integrity and uses the verified frozen
members. Group movements by the observed item; retain every captured sales-line candidate.
The combined item/line count must not exceed max_subjects (strict integer 1–10). Overflow
refuses before any costing calls; results never truncate or silently omit unknown subjects.

For each subject, select the latest confirmed review whose introducing BusinessEvent is
within the captured tenant event cursor. Every joined record is tenant-scoped. A later
confirmation cannot supply authority to an older capture. Do not fall back past a newer
incompatible retained review. Use the existing inventory_cost/reviewed_contribution services
with explicit review identities, preserving their integrity checks and financial arithmetic.

## Result contract

Each inventory/contribution entry includes subject identity, review ID/content hash when
available, state, result, basis_result and explicit gaps. Review hashes are references to
existing verified scope inputs, not a complete company input fingerprint.

- available_at_capture: a canonical reviewed result with matching captured context.
- unknown_at_capture: no matching basis; result=null. An older or incompatible review may
  remain visible as basis_result, carrying its own original knowledge time and policy.
- Missing review keeps the subject with no basis_result. This includes currently unsupported
  service/credit candidates; it does not invent zero cost or a goods-based service margin.
- Inventory requires the same effective cutoff and exact movement identities in the review
  and captured item scope. Knowledge must be unchanged through the capture cursor.
- Contribution requires its review cursor to match, its linked inventory review's cutoff
  and movement membership to match, and economic_at not to exceed the capture cutoff.
- Cursor freshness remains conservative except for proved contribution-only confirmation
  events. A bounded complete interval may contain executed owner-confirmed contribution
  reviews without invalidating inventory; another line's confirmation also leaves the
  queried contribution unchanged. Same-line and all other events remain invalidating.
  Later live events do not alter a successfully resolved older capture.
- Carrying-value support and DB2 coverage remain independent gaps in the canonical result.
  Supported DB1 is not suppressed solely because selling costs are unknown.

Header-only documents and non-interpreted source versions remain separate capture gaps.
They do not become invented monetary rows or silently disappear when a scope review exists.
No cross-scope monetary total or complete-company coverage claim is returned.

The response always states publication_eligible=false and no business/projection writes.
It does not expose a common knowledge_at. The caller must not construct PopulationBasis by
substituting observed_at, nor treat any scope hash as an entire financial input manifest.

## Operational boundary

This is internal builder work, not a report/read adapter. Capture verification may read up
to the existing capture bound; canonical scope readers retain their existing movement/input
bounds. The service performs no flush, confirmation, persistence, generation build, enqueue
or policy activation. No throughput/fixture-J qualification is claimed.

Remaining work: resolve/retain a common supported financial input manifest with explicit
subject policy/review vectors and gaps, establish precise admission/invalidation coverage,
chunk the work at company scale, and integrate transactional publication. These remain
T080/T081/T089 requirements. The existing publication guard is not invoked by this service.


## Closed contribution-only confirmation proof

The captured resolver may exempt at most 100 intervening contribution_review or
contribution_batch_review events. Require a complete contiguous tenant event interval,
schema-v1 cost.reviewed events with matching action subject/action identity, exact payload
operation, executed cost.change decisions with actor/time and a valid typed request.
The exact unique persisted contribution-review target set, action and event cursor must
match that request. Missing/extra/foreign/malformed proof remains invalidating. Do not
infer a decision from event labels or action output alone.

Inventory inputs are unchanged by this closed writer. For contribution, any review of
the queried line remains invalidating. Every other operation (including receipt/inventory
reviews, attribution, correction, new evidence and unknown events) stays conservative.
The resolver returns freshness_proof with interval cursors and verified event identities.
No cursor, review hash, policy or financial amount is rewritten by this proof. This does
not create a common financial manifest, waive source gaps, or alter other current readers.

## Common captured basis vector

The response now includes captured_basis assembled against the verified census's exact
item/line sets. Its versioned digest binds census identity/content hash, tenant, effective
cutoff, observation time, snapshot identity and event cursor; every selected review ID/hash,
own knowledge time, policy/profile/link metadata, canonical result and historical-result
digests, freshness proof, scope gaps and source/header gaps are included. Enumeration order
does not affect the digest. Missing, duplicate, extra or mixed-context subjects refuse
assembly. This field is a read-time observation; retained=false and publication_eligible=false.

Coverage counts for acquisition, carrying, DB1 and DB2 remain independent. They describe
only captured_subjects_and_candidates. Unknown/unreviewed subjects stay in denominators;
only non-null available results count as covered. Zero is known, stale basis_result is
not coverage, and an empty family has state=empty without a numeric monetary total.
Complete subject coverage does not resolve separate header/source gaps. Canonical row
results remain the explanation for currency, unit, policy, missing inputs and amounts.

The digest is not an input_fingerprint accepted by ExpectedPopulation and is not a
sealed financial manifest. It retains no new data and cannot turn observed_at into a
common historical knowledge_at. Full financial retention, company publication and
reference-scale qualification remain required. No new public tool or catalog operation.
