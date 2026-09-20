# Production costing data model proposal

**Status:** Model and staged production implementation explicitly approved by the owner.
Implementation progress is recorded in tasks.md; company policy activation and release
are separate. Earlier proposal/review wording below records the reviewed decision. Target: spec242 FR-001–027 and DR-001–005.

## 1. Recommended decision

Keep received financial amounts in the existing evidence model. Add explicit signed
cost attribution and confirmed review records. Calculate acquisition cost, stock value,
consumption and DB from that evidence; indexed generations remain disposable caches.
Deliver actual receipt cost and evidence coverage first. Inventory consumption and
commercial contribution follow on the same basis; the first slice does not claim DB.

Implement a production integration candidate after owner review of this concrete model;
keep fixture J, reference hardware and full adapter qualification as release gates.
This explicitly proposes revising the earlier pre-implementation qualification gate:
an actual integrated candidate is needed to run its tests. It does not waive any budget,
claim HGB suitability, activate a policy or authorize deployment.

The first migration slice is deliberately smaller than the complete target model below.
No Alembic revision number is reserved; parallel feature235 already has migration work.

## 2. Reuse and proven gaps

Paths in this table are under `packages/reality-core/src/reality/`.

| Existing record/service | Reuse | Gap proved by this feature |
|---|---|---|
| `db/core.py::SourceRecord` | Lossless immutable source versions, hashes, supersession | Source receipt does not mean interpretation has completed |
| `InterpretationOutcome` / `InterpretationRecordReference` | Link each accepted interpretation to resulting records | A frozen build must retain the exact accepted interpretation, not follow latest pointers |
| `Document` / `DocumentLine` | Received business evidence and billed-line relationships | Manual header/line fields can change; current IDs alone cannot reconstruct old input values |
| `db/components.py::FinancialComponent` | Exact stated net/tax/gross/base and currency; shortest evidence owner | Created lazily today, not an exhaustive register of invoice cost; version/immutability admission must be explicit |
| `ComponentAssignment` / `ComponentAssignmentPart` | Existing cost-centre classification stays unchanged | Positive cost-centre shares cannot allocate signed costs to receipt quantities |
| `Movement` / `MovementCorrection` | Quantity, physical event and correction chain | No universal recorded-at field; prior knowledge needs event membership, not occurred-at filtering alone |
| `Movement.commitment_id -> Commitment.document_line_id` | Receipt/sale commercial context | Does not assign invoice amount to exact receipt portions |
| `DocumentLine.billed_document_line_id` | Agreed/billed relationship | Does not establish disjoint invoice/fulfilment matches |
| `resolves_movement_id` / `ReturnAnnouncement` | Return resolution and original promise | Neither identifies the original outbound issue cost among split shipments |
| `ChangeProposal` (physical table `action`) | Confirmed actor, input, output, decision time | Do not duplicate confirmation identity on every detail part |
| `services/core.py::emit_business_event` | Tenant lock and transaction-serialized event sequence | Every relevant input writer must participate; event timestamp alone is not commit time |
| `ProjectionRow` / `ProjectionCheckpoint` | Existing lifecycle, job and freshness conventions | Text payload replacement does not supply indexed contribution grain or bounded generation stages |

No new document fulfillment/status fields, generic object registry, job queue or
accounting ledger. Existing gross balances and cost-centre assignments retain meaning.

## 3. Common storage rules

All proposed business and cache tables have opaque `id`, `tenant_id`, unique
`(tenant_id,id)` and same-tenant composite FKs. Money/quantity use NUMERIC(18,4) with
Decimal arithmetic; unit-cost display precision follows FR-022 and is not a stored
source price. Reject overflow/unsupported precision before a confirmed write. UTC
instants are distinct from business dates. Explicit source references preserve raw
payload precision even when normalized calculation is unsupported.

Confirmed revisions are append-only. A revision has `revision` (positive integer),
`supersedes_id` within the same subject, `effective_at`, `introduced_event_id`,
`action_id` and nonempty `reason`. Created knowledge order comes from the referenced
BusinessEvent sequence. Exactly one successor per predecessor; first revision uniqueness
and service locks prevent concurrent forks. A withdrawal is a new explicit revision,
never deletion of old decisions. Parts inherit actor, event and scope from their parent.

