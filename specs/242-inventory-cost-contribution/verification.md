# Planned acceptance evidence

Status: design fixtures only, not executed tests. Monetary examples are EUR, use fully
stated amounts and compatible units, and assume evidenced economic attribution unless
the scenario explicitly removes it. Each implementation slice must add its failing
proofs first where practical and record real results separately.

## A. One cost basis for inventory and contribution

Receive 100 units. Received goods net amount 1,000; inbound freight 100; attributable
supplier credit 50. Acquisition cost 1,050; derived unit cost 10.50. Sell and bill 60
units for a stated net 1,200. Known attributable outbound freight 30, payment fee 24,
marketplace commission 60. Remaining cost 420; consumed cost 630; DB1 570; DB2 456;
DB1 rate 47.5%; DB2 rate 38%. Input totals are never recomputed from price/quantity.
No costs are counted again through cost-center assignments or gross ledger entries.
Remove the freight evidence: actual complete EK/DB is unavailable, not silently 9.50.
Restore it and confirm category completeness: the same supported values become reviewed.

## B. Consumption method and transfers

Receive 100 at a stated total 1,000, then 100 at 1,400; sell 120. FIFO consumed cost
1,280 and remaining cost 1,120. Compare a future weighted-average algorithm separately:
consumed 1,440 and remaining 960. Never mix these results or imply both are implemented.
Move 30 remaining FIFO units between locations: company quantity 80 and cost 1,120
remain unchanged. Reserve 20: availability changes, cost does not.
For specific identification, receive serial A at 10 and B at 14; sell B: consumed
cost 14, remaining 10 regardless of receipt order. Verify physical lot picking does
not silently select a different accounting method for fungible stock.

## C. Returns, corrections, free goods and loss

From A, economically return 10 undamaged sold units with a linked sales credit 200.
Restore historical cost 105; remaining quantity 50 and cost 525; net revenue 1,000;
net consumed cost 525; DB1 475. With unchanged selling costs 114, DB2 361.
No cash refund changes DB a second time. A credit-only 200 adjustment restores no stock.
An additional separately evidenced 20 impairment on returned goods yields carrying
value 505 while historical acquisition value remains 525.
Supplier return of 5 units removes 52.50 of historical cost; independently inspect
the supplier's credit and expose any difference rather than forcing equality.
Correct a receipt/return through existing compensating links and prove no double count.
Zero-price samples consume cost with zero revenue; rates are unavailable, not divide-by-zero.
Loss without sale moves cost to a loss bridge, not to an invented customer margin.

### C2. FIFO return ordering and resale

Receive one unit A at cost 10 and later one unit B at cost 14. FIFO sale consumes A
at 10. Economically return A while B is still in stock: remaining cost is 24. A's
return layer carries 10 but is queued after B at the return time. The next FIFO sale
therefore consumes 14, leaving A at 10. The earlier sale remains at 10; no backdated
availability or consumption is introduced. In the specific-identification variant,
reselling identified A consumes 10 and leaves B at 14. Test each method independently.

## D. Late evidence and reviewed history

Receive 100 at 1,000; sell/bill 60 for 1,200. Before freight is received, known inventory
cost is 400 and known consumed cost 600; required freight coverage blocks final DB.
Later receive and attribute freight 100: inventory 440, consumed 660, DB1 540.
The earlier knowledge cutoff reproduces 400/600 and incomplete coverage; the new one
explains +40/+60. A subsequent attributable credit 50 reduces inventory by 20 and
consumed cost by 30. Review snapshots retain their exact input manifests, not mutable
latest pointers. A new relevant input invalidates current completeness and identifies
affected past sales without silently posting or rewriting a statutory close.

## E. Partial fulfilment and billing

