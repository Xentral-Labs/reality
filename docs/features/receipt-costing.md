# Acquisition costs, reviewed inventory and single-line DB1/DB2

Spec 242 receipt, bounded inventory and confirmed whole-line contribution services. Repository language: English.

The shared costing service derives the known acquisition costs of a positive goods
receipt from received supplier invoice/credit amounts and explicit, confirmed owner
attribution. It returns a complete receipt cost and unit cost only after all six cost
categories have been reviewed against retained inputs. Missing costs remain unknown.
The application tools also support a bounded owner-confirmed inventory review described
below, confirmed whole-line DB1/DB2 reviews, and a separate source-backed carrying-value
assessment. The bridge does not change acquisition cost or DB1/DB2.

## Shared entrypoints

- `cost.evidence.get` / MCP `cost_evidence_get` reads the exact received net, tax,
  gross and base amounts, fingerprint and current company event sequence. A missing
  net amount is never reconstructed from gross and tax. A document with lines must
  be attributed at line scope, avoiding duplicated header totals.
- `cost.receipt.get` / MCP `cost_receipt_get` reads known cost, reviewed cost per
  evidenced base unit, category gaps and trace IDs. `manifest_id` requests the exact
  retained input membership of an earlier review.
- `cost.inventory.get` / MCP `cost_inventory_get` reads acquisition value, carrying value
  and consumption at a confirmed item cutoff. `review_id` plus
  `assessment_revision_id` requests an exact retained historical basis.
- `cost.change` / MCP `cost_change_propose` uses the existing proposal pipeline.
  `assign` records a complete new allocation revision for one received component;
  `replace` requires fresh evidence and atomically retires the predecessor;
  `withdraw` retires attribution while retaining its history; `review` records a
  disposition and reason for all six acquisition categories. `inventory_review` confirms
  the explicit policy, ownership and complete bounded history described below;
  `valuation_assessment` records an explicit source-backed write-down or recovery.

The application dispatch and MCP handlers call `services/costing.py`. Confirmation
requires an authenticated active company owner, including when general authentication
is disabled. The service rechecks membership, tenant purpose, proposal identity,
normalized input, event sequence and received fingerprint inside the transaction.
Replaying a confirmed proposal returns its original output, after renewed access checks.
Reads use `no_autoflush` and neither normalize evidence nor persist calculations.
The authenticated web-chat adapter supplies the human caller. The current HTTP MCP
transport authenticates a company token, not a human: its cost reads work, but that token
alone cannot prepare or confirm owner-only cost decisions. CLI callers without trusted
human context are likewise refused. A company token never impersonates its creator.
The MCP catalog handlers are also the shared dispatch used by authenticated web chat;
there is no new HTTP MCP identity mechanism in this slice.

## Meaning and precision

Categories are goods, inbound freight, duty, other acquisition costs, purchase
reductions and nonrecoverable input tax. Supplier source signs remain unchanged;
separate explicit economic effects make reductions subtract regardless of whether the
supplier's credit is positive or negative. Absolute allocations cannot exceed either
received amount bucket. Unassigned source remainder remains explicit.

Nonrecoverable tax is a separate share of stated tax when the selected amount excludes
it. Gross/included tax cannot receive the tax a second time. Recoverable tax embedded
in gross does not yield a complete acquisition cost. Mixed tax requires an explicit
partial stated-tax share. Nonrecoverable tax on a supplier credit follows the economic
reduction direction, for both positive and negative source-sign conventions; it cannot
increase a reduction's acquisition cost. Unsupported or unknown tax treatment prevents completion.
Quantities and source shares use Decimal with four stored decimal places. Displayed
costs use four places and unit costs six, with half-even rounding. Allocations are
explicit; this slice does not synthesize percentage allocations or round remainders.

A reviewed receipt with goods 1000, freight 100 and purchase reduction 50 has acquisition
cost 1050; at 100 units its unit cost is 10.5. Before scope review, 1050 is known cost,
not a complete actual cost. Zero/not-applicable categories require an explicit reviewed
reason. This slice admits receipts through nonzero received attributions; admission based solely on
zero-value evidence is deferred and remains unknown rather than implicitly zero.

## Retention and invalidation

Received financial components and admitted receipt quantity/unit form retained input
bases. Attribution revisions, evidence replacements, movement correction links and
scope reviews are append-only. Manual document/header or line changes are refused
once their evidence has been admitted. Use a distinct replacement document and confirm
its replacement relationship instead. Original source payloads remain unchanged.

Sealed manifests retain exact receipt, component, attribution, correction and replacement
IDs, an event cutoff, algorithm/schema versions and a membership hash. Historical reads
verify membership integrity and do not substitute newer evidence. A correction to the
receipt makes its current cost incomplete; old manifests retain the earlier answer.
Any later company input event conservatively makes the current review stale. Other cost
reviews do not invalidate it. This deliberately favors unknown over silently final costs;
more selective invalidation belongs to the later integrated valuation work.

## Scope and verification

Supported scope is a same-currency positive goods receipt in its recorded base unit,
with at most 100 contributing financial component revisions. Returns, FX conversion,
unit conversion, inventory consumption and company-wide totals are outside this slice.
There is no second scheduler, materialization registry or automatic policy activation.

Migration `0071_receipt_costing` follows the checkout's `0063` head. It creates typed
same-tenant foreign keys and refuses downgrade if any retained costing table is populated.
An empty installation can be downgraded. The prerequisite migration ordering does not
make costing depend semantically on search.

