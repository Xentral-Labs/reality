# Feature Specification: Graph-Native Reporting Platform

**Created**: 2026-09-17
**Language**: English for all repository artifacts.
**Branch**: Existing shared working tree; no branch change.
**Status**: Model-first revision accepted by the owner. Supersedes the SQL-authoring
and engine-comparison revisions of this feature. Documentation only.
**Input**: Replace both the bespoke SQL compiler and the proposed user-authored SQL with
a declared property graph over the existing typed tables, traversed by a query the system
can check before it runs. PostgreSQL stays the engine. Sales first.

## Context and Intent

### Problem

Analytics has now been attempted three ways, and each hit the same wall from a
different side.

1. **Filter and configuration.** Every new question needed a new configuration.
2. **A bespoke SQL subset** (spec 222). Every new SQL capability became application
   development. `sql_compile.py` is 448 lines and still cannot join.
3. **User-authored native SQL** (the previous revision of this feature). The database
   supplies the capabilities, but the system can no longer tell what a query *means* —
   so grain, join multiplicity, unit and evidence must be recovered afterwards through
   gates, fixtures and adversarial suites, and every relation still has to be published
   as a static barrier view first.

All three sit on one axis: how much *language* is permitted. The third is the end of
that axis, and it still does not deliver the goal, because the goal was never more
language. It was more **model**.

### Accepted Direction

Declare the business graph that the typed tables already describe, and let questions
traverse it.

- **Nodes** are the tables that exist today. Each declares its grain and key.
- **Edges** are the relationships that exist today, mostly as foreign keys. Each
  declares direction, multiplicity and whether it is recursive.
- **Measures** are declared on nodes with their unit and their additivity.

A question is a path through that graph plus a measure. Because the compiler knows the
multiplicity of every edge it walks, it knows when a path fans out and a measure must be
folded before it is summed — the one thing neither SQL nor Cypher can know on its own.

Nothing is materialised. A traversal compiles to a single PostgreSQL statement against
the same base tables the services use today. There is no second database, no view per
relation, no view per report, and no per-tenant role: the tenant predicate is emitted by
the compiler on every node, because no author-written SQL text ever reaches the engine.

### Terminology

This feature's model is the **reporting graph**. It is not the **Context Graph**, which
remains the established term for connected Facts and keeps its meaning unchanged in all
languages. The reporting graph is an analytical declaration over retained records; the
Context Graph is the recorded connection between Facts. A later feature may publish the
Context Graph as reporting-graph nodes, which is why the two must stay distinguishable.

### Scope

Declare the reporting graph for sales and the finance relations that sales comparison
requires: party, item, order, order line, invoice, invoice line, posting, allocation,
movement, shipment, location. Provide a traversal query with two authoring surfaces that
compile to one internal form. Preserve private drafts, explicit save confirmation, exact
decimal values, shared application services and Inspector navigation. Publish temporal
coverage per node instead of assuming complete history.

This specification supersedes spec 222's unimplemented compiler-expansion roadmap and
this feature's own earlier SQL-authoring plan. It does not retrospectively change spec
222's shipped Q01 behaviour or its verification evidence. The graph executor replaces the
compiler at a coordinated cutover, after parity and isolation proofs.

### Non-Goals

- A database console, user-authored raw SQL in the primary path, write access or
  arbitrary functions.
- A graph database, a second store, a derived reporting copy, CDC, or materialised
  projections under this feature.
- Dissolving the typed tables into an entity-attribute-value store. The typed tables
  and their constraints are the asset; the graph is a declaration over them.
- Predefining every question, a view per report, or promising billion-row speed.
- New historical snapshots, guessed historical states, reconstructed source amounts,
  inferred payment links or silent currency conversion.
- Replacing private report storage, confirmation or the existing operational model.

## User Scenarios & Testing

### User Story 1 - Ask a new business question (Priority: P1)

An analyst asks for everything connected to a customer within a period and aggregates it,
combining nodes that were never combined before, without a developer adding an endpoint,
a relation, a view or a compiler node.

**Why this priority**: It is the requested flexibility, stated plainly.
**Independent Test**: Adversarial fixtures yield independently calculated expected
results for multi-hop traversal, period comparison, grouping and ranking.

**Acceptance Scenarios**:
1. Given customers present in one or both periods, a prior-year comparison includes the
   correct customers and counts each stated order amount exactly once.
2. Given a new combination of declared nodes and edges, execution requires no new
   application endpoint, database object or compiler node.
3. Given multiple currencies and missing line amounts, monthly product ranking uses
   received line amounts, retains currency and invents no missing value.