Use RESTRICT, not cascading deletion, from financial decisions/reviews to evidence.
Workers cannot create confirmed decisions. Services recheck active owner, tenant,
expected revision and evidence fingerprints in the execution transaction. Retry identity
is the existing confirmed action; repeating it returns the original result. Reads use
shared services, no autoflush and no writes/jobs.

Cross-row conservation is validated in the application service under the shared tenant
business lock plus target locks in stable opaque-ID order. SQL CHECKs alone cannot prove
sums or overlapping quantity scope. Pin reviewed input identities, not only a digest.
All new writers acquire locks in the same order as existing delivery/finance services;
do not first lock a component and later acquire the tenant lock.

## 4. First product slice: received receipt cost

### 4.1 `cost_receipt_basis`

One immutable admission of a stock-in receipt for cost evaluation. Fields:

- `movement_id`: unique same-tenant FK, shortest physical target; no duplicate order,
  document, source, item or location FKs.
- `introduced_event_id`: exact transaction establishing this cost input.
- `base_quantity`, `base_unit`: the received quantity and resolved unit as admitted,
  with the immutable unit-conversion evidence when conversion is needed.
- `unit_basis_source_id`: optional same-tenant SourceRecord for an explicit conversion;
  if no conversion is used, the basis states identity conversion. No inferred ratio.
- `input_schema_version`: fixed allowlist for replay.

The admitted movement quantity is not recomputed from current item data. Admission does
not prove economic ownership or complete cost. Receipt corrections retain the original
basis and add the compensation/replacement's basis and correction event membership.
Stock opening quantities may enter only with their existing movement identity and
explicit opening evidence; no invented purchase receipt or zero cost.

**Proof:** FR-002/005/007/013/022; repeatedly joins attribution, divides known acquisition
cost by eligible quantity and replays historical correction scope.

### 4.2 `cost_component_basis`

One immutable costing admission of an existing `FinancialComponent`:

- `component_id`: unique same-tenant FK; reaches exactly one document/line and its source.
- `introduced_event_id`: admission/interpretation event, not source receipt alone.
- `evidence_fingerprint`, `input_schema_version`: stale-preview detection and replay.
- `interpretation_outcome_id`: optional exact accepted interpretation outcome; null for
  manually stated evidence, not a fabricated source interpretation.

Reuse exact component amounts; do not copy net/gross/tax into another financial authority.
Factor the current received normalization into a shared service usable by finance and
costing. Discovery also inspects supported retained evidence with no component yet;
normalization occurs through an explicit write/intake path, never as a side effect of
an EK read. A component's absence does not mean missing supplier evidence.

Once admitted, those component amounts and their relied-on manual evidence cannot be
changed in place. Extend the existing manual-evidence correction guard to include
financial component/costing admission (it currently checks commitments/postings only).
A corrected amount needs new received evidence and a new component, then reviewed
replacement attribution. External new versions already use distinct source identities.
The first slice requires an explicit append-only manual replacement-evidence service
before it admits manual evidence; otherwise manual evidence is visibly unsupported.
Silent blocking with no correction path is not a completed first slice.

Add `cost_component_replacement` with typed `previous_basis_id`, `replacement_basis_id`,
`introduced_event_id`, `action_id` and reason. Unique predecessor and replacement links,
same-tenant FKs and a locked service check forbid forks/cycles. The initial contract is
whole-component one-to-one replacement; ambiguous split/merge replacements refuse. In
one confirmed transaction create replacement evidence/basis, withdraw the predecessor
attribution, install its reviewed replacement and invalidate affected current reviews.
The old evidence and parts remain available at earlier cursors. A commercial supplier
credit is normally an additional signed component, not replacement of the original invoice.
Replacement evidence alone creates no payable or posting; existing finance decisions
require their own explicit reconciliation, never automatic financial duplication.