Verification is recorded in `specs/242-inventory-cost-contribution/verification-results.md`.
Focused tests cover exact arithmetic, tax, missing net, category review, later costs,
replacement/correction history, manifest integrity, rollback, foreign references,
proposal replay and demotion. Full integrated/reference workload qualification remains
a release gate before any claim that inventory valuation and DB are production-ready.

## Inventory calculation foundation

`domain/inventory_costing.py` now implements the pure consumption/remaining-stock
calculation for an already admitted, frozen single-owner/item/unit/currency pool. It
requires explicit FIFO or specific identification. It preserves original receipt and
layer-entry movement references across sales, exact customer returns and resales.
Customer return observations reverse original consumption; their positive restored
layers enter inventory at return time. Losses and supplier returns remain distinct from
sales consumption; supplier returns require exact layer selections.

Cumulative half-even rounding at four decimals preserves consumed plus remaining cost.
Unknown-cost portions retain unvalued quantities and known subtotals; zero is supported
only when the caller supplies an evidenced zero amount. Late-cost replay produces a new
immutable result without changing earlier results. This does not add zero-only admission
to the receipt service. Transfers are supported only within the supplied economic pool,
where they leave acquisition layers unchanged, not as location-level valuation.

Input is bounded at 10,000 events and 20,000 combined input/output/work portions. Bounds,
shortages and invalid references refuse the complete calculation with a stable reason.
These safety bounds are not fixture-J performance qualification. The bounded inventory
service now invokes this kernel over retained reviewed inputs only. Company-wide worker
generations, correction normalization and broader service support remain separate work.
This inventory service does not supply HGB carrying value or commercial margins;
the separate contribution service below supplies confirmed whole-line DB1.


## Confirmed inventory service

The first supported inventory scope is a complete item history through a fixed economic
cutoff, with at most 100 movements and 20 receipts, one base unit/currency and one
explicit economic owner. Supported kinds are positive receipts, owner-confirmed economic
shipment issues, transfers within that pool, explicitly classified customer/supplier
returns and confirmed outbound losses. It supports explicitly confirmed FIFO and
specific identification. Specific scopes retain exact issue, layer-entry, original receipt
and quantity portions in the confirmed action; missing, duplicate or unavailable portions
refuse instead of falling back to FIFO. Supplier returns always retain exact layer
selections. Customer returns retain the original issue, entry layer, receipt and quantity;
they restore that sales cost at return time and cannot exceed the originally consumed
portion. A physical adjustment becomes a loss only through the confirmed request, and a
settlement link never becomes cost-allocation authority. Corrected pools, opening layers,
mixed/partial ownership and implicit unit/currency conversions refuse explicitly.

An `inventory_review` proposal requires `item_id`, `owner_party_id`, an explicit `method`,
`currency`, `base_unit`, `history_start`, `effective_at`, `history_complete_from_zero`,
`receipt_cost_scopes_confirmed`, all `economic_issue_ids`, and a `receipts` entry for
every receipt with its movement ID, latest complete receipt manifest and ownership
SourceRecord. A `specific` policy additionally requires `specific_selections` covering
every issue and loss with its exact retained layer identities and quantity. FIFO permits
exact selections only for supplier returns. `customer_return_ids`, `supplier_return_ids`
and `loss_movement_ids` classify those physical facts explicitly; `return_parts` binds
each customer return to exact original sales portions.
Both completeness declarations must be true. Each declaration concerns
the supplied entire scope, not an assertion inferred from a warehouse or party name.
The normal owner confirmation, reason and expected event sequence remain mandatory.

The service enumerates the whole item history through cutoff under the tenant lock and
rejects omissions. A composite tenant/item/time/ID index supports the capped query.
It requires unique original movement.recorded events and retains their sequence for
equal-time ordering. Admission uses READ COMMITTED; an older repeatable-read snapshot
is refused. The sealed cursor includes the introducing inventory review event, while
the original validation cursor remains in the action's unchanged input.

Receipt scope reaffirmation compares each pinned receipt review with current attribution
inputs and requires its prior category review to be complete. A new cost attribution
requires a fresh receipt review first. The inventory owner then explicitly reaffirms
that exact retained cost scope at the new cursor, avoiding a silent use of stale costs.
Ownership revisions retain the confirmed Party, entire receipt quantity and exact source
evidence. Policies and ownership decisions have immutable predecessor chains.

The preview displays the resulting remaining quantity, acquisition value and consumption
before confirmation. Execution retains typed policy, movement, ownership and review
membership, with a canonical integrity hash, in the same transaction as its event/action.
No calculated inventory amount becomes a new Fact or posting. Confirmed action replay
returns its original result; normal reads use retained inputs and perform no writes.

Movement corrections use the shared append-only correction chain. The original and its
compensation cancel; an optional replacement is the only effective movement and retains
its authored economic time. Its `movement.corrected` event and exact correction identity,
members and reason are bound into the inventory review digest. A correction without a
replacement removes the original from the effective history. Classification never moves
silently from the original to a replacement, and a replacement receipt needs a new
receipt-cost review plus ownership evidence. Earlier confirmed reviews continue to replay
their frozen pre-correction inputs.

`cost.inventory.get` exposes policy version, algorithm, action/reason, owner, unit/currency,
economic cutoff, knowledge cursor and original receipt/ownership links. Later tenant
events conservatively make the latest review stale: current acquisition value, remaining
quantity, consumption, returns and remaining layers are unavailable. Explicit `basis_*` fields
retain earlier observations for explanation. Passing the exact `review_id` reproduces
that historical basis, including after a movement correction or item-unit change.
A receipt's own current review state is separate from an inventory reaffirmation; receipt
explanations follow the exact `receipt_manifest_id` returned in `receipt_sources`.

