# Concept: actual acquisition cost, inventory value and DB1/DB2

Status: proposed architecture and product semantics for review, 2026-09-18.
This is not the implementation plan or an implemented feature contract.

## 1. The decision

Build one evidenced cost basis and reuse it for inventory and contribution reporting.
Do not add a mutable "actual purchase price" to Item, and do not derive margins from
gross operational ledger counterparts. Every result answers: amount for which quantity,
according to which method, based on what evidence, known at which time, with what gaps?

"Actual" means based on evidenced acquisition costs. With fungible goods it still
depends on a disclosed consumption convention. "Reviewed complete" means complete
for an explicit scope and knowledge cutoff, not immune to later information.

## 2. Baseline audit

| Existing foundation | Reuse | Missing capability |
|---|---|---|
| SourceRecord and versioned evidence | Lossless supplier invoices, freight, credits, assessments | Supported interpretation of cost semantics and attribution |
| DocumentLine, billed_document_line_id | Exact invoice-to-order evidence | Match invoice quantities to individual receipts/fulfilments where ambiguous |
| FinancialComponent | Received net/tax/gross/base amounts | Determine evidenced acquisition-cost basis without inferring missing net |
| Movement, Commitment, lots, serials, corrections | Quantity, operational provenance, physical identity | Monetary cost attribution, economic scope and consumption method |
| ComponentAssignment and cost centers | Keep responsibility classification | Cost center is not a receipt/order cost target or valuation policy |
| PriceListEntry and agreed line price | Separately labeled purchase estimate/comparison | No proof of actual historical acquisition cost |
| LedgerEntry | Preserve cash, claims and operational balances | Not a net revenue, inventory or expense ledger |
| Shared reporting/projection infrastructure | Add derived measures through shared services | Cost coverage, historical valuation and additive contribution grain |

Evidence: `packages/reality-core/src/reality/db/core.py` (DocumentLine, Movement,
PriceListEntry, LedgerEntry), `packages/reality-core/src/reality/db/components.py`,
`packages/reality-core/src/reality/services/finance/components.py`,
`packages/reality-core/src/reality/services/analytics/inventory_relation.py`,
`packages/reality-core/config/reporting_graph.yaml`, and
`packages/reality-core/config/operational_exception_catalog.yaml` (`sold_below_purchase_price`). The latter
explicitly compares agreed prices and excludes freight, duty and inventory valuation;
it must retain that meaning rather than being silently relabeled as DB.

## 3. Five different prices/values

| Name | Meaning | Authority |
|---|---|---|
| Agreed purchase price | Supplier agreement or price list | Received evidence |
| Actual acquisition unit cost | Allocated acquisition cost / attributable base quantity | Derived observation with coverage |
| Estimated acquisition unit cost | Explicit forecast using agreed price and estimates | Separate provisional observation |
| Historical inventory cost | Unconsumed acquisition cost under the selected method | Derived observation |
| HGB carrying value | Historical cost adjusted by supported valuation judgments | Derived observation; judgments retain evidence |

For purchased goods, start with a received applicable purchase amount, subtract
attributable price reductions and add attributable acquisition expenses. Input tax
recoverability must be supplied/classified; no default gross-minus-tax reconstruction
and no double addition of tax already in the selected basis. Production has a distinct
manufacturing-cost basis and must not be mislabeled as purchased EK.

The received amount is authoritative; derived unit cost is an explanatory division.
Rounding belongs to the derivation and never rewrites the supplier's stated unit price
or total. Zero cost requires evidence or an explicit justified declaration.

## 4. Evidence and attribution, not a second document system

The conceptual flow is:

    SourceRecord -> Document/DocumentLine -> FinancialComponent
                                               |
                                      confirmed cost attribution
                                               |
                           receipt Movement / delivered service / sales target
                                               |
                         shared cost, valuation and contribution observations

A receipt Movement already reaches its purchase commitment and evidence. Preserve
that path. Add only the missing relationship between a cost component and the exact
quantity/target it pays for. Two invoice lines for the same SKU are never matched by
SKU, description, partner or nearby dates alone.

Candidate domain records, subject to the later schema proof:

| Candidate | Why existing records cannot express it | Minimal business content |
|---|---|---|
| Cost attribution revision and parts | Cost-center shares do not identify consumed inventory/order costs | Component identity, category, selected basis, signed amount/quantity, typed target, reason, actor/action, supersession |
| Valuation policy revision | Price-list direction is not a valuation method | Tenant/item scope, method, functional currency, time/unit rules, effective date, approved version |
| Economic attribution assertion | A warehouse location does not establish whose inventory it is | Exact quantity scope, economic owner, effective time and supporting evidence |
| Cost scope review | No current record states that all expected costs were considered | Target scope, required categories, explicit exclusions, evidence watermark, reviewer and revision |
| Valuation assessment | Physical write-off is not a monetary impairment | Exact stock scope, cutoff, stated supported value/reason and evidence |
| Reproducible review manifest | A mutable current result cannot explain a prior review | Scope, input identities/watermarks, cutoffs, policy/algorithm versions and approving action |

