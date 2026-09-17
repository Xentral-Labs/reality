# Graph-Native Reporting Research

Date: 2026-09-17. Repository, PostgreSQL 17 documentation and graph-database
documentation reviewed. Conclusions are local design analysis, not an independent
security audit and not an executed measurement.

## Decision: a declared property graph, not a graph database

The requested model is a property graph: objects with properties, connected by named
relationships, where the same child can be referenced by many parents. That model is
right for an ERP, and it already exists in the schema — roughly seventy typed tables
whose foreign keys are the edges.

What a property graph cannot supply by itself is the meaning of an aggregate. Cypher has
the same fan-out defect as SQL: traversing `order → order_line` and summing an
order-level amount multiplies it by the line count, and `RETURN DISTINCT` addresses sets
but not sums. Grain, multiplicity and additivity have to be declared in either world.
Since they must be declared anyway, the declaration is the product, and the storage
engine is a separate question.

## Decision: PostgreSQL remains the engine

| Candidate | Verdict |
|---|---|
| Neo4j | Rejected for this workload |
| ArangoDB | Rejected for this workload |
| Apache AGE | Rejected on architecture |
| SQL/PGQ | Right direction, not assumed available |
| PostgreSQL with a declared model | Selected |

**Exact decimals decide it.** Every amount in the schema is `Decimal` over PostgreSQL
`NUMERIC` — `document.gross_amount`, `document_line.unit_price`, `document_line.quantity`,
`settlement_allocation.amount`. Neo4j's property types are 64-bit Integer and IEEE 754
Float, with no arbitrary-precision decimal; ArangoDB's AQL arithmetic is double based.
Storing minor units as integers is a workaround, but percentages, tax and currency
handling degrade and the exactness the whole specification series insists on becomes a
property of application discipline instead of the type system. This should be re-verified
against current documentation before any reconsideration, because it is the single
decisive point.

**Tenant isolation.** Roughly 5,000 tenants. Neo4j offers a database per tenant, which is
heavy at that count, or a tenant property enforced by convention. ArangoDB is comparable.
PostgreSQL enforces the boundary in the engine, and the compiler emits the predicate
structurally. Tenant isolation is a pinned, counted catalog invariant in this repository;
moving it to convention would be a regression that no benchmark could offset.

**Workload shape.** Graph engines optimise deep traversal. This workload is shallow
traversal with heavy aggregation — two or three hops over many rows with sums and
grouping — which is the relational engine's strength and the graph engine's weakness.
Adopting one for analytics would trade the strong case for the weak one.

**Apache AGE** stores vertices and edges in its own `ag_catalog` tables with `agtype`
properties. It cannot query `document` and `party` in place, so it would require copying
the ERP into a second representation inside the same database, reintroducing the
second-copy problem the design exists to avoid, plus `agtype` numeric semantics for money.

**SQL/PGQ** (SQL:2023) is exactly this design standardised: a property graph declared
over existing vertex and edge tables. Its availability in PostgreSQL core was still in
progress at the time of writing and must be re-checked rather than assumed. If it lands,
the declaration in `config/reporting_graph.yaml` maps onto it directly, which is a reason
to keep the declaration engine-neutral.

Sources reviewed: [Neo4j Cypher concepts](https://neo4j.com/docs/cypher-manual/current/queries/concepts/),
[Neo4j property types](https://neo4j.com/docs/cypher-manual/current/values-and-types/property-structural-constructed/),
[ArangoDB multi-model](https://arangodb.com/multi-model/),
[Apache AGE](https://age.apache.org/age-manual/master/intro/overview.html),
[PostgreSQL recursive queries](https://www.postgresql.org/docs/current/queries-with.html),
[PostgreSQL JSONB](https://www.postgresql.org/docs/17/datatype-json.html).

## Decision: the compiler is the trust boundary

The previous revision needed barrier views and per-tenant database roles because a user
could write SQL text. Without that text there is nothing to escape from: authoring input
becomes bound parameters and declaration lookups. The boundary returns to the compiler,
which is where every other tenant-scoped read in the product already enforces it.

Row-level security on base tables remains attractive as independent defence in depth. It
needs no per-tenant provisioning, unlike roles, and it does not depend on the compiler
being correct. It is recorded as a follow-up, not as this feature's boundary, and the
adversarial suite asserts the emitted predicate directly rather than relying on either.

## Decision: a Cypher-near surface, with one deliberate divergence

Cypher's `MATCH` and `WHERE` are a good notation for paths and filters, and people read
them. Cypher's aggregation is not adopted: `RETURN` references declared measures rather
than free arithmetic over properties, because free arithmetic along a fanned-out path
returns a multiplied total without complaint. Adopting the syntax wholesale would import
the defect the model was built to eliminate.

A typed query object stands beside the text surface. A constrained object is checkable
before execution and is produced far more reliably by a language model than correct text,
which matters because chat is the primary way questions will be asked.

`sqlglot` is already pinned at 27.29.0 and `sql_parser.py` already implements
parse-then-admit against a positive list. The traversal frontend reuses that shape.

## Decision: no materialisation in this feature

A declared traversal compiles to a statement against base tables. Ordinary indexes may be
added later as measured performance work. Materialised projections, columnar storage and a
second engine are an escalation ladder to climb only when a measurement demands it, in
that order, and each step keeps a single authoritative copy longer than the next.

## Decision: separate query freedom from certified semantics

A database cannot infer which business amount a user intended. Measures bind to canonical
services, keep their grain and evidence route, and a user's grouping stays a user
calculation rather than new stored authority. The traversal path is returned as the
derivation; exact-contributor support is declared honestly and never fabricated.

## Decision: explicit temporal coverage

Retained source versions are evidence of change, not a universal reconstruction of
mutable commitments, reservations or allocations. The first slice uses current retained
evidence with business dates. Point-in-time and knowledge-time reporting require separate
coverage proofs before publication, and an unsupported request fails rather than
silently returning today's rows.