Migration 0065 follows 0064, adds five tenant-scoped authority/input tables and the capped
movement access index, and refuses populated downgrade before dropping any table/index.
The generic data-model/resource vocabulary and MCP/CLI/application tools are registered;
dedicated inventory Inspector pages and full reporting-graph measures remain future work.
No real-company policy is automatically activated and no background queue is introduced.

## Operational cost explanation

The Warehouse stock preview now reads the existing tenant-scoped `cost.query.get` boundary
for the exact item ID. It displays acquisition value and carrying value independently,
retains exact service values beside locale-rounded money, names missing evidence, shows
valuation/knowledge cutoffs and labels stale retained bases as non-current. The browser does
not recalculate cost or persist a financial conclusion. The same component supports exact
document-line contribution scopes and separates received net revenue, consumed acquisition
cost, DB1, reviewed selling costs and DB2; those order/finance entry points remain T088 work.
Every retained review links to the existing Inspector.

Since spec 279 the `cost.query.get` guidance also carries `reason_code`, ordered `steps`,
`writable` and `value_reasons`, derived at read time by `services/cost_resolution.py` and never
stored. Inventory steps are: confirm each receipt's cost (bounded by the inventory receipt
limit), prepare the item's cost review (or renew it when stale), and a company owner confirms
the waiting `tool:cost.change` proposal, which the step links by its opaque ID. Contribution
guidance names the upstream blocker from the current preview, so an unreviewed or stale item
review comes before the contribution review; selling costs affect DB2 only and never block the
DB1 path; source-data limits get a step without an action path. The fields MCP clients already
read (`stage`, `reason`, `next_action`) keep their meaning.

Fixture M remains the product acceptance protocol: five operations users unfamiliar with
the implementation open the complete demo order, state DB1 and DB2, explain one included
cost and reach its source evidence. At least four must finish correctly within two minutes
without developer help. Automated tests do not satisfy this gate.
The executable moderator script and empty result form live in
`specs/242-inventory-cost-contribution/fixture-m-usability-protocol.md`.

## Reviewed carrying-value bridge

`cost.change` operation `valuation_assessment` records an owner-confirmed, immutable
assessment of exact remaining inventory members. Each part keeps its source record,
quantity, stated total assessed value and currency. Reality does not infer a unit value,
legal policy or journal entry. A write-down starts a revision chain; a recovery must
supersede its exact predecessor and can never raise carrying value above acquisition cost.

The inventory reader derives carrying value at read time from the retained acquisition
review and selected assessment. Current reads use the latest complete verified assessment
chain and become stale after any unrelated later event. Historical reads require both the
exact `review_id` and `assessment_revision_id`; generations and captured company bases bind
those same identities and knowledge/event cutoffs. Acquisition value remains unchanged,
and contribution DB1/DB2 continues to use the commercial acquisition-cost authority.

The Inspector exposes `cost_valuation_assessment_revision` with its exact
`cost_valuation_assessment_part` children and shortest links to inventory members and
source evidence. CLI, web chat and MCP use the existing shared `cost.change`,
`cost.inventory.get` and `cost.record.get` paths. There is no automatic statutory posting
or compliance certification.

## Evidence-backed allocation and conversion

`cost.change` operations `allocate` and `selling_allocate` distribute one explicit
received amount across exact receipt or sales-line/category targets. The owner selects
`manual`, `equal` or, for receipts, admitted `quantity` weights. The shared Decimal kernel
allocates signed four-decimal amounts by largest absolute remainder and opaque target-ID
tie breaking. Preview exposes weights, shares and residual; confirmation stores the same
ordinary acquisition or selling attribution parts. No allocation driver is inferred.

Operation `conversion_basis` retains an owner-confirmed source-backed `unit` or `currency`
ratio as positive numerator and denominator with twelve decimal places. Currency
attribution keeps the original source share and derives the converted acquisition or
selling observation at read time. Exact revision identity appears in the trace and the
Inspector. Revisions must supersede the latest exact from/to scope. Conversion chains,
automatic inverse rates and current-rate lookup are unsupported. A unit basis cannot be
used as monetary authority; quantities finer than the four-decimal contract refuse.

Recoverable tax remains excluded. Nonrecoverable tax uses its independent received bucket
and cannot be included twice. A purchase reduction requires its own received component;
a payment difference alone is not skonto evidence. None of these operations posts to the
ledger or rewrites a source value.

## Commercial contribution calculation foundation

`domain/contribution.py` provides the pure commercial_v1 calculation over frozen,
disjoint matched slices. Both the current preview and confirmed contribution service
use this same kernel. The shared service establishes supported matching, completeness,
retained context and authorization before supplying reviewed inputs. The kernel itself
creates no financial authority or automatic company policy.

DB1 subtracts acquisition/direct-service cost from received matched net revenue. DB2
also subtracts direct and allocated selling costs, which remain separately visible.
Each input retains its amount, support state and evidence/review references. Evidenced
amounts contribute to known actual subtotals; only reviewed scope yields final totals.
Provisional amounts and unknown inputs never enter actual subtotals. Known DB sums only
slices jointly supporting that DB, rather than subtracting incompatible partial totals.
Thus missing selling costs can prevent final DB2 while DB1 remains complete.

Group by position/order/item/customer/channel/month, retaining missing dimensions in
an unassigned group. Currency and unit always partition output. A call requires one
explicit tenant/generation/policy/profile/effective/knowledge context and rejects mixed
contexts, duplicate identities, future economic dates and more than 10,000 slices.
Grouping preserves source slices as immutable trace. Rates use aggregate final amounts
and positive revenue, rounded half-even to four places. Empty input means no activity.

