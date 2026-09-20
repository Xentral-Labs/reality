# Retained inventory publication through the shared worker

Approved staged production model refinement for T080, FR-007/014/016/018/019.
The first stored scope is exactly one existing confirmed CostInventoryReview. It is
bounded by the existing 100 movements / 20 receipts admission limits. No company-wide
profile, general historical admission, multi-item aggregate or contribution generation
is introduced. Current per-item policies cannot be relabeled company-wide authority.

## Storage and authority

Three disposable cache tables, each opaque ID + tenant and same-tenant FKs:
- cost_inventory_generation: exact inventory review FK, algorithm_version, completed_at,
  output_hash. Unique tenant/review/algorithm. It exists only when its one bounded work
  unit and publication succeed in the same transaction. Review is the sealed retained
  input membership; do not create a second financial manifest or copy source values.
- cost_inventory_snapshot: generation FK (unique), remaining_quantity and acquisition_value
  NUMERIC(18,4). This is the canonical one-pool observation; no JSON population or stored
  FIFO authority. Carrying value is still unsupported, never inferred from acquisition.
- cost_inventory_publication: unique tenant/review, generation FK with composite
  tenant/review/generation constraint. A publication cannot point at another review.

The shortest input links are generation -> review -> policy/members -> receipt manifests.
No duplicated item/policy/owner FK in cache rows. Typed values are justified by bounded
SQL reads and the later canonical inventory relation. The generation's output hash
verifies the canonical typed row; input integrity is checked by the existing historical
inventory reader before publication. No building-state table is necessary for this
single bounded work unit. Larger scope will require staged work and input capture.

## Build transaction

The shared application service accepts tenant + exact review identity, no client amounts
or completion flags. Require READ COMMITTED before reads; retained inputs are immutable.
Take an advisory transaction lock scoped by tenant/review/algorithm, not the tenant's
business-write lock. Concurrent same-basis builds converge to one generation. Rebuild
from the existing historical inventory service (which checks retained membership hashes),
insert one row, verify its persisted count and content, then call the production domain
publication guard and install the pointer. No commit inside the service. Failure rolls
back the complete attempt with its transaction; the worker already supplies that boundary.
A savepoint makes the maintenance service atomic even if its caller catches a refusal.

The domain manifest identity here is explicitly the existing inventory review ID; it is
not a receipt CostInputManifest or a fabricated global manifest. Policy and effective
cutoff come from retained authority. Current cursor is sampled after calculation. A late
event yields a published previous basis with pending freshness; it never approves new
freight or owner decisions. No follow-up automatically invents a new review.
Replaying a valid generation validates its row checksum without recalculation and returns
its ID. Corrupt cache refuses instead of silently changing values under that ID. Operators
can delete unreferenced caches and rebuild them from the independently retained review.

## Jobs and reads

Register costing.inventory.refresh with strict review_id config in the existing registry.
Use normal owner-authorized manual jobs / disabled schedules and existing claim fencing,
retry, deadline and rollback semantics. Revalidate active owner and tenant review on each
execution; the handler calls the shared service and returns only counts and an opaque
reference. No new queue, actor-less privilege, startup migration, timer, automatic
company activation or read-triggered enqueue. This stage does not activate a schedule.

inventory_cost_snapshot is a read-only shared service for an item with optional exact
review_id or generation_id and allow_previous=False. It resolves one review/publication,
pins one generation and uses analytics/costing_relation.py's explicit tenant/generation
SQL selectable. No FIFO replay, full-tenant scan, commits, autoflush or job scheduling.
Missing cache returns uninitialized, distinguishable from a valid zero inventory. Current
reads require READ COMMITTED and sample the event cursor after the row. Pending results
appear only as basis_result unless allow_previous is explicit. Exact review/generation
requests are historical and perform no live event-cursor lookup. Mismatched/foreign
item/review/generation refuses as not found. The result includes actual cutoffs, source
review, generation/algorithm and independent unsupported carrying-value status. There is
no general aggregate/page API or adapter-local calculation in this stage.

## Migration and proofs

Migration0069 follows the existing0068 head; add only the three caches and indexes.
Downgrade may discard disposable caches but refuses while unfinished costing jobs exist.
Retained reviews/decisions never disappear. Deployment removes the registration before
schema rollback. No migration is run in normal application/worker startup.

Test first: fixture A 40 units / 420 acquisition / carrying value unknown; retained replay,
late movement pending vs historical, no recalculation/no writes on reads, foreign IDs,
corrupt input/output refusal, transaction/savepoint rollback, same-basis concurrent builds
from independent PostgreSQL sessions, worker execution/retry/stale claim/owner revocation,
migration FK shape and populated cache rollback. Existing monetary authority and review
counts must remain unchanged by a build. Full canonical T080/T081 and fixture-J budgets
remain open; 100-movement single-work execution is not a scale qualification.


## Bounded historical selection