Order 100 units, ship with evidenced economic transfer 60, bill 40 with stated net 800;
unit acquisition cost 10.50. Match only 40: revenue 800, cost 420, DB1 380. The remaining
20 delivered units have cost 210 in the unbilled bridge. No final whole-order DB.
Bill remaining delivered 20 for stated net 400: matched aggregate becomes 1,200/630/570.
An invoice preceding fulfilment stays unmatched revenue. Multi-invoice/multi-shipment
joins cannot multiply either quantity or money. Unknown transfer date blocks finalized
period contribution; payment date cannot resolve it. Late invoices complete the original
economic fulfilment cohort in a current-knowledge view. Direct unlinked freight/service
lines require explicit targets rather than guessed matching to an order.

## F. Allocation and report conservation

Shared outbound cost 100, explicitly allocate 60 to order A and 30 to B; remainder 10
stays unassigned. A/B/unassigned sum to 100 at every report grouping. Adding two positions
to A must not duplicate its 60. With a complete company cost scope, company DB2 includes
the 10 once while position/order reports expose it outside their attributed totals.
Allocate 0.0001 across three equally weighted targets: exactly one receives 0.0001 under the
stable remainder rule. Reject over-allocation and a second cost use of the same basis.
Header 1,000 and lines 600/400 count as 1,000 once. Use original and semantic credit
signs to prove credits reduce cost once for either supported source sign convention.
An acquisition freight component included in DB1 cannot also reduce DB2.

## G. Valuation coverage and HGB bridge

80 units have acquisition value 1,120. Supported reviewed lower value 12/unit yields
carrying value 960 and an impairment bridge of 160. Later supported recovery to
13/unit yields 1,040; recovery above historical cost is capped at 1,120. Consume goods
after impairment and reconcile historical consumption, carrying-value consumption and
adjustment release without double expense.
Separately test missing opening costs/layers, negative stock, same-time ambiguous
receipt/issue ordering, missing economic ownership and physically held third-party goods.
These cannot receive a complete value from a current purchase price. Owned transit stock
is reported separately when supported; no fictitious physical receipt is inserted.

## H. Currency, units, special cases and dimensions

USD 1,000 original cost with a reviewed historical EUR basis of 920 remains USD 1,000
in source evidence and EUR 920 in the valuation basis; a later spot rate does not rewrite it.
Missing FX basis prevents combining USD/EUR. An evidenced conversion of 10 boxes to
120 base units supports quantity matching without rewriting the agreed price per box.
Missing conversion blocks it. Separate settlement FX from acquisition cost.
Exercise drop ship with exact economic purchase/sale matching; service with stated direct
cost; kit with component fulfilment and declared revenue allocation. Remove one component
or internal manufacturing cost: report unsupported/incomplete, never zero or full coverage.
External aggregate valuation alone cannot establish per-order COGS. Customer/channel
renaming does not reassign historical transactions; unassigned dimensions stay visible.
Zero/negative net revenue produces a monetary contribution but no misleading margin rate.

## I. Controls and parity

Use neighboring tenants with identical human numbers, products and amounts. Cross-tenant
reads/links fail without disclosure. Concurrent assignments cannot exceed a component's
available amount; a replay is idempotent; changed inputs invalidate stale previews.
Every new decision is confirmed through the shared application path, including chat.
Owners alone may approve every FR-019 decision. Test ordinary members, removed owners,
archived tenants and an owner demoted between preview and execution; all are denied
without writes. Agent identity never elevates the initiating actor. Projection workers
cannot approve policies, assessments or zero-cost declarations.
An agent-prepared proposal without owner confirmation is refused. The same proposal
explicitly confirmed by an active owner can execute through the shared service; changed
inputs or revoked owner authority before execution refuse it atomically. Neither the
agent nor worker may manufacture the confirmation. Replay returns the original receipt.
Open every new record reference - cost attribution, valuation policy, economic
attribution, valuation assessment, cost scope review - from an explanation, the web
pass-through, the CLI and MCP record reads: all resolve the same record under the same
inspector name and tenant scope, or all refuse it. A reference registered in one catalog
and missing from the resource vocabulary or the generated Tool Usage pages fails here.
Compare web, CLI, MCP and report results over the same scope/cutoffs. Verify no source
amount was altered, no derived amount became a Fact, and inventory quantity/ledger
behavior is unchanged. Explain every fixture through shortest links to original evidence.

