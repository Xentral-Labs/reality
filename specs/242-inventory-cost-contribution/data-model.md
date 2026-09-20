# Data model boundary for the architecture experiment

Status: Phase 0 experimental shapes, not approved production tables or migrations.
The complete product schema is deliberately gated on fixture J and the architecture
review. The candidate business entities in research.md remain proposals.

## Existing authority reused

- SourceRecord/Document/DocumentLine/FinancialComponent: immutable received amounts and
  original source identity. Source sign and semantic cost sign remain distinct.
- Movement/Commitment and correction links: physical quantity, time and provenance.
- Action: future confirmed financial decisions; no experiment action grants product rights.
- ProjectionRow/ProjectionCheckpoint: current rebuildable-cache conventions; not an
  approved monetary layer ledger or a guarantee of sufficient performance.

## Disposable experiment input relations

All use opaque IDs, tenant ID and same-tenant reference validation. UTC timestamps are
separate effective and recorded times. Exact amounts and base quantities use four decimal
places; source payload strings preserve their original authored forms.

| Relation | Required experiment fields | Purpose |
|---|---|---|
| Receipt input | movement ID, item/pool ID, quantity, economic time, recorded time, source reference | Ordered cost-bearing arrival |
| Issue input | movement ID, pool ID, quantity, economic time, recorded time, sale scope or loss/transfer classification | FIFO/specific consumption input |
| Component input | component/evidence ID, received amount, currency, category, tax basis/recoverability, recorded time | Source-supported amount, not calculated EK |
| Attribution input | revision/part IDs, component ID, exact target, amount or reviewed allocation inputs, revision times | Explicit synthetic approved assignment |
| Match input | part ID, invoice-line ID, fulfilment ID, covered quantity/received amount scope, times | Prevent evidence fan-out |
| Policy input | scope/version ID, method, currency/unit, effective range | Explicit fixed policy for the experiment |
| Return input | movement ID, original issue-part reference, quantity, economic return/recorded times | New return-time layer at original consumed cost |

These relations represent the minimal retained inputs the candidate must process. The
runner must report their relation to existing benchmark records and avoid claiming a
normalized production schema has already been proved. Do not encode a generic unchecked
object-type/object-ID relationship for later application reuse.

## Derived generation candidate

Generation metadata: opaque generation ID, tenant, input watermark, effective/knowledge
cutoffs, policy and algorithm versions, state and checksum. Derived rows retain exact
scope identities, quantity, acquisition/consumed cost, revenue, DB1/DB2 and independent
coverage. They are disposable; deleting them cannot delete or change evidence.

No persisted calculated amount becomes a Fact or input to a later authoritative cost.
A generation goes building -> ready by atomic publication, or failed without replacing
the previous ready generation. Readers select one generation throughout a response.
Late evidence creates a new generation; prior manifest replay must remain possible.

## Production schema proof still required

After qualification, choose narrow typed relations for actual receipt cost assignments,
service/sale assignments, ownership, matching, policy revisions, completeness and
valuation assessments. For every field record the requirement proving repeated use,
shortest FK, tenant/uniqueness/check constraints, concurrency invariant and rollback.
Compare reuse of existing financial component revisions against a new assignment model;
existing positive cost-center shares cannot simply become signed receipt-cost shares.
Review indexed projection storage separately from retained business authority.


## Implemented experimental subset

The measured v2 namespace contains manifest, tenant, item, trade_order, movement,
component, attribution, matching, adjustment, observation, inventory_observation and
checkpoint relations. Source amounts remain unchanged; adjustment is an append-only
source-referenced delta linked to the original component. Integer identities are
synthetic opaque keys, not business numbers. Exact relation cardinalities are validated
before timing, and declared same-tenant FKs are installed/validated after bulk generation.

Movement sequence plus authored order economic date defines this regular fixture's
chronology. `knowledge_revision` bounds appended adjustments, not arbitrary historical
source changes. The complete bitemporal policy/review/ownership shapes above and full
freshness envelopes are still targets, not a claim about the current experimental schema.
No application ORM model or migration is added by these tables.


### V3 continuation