4. Given a misleading raw aggregate, the result is not presented as a certified business
   metric merely because it executed; its path and available evidence are visible.

### User Story 2 - An aggregation that cannot silently double count (Priority: P1)

The same analyst extends the path from order to order line to item and asks for order
value by item. The order-level measure is folded to order grain before summation, or the
request is refused with an actionable message. It is never silently multiplied.

**Why this priority**: This is the reason the model exists. Without it the platform is a
faster way to produce confident wrong numbers, which is worse than the rigid version.

**Independent Test**: A EUR 1,000 order with four lines returns 1,000, not 4,000, on
every surface; the equivalent hand-written SQL and Cypher returning 4,000 are recorded
as the counterexample in the same test.

**Acceptance Scenarios**:
1. Summing an order-grain measure along a 1:n edge folds to order grain or is refused.
2. Summing amounts across two currencies is refused, not silently combined.
3. A measure declared non-additive over time is refused when grouped over time.
4. Counting distinct nodes after fan-out returns the node count, not the path count.
5. A reversed ledger posting and a corrected movement net out in a measure sum, while a
   naive row count over the same rows is refused rather than returned inflated.

### User Story 3 - Retain and reuse the executed report (Priority: P1)

The analyst reloads, reviews, confirms and reopens the exact executed definition.

**Why this priority**: Preserve spec 222's shipped bug fix through the replacement.
**Independent Test**: Chat, CLI and HTTP share one definition, parameters and results;
a lost save response and a retry create one report.

**Acceptance Scenarios**:
1. Two drafts remain distinct across reload; saving copies the selected draft exactly.
2. Revoked membership and foreign owner or tenant references fail without disclosure.
3. A report saved by the graph reopens with equivalent values, identity and ownership,
   and records the model version that produced it. No definition from an earlier
   generation is reinterpreted, because none is carried forward.

### User Story 4 - Understand time and evidence (Priority: P1)

The analyst distinguishes current retained state, dated activity and a past state, and
navigates from a number to the records behind it.

**Why this priority**: Broad querying must not turn incomplete history into certainty.
**Independent Test**: A late source correction changes a current observation without
claiming the prior state can be reconstructed from the latest row.

**Acceptance Scenarios**:
1. Sales ordered in a date range are labelled by order date and retained evidence, not
   as an as-of reconstruction and not as accounting revenue.
2. Unsupported as-of or knowledge-time requests fail before execution with a coverage
   limitation; filtering today's rows is never silently substituted.
3. A result exposes its traversal path, bound period, model version, observation time
   and authorised evidence route. The path is the derivation, not a generated
   explanation alongside it.

### User Story 5 - Extend the model by declaration (Priority: P2)

A new relationship — a bill of materials, nested handling units, a party hierarchy —
becomes queryable by declaring a node, an edge and a measure, including at variable
depth, without touching the query compiler.

**Why this priority**: It is what makes the platform future-oriented rather than merely
flexible today, and it is the property the two previous attempts lacked.

**Independent Test**: A recursive edge added only as a declaration answers a
variable-depth question, with depth bound and cycle protection, and no compiler change.

**Acceptance Scenarios**:
1. A declared recursive edge answers a bounded variable-depth traversal; an unbounded
   request is refused rather than executed.
2. A cyclic instance terminates and is reported, rather than exhausting resources.
3. A node or measure declared without grain, unit or additivity is rejected at
   declaration time, not at query time.
4. An extension node backed by `fact` obeys the same three declarations as a table node.

### User Story 6 - Share capacity safely (Priority: P2)

Concurrent reporting stays bounded and cannot disclose another company's data.

**Why this priority**: The trust boundary must be proven even though the author no longer
writes SQL, because the compiler now carries the whole burden.

**Independent Test**: Adversarial authoring attempts across two tenants with overlapping
labels and foreign canary values, plus timeout, cancellation and pool reuse tests.

**Acceptance Scenarios**:
1. No authoring input — identifier, parameter, label, depth or path — can reach SQL text
   or cause a node to be read without its tenant predicate.
2. Cancellation, timeout and oversized results never return partial totals as complete.
3. Capacity measurements record shape, hardware, concurrency and ingestion impact;
   unexecuted scale stages are explicitly recorded as unverified.

### Edge Cases

Fan-out along two sibling edges in one path; a measure reachable by two different paths
of different multiplicity; recursive edges with cycles, self-references and unbounded
depth; NULL versus zero; mixed currencies and units; a node with no rows in a period;
an edge whose foreign key is nullable; declaration drift against a migrated schema;
stale model version in a saved report; error-message disclosure; failed cutover;
late corrections and reversals; unsupported temporal coverage.