`inventory_cost_snapshots(session, tenant_id, generation_ids)` accepts a concrete list
or tuple of 1–100 distinct nonempty string IDs. It returns `mode=historical_selection`,
`count`, `rows` sorted by generation ID, and false business/projection write flags.
Each row is exactly the existing historical single-snapshot response. Its own retained
review, policy, item, owner, currency, unit, algorithm, cutoffs and processed event cursor
remain visible. The selection is not a new generation or common authority. It carries no
combined quantities/values, live target cursor or aggregate completeness assertion.

The implementation checks tenant then loads all selected canonical rows with one joined
query, constraining every joined table to that tenant. Missing/foreign membership refuses
the entire selection with the same NotFound message; no partial answer or offending ID.
Invalid input refuses before database access. Invalid stored checksum/algorithm refuses
through the same validation as the single reader. Exact generation IDs do not follow
publication pointers, load movement members, run FIFO, enqueue jobs or autoflush.
Two SQL statements maximum independent of membership size; this does not prove fixture-J
latency or full-tenant pagination. Historical reads preserve existing transaction isolation.
No new storage, grouped-report declarations, public tool or transport is introduced.

## Complete confirmed batch publication

The exact executed inventory_batch_review action is the authority for selected membership.
The joint reader validates its typed input/output against retained review/policy rows and
one cost.reviewed event (identity, sealed sequence, knowledge time and action link).
Duplicate/missing/extra members or incompatible retained scope refuse. Independently
confirmed reviews cannot be combined by presenting a list of IDs to this reader.

The joint builder wraps the existing per-review builders in one savepoint under a
batch-action advisory lock, in stable review-ID order. It does not lock business intake.
All new publication rows become visible on outer commit. Existing valid caches may be
reused, but incomplete batches expose no total. Repeated builds return the same vector
of generation IDs; there is no fabricated aggregate generation identity or cache table.
Shared worker claim fencing and deadline apply to the whole bounded transaction.

inventory_batch_snapshot defaults to historical mode; current mode samples the live
cursor after reading all rows and requires READ COMMITTED. It pins the entire vector
of per-review publication IDs in one query, then uses the checksum-validating selection
reader. It returns action_id, generation_ids, common context, expected/available item
coverage, freshness, result/rows and separately basis_result/basis_rows. Missing caches
return uninitialized and no total; corrupt/missing pinned data refuses. Pending current
values/rows are suppressed unless allow_previous is explicit. Historical reads do not
query a live maximum. At most eight bounded SQL statements, no FIFO or retained movement
membership loads, no flush or enqueue.

A complete selected-scope acquisition total sums Decimal values in the confirmed currency;
quantities partition by base unit. Carrying value remains assessment_not_supported. This
is an inventory observation, not a received source amount, DB margin or full-company total.
No graph/report/UI surface is added in this stage.

costing.inventory.refresh config accepts exactly one of review_id or action_id. Existing
review-only serialized configs remain byte-shape compatible through model serialization,
so adding optional batch support does not change old manual-run request fingerprints.
Owner/scope authorization repeats at execution. Job output contains counts and opaque
member generation references only. No automatic schedule or company activation. Drain
batch-config runs before removing support; existing migration0069's job-name guard still
protects every run using these disposable tables.


Publication-lock refinement from the real concurrency proof: compute every missing
member through the existing retained historical reader before inserting any cache rows.
Cache inserts acquire PostgreSQL tenant FK key-share locks; therefore running subsequent
financial replay after the first insert could block intake's tenant FOR UPDATE lock.
Pass only these internally verified observations to the shared private publisher, then
publish all members in the short final phase. Existing caches need no replay. If a cache
observed present disappears before publication, refuse/retry rather than replay after
writes have started. A brief commit/publication lock is permitted; blocking intake through
financial computation is not. The test separately pauses during computation to admit late
intake and between member writes to prove readers see no partial committed publication.


## Typed SQL reporting source

analytics/costing_relation.inventory_selection_source validates and freezes 1–100 exact
IDs and returns the common generation/review/policy/snapshot join, with tenant predicates
on every table. inventory_selection_relation projects explicit flat typed columns at
snapshot grain: tenant_id, snapshot_id, generation_id, review_id, review_action_id,
policy_revision_id, item_id, owner_party_id, currency, base_unit, method, effective_at,
knowledge_at, processed_event_sequence, algorithm_version, completed_at, remaining_quantity
and acquisition_value. Money/quantity retain PostgreSQL NUMERIC(18,4), not JSON or floats.
The existing checksum-validating selection reader consumes this same join source.

Neither function follows publication pointers, consults live Item attributes or loads
movement history. Missing IDs simply do not join. The raw relation does not certify
completeness, verify checksums, authorize cross-review aggregation or manufacture a zero
for an empty set. It is internal, not a public tool or graph measure. A report must resolve
one compatible confirmed scope and protect the pinned cache rows through its aggregate
query; validating metadata and then independently querying mutable pointers is forbidden.
Inventory values remain non-additive across valuation cutoffs, quantities across units,
and money across currencies. The existing graph deferral is intentionally unchanged.