**Proof:** FR-001/003/007/016; immutable amounts, exact provenance and historical input
membership. Add same-tenant uniqueness support to referenced existing tables where absent,
including BusinessEvent, Movement, MovementCorrection and interpretation outcomes;
validate existing data before adding composite constraints.

### 4.3 `cost_attribution_revision`

Complete replacement decision for one admitted component, not an additive delta:

- `component_basis_id`, common revision/action/event fields.
- `basis`: `net`, `gross` or `base`, selected only when that received field exists.
- `selected_basis_tax_inclusion`: `included`, `excluded`, `unknown`, backed by the
  received basis semantics; prevents adding tax twice.
- `tax_treatment`: `recoverable`, `nonrecoverable`, `mixed`, `not_applicable`, `unknown`.
- `nonrecoverable_tax_amount`: confirmed received-tax share, nullable when unsupported;
  bounded by the stated tax amount with consistent sign. This is an internal assignment
  of an existing amount, not a recomputed tax figure.
- `tax_evidence_source_id`: optional supporting received declaration/evidence.
- `state`: `assigned` or `withdrawn`; withdrawal has no active parts.

Gross already including tax cannot add the same tax again. In the first slice, gross
is a complete acquisition basis only with evidence that it contains no recoverable tax.
Recoverable/mixed gross requires an independently received applicable net/base amount
or remains incomplete; do not infer net by subtraction. A future gross-recovery bucket
would need a separately reviewed extension. Net plus an explicitly
assigned nonrecoverable share may use separate base/tax parts. A base amount with unclear
tax inclusion remains incomplete until its inclusion treatment is evidenced. No
`gross - tax` substitution for absent received net. Unknown tax treatment may retain
an evidenced subtotal but cannot claim a reviewed complete acquisition basis.

### 4.4 `cost_attribution_part`

Fields: `attribution_revision_id`, `receipt_basis_id`, `amount_bucket` (`selected_basis`
or `nonrecoverable_tax`), `category`, `source_share`, `cost_effect`, `assignment_kind`
(`direct` or `allocated`), and optional `allocation_weight` with `allocation_method`.

Categories in this slice: goods, inbound freight, duty, other acquisition expense,
purchase reduction and nonrecoverable input tax. `source_share` preserves the source's
sign convention; `cost_effect` is +1 or -1 with an explicit category/decision meaning.
A supplier credit that states positive 50 therefore remains positive 50 in evidence
while its acquisition effect is -50. Define the derived effect exactly as
`abs(source_share) * cost_effect`; a source stating credit -50 also has effect -50,
not +50. All shares in a source bucket retain that bucket's sign and their absolute
sum cannot exceed its absolute received capacity. Source sign and semantic effect
are not conflated.

Unique `(tenant, revision, receipt_basis, bucket, category)`; typed receipt FK only in
this slice. No object-type/object-ID target and no FK to a derived FIFO layer. Quantity
allocation uses the admitted eligible receipt quantity as its weight, not a fabricated
price. Stable target-ID residual allocation follows FR-022. Exact received subtotal,
assigned parts and derived unassigned remainder reconcile per bucket, with source-sign
rules that forbid offsetting positive/negative parts to hide overassignment.

The complete current revision replaces all prior parts for that component. Summing every
historical revision would double costs. Service-cost and selling-cost targets are added
later through separate typed part relations, not nullable arbitrary target strings.

### 4.5 `cost_scope_review` and `cost_scope_review_category`

First-slice review targets exactly `receipt_basis_id`. Parent fields: common revision/
action/event fields, `basis_event_sequence`, `effective_at`, `review_manifest_id` and
`state` (`confirmed` / `withdrawn`). A frozen review manifest is described in section 6.

Category child: `review_id`, `category`, `disposition` (`evidenced`, `confirmed_zero`,
`not_applicable`, `unresolved`), nonempty justification for zero/not-applicable, and
supporting evidence reference where supplied. Unique review/category. Required categories
are explicit in the receipt review; absent category rows do not silently imply zero.

A review establishes completeness only at its frozen basis. Later relevant input or
changed attribution makes the current review stale; preserve its original meaning.
Known costs, provisional estimates and reviewed completeness remain different states.
An assignment is not itself a declaration that all freight/customs/credits have arrived.