## Requirements

### Functional Requirements

- **FR-001**: Declare the reporting graph as versioned machine-readable data: nodes with
  grain, key, table, tenant column and correction semantics; edges with direction,
  multiplicity, recursion and the column or join that carries them; measures with node,
  source, unit and additivity. A declaration missing any of these is rejected before it
  is published.
- **FR-002**: Publish a discoverable catalog generated from that declaration: which nodes
  exist, how they connect, which measures they carry, what each measure means, what
  temporal coverage it has and which evidence route it exposes.
- **FR-003**: Execute a traversal query — path match, property filter, bounded
  variable-depth traversal over recursive edges, grouping, ordering, limit — by compiling
  it to one PostgreSQL statement with bound typed parameters.
- **FR-004**: Refuse or correctly fold any aggregation over a path that fans out. A
  measure is summed only at its declared grain. Silent multiplication is a defect, not a
  user error, and every refusal names the edge that caused it.
- **FR-004a**: Apply each node's declared correction semantics. A `revise` node resolves
  to its latest revision before aggregation; a `compensate` node permits measure sums over
  all rows, including corrections, but refuses a naive row count and offers a distinct
  count of corrected events. This is a second and independent way to count something
  twice, and it is handled structurally rather than by query review.
- **FR-005**: Enforce declared units and additivity. Amounts in different currencies are
  never combined; a measure declared non-additive over an axis is refused when grouped by
  that axis. Unknown values stay unknown and are never reconstructed.
- **FR-006**: Emit the tenant predicate on every node from the authenticated principal.
  No authoring input reaches SQL text. This replaces barrier views, per-tenant database
  roles and PUBLIC-grant provisioning entirely; row-level security on base tables may be
  added as independent defence in depth but is not the primary boundary.
- **FR-007**: Provide two authoring surfaces that compile to one internal query form: a
  typed query object, and a Cypher-near traversal text. Path matching and filtering
  follow Cypher conventions; aggregation references declared measures rather than free
  arithmetic over properties, and this deliberate divergence is documented.
- **FR-008**: Preserve the shared prepare, review, confirm, save and reopen services with
  immutable private drafts, retry semantics, exact integers and decimals, and ownership
  checks, across chat, CLI, web and export.
- **FR-009**: Publish current, activity-period and as-of coverage separately, per node.
  Unsupported historical and knowledge-time questions fail explicitly before execution.
- **FR-010**: Explain a result through its traversal path and the authorised underlying
  records. The path is the derivation. Declare exact-contributor capability honestly and
  never fabricate contributor membership.
- **FR-011**: Bound admission, traversal depth, elapsed execution, result size and
  database resources; protect against cycles; cancel cleanly; never use the operational
  connection identity for reporting execution.
- **FR-012**: Record the model version that interpreted each saved report. No
  compatibility layer for earlier definitions is built: spec 222 was never committed and
  never shipped, so there is no deployed artifact to preserve, and the owner decided on
  2026-09-17 to discard the local development reports rather than carry a version
  mapping. The replaced generation — the configured catalog, comparison, contributors,
  finance and operations readers — is removed in the same change that makes the graph
  live, so the product is never without Analytics and two paths never coexist.
- **FR-013**: Extend the model by declaration only. A new node, edge or measure — table
  backed or `fact` backed — requires no compiler change, and requires grain, unit and
  additivity before it can be aggregated.
- **FR-014**: Keep the stored query form free of SQL dialect, so a different execution
  backend is a compiler change rather than a migration of stored artifacts. A second
  engine remains unauthorised and is revisited only under the deferred measurement
  trigger recorded in `engine-comparison.md`.

### Domain Requirements

- **DR-001**: Preserve Source → Evidence → Reality and shortest opaque evidence links.
  Operational state stays derived from Reality and is never owned by document status.
- **DR-002**: Preserve received amounts, currency and unit separation and unknown values.
  Measures bind to canonical services and declare their grain; a user's grouping is a
  user calculation, not new stored authority.
- **DR-003**: Add no operational business table, stored report result, snapshot authority,
  materialised projection, recurring job or second database. The model declaration is
  configuration, not business data.

### Key Entities

Reporting-graph declaration (nodes, edges, measures, versioned); traversal query
definition; immutable private draft; query observation; temporal coverage descriptor;
authorised evidence reference. Existing report and draft records remain their storage
owners.

## Success Criteria