The v3 fixture adds exact original-issue references on receipt-family returns, quantity
on revenue matching parts, and an input revision on the disposable checkpoint. Split
matching aggregates before joining movements; partial/missing quantity match yields
incomplete revenue/DB rather than duplicating a cost. Partial received amounts remain
in input evidence; a full product slice relation must expose their matched and unmatched
subtotals separately. Returns expose negative COGS at return time; without matching
credit revenue their contribution remains incomplete. Explicit synthetic zero incremental
return fees do not imply that real-world missing costs are zero.

Late changes share only the short publication lock. Scoped replay uses a frozen
append-only adjustment revision, allowing new evidence to commit while it calculates. Refreshing
a different pool cannot advance the global watermark; several dirty pools conservatively
require complete replay. Production uses the fully tracked dirty-set/generation design
in contracts/product-integration.md. This deliberately simpler experimental fallback is
not the production scheduling implementation.

## Experimental staged generations (qualification only)

The disposable `costing_spike` namespace additionally holds `generation`,
`generation_range`, `generation_observation`, `generation_inventory` and
`published_generation`. Composite tenant/generation keys connect every stage to its
owner. One partial unique index permits at most one building generation per tenant.
The revision and algorithm identify a frozen derivation; the cursor identifies durable
work progress. These are disposable derived rows, never a new received-cost authority.
The published pointer changes only after all planned issue/return observations and
inventory pools exist. Indexed order/date queries join that pointer through the shortest
true tenant/generation relationship. No business document status or product schema is
introduced. Retention and general versioned source history remain production design work.

## Planned adapter-facing shapes

[Adapter delivery](contracts/adapter-delivery.md) adds no tables. It specifies proposed
in-memory request/result contracts: requested cutoffs/policy/profile/freshness; resolved
generation/algorithm/watermark; independent metric coverage and exact known subtotals;
and canonical contribution/inventory/finding relation grains. A disjoint production
contribution slice may be smaller than one movement because matching can split both
revenue and fulfilment. The issue-keyed v3 fixture must not become the production key.

Separate three identities: a saved query holds requested selectors; a generation pins
disposable calculated output; an approved financial review retains authoritative input
identities and decisions. Deleting a cache cannot destroy the ability to explain a
review. Persisted decisions, retained history and generation retention still require
concrete production schema proof and owner review before implementation.

## Concrete product model ready for review

[Production data model](contracts/production-data-model.md) is the field-level proposal.
It distinguishes eight first-slice receipt-cost table families plus manifest/member
storage from later policy, economic ownership, revenue/return matching, context history
and disposable generation tables. The document specifies target keys, conservation,
revision/withdrawal, same-tenant constraints, source/semantic signs, tax inclusion,
current/historical selection and restricted rollback.

This is a proposal, not an ORM or migration. Earlier experimental shapes retain their
status. `Movement.resolves_movement_id` is explicitly not original-sale cost provenance;
matching to the actual issue is a later typed relationship. A retained review manifest
pins authoritative inputs independently of disposable cached amounts.


## Delivered receipt foundation

The first approved production slice is documented in
`docs/features/receipt-costing.md` and the `Receipt Costing` section of
`packages/reality-core/config/data_model.yaml`. Migration 0064 contains the typed
receipt/component/correction admissions, signed allocation revisions and parts,
replacement links, six-category reviews and exact retained manifest memberships.
Received financial components remain the original amount authority; no calculated
EK, inventory value or DB result is stored as a new business authority.

Current unit admission copies the Movement quantity and the Item base unit at the
explicit costing admission. No source-unit conversion is inferred. Receipts supported only by zero-value evidence
have no admission command in this slice and remain unknown. These bounds
must not be advertised as complete inventory valuation or as all-spec acceptance.

## Production inventory calculation values

`domain/inventory_costing.py` adds immutable calculation inputs/outputs only, no tables.
`InventoryEvent` identifies an admitted movement with UTC economic time and retained
sequence, positive base quantity, explicit kind and optional receipt acquisition cost.
`Selection` references a layer by its entry Movement and original receipt Movement;
`ReturnPart` additionally references the exact original sales issue. These references
are calculation inputs, not new authoritative relationships or unverified database FKs.

`CostPortion` preserves those original identities in consumption and remaining stock.
`Consumption` separates outbound kinds and signed customer-return reversals, known cost,
complete cost and unvalued quantity. `InventoryResult` is disposable and immutable.
No carrying value, policy approval, ownership assertion or knowledge cursor is inferred.
The future service must resolve those authorities and normalize corrections before
supplying a complete frozen pool. Derived layer identity never replaces an authority FK.