### 4.6 `cost_correction_basis`

Fields: `movement_correction_id` (unique same-tenant MovementCorrection FK),
`introduced_event_id`, `input_schema_version`. Capture this admission in the exact
correction transaction. It reaches original, compensation and replacement movements
through the existing correction record; do not duplicate those FKs. First-slice
manifests include correction-basis members as well as receipt bases. Selection at
cursor N applies only admitted corrections introduced by N. Later live correction
predicates cannot rewrite a sealed historical receipt basis. Missing correction
admission makes scope unsupported, not silently corrected under today's rules.

**First-slice scope:** eight new table families above (including component replacement
and correction admission), plus the manifest/member storage
needed for durable reviewed input identity. No policy method is required to sum receipt
cost; FIFO/ownership and sales-margin tables are later slices. First-slice acceptance
covers actual receipt cost and missing basis, not remaining-stock valuation or final DB.

## 5. Later authoritative records required for stock and contribution

These are target schema proposals, not implicit additions to the first migration.
Every row is tenant-scoped; revision headers retain the common action/event contract,
and detail parts inherit those decisions through their parent rather than duplicate FKs.

| Proposed record | Required typed fields/links | Invariant and requirement |
|---|---|---|
| `cost_policy_revision` | Tenant scope or item FK, method (`fifo`, `specific`), valuation currency, effective range, time-order rule, predecessor | One applicable policy for a pool/cutoff; changed methods require explicit review/replay, FR-004/005/007 |
| `contribution_profile_revision` | Fixed `commercial_v1` definition/version, required selling-cost categories, effective range | Versioned DB meaning, no arbitrary formula language; FR-011/014 |
| `cost_ownership_revision` + parts | Receipt/movement basis FK, economic owner Party FK, covered base quantity, effective instant, evidence SourceRecord FK | Reviewed portions cannot exceed the actual quantity; location is not owner; transit/consignment stay explicit, FR-008 |
| `cost_service_attribution_part` | Attribution revision FK, existing service commitment FK, exact source share, effect, category | Only supported service commitment kinds; no fake goods movement; same component conservation across target families, FR-010/017 |
| `cost_selling_attribution_part` | Attribution revision FK, sold DocumentLine FK, exact source share, effect, category | Allocation to derived contribution slices is calculated; direct/allocated distinction retained, FR-011 |
| `cost_revenue_match_revision` + parts | Revenue component basis FK, original match predecessor; part points to outbound Movement FK or evidenced service commitment FK, covered quantity, allocated received net amount | Complete revision, no overmatched source amount or fulfilment quantity; concurrency locks both sides; no SKU/date guessing, FR-010/012 |
| `cost_return_match_revision` + parts | Returned Movement FK, original outbound Movement FK, covered quantity, optional evidenced specific receipt identity | Total returned original quantity bounded; original consumption portions reconstructed at frozen basis; `resolves_movement_id` not reused, FR-005/017 |
| `cost_specific_consumption_part` | Outbound Movement FK, original receipt basis FK, quantity, confirmed evidence/action revision | Explicit physical identity, no physical-lot-to-cost assumption without evidence; never references a disposable layer ID, FR-005 |
| `cost_valuation_assessment_revision` + scope parts | Exact inventory-review FK, cutoff, assessment kind and predecessor; parts identify remaining inventory-member quantities, source evidence and source-stated total assessed value/currency | Reconcile carrying value separately; recovery cannot exceed supported original cost; no duplicated policy/item/owner link and no inventory movement for monetary impairment, FR-009 |
| `cost_scope_review` extensions | Separate typed stock-policy scope and sold-line review relations | No polymorphic target registry; reuse category/status semantics without copying receipt FK, FR-014/015 |

An unassigned cost component exists before any receipt/sale match and must remain visible.
Cost-centre allocation and acquisition/selling allocation describe different dimensions
of the same evidence; they are never summed together as two costs. Reductions after
payment require received discount/credit evidence and attribution, not payment residual
inference. Currency conversion requires retained reviewed basis; current rates cannot
rewrite historical source amounts. Unsupported internal manufacturing/WIP stays explicit.

