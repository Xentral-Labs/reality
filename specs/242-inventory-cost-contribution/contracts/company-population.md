# Company population closure

Status: internal domain prerequisite under the approved staged production model.
No company census, generation storage, publication job or company report is delivered
by this contract alone.

## Builder obligations

1. Freeze tenant, effective cutoff, knowledge cutoff, committed event watermark and
   algorithm identity from trusted source/evidence history. Enumerate expected subjects
   independently of reviews and successful calculations. Unreviewed subjects must remain.
2. Resolve each subject's canonical inputs, own policy/review revisions and gaps. Produce
   a SHA256 fingerprint. A fingerprint does not replace retaining the input membership.
3. Evaluate every expected subject exactly once. Unknown financial inputs produce an
   explicit unknown observation. A worker failure or skipped subject produces no closure.
4. Validate expected/evaluated identity sets, input fingerprints and common context with
   domain/cost_population.py. Financial gaps may coexist with complete population closure.
5. Independently verify persisted output hashes, work and trace counts, worker fencing
   and publication CAS. Integrate the company-aware domain guard with retained storage before publication: the selected-scope single-policy basis cannot represent this population. Never invent one policy revision to satisfy that old interface. The domain
   closure result is neither financial approval nor monetary integrity verification.

Inventory uses item identity within the currently supported single-ownership-pool model;
multiple ownership pools require the separately specified ownership expansion. Contribution
uses whole document-line identity within the currently admitted matching model; split
revenue/fulfilment slices require the separately specified matching expansion. Never widen
these keys silently to hide unsupported scenarios or merge distinct slices.

## Coverage

Each of acquisition value, carrying value, DB1 and DB2 reports expected, covered and
unknown subject counts and empty/partial/complete state. Carrying-value gaps do not alter
acquisition coverage. Selling-cost gaps may keep DB1 complete while DB2 is partial.
DB2 cannot be known for a row with unknown DB1. Financial amounts are not calculated or
accepted by this helper. Empty coverage grants no numeric zero.

## Subsequent integration

The source-backed census must be retained with explicit unknown/unadmitted scopes. Staged
worker chunks must preserve membership and retained input identities through retries.
Publication must verify the exact persisted population and pin one generation across
page, totals, cursors and exceptions. Full-company current status requires source cursor
coverage and input-specific invalidation; several historical batch actions are not one
company generation. Benchmark the resulting real services against unchanged fixture J.

## Delivered current discovery boundary

`costing.capture_company_cost_census` is an internal builder service requiring a caller
transaction at PostgreSQL REPEATABLE READ. It records snapshot identity, observation time
and the visible tenant event cursor. It does not claim a historical knowledge cutoff.
All tenant movements through the effective cutoff contribute inventory membership, even
without reviews; missing or ambiguous movement events remain explicit gaps. All sales
invoice and credit-note lines remain economic-scope candidates, including service lines
and future invoice dates. Header-only documents remain gaps. Line history and economic
scope require subsequent assessment.

Latest source versions retain their current import classification; absent outcomes are
unresolved. Non-interpreted sources are conservatively counted as unresolved, without
claiming they all have financial relevance. Combined movement/header/line/source reads
are bounded to at most 100,000 records; overflow refuses instead of truncating. This is
not reference-scale qualification or an ordinary report endpoint.

Record fingerprints identify the visible records only. They are not complete financial
input fingerprints and cannot be passed directly into ExpectedPopulation. Discovery
neither retains a manifest nor evaluates, approves, persists or publishes financial
results; publication_eligible is always false. Retention, per-subject financial input
resolution and the manifest-aware publication guard remain required integration work.

## Company publication domain guard

`CompanyGenerationBasis` now binds the shared historical PopulationBasis to a retained
manifest identity and canonical expected-population digest. Each subject's complete
input fingerprint remains separate. `publication_decision` requires both expected and
evaluated populations for this basis, validates the digest and common context, performs
exact closure and reconciles row counts before returning a pointer-change decision.
The existing sealed/content/work/trace/cursor/CAS guards still apply. Unknown money does
not imply unfinished work or complete financial coverage. Selected-scope inputs cannot
masquerade as a company basis, and cannot accept company-population proof arguments.

The digest uses sorted typed membership and canonical JSON with the complete context;
it is an integrity binding only. The service must load and verify retained financial
inputs and persisted outputs under tenant scope and hold the publication lock through
commit. No storage/service currently supplies this company proof. Census snapshot metadata
cannot supply a historical knowledge cutoff, and record hashes cannot substitute for
resolved input fingerprints. No company publication or durable manifest is delivered here.