## Implementation verification layers

- Domain: exact allocation, sign, rounding, consumption, matching and coverage proofs.
- PostgreSQL services: tenant FKs, concurrent allocation, revisions, replay, corrections,
  transaction rollback, effective/knowledge cutoff and opening evidence.
- Business stories: complete A–M with independently calculated expected outputs.
- Adapters/reporting: shared-service parity, confirmation, missing states, fan-out,
  currencies, accessible explanations and localized labels.
- Fixture J qualification: `test_costing_product_qualification.py` proves the release
  decision fails closed for incomplete evidence; `test_costing_product_workloads.py`
  proves timed reads use the shared tenant-scoped product tools, graph, Exceptions and
  MCP entrypoints rather than benchmark-only SQL.
- Required repository gates after implementation: spec policy, lint, full tests,
  migrations, web build and applicable browser/i18n checks; classify every new public
  core function in `packages/reality-core/config/tenant_isolation_catalog.yaml`, update
  its expected coverage count and run tenant-isolation catalog/coverage checks; raise the
  pinned operational exception class count in
  `packages/reality-core/tests/test_reference_integrity.py` and keep the shared class
  ordering contiguous; generated catalog checks when catalogs/tools change. Fixture J
  is the mandatory performance gate before architecture approval, not a deferred
  implementation detail.

## J. Reproducible performance and reconstruction acceptance

Extend the existing `packages/reality-core/benchmarks/large_tenant_registers` dataset and
its profile conventions; spec 033 owns that harness and no second benchmark framework is
created. The owner-approved mandatory full profile uses deterministic seed 234 and these
exact per-tenant cardinalities (repeat the profile for a neighboring control tenant):

| Record family | Count and distribution |
|---|---|
| Orders | 100,000 total: 10,000 on the test day and 90,000 over the preceding 24 months |
| Items | 10,000 |
| Movements | 1,000,000: 300,000 receipt movements, 600,000 issue movements, 100,000 transfer movements |
| Financial cost components | 1,000,000: 300,000 purchase, 300,000 acquisition ancillary/reduction and 400,000 selling/fulfilment components |
| Cost attribution parts | 1,000,000 total; explicit splits and unassigned components must preserve this count |
| Revenue/fulfilment matching parts | 600,000 total, separate from cost attribution parts |

The 90,000 historical orders comprise 3,750 in each calendar month before the test-day
month, deterministically spread over that month's days. Use calendar boundaries, not
24 fixed 30-day windows. Fix the test business date and exact generated record-family
counts in the versioned dataset manifest; corrections/returns are subsets of the above
movement counts, not unreported additions. All cost-bearing receipts and selling costs
have cost components; deliberate incompleteness may be a missing expected additional
component or an unassigned existing one. The generator must assert the listed totals.

Define a reduced profile for the normal fast suite using 033/FR-013's profile convention:
correctness and refusal behavior are proven there, budgets only on the full run. This
full profile tests historical cardinality, not 100,000 orders in one business day or
100,000-orders/day ingestion throughput. The latency and reconstruction budgets remain
unchanged; those separate capacity claims remain outside this feature.

Include 1% missing costs, skew with 50% of movements on 100 items, split invoices,
returns and late freight. For receipt/issue quantities ensure a known nonnegative
baseline; explicit negative cases are separate. Record the seed/version, exact
cardinalities, dataset build time and sampled reference totals in results; a gate whose
dataset cannot be rebuilt within the harness's existing disposable-database lifecycle is
not reproducible and does not count.

Reference execution envelope: dedicated 4-vCPU/16-GiB host, local SSD-backed PostgreSQL,
application/database/worker combined within that envelope, five concurrent readers,
one committed cost change per second and one projection worker. Pin database/app
versions and resource settings; report full hardware, memory, I/O and query evidence.
No other tenant's rows may enter results. Budgets apply to service wall time including
input reads/serialization, excluding network transit and browser rendering.