### Reviewed carrying-value assessment

`cost_valuation_assessment_revision` is an immutable tenant-scoped decision header with
`inventory_review_id`, optional unique `supersedes_id`, positive `revision`, `kind`
(`write_down` or `recovery`), `effective_at`, `knowledge_at`, `target_event_sequence`,
`introduced_event_id`, `action_id`, `reason`, `input_schema_version=1` and a canonical
content hash. The inventory review is the only business-scope link; policy, item, owner,
currency and unit are reached through it.

Each `cost_valuation_assessment_part` belongs to that revision and references one exact
remaining `cost_inventory_member`, one `source_record`, a positive quantity, a currency
matching the review and the source-stated total `assessed_value` for that quantity. A
revision cannot repeat or overlap a member. A write-down value is non-negative and below
the frozen acquisition-cost ceiling for its part. A recovery supersedes the immediately
prior exact-scope assessment, is not below its carrying amount and cannot exceed the
historical acquisition-cost ceiling. The database enforces shape, precision, same-tenant
links and immutable identity; the service enforces remaining-scope membership, exact
scope continuity and monetary ceilings under row locks.

The calculated carrying value, adjustment, unit display and aggregate reconciliation are
never stored in these authority tables. Historical reads select explicit revision IDs;
current reads select the latest valid successor and conservatively report stale after a
later relevant event.

### Full-history typed context versions

Contribution requires immutable versions of mutable document/customer/channel/date and
line/quantity/unit/matching context. Proposed `cost_document_context_version` references
Document plus event and records only party ID, channel, currency and relevant received
business dates. `cost_line_context_version` references DocumentLine plus that exact
header context and records item, received quantity/unit and billed-line relation. These
are exact retained input copies for replay, not invented financial totals or new Facts.

Capture new context versions in the same transaction as relevant manual corrections or
accepted interpretation. Once a line is admitted to costing it is retained, and removal
uses the reviewed replacement/correction workflow instead of hard-deleting a referenced
line. Unadmitted manual lines keep current behavior. Dimension display labels may use
current names, but grouping uses retained IDs/transaction channel; disclose that distinction.
No general master-data time machine is introduced. Concrete migration/tests for these
context versions belong to the contribution slice, before advertising historical DB.

## 6. Retained knowledge and review manifest

### 6.1 Cursor semantics

Reuse tenant-serialized BusinessEvent sequence; no second sequence generator.
Capture the committed maximum in a fresh transaction under the existing brief tenant
lock, with a snapshot that sees earlier lock holders' commits; release it immediately.
An old repeatable-read snapshot acquired before waiting is not a valid capture shortcut.
Every admission, attribution, review, match, ownership/policy change and relevant correction
commits its exact input identity and event together. A source received but not interpreted
is visible as source-pending coverage, not a usable normalized cost input. Workers never
follow current source/assignment pointers after choosing their target cursor.

For first-slice inputs, admitted immutable components and receipt bases plus revision
chains are sufficient. Later context versions close the mutable-document gap before
historical contributions ship. Do not describe existing header-change events as full
before/after history; they currently contain changed-field names without all old values.

Knowledge is identified exactly by retained revision membership and event cursor. An
arbitrary requested wall-clock cutoff is supported only where the evidence can establish
that cursor; recorded_at is not database commit time. Reviews and saved fixed contexts
must retain the resolved cursor as well as the displayed time. Refuse unsupported
pre-admission knowledge; do not invent commit timestamps. An input transaction that
started before capture but commits afterward must fall beyond the sealed input set.

### 6.2 `cost_input_manifest` and typed member relations

Fields: `id`, `tenant_id`, `target_event_sequence`, `effective_at`, `knowledge_at`,
`input_schema_version`, `algorithm_version`, optional policy/profile revision FKs,
`state` (`building`, `sealed`, `failed`), `sealed_at`, and content hash plus row counts.
First-slice receipt manifests have no invented FIFO policy/profile. A confirmed review
references a sealed manifest. A build cannot use a building/failed manifest.