These are candidates, not six mandatory new generic tables. Use narrow typed links
and same-tenant constraints; reject a free-form polymorphic object registry. Initially
receipt and sales fulfilment/position targets suffice. Reuse Action for approval and
source-backed Evidence/Fact only when their existing semantics genuinely fit.
Do not store a computed FIFO layer balance, unit cost or DB as an authoritative Fact.
Derived layers/consumption parts can be reconstructed; an existing rebuildable projection
may accelerate reads under its established contract.

An existing cost-center allocation and a new cost attribution may describe the same
component along different dimensions. They are not two expenses. Classification,
economic use and cost responsibility must remain distinct.

## 5. Acquisition costs and allocation rules

The initial closed category set is goods purchase, inbound freight, import duty,
other reviewed acquisition cost, acquisition reduction, outbound freight, fulfilment,
packaging consumed for sale, payment fee, marketplace commission, sales commission,
return handling, direct purchased service, and unclassified. Categories select only
their reviewed allowed treatment; an arbitrary source account/name cannot decide it.

Every source component has a selected exclusive amount basis for a cost use. Where
header and line values both describe the same amount, choose one authoritative grain
and reconcile the other; never sum them together. A credit preserves its source sign
and uses an explicit semantic sign for the calculation, avoiding double negation.

One freight invoice may cover many receipts. A confirmed allocation can use stated
amounts, quantity, evidenced weight or evidenced value. Retain the rule and its input
scope; derive shares on read without promoting calculated shares to source evidence.
Explicit human-assigned amounts remain decisions, with actor and reason. Freeze the
allocation inputs to a reviewed version so later receipts do not change old splits.

Use exact decimal arithmetic under spec FR-022. Allocate at 0.0001 currency-unit
precision using largest absolute remainders with stable target-ID tie breaking and
restore the sign for reductions; assigned parts plus the visible
remainder must equal the selected source amount exactly. Unit-cost displays may round,
but valuation operates on cost totals/quantities rather than multiplying rounded labels.
Sequential consumption uses cumulative half-even rounding at four decimals. For layer
cost C, quantity Q and cumulative consumed quantity q, cumulative cost is round(C*q/Q);
the next issue gets the difference from the previous cumulative cost. Remaining cost
is C minus that cumulative amount. For C=1 and Q=3, three unit issues receive 0.3333,
0.3334 and 0.3333. Compute before filtering/grouping, never restart rounding inside a
report. Late cost evidence recalculates the sequence at its new knowledge cutoff.
A returned quantity retains its attributed share of the original issue cost; derive a
new return layer from that cost and quantity, rather than rewinding earlier issues.

Do not infer a volume rebate or expected skonto from a payment difference. Once evidenced,
attribute it to its purchase scope and redistribute the cost delta consistently across
remaining and consumed quantities. A supplier invoice arriving before receipt stays
unmatched acquisition evidence; it does not create physical or economically owned stock.

## 6. Valuation scope and movement semantics

Proposed first method: FIFO for interchangeable purchased goods; specific identification
where a reliable serial/individual identity and corresponding cost evidence exist.
The company must explicitly adopt an appropriate policy. Weighted average and LIFO
are separate later algorithms, not aliases or automatic fallbacks.

Proposed pool: tenant + item + economic ownership + base unit + valuation currency,
across ordinary locations. Physical lot/serial controls still constrain actual goods
movement; a physical lot is not automatically a FIFO cost layer. Location reports are
secondary views reconciled to the common valuation pool. Specific identification uses
the evidenced identity rather than a pooled consumption assumption.

- Receipts contribute quantity and cost basis; late cost evidence enriches their basis.
- Sales consume cost according to the selected method when economic fulfilment is
  established. Physical shipping alone is not universal evidence of ownership transfer.
- Transfers carry cost without creating purchase, revenue, or company-level consumption.
- Reservations change availability, never inventory ownership or value.
- Supplier returns remove the corresponding quantity/cost; credit differences are
  separately explained. Customer returns restore evidenced original consumed cost only
  for the quantity economically returned. The return layer enters FIFO at economic return
  time, not original purchase time, so past issues remain unchanged. Specific identification
  follows the actual item. Damage/impairment is a separate assessment.
- Loss and inventory adjustments affect stock and a separate loss bridge, not fabricated
  customer sales. Correction relations cancel/replace valuation effects consistently.
- Opening stock requires both quantity and cost evidence. FIFO needs surviving layers
  or a reviewed, explicitly labeled opening valuation assumption; quantity alone is not enough.
- Negative stock, incompatible units or uncertain ordering prevent complete valuation.
  Stable technical sorting ensures replay but never proves an unknown business sequence.

Base-unit conversions require a received or explicitly reviewed ratio with effective
scope. FX needs evidenced original/functional amount or an approved dated rate and rule;
no live rate silently changes history. Settlement FX is separate from historical inventory
cost. Inputs lacking the basis remain unconverted and cannot enter a combined total.

Consignment, third-party stock, goods in transit and drop shipping require economic
attribution evidence. Do not create fake warehouse movements to accommodate a cost.
Shipments whose economic transfer basis is unknown remain visible reconciliation items.

## 7. Time, late invoices and what complete means

Every result has an effective cutoff (business scope) and knowledge cutoff (which
recorded evidence/decisions were available), plus method and algorithm versions.
Track recorded time for every new input/revision; legacy inputs without adequate history
must report that an earlier knowledge view cannot be reconstructed.