Use 20 warm-up requests then 200 timed requests per read workload over disjoint sampled
orders/filters; report p50/p95/max and errors. Measure first read after restart/cache
absence separately: state response must respect the same read budget and never execute
a full rebuild. Ready one-order reads (<=100 lines) p95 <=500 ms; first 100 inventory
rows with complete filtered totals <=2 s; one-month report grouped by product/customer
<=3 s; the Exceptions/attention first page including its counts, with the four new cost
classes active, <=2 s; a chat/MCP cost or margin answer <=3 s. Measure the queue with and
without the new classes and report the delta: the queue is read constantly and derives
across the tenant, so it is the surface most likely to fail. Report measurement cannot
truncate contributing input rows to meet its budget.

Run three full reconstructions from retained inputs with derived projections deleted,
one with a cold database cache and two warm: each <=120 s, with equal result checksums.
Run 30 late-cost changes on the highest-volume receipt scopes: committed-to-published
latency p95 <=30 s under the stated load. Track memory and processed-row counts; no
interactive read may replay the whole company history. Publication must be atomic and
watermark-correct. Demonstrate worker failure, stale reads, retries and recovery.

These are proposed acceptance targets, not measured claims. Before schema/architecture
approval, benchmark a thin costing spike against this fixture. If synchronous replay
fails, use existing versioned rebuildable projections with dependency-scoped invalidation;
if that also fails, revise the design and review the targets explicitly. Live tools
must preserve their freshness contract: bounded exact calculation or a stable not-ready
response, never silently substitute stale cached totals. No new queue/timer is permitted.

## K. Tax, duty, cash discounts and precision

Receive 100 units with stated purchase net 1,000 and stated tax 190, plus stated import
duty 50. With evidenced fully recoverable tax, acquisition cost is 1,050 (10.50/unit).
With evidenced wholly nonrecoverable tax, acquisition cost is 1,240 (12.40/unit).
For evidenced recoverable tax 100 and nonrecoverable tax 90, cost is 1,140 (11.40/unit).
Do not calculate a missing tax split from a guessed percentage. Selecting a received
basis already containing the 190 prevents adding that tax again. Unknown recoverability
blocks complete cost even though the original amounts remain inspectable.

A separate source states a net acquisition cash discount of 20 and a tax correction of
3.80 against the fully recoverable case. The economic purchase reduction is 20, not
23.80: revised acquisition cost 1,030. After 60 sold, remaining cost 412 and consumed
cost 618 (previously 420/630); no second deduction occurs if the discount was already
included in the selected source basis. A payment shortfall of 23.80 without that evidence
remains unexplained, creates no discount, and cannot finalize its cost scope. Test a
signed credit and a positive credit-document convention. Tax-correction recoverability
must follow its evidenced classification, not this example's implicit reuse elsewhere.

Allocate 0.0100 over equal targets A/B/C: 0.0034, 0.0033, 0.0033 in stable ID order.
Allocate -0.0100: -0.0034, -0.0033, -0.0033. A displayed cent rounding must not change
those exact allocation/export amounts. For a 1.0000 amount across 3 units, unit display
is 0.333333, but the whole value remains 1.0000. Half-even output examples at four places:
1.23445 -> 1.2344; 1.23455 -> 1.2346. Preserve a higher-precision received payload and
report unsupported normalized cost precision rather than truncating it. Refuse typed
quantity precision that cannot represent the source; no partial rounding-driven matches.

### K2. Sequential consumption and filter-independent rounding

Receive three units with total acquisition cost 1.0000 and issue them one at a time.
Cumulative quantities 1/2/3 yield cumulative rounded costs 0.3333/0.6667/1.0000;
individual issues cost 0.3333/0.3334/0.3333. Remaining costs are 0.6667/0.3333/0.0000.
Every prefix conserves original cost = consumed cost + remaining cost. A report filtered
to the second issue must still show 0.3334; pagination, grouping or separate requests
cannot restart the calculation. Three issue amounts sum to exactly 1.0000.

