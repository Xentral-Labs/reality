# Research: Canonical Core Catalogs

## Split by semantic lifecycle, compose in Python

**Decision:** Use four reviewed YAML files and one loader.  
**Rationale:** Categories have different contracts and drift rules; consumers still
need one stable view.  
**Alternatives:** One YAML retains weak ownership; Python-only registries duplicate
documentation; a generator framework is excess scope.

## Explicit public Command registry

**Decision:** Catalog membership defines public Commands.  
**Rationale:** Service functions mix public use cases and internal compositions.  
**Alternatives:** Naming heuristics and adapter-route inference misclassify helpers.

## AST Event completeness

**Decision:** Compare literal emission calls with catalog types.  
**Rationale:** Deterministic and offline.  
**Alternatives:** Runtime tracing needs exhaustive scenarios; database samples miss paths.

## Runtime Projection completeness

**Decision:** Compare materialization names with `OPERATIONAL_PROJECTIONS`.  
**Rationale:** That registry controls accepted reads and rebuilds.  
**Alternatives:** Generated constants are outside scope; builder inference is brittle.

## Explicitly empty Fact vocabulary

**Decision:** Start with no stable predicates.  
**Rationale:** Generic Facts exist, but no repeated production predicate contract does;
inventing one violates Proven Schema. `fact.observed` remains an Event.  
**Alternatives:** Test predicates are incidental; stored tenant values are not contracts.

## Tenant-authenticated reference

**Decision:** Reuse membership for a global metadata response.  
**Rationale:** Fits Processing without exposing business rows.  
**Alternatives:** Public exposure is unnecessary; frontend bundling duplicates sources.

