# Product adapter delivery contract

**Status**: Concrete implementation design, not implemented or production-schema approval.
**Scope**: Spec 242 FR-010–018, FR-024–027 and DR-001–005.
**Decision basis**: Existing product code inspected on 2026-09-18; bounded worker proof
in [verification-results.md](../verification-results.md). This contract refines
[product-integration.md](product-integration.md); it does not replace accounting semantics.

## 1. Findings that determine the implementation

Paths below are relative to `packages/reality-core/` unless stated otherwise.

| Existing boundary | Observed behavior | Required change |
|---|---|---|
| `src/reality/domain/reporting_graph.py::Node` | A node requires a mapped table or facts; derivations are allowlisted | Add an explicit allowlisted selectable-backed mode at its own declared grain |
| `services/analytics/compile_sql.py::build` | Every derivation joins a mapped anchor, with hard-coded anchor tenant column | Preserve existing anchored mode; compile costing directly from the validated canonical selectable |
| `compile_sql.py::_measure_expression` | Column measures use `SUM`, which ignores unknown rows | Add declared coverage-aware sums and ratios; do not change ordinary existing sums implicitly |
| `domain/traversal.py::Traversal` and `compile_sql.py::execute` | No costing policy/knowledge context; only special position-history dates | Add typed context validation and resolve one compatible generation before execution |
| `services/analytics/traversal.py::TraversalResult` and `tools/graph.py::invoke` | Results carry model version and SQL, but no costing manifest | Propagate structured context and independent metric coverage |
| `services/analytics/reports.py::_graph_kind` | Saves validated questions and model version | Store the requested costing context in the question; validate it again on execution |
| `services/exceptions.py::operational_exceptions` | Eagerly loads shared inputs, derives every class and sorts a complete list | Introduce a canonical bounded cost-finding provider and generation-aware page/count path |
| `web/read_models.py::exception_page` / `exception_count` | Slices/counts only after complete live derivation | Route the operational page and count through one compatible shared snapshot contract |
| `tools/application.py::_exceptions` | Calls the complete live exception derivation | Add bounded page response while retaining an explicit compatibility policy for old callers |

This is not resolved by adding DB labels to YAML. Nullable DB columns alone are also
insufficient: ordinary SUM would still report an incomplete group as a complete margin.
A temporary registry override against complete current fixture rows would not prove the
missing coverage/history interfaces, so it is not the selected next experiment.

## 2. One context, one result basis

Introduce proposed domain models in `src/reality/domain/costing.py`. The compiler and
detail services consume the same validated context, not adapter-local policy defaults.

| Requested field | Rule |
|---|---|
| `effective_at` | Business valuation cutoff; separate from the activity-period filter |
| `knowledge_at` | Explicit retained-knowledge cutoff, or explicit `current` selector |
| `policy_revision_id` | Same-tenant reviewed valuation policy revision |
| `profile_revision_id` | Same-tenant commercial DB definition revision |
| `freshness` | `current_required` for actionable current answers; `allow_previous` for explicitly stale display |

Resolve `current` once inside a consistent read, never once per page total or relation.
Policy/profile IDs are not evidence of authorization to activate them. Referenced
revisions must cover the scope and effective date. Tenant comes from caller identity,
not a request field. Arbitrary client-supplied SQL, relation names and algorithm selection
are not accepted. A historical request must resolve supported retained inputs; a current
cache cannot be reused by changing a response timestamp.

The resolved result context contains generation ID, algorithm version, policy/profile
revision IDs, actual cutoffs, processed/target event sequence, completion time and
freshness state (`uninitialized`, `pending`, `ready`, `failed`). It also identifies the
requested-scope assessment when a bounded direct order answer is used. Evidence coverage
is a separate field: `ready` can coexist with missing acquisition or selling costs.
Each cost dimension retains its independent support state (`unknown`, `provisional`,
`evidenced`, `reviewed_complete_at_cutoff`) and relevant evidence/review revision IDs.
A provisional numeric estimate is not supported actual cost. Numeric presence alone
cannot promote an estimate, prove completeness or replace the required scope review.

Pin the actual generation ID in every SQL relation. A mutable pointer lookup in a later
statement can race with metadata. Use a single statement or an explicitly established
repeatable-read transaction covering manifest, rows, totals and finding counts. For the
bounded historical inventory graph slice (T125–T128), an equivalent protected basis is
admitted: pin the exact member vector, lock those generation/snapshot rows FOR SHARE
before checksum validation, then keep those locks through final SQL aggregation. Missing
locked members refuse; later pointer changes do not alter the pinned vector. This
exception is limited to immutable retained historical membership and disposable cache
rows, not current/contribution reporting or mutable source authority. Do not
change transaction isolation after a caller has already issued a read. The entrypoint
must establish the boundary; a service that cannot guarantee it refuses that execution
mode. Use `session.no_autoflush`; no read commits, stages rows or enqueues jobs.