Later evidence adds 0.0001 to this layer. At the new knowledge cutoff, cumulative costs
become 0.3334/0.6667/1.0001 and issues 0.3334/0.3333/0.3334. The net correction is 0.0001;
explain each issue delta and retain the original sequence for the previous cutoff.
Return the second issue in the original-cutoff example: its new return layer retains
0.3334, not the rounded label 0.333333. Resale consumes that exact returned cost and
never rewinds the original layer's completed consumption.

## L. Existing reporting, terminology and Exceptions

Add catalog-backed measures to the existing Analysis Builder/graph/report pipeline;
compare builder, saved-report, CLI/MCP and operational results for fixture A. Assert
all FR-023 label pairs and declared units/currencies/grains in catalog-generated output.
A sum over successive daily inventory values is refused; disjoint DB slices may sum;
DB rates use sum(DB)/sum(net revenue) when the denominator is positive, never the
average of row percentages. If aggregate net revenue is nonpositive, omit its rate.
Negative-revenue rows remain in both aggregate amount totals, not silently excluded.

Exercise unsupported traversal/fan-out and missing cost: stable refusal or explicit
partial result, no raw evidence sum. Old saved reports retain their meaning. Different
policy versions/currencies/cutoffs cannot be grouped into an unlabeled measure.

Register four proposed classes in the existing operational exception catalog under its
existing field contract. Proposed values, to be confirmed against the catalog at
implementation:

| Class | `record_type` | Accountable area (`owner`) | `severity` |
|---|---|---|---|
| Missing acquisition cost | `movement` (the receipt) | Purchasing, with accounts payable when the invoice has not arrived | normal |
| Unassigned cost component | `document` (the invoice carrying the amount) | Accounts payable, with purchasing when the goods scope is unclear | normal |
| Stale cost review | `item` (the reviewed valuation scope) | Accounts payable, with whoever accepted the review | normal |
| Negative actual DB1 | `document_line` (the sold line) | Sales management, with purchasing when the acquisition cost is the stale figure | high |

A component hangs on either a document or a line, so the unassigned class takes the
document and reports once per invoice rather than fanning out over its lines. Negative
DB1 deliberately shares the subject and area of the existing purchase-price comparison
without sharing its meaning. Assert every required catalog field, that each severity is
one of the four existing values, that the four ranks in the shared class ordering stay
contiguous, and that the pinned class count rises from 35 to 39. A class that cannot
honestly take an existing record type is not registered until a catalog extension is
separately reviewed; no new severity word or area vocabulary is introduced here.
Verify Rules counts, Exceptions list, operational cost coverage and explanation identify
the same tenant/scope and knowledge watermark. Supply evidence/assign/review to clear
the first three; credit/cost correction clears negative DB1 only when DB1 is no longer
negative and complete. Cost incompleteness suppresses negative-DB1 detection and yields
a gap finding. The pre-existing `sold_below_purchase_price` finding remains independent.

## M. Demo and user outcome

Extend the canonical versioned profile with fixture A's exact source-backed complete
trade chain, a second item with an intentional missing freight basis, and a linked
late-cost/return story. Existing setup admission, lesson boundaries and durable completion
markers remain unchanged. Reads do not seed, replay creates no duplicates, and replay
never overrides later pause/stop or financial policy choices. Verify every initialized
financial decision is within the narrowly reviewed profile initialization authority;
an arbitrary background job cannot borrow that authority. Ongoing synthetic cases
without fulfilment/cost evidence remain explicitly incomplete.

For the complete item: all 40 remaining units valued at 420; all 60 fulfilled/billed
units matched at 630; DB1 570 and DB2 456. Its quantity coverage is 100%. The incomplete
item cannot inherit this status or be hidden from company coverage. Check default demo
reports and screenshots show the complete example and visible gaps together.

With five operations users unfamiliar with implementation, open the complete demo order
and ask each to state DB1/DB2, explain one deducted cost and open its source evidence.
At least four finish correctly within two minutes without developer assistance. Record
time, correctness and failures; this is an implementation acceptance study, not a
claim that the current draft or application already passes it.

Run the study using [the Fixture M moderated usability protocol](fixture-m-usability-protocol.md).
Its participant table is intentionally empty until five real sessions occur; automated evidence
must not be entered as participant success.