A late EUR 100 freight invoice for 100 units, 60 already sold, adds EUR 40 to remaining
cost and EUR 60 to consumed cost under that receipt's allocation. The current sale cohort
margin changes by EUR 60. An earlier review still reproduces the old result; the change
view explains the new evidence and affected scopes. Do not silently restate a reviewed
statutory period or post a journal adjustment. Accounting treatment is a separate decision.

Use independent coverage dimensions, not one persistent financial status on a document:

1. Unknown: quantity, amount, allocation, attribution or policy is missing/conflicting.
2. Provisional: a declared estimate exists, shown separately from actual evidence.
3. Evidenced: the included inputs are supported; completeness is not yet confirmed.
4. Reviewed complete at cutoff: all declared required categories and quantities are
   accounted for, with explicit zero/not-applicable decisions and no blocking gaps.

Reviews define expected cost categories by business scope. A missing freight invoice
cannot become zero merely because the other invoices arrived. New relevant evidence
supersedes current completeness and requires renewed review. DB1 may be complete while
DB2 remains incomplete. Show valued/unvalued quantity and matched/unmatched revenue;
never assign unknown cost a fabricated monetary coverage percentage.

## 8. Contribution margins and recognition

Proposed named/versioned profile: Commercial contribution v1.

    Net revenue = received attributable net sales amounts
                  - semantic effect of credits/discounts not already included
    DB1 = Net revenue - matched acquisition cost/direct purchased service cost
    DB2 = DB1 - attributable selling and fulfilment costs
    DB% = DB / Net revenue * 100, only where Net revenue > 0

Include charged shipping revenue once with its actual classification. Include payment
fees as separate costs; a payment provider's net payout is not sales revenue. Exclude
recoverable sales tax, inventory impairments, general overhead, settlement FX and
income taxes from this commercial profile, showing relevant bridges separately.
Inbound freight capitalized in acquisition cost must never be subtracted again in DB2.
Packaging purchased as inventory enters DB2 only when consumed for fulfilment, not again
when purchased. Direct production costs included in an evidenced manufacturing cost
cannot also enter DB2. DB2 after product-fixed costs requires a separately named profile.

Canonical report grain is an evidenced matched revenue/fulfilment slice. Use existing
invoice-to-order and movement-to-commitment links where unambiguous. For multiple
shipments/invoices/returns, require an explicit matching decision or approved deterministic
quantity allocation; retain the decision/rule, not an invented factual relationship.
Allocate a stated invoice-line net total over covered quantities only as a labeled
derived split; never recalculate or replace the received invoice-line total.

The initial period report uses matched economic fulfilment date, with invoice date
available as a separate evidence filter. An economic date must be evidenced or reviewed;
unknown dates remain outside finalized period contribution. Late invoices can complete
earlier fulfilment cohorts in a current-knowledge view. Unbilled deliveries retain cost
in an unmatched bridge, billed-but-unfulfilled amounts remain unmatched revenue, and
neither is labeled final DB. Pre-sale quotation margin is a separate forecast.

Commercial credit-only adjustments change revenue without inventing stock returns.
Physical/economic returns change goods cost according to their linked original sale;
cash refunds do not independently change revenue or cost again. Return processing and
damaged-return loss remain visible. A credit without known sale scope is unassigned.

All dimensions group the same atomic contributions. Order/customer/channel are obtained
through shortest true sale links; product through evidenced line/fulfilment identity.
Retain transaction-time dimension meaning and separate historical from current labels.
Do not sum order-level costs once per line. Unassigned costs remain in company totals
and an explicit unassigned bucket; product totals plus that bucket reconcile to company.
Supplier and cost center can be additional cost-analysis dimensions but do not imply
an automatically meaningful sales-margin dimension.

## 9. Coverage beyond simple trade

| Business case | Treatment |
|---|---|
| Ordinary purchased goods | Full target path: receipt costs, consumption, DB1/DB2 |
| Drop shipping | Evidence-backed economic purchase/sale matching; no fake stock |
| Purchased service/resale service | Direct received service cost matched to sale; no stock valuation |
| Bundles/kits | Evidenced component fulfilment and reviewed revenue allocation; missing components block completeness |
| Externally supplied manufactured cost | Preserve received cost and basis/version; expose external origin and scope |
| Internal manufacture/WIP | Explicitly unsupported until production quantities, consumption and manufacturing-cost rules are specified |
| Own labor/projects/subscriptions | Only evidenced direct cost within defined scope; no assumed zero labor or generic profitability claim |
| General overhead/brand advertising | Separate period cost unless an explicit reviewed allocation profile exists; not quietly assigned to orders |

External valuation imports use the same provenance and scope rules. An externally
stated aggregate inventory value can be displayed and reconciled, but cannot manufacture
per-order consumed cost. Locally derived and externally stated values are compared only
for like-for-like scope; they are never added or averaged into a hybrid authority.

## 10. HGB boundary and carrying-value bridge

HGB does not define DB1/DB2 and does not impose one universal FIFO method. The following
primary sources informed this design (checked 2026-09-18):