Membership uses typed relations, not free-form entity-kind strings: receipt-basis members,
component-basis members, attribution-revision members, replacement/correction-basis
members and prior review members for the first slice; policy, ownership, match and
context-version members for later slices.
Each member has `(tenant_id, manifest_id, input_id)` with same-tenant composite FKs and
uniqueness. Reuse exact authoritative input revisions; do not copy calculated EK/DB.
A manifest does not include the review that will approve it. Included reviews must
predate the target cursor and reference an already sealed predecessor manifest; service
validation forbids transitive cycles, not just a direct self-reference.

The manifest is an immutable reproducibility record once sealed, not a new financial
assertion. Its referenced inputs are retained while any review references it. A digest
is only an integrity check and cannot replace input membership. Unreviewed temporary
manifests can be cleaned when unreferenced; reviewed ones cannot disappear with cache GC.

Large membership enumeration is itself bounded shared-worker work. Establish the target
cursor first; version membership must be resolvable at that cursor without a long database
snapshot held across child processes. Capture is complete only when all input families
have been enumerated and counts/digests checked. Every subsequent chunk reads immutable
versions at that cursor, even if new evidence arrives. This admission/manifest stage is
included in full reconstruction timing; the earlier fixture already had immutable input
and therefore did not measure this production overhead.

Bootstrap records the earliest supported knowledge boundary and exact retained input
set. Existing invoices/movements may be admitted in bounded batches, but a bootstrap is
not final until input/correction races are reconciled and unsupported old history is
reported. Do not claim earlier historical snapshots based on present-day values.

## 7. Disposable calculation storage

Select the locally measured staged-generation strategy for the proposed candidate;
production benchmarks and schema review remain gates.

| Table | Essential columns / key | Index/use |
|---|---|---|
| `cost_generation` | tenant/id, sealed manifest FK, algorithm version, state, start/completion, failure code | One active build per compatible requested scope; requested context digest is not authority |
| `cost_generation_work` | tenant/generation, opaque work ID, typed pool bounds, ordinal, cursor/state, counts | Unique generation/ordinal; shared queue claim fences execution |
| `cost_contribution_row` | tenant/generation/slice ID, matched input identities, dimension IDs, activity date, currency/unit, quantities, revenue/cost/selling amounts, independent support/coverage | Order/item/period/customer/channel indexes; disjoint slice uniqueness |
| `cost_inventory_row` | tenant/generation/pool/item/currency/unit/cutoff, physical/owned/covered quantities, known acquisition and supported carrying values | Inventory page/filter indexes; non-additive across cutoff |
| `cost_trace_part` | tenant/generation/slice, original receipt/match/attribution input IDs and allocated quantity/effect | Bounded explanation; no authoritative FK points into this cache |
| `cost_finding_row` | tenant/generation, class, existing subject FK family, cause input IDs, severity, sort key | Shared exception snapshot consumption, no new FIFO computation |
| `cost_publication` | tenant plus canonical scope/context key -> completed generation FK | Atomic pointer; never mixed per-pool cutoffs in a whole-scope report |

Current and historical context keys include compatible policy/profile, currency/unit and
cutoffs; a tenant-only publication pointer is insufficient for simultaneous historical
and current requests. Foreign generations behave as absent. Cached rows do not acquire
financial authority because they are persisted. Rebuilding can change algorithm output
only under a new declared version, with old review basis still explainable.

Final publication validates planned work and row counts then switches a pointer in a
short transaction. Intake remains available during computation. A new relevant event
beyond the target makes the result pending and requests follow-up through shared jobs.
Reads never request that work. Metadata, page/count/totals and trace pin one generation.

Retain current and previous publication while in use; active build and cursor references
prevent cache deletion. Propose a bounded 24-hour read cursor lifetime, encoded in the
cursor; after expiration return explicit expired-basis refusal. Reviewed manifests/input
history remain retained independently of this cache lifetime. Production cleanup uses the
shared scheduler only after its registry/retention design is reviewed; no new timer loop.

## 8. Transaction examples