The kernel accepts signed, already matched credit/return shares; it does not allocate
credits, prove return links, infer unit conversions or resolve unmatched residuals.
HGB carrying-value changes remain separate from commercial margins. General partial
matching, historical context beyond explicitly admitted reviews, reporting/graph/UI
integration and reference-host performance qualification remain pending.

## Current contribution preview through application tools

`services.costing.contribution_preview`, application tool `cost.contribution.preview`
and MCP `cost_contribution_preview` now connect the pure calculation to current company
evidence. Input is a sales invoice document-line ID. All transports use the same service.
The read follows billed order-line -> customer-delivery commitment -> shipment, then
uses that shipment's current reviewed inventory consumption. Only an unambiguous whole
line with matching quantities, item, unit, currency, customer and economic owner qualifies.
No fuzzy item/date matching, source-total recomputation or proportional allocation occurs.

A supported scope returns `state=candidate` and `known_db1`, plus original received net
revenue, shipment consumption portions, used receipt evidence and policy/review references.
Invoice date, proposed shipment economic date and inventory cutoff remain distinct.
Current document/customer context is not advertised as retained history. Final DB1, DB2
and rates remain null: commercial matching/profile reviews and selling-cost coverage
are missing. This tool does not publish an actual finalized company margin.

Partial/multiple billing, multiple shipments, missing net, incompatible quantities or
units, credits, revised commitments and unavailable/stale inventory return explicit gaps.
Foreign references are unavailable. The service performs bounded ambiguity checks, no
business/projection writes, no autoflush, requires READ COMMITTED and refuses a changed
start/end tenant event cursor. There is no historical parameter, stored commercial match
or profile revision. Pure preview contexts likewise cannot finalize totals even when
all numerical inputs are reviewed. The separate confirmed contribution review below
provides a reviewed result for the supported whole-line candidate.

## Confirmed whole-line DB1 and retained history

An active owner can confirm `contribution_review` through the existing `cost.change`
proposal/approval path. Require the current candidate hash and event cursor, explicit
commercial_v1 profile and revenue-completeness declarations, and confirmation of revenue
recognition at the exact supported shipment time. This scope-specific profile approval
does not activate a company-wide default. Recheck authorization and inputs at execution.

`cost_revenue_match_basis` retains exact received net revenue, full quantity and source
context, bound uniquely to both invoice line and retained movement input. Neither full
quantity can be reused or silently rematched. Both invoice and billed order documents
are protected against destructive changes once admitted; general replacement/rematching
requires future support. `cost_contribution_review` retains the confirmed decision and
one exact inventory issue member. Later cost reviews can produce a new contribution
review without rewriting original revenue, old membership or earlier DB1.

Use shared `reviewed_contribution`, application `cost.contribution.get` or MCP
`cost_contribution_get` with the invoice document-line ID. Optional `review_id` selects
an exact historical review. Fixture A yields DB1 570 and 47.5%; after late freight and
renewed confirmation the current result is 540, while the original review still yields
570. Without the optional selling checklist below, DB2 and its rate remain null with
`selling_costs_unknown`. The result exposes
review/action/profile identity, reason, original invoice date, confirmed economic time,
knowledge cursor, retained revenue and the exact inventory-member/consumption trace.

Current reads require READ COMMITTED and become stale after any later tenant event;
stale DB1/rate are null while `basis_db1` labels the retained value. A newly confirmed
review includes its own event in the sealed cursor, so it is current immediately.
Its event conservatively makes the separate inventory review stale; later inventory
and contribution reaffirmations are explicit, not an automatic refresh loop. Historical
reads do not enumerate live movements or follow current mutable revenue values. Exact
identity lookups for tenant validation remain permitted. Corrupt membership digests
refuse. Reads never flush pending objects or write business/projection rows.

Static migration 0066 adds these two tenant-scoped families with composite FKs and
uniqueness. Empty rollback is supported; populated downgrade refuses before deleting
either authority table. Grouped reporting integration, partial allocations,
credits/returns, replacement/rematching and HGB assessment remain open.


## Source-backed selling expenses and reviewed DB2

`selling_assign` uses `cost.change` to attribute
received supplier net amounts to exact sales-invoice lines. Each owner-confirmed share
has a category, preserved source sign, economic charge/credit effect and direct or
allocated kind. The request explicitly confirms selling expense, excluding acquisition,
inventory purchases, already included manufacturing costs and general overhead.
Only recoverable input tax or explicitly inapplicable tax is supported here; unknown,
mixed and nonrecoverable treatment requires later support. Missing net is not calculated
from gross. Currency conversion and mixed acquisition/selling components refuse.

A new assignment is the complete replacement revision for its source component; its
shares cannot exceed the received net. `withdraw` retires the current revision. Any
component ever attributed as acquisition cost cannot also fund selling costs, and vice
versa, including after withdrawal. Receipt replacement cannot silently retire selling
evidence. Fresh replacement-evidence workflows for selling remain future work.

The optional `selling_categories` on `contribution_review` explicitly reviews all seven
commercial_v1 categories: outbound freight, fulfilment, packaging, payment fees,
marketplace commissions, sales commissions and other selling costs. Each category has
an explanation and an evidenced, confirmed-zero, not-applicable or unresolved decision.
Active costs contradict a zero/not-applicable decision. Missing evidence or unresolved
scope leaves DB2 unknown independently of DB1. The review captures all current selling
parts for this sold line, bounded to 100; assignments likewise accept at most 100 parts.