For current-required queries, stale/unavailable basis returns a typed state/refusal,
not a successful empty result. For previous-generation display, values and causal findings
retain the old generation and visible lag. Foreign IDs are indistinguishable from absent
ones. Stable proposed refusal codes include `cost_basis_unavailable`,
`cost_context_unsupported`, `cost_scope_unresolved` and `cost_query_too_large`; ordinary
no-result queries on a valid basis remain distinguishable from these conditions.

## 3. Canonical relations and aggregation

`services/costing.py` resolves the basis and owns the canonical read contract.
`services/analytics/costing_relation.py` returns typed SQL selectables and their validated
context. Extend `services/analytics/derivations.py::Derivation` with an explicit mode and
result contract; existing anchored derivations remain unchanged. Do not convert the
population to JSON or move source-matching calculations into the compiler.

Contribution grain is a disjoint matched revenue/fulfilment slice, including signed
return/correction slices. The v3 fixture's one issue/return row is insufficient as the
production identity. A sale position fulfilled by two movements and billed by two lines
may produce several slices: neither order ID, document-line ID nor movement ID alone
is a unique contribution key. Production slice identity is opaque within its generation.

Each slice supplies tenant, generation, slice key, economic date, currency, unit,
quantity, resolved dimension IDs, received revenue share, consumed cost, selling cost
and independent required/covered indicators plus support/review states. Preserve
attributable versus allocated cost breakdowns and reconciliation residuals under FR-011;
trace these to the original classification/assignment, including after regrouping.
Inventory valuation effects stay in their separate reconciliation bridge. Do not fold
unassigned residuals into matched contribution or silently drop them.
Grouping IDs are derived through shortest
true links. Missing order/customer/channel is an explicit unassigned group, never an
inner-join exclusion. Missing quantities must not be summed across incompatible units.
Unmatched fulfilment, unmatched revenue, losses and unsupported production costs remain
separate reconciliation bridges, not invented matched sales.

Inventory grain is item + economic ownership pool + currency + base unit + valuation
cutoff. Acquisition value, independently supported carrying value, physical quantity,
economically owned quantity and uncovered quantity remain distinct. Inventory values
cannot be summed across dates; carrying-value adjustments do not change commercial DB.

Declare fixed aggregate operations in the graph model, not arbitrary caller expressions:

- **Covered sum**: sum known amounts and required/covered indicators together. A final
  amount exists only when every required input in the filtered group is covered with
  the support and review status required for that final measure. Provisional values
  may appear only in separately labeled estimates, never in actual subtotals.
- **DB1**: final revenue minus consumed cost for the same compatible slice population.
- **DB2**: final DB1 minus attributable selling cost for that population.
- **Ratio**: 100 × final aggregate DB / final aggregate revenue; unavailable when either
  is incomplete or revenue is zero/negative. Never sum or average per-row percentages.

A known DB subtotal sums only slices where that specific DB is supported. It must not
subtract a partial cost subtotal from a complete revenue subtotal. Example: two slices
have revenue 100 each; costs 60 and unknown; selling costs 10 each. Known revenue is
200, known acquisition cost is 60, known DB1 is 40 and known DB2 is 30. Final DB1/DB2
and rates are null, with one of two slices covered. Reporting DB1=140 would be wrong.
If only the second selling cost is unknown but both acquisition costs are 60, final DB1
is 80 while final DB2 remains null. Evidenced zero is covered; missing is not zero.

Coverage counters prove slice coverage, not quantity or monetary coverage percentages.
Where quantitative coverage is meaningful, expose required/covered base quantity within
its unit partition separately. An empty scope has zero rows and `no_activity`; it does
not imply evidence that expected costs are zero. Totals cover all filtered slices before
pagination. Currency and incompatible policy/profile partitions cannot be collapsed.

Preserve `check_fan_out`, unit and additivity checks. A 1:n evidence join must become
an existence predicate when it is only a filter; otherwise refuse an aggregate whose
slice amounts would multiply. Declared selectable edges require column/type and
multiplicity validation in `graph_model.py`, not a blanket bypass of schema checks.

## 4. Reporting, saved analyses and tools

Add optional typed costing context to `Traversal`; require it whenever the resolved path
or an existence subpath uses costing. Keep ordinary graph questions compatible. Extend
`TraversalResult`, `tools/graph.py::invoke` and `web/analytics_api.py` to carry the same
structured result context and metric coverage. The browser formats returned values;
it never derives DB from independently fetched inventory and invoice totals.