## Reviewed inventory service authority

The bounded service implements `cost_policy_revision`, `cost_movement_basis`,
`cost_ownership_revision`, `cost_inventory_review` and `cost_inventory_member` as specified
in contracts/inventory-service.md. Same-tenant composite references link existing Item,
Party, Movement, SourceRecord, BusinessEvent, Action, receipt bases and exact receipt
manifests. No amount column is introduced for a derived stock or consumption value.

Original movement-event sequence supplies stable ordering; the distinct introducing
inventory event establishes admission knowledge. The review's sealed cursor includes
all newly retained decisions. Canonical hash encoding normalizes equivalent Decimal and
UTC timestamp representations across a database round trip without altering received
values. A composite Movement tenant/item/economic-time/ID index supports bounded admission.

Every review creates a policy successor and full-quantity receipt ownership successors.
Retained history reads select exact members rather than latest policy/evidence pointers.
Specific/return matching, correction normalization, partial owners and carrying-value
assessments remain unimplemented service families, not implicit default interpretations.

## Reviewed carrying-value assessment

The assessment authority adds only two tenant-scoped records. The immutable revision
header references one exact `CostInventoryReview`, its optional unique predecessor, the
kind (`write_down` or `recovery`), effective and knowledge cutoffs, target event sequence,
action/event audit, reason, schema version and content hash. It does not repeat policy,
item, owner, currency or unit because the inventory review already owns that context.

Each immutable part references its revision, one exact remaining `CostInventoryMember`
and one evidence `SourceRecord`. It records positive assessed quantity, matching currency
and the source-stated total assessed value for that quantity. A unit value is derived for
display only. Domain/service validation proves non-overlap, remaining membership, exact
predecessor scope, write-down direction and recovery bounded by the frozen acquisition
cost. Carrying totals and adjustments remain read-time observations.

## Contribution foundation types (no persisted schema)

ContributionContext fixes tenant, generation, policy/profile revision, commercial_v1
and effective/knowledge cutoffs. MatchedSlice retains opaque slice/dimension identities,
economic date, currency/unit, signed matched quantity and four independent evidence
inputs: revenue, goods/direct-service cost, direct selling cost and allocated selling
cost. ContributionInput retains amount, support state and bounded basis references.
Frozen outputs preserve input slices, independent required/covered/evidenced/provisional
counters, known actual subtotals, optional final totals and aggregate rates. None of
these output types is financial authority or a new database table.

## Current contribution preview (no new schema)

ContributionContext adds explicit preview mode with absent generation/profile revision
identities. Reviewed mode still requires both identities. Preview output is non-authoritative
and cannot finalize amounts or rates. Existing DocumentLine.billed_document_line_id,
Commitment.document_line_id and Movement.commitment_id form the shortest current path;
no duplicated links or commercial match table are introduced in this read-only stage.

## Confirmed contribution storage

See contracts/contribution-service.md for the two typed admitted-basis/review families,
shortest-link proof, uniqueness, immutable context and static migration 0066. No derived
margin or consumption amount is stored; no global profile is activated.

## Selling decisions and DB2 membership

See contracts/selling-service.md. Add cost_selling_attribution_part linked to the
existing cost_attribution_revision and sold document_line; cost_selling_review_category
and cost_selling_review_member link decisions/exact parts to cost_contribution_review.
No persisted calculated cost or margin; existing component basis owns received evidence.


## Production inventory cache refinement (T080)

See contracts/inventory-publication.md for three disposable relations:
cost_inventory_generation (typed retained review, algorithm/completion/output digest),
cost_inventory_snapshot (one typed quantity/acquisition observation per generation),
cost_inventory_publication (atomic same-review generation pointer). All tenant scoped
with composite same-tenant links. No source values or financial decisions are duplicated;
review membership survives cache deletion. No generalized manifest/profile is invented.


### Joint inventory confirmation without schema expansion