With complete selling scope, DB2 = DB1 minus direct and allocated selling costs. Fixture A
has revenue1200, consumption630, direct90 and allocated24: DB1=570, DB2=456, DB2 rate38%.
Explicitly confirmed zero with no active costs gives DB2=DB1. Known selling subtotals
remain labeled separately from final DB2 when completeness is missing. Received amounts,
allocation revision IDs, category decisions and exact historical membership are in trace.

Three new retained families (`cost_selling_attribution_part`,
`cost_selling_review_category`, `cost_selling_review_member`) reuse the existing component,
attribution and contribution-review authority. Static migration0067 adds composite tenant
FKs and uniqueness. Empty rollback works; retained rows prevent destructive downgrade.
The integrity digest includes selling membership, decisions and received component inputs;
DB1-only reviews from before this extension retain their original digest.

After another event, current DB1/DB2 and rates are unavailable; `basis_db1`/`basis_db2`
identify the retained values. Exact `review_id` reads reproduce the original calculation,
even after attribution revision, withdrawal or reassignment to another sale. Reaffirmation
explicitly refreshes inventory before the next contribution review. No refresh loop,
stored margin, dedicated UI or alternative adapter calculation was added.


## Retained cost-record inspection

`cost_record` is the shared read boundary for 24 fixed costing families and four
allowlisted evidence bridges. `cost.record.get`, MCP `cost_record_get`, CLI
`cost-record KIND ID --tenant-id TENANT`, and the existing web Inspector all use it.
The Inspector register discovers the costing families with English/German labels.

Inspection exposes retained values and shortest validated same-tenant links to received
components, documents, source records, movements and approval actions. Exact monetary
strings preserve stored precision. Action input/output is excluded. Reviews, manifests
and attribution revisions expose their exact owned members in stable pages of 25;
following a link or going back resets paging. Reads do not flush or persist data.
A retained record is explicitly not proof of current cost completeness. Grouped
reporting, reusable query context, HGB carrying-value assessment and other convergence
tasks remain open; this integration introduces no valuation rule or migration.


## Shared retained query context

`cost_query` / `cost.query.get` / MCP `cost_query_get` wrap the existing inventory and
reviewed contribution readers. CLI `cost-query inventory ITEM_ID --tenant-id TENANT_ID`
or `cost-query contribution INVOICE_LINE_ID --tenant-id TENANT_ID` uses the same service. HTTP GET `/api/tenants/{tenant_id}/cost-query` accepts
the same selectors through the shared read tool.
Optional `--review-id` selects exact history; `--effective-at`, `--knowledge-at` and
`--policy-revision-id` constrain that retained basis rather than reconstructing unsupported
history. Omitted cutoffs are explicitly unspecified. Mismatches refuse.

The response separates requested selectors from actual UTC cutoffs, review and policy
identities, inventory ownership/currency/unit, algorithm versions and input hashes.
A stable context_id identifies only this retained tenant/scope basis. Canonical generation
and profile revision IDs remain null; contribution profile approval is explicitly scoped
to its review. These independently approved single scopes cannot be summed as though
they shared company-wide authorization. Existing calculation responses and digests are
unchanged. Historical receipt reconstruction no longer reads the current event maximum.

Freshness is ready, stale, uninitialized or historical. Current reads require READ
COMMITTED and compare the retained cursor with the tenant cursor sampled after the read.
Only ready/historical responses contain result; basis_result keeps the delegated retained
answer and its evidence gaps. Historical freshness does not assess current validity.
Ready does not imply DB2 or carrying-value completeness. Queries neither flush nor write
and never enqueue work. Generalized profile authority, canonical publication and grouped
reporting remain separate work.

## Publication guard implementation status

The pure domain guard in `domain/cost_generation.py` validates whether trusted
completion facts permit a generation pointer change. It refuses unsealed or
unverified inputs, unfinished work, mismatched output counts, foreign/incompatible
contexts, obsolete builds and unexpected pointer replacements. A completed basis
behind the sampled event cursor remains `pending`; readiness is independent of
financial coverage. Exact retries return an unchanged-pointer decision.

The guard is now used by the bounded retained-inventory builder described below.
It does not make single-line approvals compatible or enable grouped cost reports.
The transactional integration verifies retained membership, obtains a scoped lock
and uses shared worker fencing. General multi-pool publication remains open. See
[the publication contract](../../specs/242-inventory-cost-contribution/contracts/generation-publication.md).

## Stored inventory review observations

The first production cache integration builds one already confirmed inventory review
through `costing.inventory.refresh` in the shared worker. The service
`costing.build_inventory_generation` validates retained input membership with the
existing historical inventory reader, writes the canonical numeric observation and
publishes it atomically. Duplicate builds converge to one generation. Failure leaves
no partial cache. Migration `0075_inventory_generations` adds only disposable caches;
confirmed review, ownership and source inputs retain their existing meaning.

`costing.inventory_cost_snapshot` reads the pinned row without FIFO replay or enqueue.
It returns actual review/cutoffs, generation and independent freshness. An absent cache
is `uninitialized`. A later tenant event makes current output `pending`; the old value
is in `basis_result`, or in `result` only with explicit `allow_previous`. Exact review
or generation selectors read history without consulting current events. Carrying value
remains unsupported. The existing `cost.query.get` API is unchanged.

This is an operator/shared-service integration for the existing 100-movement/20-receipt
item scope. It does not yet add a browser report, company-wide generation, grouped DB,
automatic rebuild scheduler or financial approval. No schedule is activated implicitly.
The complete canonical-generation scale and performance gates remain open. Storage
and tests are specified in [the integration contract](../../specs/242-inventory-cost-contribution/contracts/inventory-publication.md).