Use the existing `graph.ask` / MCP `graph_ask` for grouped contribution questions.
Proposed detail entrypoints are `cost.order.get`, `cost.inventory.page` and
`cost.trace.page`, implemented through `tools/costing.py` and the same application
service. Do not add a competing margin-report engine. Object/path surfaces share the
context model: preserve it beside a formatted path, or explicitly refuse a representation
that would drop it. Round trips must not silently fall back to current knowledge.

Saved questions retain their requested context and graph model version. A `current`
selector remains current when reopened and resolves to a new disclosed manifest; it
is not a reviewed historical snapshot. A fixed historical query retains its cutoffs
and policy/profile revisions and must reproduce that basis or refuse. Financial review
manifests, not saved report definitions, hold immutable approved evidence identities.
A semantically incompatible model revision is not silently accepted on execution.

All money/quantity values serialize as exact decimal strings; null remains null.
Fixture A must yield EK 10.5000, consumed cost 630.0000, remaining acquisition value
420.0000, DB1 570.0000 and DB2 456.0000 consistently across detail, graph, CLI and MCP.
Rates are 47.5% and 38%. Every returned subtotal links to bounded slice provenance;
trace pagination then reaches movement/match/attribution, component, document and source.
Opaque cursors bind tenant, generation, filters and ordering. Expired generations yield
an explicit cursor/basis refusal; pages must not silently switch generations.

Do not expose catalog measures or tools before these services and refusal tests exist.
Register labels centrally in `config/reporting_graph.yaml` and `config/resource_catalog.yaml`,
including Anschaffungskosten, Wareneinsatz, Deckungsbeitrag 1/2, bekannte Teilsumme,
Kostenabdeckung and Buchwert. Preserve the existing agreed purchase-price vocabulary.

## 5. Exceptions use the same basis

Retain the four classes and existing subject kinds proposed in product-integration.md.
A cost-finding relation supplies the existing `OperationalException` fields and basis
metadata from the canonical generation. It does not run FIFO separately per class.
Stable identity uses existing subject plus class and any genuinely distinct causal scope;
generation identifies the basis, not a new business subject or a reason to duplicate
one finding every rebuild. Cause IDs retain the relevant evidence/review revisions.

Negative actual DB1 requires supported actual DB1 (never provisional/estimated DB1),
compatible currency and a current basis for
the subject's declared commercial scope. Incomplete selling cost does not prevent that
DB1 finding. Incomplete acquisition cost does. Do not replace `sold_below_purchase_price`;
that existing class continues to compare agreed prices only.

Pending/failed reconstruction keeps previous findings visibly stale. Neither absence
of staged rows nor unavailable basis clears a finding. When there is no previous
basis, queue metadata states that the cost classes have not been evaluated. An evaluated
empty set and an unevaluated cost scope are different outcomes. Missing acquisition cost,
unassigned components and stale reviews must also cover receipts/components that have
never produced a sale; a contribution-only relation cannot discover them all.

The existing queue page, filtered count and explanation must share one compatible basis.
Use the existing shared projections/read infrastructure to serve bounded reads. Cost
publication and exception projection can finish at different times: track the consumed
cost generation on the exception snapshot and expose lag until the downstream snapshot
catches up. Trigger follow-up through the shared job services after commit, never from
an exception read. Do not label an old exception snapshot current against a newer cost
manifest. Whole-queue counts across cost and non-cost classes require a compatible
snapshot envelope; adding a fast cost provider alone does not fix eager legacy classes.

Preserve the legacy list contract while adding an explicitly bounded page format through
shared services and tools; migrate operational web/attention consumers to it. Qualification
includes old and new classes together, with counts and filters, under the two-second
budget. Tests must preserve ordering, identity, severity, explanation and clearing for
existing classes. This is a narrow queue-read integration, not a rewrite of their rules.

## 6. Prerequisites, implementation order and acceptance

The product prerequisite is a reviewed production evidence/assignment/policy/history
model and canonical costing service. Fixture generation tables do not satisfy it.
Keep approval of retained business authority separate from disposable observation
storage. No migration revision is reserved by this design.