A bounded inventory_batch_review reuses existing CostInventoryReview.action_id and
introduced_event_id links for exact selected-item membership. Every member references
the one confirmed action and cost.reviewed event, with identical effective_at,
knowledge_at and target_event_sequence; policy IDs remain per-item. The action retains
the exact typed input and result. No batch financial table or inferred company policy.
Existing caches remain independently keyed by retained review; joint admission alone
must not be called atomic multi-item cache publication. Context inspection exposes the
actual review_action_id, including for independent single-item reviews.


## Joint contribution cache refinement (T141–T144)

Approved production cache design specialized to one bounded executed joint action:
`cost_contribution_generation` -> existing action; `cost_contribution_snapshot` ->
generation and existing contribution review. Unique tenant/action/algorithm and
tenant/generation/review prevent duplicate publication and grain. All links include
tenant. Three NUMERIC(18,4) derived cost columns and selling_complete support ordinary
SQL aggregation; amounts may be signed for selling reductions. Goods cost is nonnegative
for currently admitted whole positive shipments. Received revenue and dimensions are
joined through review -> revenue basis, not duplicated. No DB/rate column, generic
JSON result population or separate publication pointer. These two disposable tables
can be deleted and rebuilt independently of financial authority; unfinished worker
runs block migration downgrade.

Selling subtotals are nullable together when no selling review exists. A completeness
CHECK requires nonnull subtotals for selling_complete; absent review is never coerced
to a zero cache value. Partial reviews retain known subtotals without final DB2.

## Company population closure (domain only)

PopulationBasis freezes tenant, valuation/knowledge cutoffs, committed event watermark
and the existing inventory/commercial algorithm versions. Separate expected inventory
items and contribution document lines carry canonical per-subject input fingerprints.
Evaluated counterparts retain exact keys/fingerprints plus independent known/unknown
support states. No amounts, policy authority or database tables are added. Population
closure refuses incomplete/duplicate/extra/stale membership and returns independent
coverage, including explicit empty state. Fingerprints do not replace retaining inputs.

The future company manifest must retain actual source/evidence membership and per-subject
policy/review revisions. The existing GenerationBasis requires one policy revision and
must be extended with a reviewed company-manifest variant; do not fabricate one revision
or concatenate unrelated batch IDs. No company publication has been implemented here.


## Retained current company discovery (owner-approved, migration 0071)

CostCompanyCensus retains the current observation context and request retry identity;
CostCompanyCensusMovement/Document/Line/Source retain typed membership and exact observed
mutable values or immutable source references. The line member references the frozen
header in the same census. Every FK is tenant-scoped; retained source identities cannot
be deleted. Sealed census rows and members have SQL mutation guards. No knowledge_at,
policy, approved financial amount or publication pointer is invented. Details and rollback
restrictions: contracts/company-census-retention.md. This is observation retention, not
CostInputManifest financial admission. Cash/EK/DB are not calculated by this storage.

## Captured review selection retention — approved continuation

The owner approved the distinct three-table captured-selection model on 2026-09-19.
Migration 0072 implements cost_captured_basis, cost_captured_inventory_basis and
cost_captured_contribution_basis as specified in contracts/captured-basis-retention.md.
Typed same-tenant census/subject/review links preserve existing authority; versioned
JSONB holds only review-vector, coverage/gap and integrity metadata, not derived money.
This is separate from both the five-table current census and historical financial inputs.


### Approved fixed captured report caches

Owner approval on 2026-09-19 authorizes cost_generation, cost_inventory_row,
cost_contribution_row and cost_publication under contracts/captured-report-publication.md.
Migration 0073 follows 0072. Generation -> captured basis -> census/review membership is
the authority path; monetary rows are disposable observations. Typed member links prevent
foreign-basis mixing, SQL sealing protects rows and an unpublished whole-cache deletion
retains all input authority. No new historical knowledge_at or financial approval record.

## Financial company manifest and generation — owner approved

`cost_company_manifest` plus typed inventory/contribution input members retain the exact
company population, actual committed event cursor/knowledge time, per-subject approved
review/input fingerprint and exact unresolved header/source gap counts with a canonical
gap digest. `cost_company_generation` plus typed result members form a
disposable complete evaluation by referencing existing verified per-review generations or
an explicit unknown state. `cost_company_publication` is a scope-keyed atomic pointer.

This seven-table family is defined in contracts/company-generation-publication.md and was
approved for migration and internal implementation on 2026-09-19. It remains distinct from
current census observation, captured review selection and diagnostic captured-report
publication.