### Historical inventory selection

The shared `costing.inventory_cost_snapshots` service reads 1–100 exact stored generation
IDs in at most two SQL statements, without recalculation, writes, live freshness checks
or publication-pointer resolution. Rows retain the existing single-snapshot historical
response and their individual review/policy/cutoff basis. Missing or foreign membership
refuses the whole selection without disclosure. Independently reviewed items are not
silently summed or relabeled a common generation. This is a service foundation; grouped
reports, common multi-item capture and tool/UI exposure remain open under spec242 T080/T081.


### Joint inventory review

The existing `cost.change` / `cost_change_propose` operation `inventory_batch_review`
previews and atomically confirms 2–10 distinct whole-item scopes under one active-owner
decision. Same cutoff, economic owner and currency are required; total admission stays
within 100 movements and 20 receipts. Existing source-backed receipt reviews, ownership,
empty-opening and FIFO admission rules apply to every member. There is no new table.
One confirmed action/event records the exact selection with a common knowledge timestamp
and event cursor; each item retains its own policy and immutable review membership.
Stale input, missing/foreign evidence or a failed member refuses the whole transaction.
Stored snapshots expose the actual `review_action_id`; ordinary independent reviews
remain distinguishable from joint confirmation. This does not establish a company-wide
policy, a common published cache, aggregate DB report or automatic job schedule.

### Complete joint inventory observations

`build_inventory_batch_generation` rebuilds the exact members of one confirmed batch
within one shared transaction. `inventory_batch_snapshot` reads that action's complete
publication vector, validates its retained membership, and only then exposes an acquisition
value total in the confirmed currency. Quantities remain partitioned by base unit. Partial
cache availability is uninitialized with expected/available item counts, not a zero or
partial total. The action remains the selected-scope authority; no global generation ID
or tenant-wide completeness is invented. Historical mode is the default. Explicit current
mode requires READ COMMITTED and suppresses numbers after later events unless a previous
basis was explicitly requested. Reads are bounded to eight SQL statements with no FIFO
replay, flush or work enqueue. HGB carrying value and grouped DB remain separate work.


### Canonical SQL inventory source

The internal analytics/costing_relation module now exposes a flat, typed SELECT over
exact stored generation IDs, at one inventory snapshot per retained item-review grain.
It uses the same tenant-constrained joined source as inventory_cost_snapshots. Currency,
base unit, economic owner, cutoffs and shortest review/action/policy/item links come from
retained records; current Item metadata and publication pointers do not redefine history.
Numeric values stay NUMERIC(18,4). SQL grouping tests agree with the complete selected
batch service. The primitive does not certify completeness or allow arbitrary cross-basis
aggregation; shared admission/checksums and a protected graph execution context remain
required before exposing graph measures or Analysis Builder results.


### Joint contribution confirmation

The existing `cost.change` / `cost_change_propose` operation
`contribution_batch_review` confirms 2–10 distinct full invoice-line positions together.
Each entry in `positions` supplies its candidate hash, commercial_v1/profile and revenue
completeness confirmation, exact shipment economic time and optional selling-category
review. The action carries the common expected event sequence and reason.

All members must use one confirmed inventory action with the same cutoff, knowledge
basis, economic owner and currency; duplicate shipment bindings refuse. Units and
economic dates remain per position. Preview creates no financial authority. An active
owner must confirm; execution validates all members and rolls back the entire decision
if any member fails. Retained reviews share one event/action and knowledge timestamp.

The result names `profile_scope_action_id` and exact individual reviews. Missing selling
costs stay unknown even when another member has a complete DB2. Existing historical
member reads reproduce the decision after later intake. No company-wide profile, summed
DB, cache publication or DB report UI is implied. See the
[contribution contract](../../specs/242-inventory-cost-contribution/contracts/contribution-service.md).


### Stored historical contribution selections

`build_contribution_generation` reconstructs the exact executed joint contribution
action through the existing historical financial readers. It calculates every position
before writing caches and commits all 2–10 observations atomically. A scoped advisory
lock makes concurrent builds/retries reuse one generation. This is maintenance of
derived observations, not a worker approval of financial evidence.

`contribution_snapshot` validates exact action membership and cached input/output digest,
protects pinned cache rows through aggregation, and returns historical position values
and totals partitioned by currency and base unit. It neither replays inventory nor
flushes business writes. An absent generation is uninitialized; partial/corrupt published
output refuses. A later event does not rewrite the explicitly selected historical result.
Missing selling review remains null; known partial selling subtotals remain distinct
from reviewed DB2. Received revenue and retained dimensions are joined, never copied.

The two disposable tables are cost_contribution_generation and cost_contribution_snapshot.
They store consumed goods cost, nullable known selling subtotals and completeness; DB
amounts/rates are calculated through the same fixed SQL terms and coverage rules as
the domain kernel. The shared costing.contribution.refresh job rebuilds the selected
action with an active owner's authorization. No schedule is automatically activated.
Graph/UI and current/company-wide contribution reporting remain separate work.

### Historical contribution reports

The analysis builder now offers **Confirmed contribution**. Select one retained joint
confirmation explicitly; discovery lists metadata without promising cache readiness.
`graph.contribution_reviews.list` and `GET /analytics/graph/contribution-reviews` share
that bounded, tenant-scoped discovery. `graph.ask` admits and locks the exact complete
historical generation using `contribution_cost_context` before executing typed SQL.
It never refreshes observations or replays inventory during report reads.