| Slice | Tests written first | Implementation paths | Completion evidence |
|---|---|---|---|
| A. Context and canonical read boundary | Proposed `tests/test_costing_context.py`, `tests/test_costing_relations.py`: history, foreign IDs, revision compatibility, pinned snapshots, no writes/jobs | `domain/costing.py`, `services/costing.py`, `services/analytics/costing_relation.py` | Actual production-backed relation; unsupported states explicit |
| B. Graph and aggregation | Extend `test_reporting_graph_declaration.py`, `test_reporting_graph_traversal.py`, `test_reporting_graph_isolation.py`; add costing integration cases | `domain/{reporting_graph,traversal}.py`, `services/analytics/{derivations,graph_model,traversal,compile_sql}.py` | Partial/zero/provisional/return cases, attributable/allocated/residual reconciliation, split-matching fan-out, units/currencies, ratio and time refusals |
| C. Shared surfaces and saved meaning | Extend `test_reporting_graph_tools.py`, `test_reporting_graph_surfaces.py`, `test_reporting_graph_lifecycle.py`; add costing MCP contracts | `tools/{costing,graph,application}.py`, `mcp/catalog.py`, `services/analytics/reports.py`, `web/analytics_api.py` | Same values/coverage/context/trace across surfaces; path/context round trips |
| D. Findings and operational reads | Extend `tests/operational_exceptions/test_derivation.py`; add page/count and generation-race tests | `services/{exceptions,projections,read_contracts}.py`, `web/read_models.py`, relevant catalogs | New plus legacy classes, provisional-cost exclusion from actual-DB findings, correct stale/clearing behavior, bounded page/count |
| E. Catalogs and qualification | Tenant-isolation catalog cases, generated docs checks, fixture J on real entrypoints | Catalogs, generated Tool Usage, existing benchmark harness | Full required suites and actual serialized response budgets on reference host |

Slice A depends on reviewed production schema/services; B depends on A; C and D use
that same approved relation; E qualifies the assembled paths. Before implementation,
generate detailed test-first tasks and run consistency analysis for the chosen slice.
All public core entrypoints enter `config/tenant_isolation_catalog.yaml`; tests enter
`docs/SPEC_COVERAGE_MATRIX.md`. Run `make docs-generate` and `make docs-catalog-check`
after actual catalog changes. No product catalog or generated page changes in this
planning-only continuation.

Rollback of adapter registration must leave retained financial decisions untouched.
Saved incompatible questions return a version/context refusal. Cache deletion is safe
only when reconstruction from retained evidence is proved; review snapshots cannot
rely solely on retained cache rows. Production retention and cursor lifetimes belong
in the storage review, not an implicit policy in this adapter layer.

## Historical inventory selector delivery (T129–T132)

The existing visual editor preserves inventory_cost_context in its plan/question
round trip. graph.inventory_reviews.list exposes bounded retained confirmation metadata
through shared service/tool/MCP/HTTP. It does not certify cache readiness; graph.ask
continues to enforce complete checksummed generation membership. Selection is explicit,
paged by retained event order, and never triggers confirmation, maintenance or replay.
The historical result shows actual cutoffs/coverage and links to its action and retained
reviews. Text conversion remains unavailable for this context. This slice adds no DB
profile/contribution graph measures or current valuation semantics.


## Implemented contribution aggregate arithmetic (T133–T135)

`analytics/contribution_aggregates.py::contribution_aggregate_columns` builds internal
SQL expressions from the same immutable commercial term definitions as
`domain/contribution.py`. It exposes known/total/required/covered/evidenced/provisional
columns for each input and margin, plus half-even rounded aggregate percentage rates.
It performs no reads, writes, grouping or tenant/context admission. The eventual caller
must supply an admitted unique-slice relation, preserve currency/unit/context partitions
and protect the pinned population through execution. PostgreSQL VALUES is used only
by parity tests, not as a production report population.

This helper does not unblock public contribution reporting on its own. Retained
contribution generations, common scope confirmation, protected canonical relation,
fixed graph measure registration and UI context selection remain open. Reusing current
per-line preview output as a report relation remains forbidden. No schema or catalog
change accompanies this arithmetic stage.


## Protected joint contribution observation (T141–T144)

The bounded historical cache service extends the earlier protected inventory basis
pattern: select the complete immutable action membership, pin the exact generation,
lock its generation/snapshot rows FOR SHARE, validate digests, and hold these cache-only
locks through both per-position and grouped SQL aggregation. No tenant row lock, live
cursor, JSON population or FIFO read is introduced. The canonical contribution_relation
itself is internal and does not authorize scope or validate complete membership.

Selling subtotals are nullable: no selling review is not an observed zero. A partial
review may expose known subtotals but keeps selling_complete false. SQL DB2 input remains
unknown until every required category is reviewed. Two tables suffice because only one
fixed algorithm is admitted and all selected positions are one atomic bounded work unit.
Readiness is complete generation existence plus exact membership/digest validation.
No separate publication pointer or invented common item-policy revision is introduced.
Public graph/UI admission and measures remain deferred.

Cache maintenance/eviction follows generation-before-snapshot lock ordering. The
observation digest also binds the confirmed action's input/output fingerprint, so later
changes to its retained representation invalidate the cached result. The canonical
relation uses retained dimension IDs rather than mutable item/customer attributes.
