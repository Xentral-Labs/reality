# Analytics and private reports

Spec: [224](../../specs/224-native-reporting-platform/spec.md). It replaced the
configured generation of [185](../../specs/185-analytics-workspace/spec.md), whose
fifteen fixed datasets could only answer questions somebody had anticipated.

## What is declared

PostgreSQL remains the only database, and no records are copied. A declaration —
`packages/reality-core/config/reporting_graph.yaml` — says which existing tables are
business records (**nodes**), how they connect (**edges**), and what may be counted
(**measures**). Four things are mandatory, because each one is a way to be wrong:

- **Grain** on a node: what one row is. Without it a count has no unit.
- **Multiplicity** on an edge: `n:1` or `1:n`. It is what tells the compiler that a
  hop fans out, and a total taken after a fan-out is multiplied.
- **Unit and additivity** on a measure: amounts in different currencies are not added,
  and a stock level is a state, so it does not add up over time.
- **Corrections** on a node: whether a correction replaces, revises or compensates.

Nothing is materialized. Adding a node, an edge or a measure is a change to the
declaration, not a migration, a view or a compiler branch.

## Asking

A question is a checked object — a path, some filters, some measures — never SQL
text. Two surfaces produce it and both compile to the same object:

- the typed traversal accepted by `graph_ask` and `POST /analytics/graph/ask`;
- a Cypher-near path syntax for people who would rather type it.

The path syntax follows Cypher for matching and filtering. It deliberately diverges
in one place: aggregation names a declared measure instead of doing arithmetic over
properties, because the declaration is what knows whether the arithmetic is sound.

Whatever is asked, the compiler emits **one** statement and puts the tenant predicate
on **every** node in it, including inside recursive terms and existence tests. That is
why the model needs no barrier view and no role per company. Each request owns a
read-only transaction with a statement timeout, a bounded traversal depth and a
bounded result size.

## Refusals

A question that cannot be answered correctly is refused with a stable code and a
sentence, rather than answered with a number that is wrong:

| code | what it means |
| --- | --- |
| `fan_out` | summing here would multiply the total |
| `unit_mismatch` | the values are not in the same unit |
| `not_additive` | the number is a state, not a flow |
| `not_temporal` | the field is not kept as a date, so it has no period |
| `measure_unreachable` | the path never reaches the record that number lives on |
| `depth_exceeded`, `path_too_long` | the traversal is bounded, and this exceeds it |

A hop that is filtered but never referenced narrows to `EXISTS` instead of joining, so
it cannot multiply anything. A hop that *is* referenced after a fan-out is refused by
name. Money partitions by currency, quantity by unit; no conversion is introduced.

## Agent operation

1. Call `graph_catalog` to discover the records, connections and measures this company
   declares, in the reader's language.
2. Call `graph_ask` with a traversal, or with a path string.
3. Read the refusal if one comes back. It names the edge that fanned out or the unit
   that cannot be added; asking the same question again will not help.

## Web and persistence

The sidebar lists Analytics last under Workspaces, after Master data, with no separate
Analytics group. Its name and tooltip are Analytics in every language (spec 221).
Default links and links naming a retired view open the business graph.

The page builds a question as an ordered stack of steps — start, reach, narrow, count,
split, sort, bound — where each step offers only what the declaration makes valid at
that point, and a hop says whether it fans out before it is taken. A query console
beside it takes the path syntax directly and shows the statement it became.

`analytics_report` stores a saved report: the **question**, never its answer, with the
model version that gave it meaning, its owner, a revision and a retry key. Reopening
one re-executes it, so what comes back is a fresh observation rather than a preserved
number — the only honest thing a report can be when the records underneath it keep
changing. Reports are private to their author, and every change is confirmed
explicitly. Migration 0062 added `kind` and `model_version` additively.

Reports saved by the configured generation are still in the table with neither column
set. Nothing reads them, and nothing writes over them: they belonged to a generation
that was replaced rather than translated.
