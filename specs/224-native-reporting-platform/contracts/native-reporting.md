# Traversal Reporting Service Contract

Proposed. Not a description of the currently active spec-222 compiler.

## Shared entry points

Keep the analytics catalog, query, draft prepare and get, proposal save, report get,
export and evidence application services. Transport adapters neither open database
connections nor build queries. Saving remains explicit preview and confirmation.

## Authoring surfaces

Two surfaces compile to one internal query form, and the internal form is what is
stored, fingerprinted and executed.

**Typed query object.** Nodes, path, filters, measures, grouping, ordering, limit as
validated structured data. This is what chat and the API author, because a constrained
object is checkable before execution and an LLM produces it far more reliably than it
produces correct text.

**Cypher-near traversal text.** For people who want to read and write the path directly:

    MATCH (k:party {id: $customer})<-[:ordered_by]-(o:order)
    WHERE o.ordered_at >= $from AND o.ordered_at < $until
    RETURN month(o.ordered_at), o.currency, sum(stated_order_amount)

Path matching and filtering follow Cypher conventions. Aggregation deliberately does
not: `RETURN` references declared measures, not free arithmetic over node properties.
Literal Cypher would allow `sum(o.gross_amount)` along a fanned-out path and return a
multiplied total without complaint, which is precisely the defect this feature exists to
remove. The divergence is documented in the catalog and in the editor's help.

Both surfaces are parsed and then admitted against a positive list, the shape already
established by `sql_parser.py`. Neither surface produces SQL text.

## Admission

Admitted: a declared path, declared property filters, bounded variable-depth traversal
over declared recursive edges, declared measures, grouping, a filter on an aggregated
measure (`having`), an existence test over a declared sub-path, ordering by grouped
expressions and measures, a bound limit, and typed bound parameters.

Not yet admitted, and recorded as the next capability question rather than as an
oversight: window expressions over ordered events — "the customer's second order",
retention curves, cohort and gap analysis. These need declared window forms with their
own grain rules; free window arithmetic would reopen the silent-multiplication hole.

Refused: an undeclared node, edge or measure; an unbounded depth; a write of any kind;
session or catalog access; an arbitrary function; free arithmetic standing in for a
measure; an aggregate whose grain, unit or additivity check fails.

A refusal is stable, sanitised and actionable. A fan-out refusal names the edge that
caused it and offers the measure that lives at the traversed grain. A unit refusal names
both units. These messages are the product, not an error path.

## Trust boundary

The authenticated principal determines the tenant. The compiler emits the tenant
predicate on every node in the statement. Authoring input becomes bound parameters and
declaration lookups, never SQL text, so there is no injection surface to defend and no
barrier view, per-tenant role or PUBLIC-grant audit to maintain.

Reporting executes under its own connection identity, never the operational one.
Membership is rechecked on every operation. Row-level security on base tables may be
added as independent defence in depth; it is not the primary boundary and does not
replace the compiler's obligation.

## Result and evidence

Return exact numeric text, typed columns, observation and coverage, definition
fingerprint, model version and explanation capability. Always expose the traversal path
and bindings: the path is the derivation, not an explanation generated beside it.

`exact_contributors` is available only where the traversal establishes actual result
membership; otherwise an exact request fails with `evidence_capability_unavailable`.
Input browsing is labelled input browsing. An unverified grouping stays a user
calculation and chat may not call it certified.

Top-N is resolved before response pagination. Stable paging requires a deterministic
order; otherwise return a single bounded result or an actionable ordering error.
Oversized results fail explicitly. CSV retains exact values and formula escaping.

## Temporal requests

`current` and `activity_period` are available only for nodes that declare them. Business
period bounds are half-open and resolved with a declared timezone. `as_of_effective` and
`as_of_knowledge` are reserved, rejected until backed by a tested history model, and
never silently downgraded to current rows.

## Compatibility and mutation

The stored definition records its model version. Preserve report identity and ownership.
Compatibility tests must prove spec-222 v1 semantics before any mapping is accepted.
Pending proposals retain their sealed meaning; an unknown version fails clearly.
Preparation persists a draft only after successful execution. A retry returns its
original receipt; a rerun produces a fresh observation. Confirmation uses the existing
report services unchanged.