The standalone `contribution_valuation` node groups confirmed positions by article,
customer, order/invoice position, channel and UTC economic date. Currency and base unit
must be grouped or pinned. DB totals are unknown for incomplete filtered populations;
known subtotals and covered/required position counts remain distinct measures. Rates
are recalculated from grouped totals with half-even precision. The editor retains the
selected action when saving and reopening, explains missing costs and links reviews
and confirmation evidence. Loaded positions do not imply complete selling costs.

This historical selection is not a current full-company margin or a carrying-value
assessment. Automatic review, broad publication/scale qualification and release gates
remain separate tasks.

Contribution reads can require unchanged knowledge through `mode: current`. This checks
the tenant business-event cursor after the final aggregate under READ COMMITTED.
Newer events conservatively make the selected scope pending; service rows/groups are
withheld and `graph.ask` refuses with `cost_basis_pending`. The selector preserves this
requirement through editing and saving. Historical mode still reads the retained basis.
The cutoff and selected positions stay fixed: readiness does not imply company-wide
coverage, today's valuation cutoff, complete DB2 inputs or a lasting freshness guarantee.
Rebuilding a cache never confirms newly arrived evidence. No new scheduling is activated.

### Internal company population guard

`domain/cost_population.py` validates a trusted builder's expected/evaluated inventory
and contribution membership before publication. Equal counts cannot hide replaced,
duplicate, omitted or stale-input subjects. Explicit unknown observations are valid
completed work and retain independent acquisition/carrying/DB1/DB2 coverage. Empty
membership has an explicit empty state and does not establish a numeric zero.

This helper has no public API, storage, numerical calculation or approval. Current discovery retention and company-aware domain publication validation are described
below. Resolved financial input retention, chunked workers and transactional company
publication are still required. Existing selected-scope reports are unchanged;
the helper alone neither certifies company coverage nor satisfies fixture-J qualification.

### Current company input discovery

The internal `costing.capture_company_cost_census` service now discovers inventory
movement subjects and sales-invoice/credit-note candidates independently of cost reviews.
A single REPEATABLE READ snapshot keeps concurrent intake consistent. Missing event
provenance, header-only documents and unresolved source interpretations remain visible;
service lines and unassessed economic dates are not silently excluded.

The builder refuses combined input overflow, performs no writes or cost calculation and
always returns publication_eligible=false. Its current record fingerprints cannot replace
retained financial inputs or establish historical line membership. Company manifests,
chunked evaluation/publication and fixture-J qualification remain outstanding.

### Company publication validation

The shared domain publication guard accepts a distinct company basis with a retained
manifest identity and exact expected-population hash. It requires matching evaluated
subjects and row counts in addition to existing integrity/work/cursor/pointer checks.
Missing money remains explicit completed work; missing subjects refuse publication.
No common item policy is fabricated. Existing selected-scope publication stays separate.

This is pure builder validation. Durable company input retention, historical financial
input resolution, transactional publication services and scale qualification are still
required; the current discovery snapshot is not an admitted historical financial manifest.

### Retained current input observations

Migration 0071 adds a dedicated current-census header and typed movement/document/line/
source members. `costing.retain_company_cost_census` captures the existing discovery in
one clean REPEATABLE READ transaction; caller owns commit/rollback. Request identity is
unique per tenant and replay returns the original verified capture. Sealed history is
protected from SQL mutation. The existing discovery endpoint remains read-only.

`company_cost_census` returns metadata; `company_cost_census_members` inspects up to 500
frozen members per page with a capture-bound cursor; `verify_company_cost_census` performs
bounded full integrity verification for builders. Reads do not flush, calculate costs or
enqueue jobs. Pages do not claim whole-capture integrity. All services are internal shared
entrypoints, with no new public chat/HTTP/MCP write surface or scheduled registration.

Later manual changes and source versions do not rewrite captured values. Retained manual
line identities cannot be removed: correct the existing line or add replacement evidence.
Migration downgrade refuses retained history. There is no automatic cleanup policy.

Capture bounds are 100,000 combined records, 1 MiB canonical data per member and 64 MiB
per capture. These bound retained output, not peak query memory or fixture-J performance.
A census still cannot supply historical financial knowledge or approved cost fingerprints;
financial input resolution and company-wide publication remain outstanding.

### Resolving captured subjects to existing reviews

`costing.resolve_company_cost_census` now resolves a verified retained census against
confirmed inventory/contribution reviews introduced by the captured event cursor. It
requires REPEATABLE READ and refuses more than ten combined items/lines before valuation.
Existing canonical readers own integrity checks and all EK/DB arithmetic.

Matching cutoff, movement membership and review cursor can yield an available_at_capture
scope result. Missing, older or incompatible reviews leave result=null; older reviewed
values remain clearly separate as basis_result. Later confirmations cannot upgrade old
captures. Missing carrying assessment or DB2 inputs remain independent of supported
acquisition cost/DB1. Header/source gaps stay visible. Cursor freshness remains conservative
except for explicitly proved contribution-only confirmations: those do not change inventory
inputs, and another line's confirmation does not change the queried contribution. Exact
executed owner-decision/event/target membership is required across a complete interval of
at most 100 events. Unknown, same-line and all other events remain invalidating. The response
retains freshness_proof event identities; this is not general affected-input invalidation.

This internal builder service writes nothing, returns no company total or common knowledge
cutoff and always sets publication_eligible=false. It does not publish or expose a new
report/tool. A retained common financial manifest, company-scale chunking and transactional
publication still need integration. See spec242 contracts/company-census-resolution.md.

### Common captured review basis