- **SC-001**: First-slice customer period comparison and monthly product ranking,
  including missing customers, duplicate lines and two currencies, match all
  independently calculated expected values.
- **SC-002**: Every fan-out fixture either folds correctly or is refused with the causing
  edge named; no fixture returns a silently multiplied total. The equivalent hand-written
  SQL counterexample is recorded alongside each.
- **SC-003**: All save, reopen, retry and isolation cases pass across shared adapters,
  and every spec-222 saved artifact reopens with equivalent values.
- **SC-004**: Every result states its temporal coverage and explanation capability; all
  unsupported as-of fixtures fail explicitly with no substituted current-state answer.
- **SC-005**: No foreign canary and no business mutation is observed in the adversarial
  suite; no authoring input reaches SQL text; cancellation releases admission and
  connections for subsequent valid queries.
- **SC-006**: A recursive edge, a node and a measure are added by declaration alone, and
  a variable-depth question is answered with no change to the query compiler.
- **SC-007**: A reproducible capacity report records measured and unrun stages without a
  production-scale claim, and no report-specific endpoint exists for any of the first
  slice questions.

## Assumptions and Dependencies

- The owner accepted this direction after rejecting filter-configuration, the bespoke SQL
  subset and user-authored SQL in turn. This artifact plans that direction; it does not
  claim a deployed replacement.
- PostgreSQL is the only supported database; local Compose targets version 17. Recursive
  traversal uses recursive common table expressions. No extension is introduced; Apache
  AGE is explicitly not adopted, because it stores its own graph copy rather than
  querying the existing tables.
- **Spec 222 was never committed.** `sql_compile.py`, `sql_parser.py`,
  `reporting_relations.py`, migration 0062 and the SQL editor exist only as uncommitted
  work in one shared working tree; the git history contains none of them. This feature
  therefore branches from `main` and does not carry that generation forward. Nothing is
  deleted to achieve that.
- What `main` actually carries, and what this feature replaces, is the configured
  generation: `services/analytics/catalog.py`, `comparison.py`, `contributors.py`,
  `finance.py`, `operations.py`, with `AnalyticsExplorer.tsx`, `AnalyticsPivot.tsx` and
  `useAnalyticsExecution.ts` on the web side.
- The saved reports Q01 and Bene 1 exist only in the local development database, because
  migration 0062 is not on `main`. The owner decided on 2026-09-17 to discard them.
- The typed tables are the substrate. `fact` remains the extension mechanism for objects
  the schema does not model, not the primary analytical store.
- `location.parent_location_id` is the only recursive edge in the schema today. Bills of
  material, nested handling units and party hierarchies are anticipated, not present.
- Measures bind to existing canonical services. No new accounting or revenue-recognition
  rule and no typed finance model is authorised here.
- Architecture is checked against the roughly 5,000-tenant bounded-connection deployment
  in ADR 0004, not only a single-tenant local demo.
- `sqlglot` is already a pinned dependency and `sql_parser.py` already implements
  parse-then-admit. The traversal frontend reuses that shape.

## Requirement Traceability

| Requirement | Acceptance | Planned evidence |
|---|---|---|
| FR-001 | US1.2, US5.3 | T002/T003 declaration schema and validation |
| FR-002 | US1.1–2, US4.3 | T003/T009 generated catalog |
| FR-003 | US1.1–3 | T004/T005 traversal compilation and sales fixtures |
| FR-004 | US2.1, US2.4 | T004/T005 fan-out fixtures and counterexamples |
| FR-004a | US2.5 | T004/T005 correction and reversal fixtures |
| FR-005 | US2.2–3 | T004/T005 unit and additivity fixtures |
| FR-006 | US6.1 | T006/T007 adversarial authoring and isolation |
| FR-007 | US1.1, US3.1 | T008/T009 dual-surface parity |
| FR-008 | US3.1–3 | T010 lifecycle and exact values |
| FR-009 | US4.1–2 | T011/T012 temporal coverage |
| FR-010 | US1.4, US4.3 | T005/T012 path-derived evidence |
| FR-011 | US5.1–2, US6.2 | T007/T013 depth, cycle and budget controls |
| FR-012 | US3.3 | T010/T014 parity and cutover |
| FR-013 | US5.1–4 | T015 declaration-only extension proof |
| FR-014 | non-goals | T016 deferred measurement trigger |
| DR-001 | US4.3 | T005/T012 canonical evidence |
| DR-002 | US1.3, US2.2 | T003/T005 amount and grain correctness |
| DR-003 | US5, non-goals | T002/T014/T016 architecture review |