- [Section 255](https://www.gesetze-im-internet.de/hgb/__255.html): acquisition expenses,
  attributable incidental costs and reductions; manufacturing costs are a distinct basis.
- [Section 252](https://www.gesetze-im-internet.de/hgb/__252.html): individual valuation,
  prudence, period attribution and continuity of valuation methods.
- [Section 240(4)](https://www.gesetze-im-internet.de/hgb/__240.html): weighted-average
  group valuation under its conditions.
- [Section 256](https://www.gesetze-im-internet.de/hgb/__256.html): permitted consumption
  assumptions for qualifying interchangeable inventory, subject to proper accounting.
- [Section 253(4–5)](https://www.gesetze-im-internet.de/hgb/__253.html): lower-value
  assessment for current assets and reversal when the relevant grounds no longer exist.
- [Section 246](https://www.gesetze-im-internet.de/hgb/__246.html): economic attribution.

Model historical acquisition cost and carrying value separately. A supported impairment
assessment needs quantity scope, date, stated market/attributable value, evidence and
reviewer. Do not automatically interpret age or expiry as a legally correct percentage.
Recovery cannot exceed the applicable historical-cost ceiling. On subsequent disposal,
reconcile commercial acquisition-cost consumption with carrying-value consumption and
release of related adjustments so impairment is not charged twice.

The output is a traceable valuation schedule for accounting review. Complete financial
statements, postings and assurance of legal compliance remain outside this concept.

## 11. Product experience and shared services

Inventory adds quantity, valued quantity, unknown quantity, acquisition value, carrying
value, method and gaps. Item detail exposes receipt costs and remaining cost layers.
Order detail shows net revenue -> goods/direct cost -> DB1 -> selling costs -> DB2,
with actual/estimate distinction and completeness. Finance exposes cost evidence,
unassigned amounts, pending completeness reviews and valuation assessments.

Every amount opens the same explanation: included components and quantities, excluded
scope, formula, method, cutoffs, assignment decisions and source payload links. Reports
and exports carry method, currency, time basis and coverage. Unknown is never a green
zero. A dashboard subtotal over known costs must say partial and cannot be styled as
total profit. Filters apply before totals and all grouping respects exact grain.

Future implementation order is domain rules -> shared services -> tools -> adapters.
CLI, MCP/chat, web and reporting call these services. Confirmation previews show the
affected quantities, allocations and cost/margin delta, then revalidate against the same
input revision. PostgreSQL constraints and serialization guard concurrent assignments;
Decimal handles money and quantities. No browser-side formulas or direct ORM chat writes.
New recurring materialization, if proven necessary, follows the existing scheduler/
worker contract; no new timer or queue is proposed. Catalog changes trigger generated
Tool Usage documentation and resource/translation registration.

## 12. Delivery order and approval boundaries

| Slice | Outcome | Requirements | Release gate |
|---|---|---|---|
| 0. Costing spike | Thin end-to-end cost read against the benchmark fixture; architecture decision on live derivation versus projection | FR-018 | Fixture J budgets, including the Exceptions queue and chat answers. A failure here revises the architecture before any slice is planned |
| 1. Evidence and actual receipt cost | Costs, categories, allocations, tax and cash-discount basis, explicit gaps; the three cost-gap exception classes | FR-001 to FR-003, FR-016, FR-019 to FR-023, FR-025 (gap classes), FR-027 | Fixtures A, F, H, I, K and the gap half of L; no inventory or DB completeness claim yet |
| 2. Inventory acquisition valuation | Opening basis, FIFO/specific identification, economic scope, corrections and returns | FR-004 to FR-008, FR-014, FR-015 | B, C, D, G; quantity/value conservation and replay |
| 3. Commercial margins | Matched revenue/cost, DB1/DB2, measures in the existing Analysis Builder, negative-DB1 class, canonical demo chain | FR-010 to FR-013, FR-017, FR-024, FR-025 (negative DB1), FR-026 | A, E, F, H, L, M; no fan-out or missing-cost zero |
| 4. Reviewed HGB schedules | Assessments, carrying-value bridge, completeness and historical reviews | FR-009, FR-015 | D, G, I and company accounting policy review |
| 5. Additional algorithms/industries | Average cost/LIFO or internal production only where separately specified | - | Dedicated requirements and independently verified numerical fixtures |

Authorization (FR-019), record references on every surface (FR-027) and the FR-018
budgets are not a late slice: they hold from the first release, which is why the
authorization story is P1 while scale and integration are P2. Each slice updates the
canonical demo rather than waiting for slice 3 to introduce costs into it.

All slices inherit provenance, tenancy and service constraints from day one. A company
that requires another method cannot be migrated to FIFO for convenience. Existing
data remains usable with explicit gaps; do not backfill current price lists as historical
actual cost. Activation is tenant-scoped after evidence/policy review. Disabling the
feature leaves original evidence and operational behavior intact.

No implementation-ready plan/tasks or schema are claimed here. The feature branch is
`242-inventory-cost-contribution`, based on `origin/main`; unrelated Inbox commits
remain outside this feature history. Next, review this concrete
scope, then create the technical plan with Constitution Check, data-model proof, tests,
performance limits, migration/rollback and traceable tasks; analyze before implementation.
The main schema tradeoff to prove is which precise cost/matching/ownership decisions
need new typed relations rather than existing evidence. Calculated values themselves
must remain derived observations, not a second accounting authority.

## 13. Constitution compatibility review

This is a concept-level review, not the mandatory technical plan Constitution Check.

| Principle | Design response | Proof still required in planning |
|---|---|---|
| I. Source, Evidence, Reality | Cost inputs retain their evidence; attribution is a reviewed decision | Exact intake and source trails for every supported category |
| II. Reality authority | Quantities remain movement-derived; completeness is a cost-scope observation | No document financial/fulfilment status or duplicated operational state |
| III. Proven schema | Candidate records each answer a named missing business relationship | Minimal typed schema, alternatives and concrete scenario per field |
| IV. Tenant/service boundaries | Shared services, same-tenant links and confirmed mutation | Constraints, locks and adapter parity tests |
| V. Specification and tests | Requirements and independent numeric fixtures precede code | Owner scope review, plan, tasks, analysis and failing-first proofs |
| VI. Explainable product | Each amount discloses evidence, method and missing scope | Inspector and operational page acceptance tests |
| VII. Simplicity/storage | Existing PostgreSQL/projection architecture; no new queue or generic engine | Bounded replay, decimal precision, indexes and migration/rollback design |
| VIII. Received values | Supplier amounts unchanged; local valuation/DB is a derived observation | No computed authority, round-trip source tests and reproducible manifests |

The approach deliberately proposes an analytical valuation capability, not a local
authoritative accounting posting engine. If a later requirement asks Reality to issue
statutory valuation postings or own an externally responsible figure, that requires a
separate reviewed authority decision before extending this design.


## 14. Review revisions: performance, integration and authority

The first draft left performance feasibility to implementation. FR-018 and fixture J
now make it an architecture acceptance gate: no interactive full-history replay.
Derived-on-read describes authority, not permission for an unbounded calculation.
Reuse spec 179's rebuildable projections when required, with atomic publication,
input/policy/algorithm watermarks and existing scheduled workers. Read requests never
start a missing projection rebuild. Stale output is visibly stale; tools requiring
live consistency calculate within a bound or return not-ready. Cache values cannot
approve costs or replace evidence. Review manifests and projections are distinct.

Use the existing reporting graph/Analysis Builder and saved reports (224/228/229/232).
Declare service measures and their currency, unit, temporal and grain restrictions in
`packages/reality-core/config/reporting_graph.yaml`; no raw sum of cost evidence can
stand in for DB. Operational pages consume the same service outputs. Inventory values
are point-in-time measures, DB amounts aggregate over disjoint slices, and ratios are
recomputed from totals. Existing reports are not reinterpreted. The canonical glossary
in spec FR-023 governs catalog and UI labels, including German ERP labels.

Cost gaps are both coverage information and cataloged operational findings. The former
explains the amount; the latter routes work through existing Exceptions and the spec 178
Rules register. They share derivation/scope/freshness rather than maintaining competing
lists. Missing acquisition cost, unassigned components and stale reviews clear through
the relevant evidence/confirmed decisions. Negative actual DB1 requires complete cost
basis, distinct from the existing purchase-price comparison exception.

Reuse the current owner/member permission model: owners confirm financial judgments;
members inspect. This includes valuation method, assignments, recoverability, FX/unit
basis, ownership, impairment/recovery and zero/not-applicable completeness declarations.
Check actor authorization and the previewed data revision again at execution. Agents
may prepare and execute proposals explicitly confirmed by an active owner through the
shared service, but cannot approve them themselves. A projection worker is not a finance
approver. No new finance role is implied; delegation remains an explicit scope decision.

Tax and skonto are now explicit requirements with fixture K. Received attributable
nonrecoverable tax belongs in the selected acquisition basis once; recoverable amounts
do not. Payment differences alone establish neither a purchase reduction nor tax.
Exact four-decimal cost totals are separate from rounded UI labels and six-decimal
unit-cost displays; base quantities initially support four decimals; signed remainder
allocation preserves totals. Unsupported source precision remains lossless in the
payload and is disclosed rather than truncated.

Canonical demo changes follow docs/features/company-setup-demo.md and spec 146. Add a
versioned complete cost chain through normal intake/shared services with narrowly
reviewed initialization authority, alongside deliberate incomplete/late-cost cases.
Preserve replay markers, lessons and source controls. No demo-only costing rules,
automatic blanket owner approvals, new browser timer or separate job queue are introduced.

The exception classes must fit the catalog that exists rather than a convenient one.
Its severities are `critical`, `high`, `normal` and `low`; its accountable areas are
named the way it names them (accounts payable, purchasing, sales management, billing);
its subject records are a closed set, so a cost-gap finding attaches to the receipt
movement, the invoice document, the reviewed item or the sold document line. The shared
class ordering is contiguous and its count is pinned by a test, so four new classes move
that count. A finding whose natural subject is a new record type waits for a separately
reviewed catalog extension instead of inventing a subject kind here.

The owner-approved benchmark extends spec 033's harness with 10,000 test-day orders
and 90,000 historical orders over 24 months, 1,000,000 movements and the fixed supporting
cardinalities in fixture J. The reduced profile remains the fast correctness suite.
This is a historical-volume read/reconstruction test, not the separately deferred
100,000-orders/day ingestion capacity initiative. Proposed time budgets are unchanged.

All new public core entrypoints require tenant-isolation catalog classification and
coverage-count verification in addition to generated Tool Usage/resource vocabulary.
Every new cost record reference resolves identically from explanations, web, CLI and MCP
or the delivery is incomplete.
The review changes are still design-only; no numerical performance, usability or runtime
acceptance is claimed before the specified experiments and tests have run.


## 15. Technical planning research: measured seams before schema approval

The owner's subsequent instruction to continue authorizes progression into planning.
The four accepted review rules remain binding. Use the proposed commercial profile and
sequential slices as the design baseline without treating that as tenant accounting
activation, statutory suitability approval or permission to migrate an active database.

### Decision: qualify two costing strategies before product schema

Rationale: fixture J is explicitly required before architecture approval. The existing
`services/analytics/inventory_relation.py` refuses more than 100,000 movement inputs;
its tenant-wide in-memory materialization cannot simply be reused for one million.
`services/projections.py:_replace_rows` loads the entire old result into Python, and
`rebuild_projections` serializes tenant publication with an advisory lock. Invalidation
is by projection/event type, not a receipt/layer dependency index. Scoped replay and
publication remain work to prove, not capabilities that already exist.

Alternatives considered: increasing limits without proof is rejected; always replaying
all history on a request violates FR-018. Compare bounded indexed direct derivation
against rebuildable indexed generations using one calculation kernel. Reuse the existing
queue/freshness/publication contract without assuming its storage loop meets the budget.
See plan.md and contracts/spike-contract.md for the isolated qualification scope.

### Decision: prefer an allowlisted typed costing relation for reporting

Rationale: `services/analytics/compile_sql.py` explicitly refuses declared service
measures with `service_measure`. Merely adding YAML measures cannot deliver DB reporting.
The existing `services/analytics/derivations.py` registry permits canonical typed relations
such as finance aging and warehouse inventory. Extend that established seam only after
proving cost grain, policy/cutoff context, filtering and bounded data access in the spike.

Alternatives considered: a new generic service-measure execution engine is broader;
SQL arithmetic directly over source evidence bypasses canonical cost rules and is rejected.
The experiment must prove an executable relation path, not only a fast kernel benchmark.

### Decision: reuse confirmation infrastructure, not cost-center target semantics

Rationale: finance component preview/assignment already validates tenant, evidence hash,
finance revision, actor/action and immutable history. Reuse those patterns. Existing
assignment parts target cost centers and accept strictly positive amounts against a
nonnegative basis; acquisition reductions and receipt targets cannot be introduced by
silently changing that contract. A later schema proof must justify narrow typed cost
attribution links and independent signed basis rules.

Alternatives considered: reusing the positive cost-center part table would change existing
finance meaning; adding computed EK/DB fields to Item/Document would create competing
state. Both are rejected. No final new business table is approved during qualification.

### Environment and evidence

Python 3.12.4 is available. Read-only Docker discovery was denied by the current sandbox;
no benchmark database or full measurements were produced during planning. Future execution
requires normal tool approval for a dedicated disposable database and the reference resource
envelope. This is an execution prerequisite, not a reason to mark performance or production
architecture complete. Existing unrelated web/chat edits were left untouched.


## 16. Phase 0 implementation and provisional architecture result

The isolated experiment now exists under `benchmarks/large_tenant_registers/costing_*`.
One pure Decimal kernel serves direct observations and PostgreSQL-derived output.
The v2 generator fixes the accepted two-tenant cardinalities, preserves received amounts,
and appends separately source-referenced late adjustments. Prior adjustment cutoffs,
return layer provenance, exact rounding, same-tenant links and atomic publication have
independent tests. No application schema or public core catalog is changed.

Decision supported by current local measurements: retain a single canonical calculation
kernel, investigate bounded direct scope for order explanation/live consistency, and use
indexed rebuildable observations for aggregate screens. Direct order reads do not require
a whole-company replay. Full reconstruction is deliberately kept off interactive reads.

Alternatives: pure request-time whole-company replay has no evidence of meeting the
inventory budget; a second calculation engine in SQL/UI is rejected regardless of speed.
A mandatory projection for every tiny question is unnecessary if an exact bounded direct
path meets its budget. The benchmark supports this direction, not final schema approval.

The result is explicitly exploratory: the combined reference resource envelope, product
compiler/exception integration, full freshness/review semantics and adversarial full-load
history remain unqualified. Fixture J stays open. Exact numbers, code digests, input
revisions and remaining work are recorded in verification-results.md and evidence/.


## 17. Integration continuation findings

Decision: use one canonical service with indexed contribution-slice and inventory-pool
relations, with explicit grain/cutoff context in the analytics compiler. Reuse financial
components and the existing scheduling/exception contracts; do not overload positive
cost-center assignments. Details and exact repository seams are recorded in
[product-integration.md](contracts/product-integration.md).

Rationale: current anchor joins cannot safely represent arbitrary matched slices; current
Python relation materialization and whole-projection replacement do not establish the
million-movement budget. Shared worker execution has a 30-second child timeout and a
20-second statement timeout, so a possible 120-second reconstruction needs bounded
parts and atomic final manifest publication. A global watermark cannot advance after
refreshing one pool if another affected pool remains unpublished.

Alternatives rejected: YAML-only measures, raising inventory materialization limits,
parallel financial formulas in adapters, a second queue and increasing shared worker
timeouts. These either lack executable semantics, break parity or hide unbounded work.
No final production schema is selected by this research.

## Bounded reconstruction through shared jobs

The whole-tenant prototype rebuild exceeded the shared child lifetime in earlier runs.
The new experiment stages whole-pool ranges and moves a publication pointer only after
all ranges commit. This keeps the existing queue, claim, retry and watchdog semantics
while preventing a partially rebuilt valuation from becoming visible. Whole-pool work
preserves FIFO dependencies without designing unreviewed cross-job cost checkpoints.
An oversized single pool must therefore fail explicitly in this experiment; production
handling of such pools remains a separate requirement/design decision.

The experiment uses a static child bootstrap to bind its isolated fixture handler to the
existing projection job definition with unchanged authorization. This is test scaffolding,
not a recommendation to patch the production registry. A production integration should
use an explicitly registered/versioned handler and the shared job services, with full
source-history cutoffs and reviewed generation retention. Reporting and operational
reads must use the same canonical published relation and coverage rules. The published
pointer avoids copying hundreds of thousands of observations in the final transaction.

## Actual product adapter interfaces: design decision

**Decision:** Use an explicit own-grain canonical SQL selectable, opt-in covered-sum and
ratio semantics, and a typed costing execution context through the existing graph/report
and tool pipeline. Use the same generation basis for cost findings, page totals and
explanations. Detailed contract: [adapter-delivery.md](contracts/adapter-delivery.md).

**Rationale:** `compile_sql.build` currently always joins derived results to mapped
anchors; `_measure_expression` uses SUM and therefore drops unknown contributors.
`TraversalResult` has no generation/cutoff/coverage envelope. Separately,
`web.read_models.exception_page` and `exception_count` currently derive the entire live
exception population before slicing/counting. A costing-only fast query cannot certify
the actual queue budget. These are observed source constraints, not measured regressions.

**Alternatives considered:** YAML-only measures cannot execute the new relation or prove
coverage. An isolated temporary graph/derivation binding can exercise complete current
rows but bypasses the hardest production semantics; reject it as the next integration
proof. JSON expansion of the full population defeats the indexed canonical relation.
A new margin-report API beside the graph duplicates semantics. Globally changing SUM
would alter existing reports unnecessarily; new aggregation behavior is explicitly
opt-in. A cost-only exception page would fragment the existing register and conceal its
whole-queue performance constraint.

**Outcome:** The adapter design is concrete and code-grounded. Production authority,
source history, generation retention and storage review are still prerequisites, not
claims proved by the disposable benchmark. Reference-host and actual integrated response
budgets remain open. No runtime behavior was changed by this research.

## Production authority and history: concrete model decision

**Decision:** Reuse exact FinancialComponent evidence and tenant-local serialized
BusinessEvent sequence. Add separate signed receipt-cost attribution/reviews, immutable
cost input admission and sealed typed input manifests. Stage production delivery from
receipt cost/coverage to inventory and contribution. Field-level proposal:
[production-data-model.md](contracts/production-data-model.md).

**Rationale:** Existing financial assignment parts require positive cost-centre shares,
so they do not express signed receipt costs. `_received` already normalizes source-stated
amounts, but components are initialized lazily by assignment. SourceRecord is immutable;
manual document headers/lines are not universally immutable. A header-correction event
records changed field names without all before-values. Movement has economic occurred_at
but no universal knowledge timestamp. Source receipt and accepted interpretation can be
different transactions. A simple source-ID/timestamp cutoff therefore cannot freeze the
complete calculation basis across bounded worker jobs.

`emit_business_event` locks Tenant, allocates max(sequence)+1 and retains the lock through
the caller transaction. Reuse that ordering only after proving every cost-relevant writer
emits its event and input identity atomically. Do not use UUID order, an unlocked database
sequence or recorded_at as commit time. Sealed review manifests retain exact input IDs;
current evidence pointers and cache rows cannot substitute for them.

**Alternatives considered:** Expanding cost-centre parts into polymorphic receipt/sales
shares changes their established meaning and loses target constraints. Persisting computed
EK/DB as Facts creates another authority. Copying all live input tables in every child
cannot preserve one snapshot across process boundaries. Holding a global transaction/lock
through full reconstruction blocks intake and conflicts with bounded workers. Replaying
arbitrary old state solely from incomplete event payloads invents history. Admitting
immutable financial evidence and capturing narrow later context versions is explicit about
both retained history and the earliest supported knowledge boundary.

**Review decision still needed:** Approve the concrete production model and first slice,
plus the explicit move of full integrated/reference qualification to a mandatory release
gate after implementation of a reviewed candidate. The proposal changes no existing gate
until the owner accepts it. Company policy activation and deployment are not included.

## Inventory kernel decisions

The experimental kernel loses the original receipt identity when a return is resold and
accepts caller ordering. Production needs structured entry/receipt references, explicit
return allocations and canonical economic ordering. A specific selection identifies both
the layer-entry movement and original receipt, so a split return is not ambiguous. Return
allocation is bounded against the exact original sales-issue portion, including earlier
returns, using cumulative rounding of that portion. Supplier returns require explicit
layer identity and are not sales. Aggregate layers with the same returned entry/receipt
only after retaining exact original issue references in the return observation.

Rejected: importing benchmark code, introducing a temporary public preview API, silently
choosing FIFO, treating physical location as ownership, or rebuilding inventory in a
receipt read. No technology unknown requires new research infrastructure or delegation.

### Service integration seams verified during kernel delivery

- `core._append_movement` emits `movement.recorded`; correction-created compensating
  and replacement movements explicitly suppress that event. `core.correct_movement`
  emits one `movement.corrected` event linking both via MovementCorrection. Admission
  cannot require a recorded event per movement or classify compensations as new supply.
- Current `_capture_correction` in `services/costing.py` only retains corrections whose
  original movement has a receipt basis. Inventory integration must extend retained
  membership to admitted outbound/return/transfer inputs before claiming their history.
- Tenant has no single own-Party FK. Manual order creation receives an explicit
  `company_party_id` and records it in source evidence/commitment context. That context
  may support a reviewed ownership decision, but neither Tenant identity, Party display
  name nor physical Location proves ownership. Unlinked receipts need explicit evidence.
- Existing Movement `return` / `resolves_movement_id` describes physical receipt and
  settlement, not the original sales cost portion. The new kernel's exact return input
  must come from the approved retained match authority, never that settlement shortcut.

These are read-only integration findings, not completed admission/ownership services.

## Bounded inventory service review

Decision: a complete owner-confirmed item pool freezes policy, full receipt ownership,
exact receipt reviews and admitted movement members in one transaction. This avoids
unbounded live replay and does not infer economic ownership from location or shipment.
The service is a bounded first integration, not a company-wide generation substitute.

Independent read-only research identified two cursor/order gaps, resolved before code:
use the introducing review event as sealed knowledge boundary (the original validation
cursor remains in action input), and retain each movement's original recorded-event FK
for stable equal-time sequence. A missing or ambiguous recorded event refuses. Typed
correction authority is checked across original, compensation and replacement IDs;
corrected pools remain explicitly unsupported while old admitted snapshots stay readable.
No unresolved design clarification remains in this bounded implementation.

## Contribution foundation decisions

Reuse commercial_v1 and adapter-delivery's joint-slice coverage rule. A known actual
subtotal may use evidenced inputs; finalized output requires reviewed inputs for every
slice in that particular measure. Keep provisional amounts solely in retained input
trace. Separate direct and allocated selling cost inputs rather than introducing a
formula language or inferred cost categories. Partition currency/unit and refuse mixed
revision contexts. Do not infer matching from order, invoice or shipment identity.

A pure frozen-input kernel is the next domain-first step: it proves arithmetic before
adding commercial authority/services. It introduces no new table, policy activation,
source recomputation or graph measure. Existing reviewed inventory services remain
unchanged. Data-level evidence references are supplied by the future trusted service;
the kernel is not an authorization or evidence-validation endpoint.

## Current preview integration choice

Existing billed_document_line_id and commitment/movement FKs support an exact current
whole-line candidate without adding match authority prematurely. A one-to-many quantity
match requires explicit allocation/revision authority and is deliberately refused.
Use the existing finance received-net contract, never line unit_price or gross/net tax
reconstruction. The current inventory review already confirms economic consumption and
owner; it does not confirm revenue recognition or commercial profile completeness.
Therefore preview mode has absent generation/profile revisions and disables all finalized
amounts. Historical customer/channel context cannot be inferred from mutable documents.

## Confirmed contribution specialization

A full-quantity unique binding needs no allocation parts. Store the source line and
movement-basis identity once; later reviews select an exact inventory member without
repeating the physical Movement FK. Freeze received context at admission and protect
admitted documents until replacement/rematching is supported. One scoped owner review
can establish commercial_v1 approval and revenue completeness without introducing an
unused company-wide profile registry. Preserve this distinction in responses and docs.

## Selling attribution continuation

Reuse the existing revision family rather than introduce a competing component ledger.
Conservative cross-family exclusion avoids shared-bucket double consumption while mixed
receipt/selling revisions remain unimplemented. Retain complete category decisions and
exact member IDs instead of looking up current assignments during historical replay.
Received net with confirmed recoverable/no tax is the initial supported basis; unknown,
mixed or nonrecoverable tax needs later explicit support, never silent net treatment.

## Financial company generation storage decision (proposal, 2026-09-19)

**Decision**: Retain one typed company financial-input manifest and publish a disposable
company generation whose typed results reference the existing verified per-review caches.
Use separate inventory and contribution member/result relations plus a scope-keyed CAS
pointer; require explicit owner approval before migration.

**Rationale**: A retained current census proves discovery but not financial knowledge;
captured reports are deliberately diagnostic; independent batch actions do not prove exact
company population. Reusing canonical caches avoids duplicating received values and
arithmetic while the manifest supplies the missing common cursor, knowledge time, exact
population and per-subject input fingerprints.

**Alternatives considered**: promoting captured publication (wrong authority), joining
independent batch publications (no population closure), copying all amounts into a second
cache (duplicated arithmetic), polymorphic membership (weak typed tenant links), and a
tenant-only latest pointer (cannot represent concurrent historical/current contexts).