The bounded retained-census resolver also returns captured_basis: one deterministic
digest binds its verified census context, exact item/sales-candidate membership, selected
review vector, canonical result digests and gaps. Per-review knowledge times and policies
remain distinct. Acquisition, carrying, DB1 and DB2 report separate subject coverage;
unknown and stale subjects remain in the denominator. Zero counts as known, empty
coverage never invents a zero monetary total, and source/header gaps remain separate.

This read-time basis is not retained financial input authority or a company report.
It has no common historical knowledge_at, monetary totals or publication eligibility.
Existing ten-subject bounds, canonical financial readers and SELECT-only behavior remain.

### Retained captured review selection

The owner-approved three-table storage now pins captured inventory/contribution review
selection, including unknown subjects, gaps and canonical result digests. Internal
retain_captured_cost_basis, captured_cost_basis and replay_captured_cost_basis services
share the existing costing boundary. They require clean REPEATABLE READ transactions;
the caller commits retention. Retry identity binds census/version/bounds and returns the
same verified basis. Failed retention rolls back its savepoint, including when the caller
catches the error and commits unrelated work.

Sealed records cannot be updated/deleted or gain members through direct SQL. Tenant FKs
retain the census and existing reviewed input chains. Metadata reads perform no financial
calculation. Explicit replay uses pinned reviews and refuses a changed result digest; it
never selects a newer review. Unknown/stale values stay unknown rather than becoming
financial approval. Version 2 excludes lifecycle flags from the content digest; the
version-1 export verifier remains available without relabelling old digests.

Limits remain ten combined subjects, 1 MiB per canonical header/member and 8 MiB per basis.
Census verification still uses the existing bounded full-capture contract. No financial
amounts are stored as new authority, and no company publication or historical common
knowledge boundary follows from this storage. No public write adapter or job is exposed.

### Captured known subtotals

The internal `captured_cost_summary` service replays one verified retained basis and
groups its available results. Contribution groups preserve currency and base unit;
inventory groups additionally preserve owner and valuation method. Member and review
identities, canonical details, unavailable subjects and source/header gaps remain visible.
Group coverage counts available subjects only; the retained basis keeps full population
coverage, including unknown subjects.

Existing SQL contribution aggregates calculate supported row-level DB1/DB2 subtotals.
Missing goods costs cannot turn full revenue minus partial costs into a margin. Missing
selling costs leave supported DB1 intact but cannot support DB2. All final totals and
rates remain null, including when every captured member is available. A known zero with
zero covered subjects is not a completed valuation. Empty populations have no groups.

This SELECT-only, ten-subject diagnostic accepts a retained basis ID, not arbitrary
amounts or row arrays. Its internal typed SQL VALUES adapter does not extend the reporting
graph or establish a common financial context. Publication eligibility remains false;
company-wide admission, reporting integration and scale qualification remain separate.


### Fixed captured report caches

The approved four-table report slice retains disposable outputs in cost_generation,
cost_inventory_row and cost_contribution_row; cost_publication selects one sealed cache
for a service-derived captured scope. Retained basis and review history remain separate.
Internal build_captured_cost_generation uses canonical pinned replay in a clean REPEATABLE
READ transaction and verifies exact persisted content before sealing. A savepoint prevents
partial output when a caller catches a failure. Callers commit. Concurrent builders may
require a fresh-transaction retry; unique basis/algorithm identity prevents duplicate output.

Internal publish_captured_cost_generation uses READ COMMITTED, tenant serialization and
compare-and-swap. It refuses incompatible, obsolete and different equal-cursor bases.
Identical retries do not republish. Publication establishes a coherent diagnostic cache,
not financial approval; final totals/rates remain absent. Advancing live events leave a
fixed report intact while its current assessment becomes pending.

Internal captured_cost_report resolves a fixed generation, verifies at most ten cached
members and returns generation-bound pages and known subtotal groups. Reads perform no
financial input replay, autoflush, writes or enqueue. The complete retained population
coverage and header/source gaps remain separate from available-only group coverage. Each
row links to its retained member and original review metadata. Foreign identities are absent.

Internal discard_captured_cost_generation removes an entire unpublished cache only; SQL
guards preserve published output and all retained selection/evidence. Sealed rows cannot
be edited or gain members. Graph/saved-report adapters, shared-worker orchestration and
company-scale qualification remain pending. These internal services add no public report
UI and do not complete historical company financial admission.

## Drafted cost reviews (spec 282)

`cost.review.draft` (MCP `cost_review_draft`, also offered to chat) drafts the
`inventory_review` or `contribution_review` arguments that held records support, at read time
and without storing anything.

- **Contribution drafts** copy the current preview: candidate hash, economic date, event
  sequence and the fixed `commercial_v1` profile.
- **Inventory drafts** derive the following by the rules of the inventory check:
  - the owner (the party with role `company`);
  - currency, unit and history;
  - the class of every effective movement;
  - each receipt's current manifest and ownership evidence (the receipt's source, else the
    source of the document behind its goods cost).
- **Open inputs:** whatever no source states becomes an open input with catalog wording:
  - the valuation method, always asked with FIFO preselected;
  - an absent company party;
  - an incomplete receipt;
  - an opening without a stated cost;
  - customer return portions and specific selections.
- **Web path:** the web proposes through `POST /cost-review-proposals`, which re-drafts on the
  server and refuses a drifted draft with `409 draft_changed`.
- **Opening cost:** opening stock may carry `opening_cost` (the total value as its evidence
  states it, the currency and the evidence reference). It is recorded as an
  `opening_cost_statement` SourceRecord that the opening movement points to, and the draft
  copies that amount unchanged.