**Receipt A:** admit 100 units and the received goods/freight/credit components; owner
confirms +1,000, +100 and -50 attribution effects. Category review pins those inputs.
Read derives 1,050 acquisition cost and 10.50/unit. It stores neither as a new Fact nor
as a replacement supplier unit price. Until review, expose support/coverage honestly.

**Late freight:** a new component and reviewed attribution appear after cursor N.
Manifest N is unchanged; current review becomes stale. A new generation includes the
new input and splits the effect between consumed and remaining quantities. Earlier
reviewed values remain explainable through retained inputs, not mutable cache rows.

**Split sale/return:** match 40 of 60 delivered units to the received revenue scope.
Matched DB covers 40; the remaining 20 units remain unbilled reconciliation. A return
references the actual original issue quantity, then reconstructs its cost portions;
resale consumes the restored layer at return-time ordering, not original receipt ordering.

**Correction race:** owner previews allocation revision R and source fingerprints.
Another transaction corrects evidence or publishes R+1. Execution refuses the stale
preview without parts, event or partial review writes. A lost reply after successful
commit returns the same action result; it does not append another allocation.

## 9. Migration, rollback and release gates

1. Add the reviewed first-slice tables, same-tenant uniqueness prerequisites and indexes.
   No write on normal scheduler/worker startup. Deploy schema through the migration path.
2. Add domain rules and shared admission/preview/execute/read services; tests first.
   Keep normal companies unactivated until explicit reviewed setup. No mass auto-allocation.
3. Add the append-only manual replacement path and mutation guard, plus atomic input/event
   capture. Test existing finance workflows for unchanged cost-centre semantics.
4. Bootstrap only explicit test/owner-selected scope, preserving incomplete/unsupported
   cases. Emit no invented early knowledge times or complete reviews.
5. Add subsequent inventory/contribution authority and context versions, then canonical
   cache and adapter slices. Integrate inspector/resource/tenant catalogs and generated docs.
6. Run full domain/service/migration/permission/isolation/adapter suites and fixture J
   with actual manifest capture, workers, reports and exception page/count. No release
   while required checks, timings or reference-host qualification are red.

Rollback disables adapter/worker registrations first. Unreferenced derived caches can be
dropped and rebuilt. A downgrade that would delete confirmed attributions, review
manifests or sole retained historical inputs must refuse; use forward-compatible service
rollback or an explicit reviewed export/migration. Add/drop-only reversibility is not an
adequate rollback for financial decision history.

## 10. Required test-first proofs and proposed approval boundary

| Proof | Required cases |
|---|---|
| Received evidence | Lazy component discovery, no net recomputation, normalization parity with finance, corrected evidence admission, unsupported precision |
| Attribution | Split/shared freight, both positive/negative-stated credits yielding negative effects, recoverable/mixed gross refusal, net/tax/gross no double-count, residuals, competing assignments |
| Ownership/reviews | Member refusal, owner demotion, stale preview, exact zero/not-applicable, later evidence invalidation, full rollback/idempotency |
| Knowledge | Late commit, late interpretation, correction chains, historical cutoff refusal, input mutation guard, source change between worker chunks, bootstrap boundary |
| Matching | Split invoice/fulfilment, partial service coverage, no overmatch, exact return issue, original cost restoration, explicit unsupported scope |
| Generation | Manifest stages count in timing, oversized pool refusal/checkpoint design, timeout/retry/fencing, atomic publication, cache deletion/rebuild parity |
| Surfaces | Adapter-delivery vectors, identical basis/values, known vs final subtotals, current/historical saved questions, exception lag and clearing |
| Migration | Same-tenant constraints/indexes, existing finance regression, restricted downgrade, absence of automatic company activation |

The concrete approval requested is: (1) retain shared received components and add signed
receipt-attribution/review authority; (2) require immutable admitted evidence and exact
manifest history, with an honest earliest supported boundary; (3) implement receipt cost
and coverage first, then inventory and DB on the same model; (4) allow this reviewed
production candidate to be built before integrated fixture-J qualification, with all
qualification gates mandatory before release. Approval does not activate a company
policy or authorize deployment/merge. Detailed per-slice tasks and consistency analysis
follow approval, before code implementation.
