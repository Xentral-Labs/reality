# Implementation Plan: Graph-Native Reporting Platform

**Date**: 2026-09-17 | **Spec**: [spec.md](spec.md)
**Working branch**: Existing shared working tree; no switch or commit.
**Status**: Design only. Direction accepted; every executable proof is open. No database
object, migration or runtime configuration has been changed.

## What changed against the previous revision

The earlier plan had two halves that are both withdrawn.

**User-authored SQL is withdrawn.** With it go the barrier views, the per-tenant database
roles, the PUBLIC-grant audit, the role lifecycle question against ADR 0004's tenant
count and the `SET SESSION AUTHORIZATION` design. They existed only because untrusted
SQL text needed a boundary inside the database. No authoring input reaches SQL text any
more, so the boundary moves back to the compiler, where it already is for every other
read in the product — and where it is enforced by construction rather than by
provisioning that has to be maintained for roughly 5,000 tenants.

**The engine comparison is withdrawn as a gate.** It is preserved as a deferred
measurement with an explicit trigger in [engine-comparison.md](engine-comparison.md). The
stored query form carries no SQL and no dialect, so choosing a different execution
backend later is a compiler change, not a migration of saved artifacts. That is what
makes deferral safe; it is not a judgement that the question was uninteresting.

## Summary

Declare the reporting graph over the existing typed tables. Compile traversal queries to
single PostgreSQL statements. Keep spec 222's prepare, confirm, save and reopen journey
unchanged. Deliver sales first, then the finance branches that sales comparison needs.
Retire `sql_compile.py` only after parity.

## Technical Context

Language: Python 3.12, SQLAlchemy 2, PostgreSQL 17, `sqlglot` 27.29.0 already pinned.
Web: React and TypeScript under `apps/web`. The traversal frontend reuses the
parse-then-admit shape already implemented in `sql_parser.py`; the declaration is YAML
configuration under `packages/reality-core/config/`, validated on load and in tests.

Recursive edges compile to recursive common table expressions. No database extension is
introduced. Apache AGE is explicitly rejected: it stores its own graph copy in
`ag_catalog` rather than querying the existing tables, which would reintroduce the
second-copy problem inside the same database, together with `agtype` numeric semantics
that are unsuitable for money. SQL/PGQ is the standardised form of this design and is
worth re-checking when it reaches PostgreSQL core; it is not assumed available.

## Constitution Check

| Principle | Assessment |
|---|---|
| I. Source → Evidence → Reality | Preserved. The traversal path *is* the evidence route; every node declares its shortest opaque link. |
| II. Reality is operational authority | Preserved. Reporting reads; nothing here owns operational state. |
| III. Proven schema only | No schema change. The declaration is configuration validated against the live schema, and drift fails a test. |
| IV. Tenant and service boundaries | Strengthened. The tenant predicate is emitted on every node by construction; new public functions are classified in `tenant_isolation_catalog.yaml` and the pinned count is bumped. |
| V. Specification and test evidence | Every task below is test-first; no task is complete without recorded evidence. |
| VI. Explainable web product | The path is shown, not a generated explanation; refusals name the causing edge. |
| VII. Simplicity and storage discipline | Net removal: the bespoke compiler goes, and the withdrawn view and role provisioning never arrives. No new table, no materialisation, no job. |
| VIII. Received values recorded, never recomputed | Enforced in the declaration: unknown stays unknown, no `unit_price * quantity` reconstruction, units never mixed. |

No principle requires an exception. The complexity that the previous revision would have
added — database roles per tenant, barrier views, a second engine — is removed rather
than justified.

## Repository Structure

    packages/reality-core/
      config/reporting_graph.yaml              new: the declaration
      src/reality/domain/reporting_graph.py    new: declaration types and validation
      src/reality/services/analytics/
        graph_model.py                         new: load, validate, publish catalog
        traversal.py                           new: query form, grain and unit checks
        compile_sql.py                         new: traversal → SQLAlchemy statement
        cypher_surface.py                      new: Cypher-near text → query form
        execution.py                           changed: bounded execution
        lineage.py                             changed: path-derived evidence
        sql_compile.py                         removed at cutover
        sql_parser.py                          reduced to v1 compatibility at cutover
      tests/test_reporting_graph_*.py          new
    apps/web/src/unified/analytics/            changed: traversal editor and catalog

## Design: the compiler carries the boundary

Every node in a compiled statement receives its tenant predicate from the authenticated
principal. Authoring input becomes bound parameters and declaration lookups; no path,
identifier, label or depth is ever concatenated into SQL. This is the same boundary the
other roughly 233 tenant-scoped reads in `services/core.py` already rely on, applied in
one place instead of hand-written per query.

Row-level security on base tables is a worthwhile independent layer and is listed as a
follow-up, not as this feature's boundary. It is cheaper than per-tenant roles because it
needs no provisioning, but it must not become an excuse for a compiler that forgets a
predicate: the adversarial suite asserts the predicate directly.

## Design: grain, fold, refuse

The compiler computes the effective grain of a path, compares it to each measure's
declared grain, and then folds, aggregates or refuses. This is the whole feature in one
sentence, and the fixtures in T004 are its specification: a EUR 1,000 order with four
lines returns 1,000, and the hand-written SQL that returns 4,000 is recorded in the same
test as the counterexample, so the guarantee is visible rather than assumed.

Independent branches are compiled as separate aggregates joined on the grouping keys.
A chain would multiply order value, invoiced amount and allocated amount against each
other; this is the E03 question from the previous revision, and it is the reason the
rule is structural rather than advisory.

## Design: extension without compiler change

A node, an edge or a measure is a declaration. A recursive edge additionally declares its
depth bound and cycle policy. The proof that this works is T015: add a recursive edge and
answer a variable-depth question with no diff outside configuration and its test.

`fact`-backed extension nodes obey the same rules, with an explicit cast for the text
value; a failed cast is an error and never a zero.

## Migration and Rollback

Existing v1 SQL definitions keep their stored envelope and are read through an explicitly
tested mapping. Stored drafts are never rewritten. Cutover removes the relational
lowering only after Q01 and the saved report Bene 1 reopen with equivalent values.
An incompatible rollback disables Analytics and preserves artifacts; there is no silent
fallback to the retired compiler.

## Delivery order

Declaration and validation, then the sales slice with its fan-out fixtures, then
isolation and budgets, then the dual authoring surfaces, then lifecycle and temporal
work, then extension proof, then cutover and documentation. The fan-out fixtures come
before the compiler that satisfies them, because they are the acceptance criterion for
the whole design.

## Complexity Tracking

| Added | Justification | Simpler alternative rejected because |
|---|---|---|
| A declaration layer | It is the only place grain, multiplicity and additivity can live | Inferring them from foreign keys gets multiplicity right and meaning wrong |
| Two authoring surfaces | An LLM authors objects reliably and people read paths reliably | One surface forces either unreadable JSON on people or free text on the model |
| A Cypher divergence in `RETURN` | Literal Cypher reintroduces the silent multiplication | Full Cypher compatibility would make the central guarantee unenforceable |

Removed by this plan: the bespoke relational compiler, barrier views, per-tenant roles,
PUBLIC-grant provisioning and the second-engine decision gate.
