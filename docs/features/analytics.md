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

A measure may also be a **difference**: a declared measure taken off its own column
along a declared path — promised less moved, ordered less billed. "What is still open"
is what an operational report is really asking, and it is never one column. It compiles
to a correlated subquery and never a join, because a join to the far side would repeat
the row once per movement and multiply the number it is supposed to be reducing. Both
sides must be the same kind of unit, and a difference of differences is refused.

Where a canonical service already derives the number — a receivable balance, which
covers opening items, several document types and reversal groups — the measure binds to
that service instead. A second, simpler derivation beside it would be the more dangerous
kind of wrong, because it would agree most of the time.

Nothing is materialized. Adding a node, an edge or a measure is a change to the
declaration, not a migration, a view or a compiler branch.

## Asking

A question is a checked object — a path, some filters, some measures — never SQL
text. Two surfaces produce it and both compile to the same object:

- the typed traversal accepted by `graph_ask` and `POST /analytics/graph/ask`;
- a Cypher-near path syntax, reachable through the tools and the CLI; the browser
  surface for it was withdrawn, because nobody reads a path syntax to answer a
  business question.

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

| code                              | what it means                                                  |
| --------------------------------- | -------------------------------------------------------------- |
| `fan_out`                         | summing here would multiply the total                          |
| `unit_mismatch`                   | the values are not in the same unit                            |
| `not_additive`                    | the number is a state, not a flow                              |
| `not_temporal`                    | the field is not kept as a date, so it has no period           |
| `measure_unreachable`             | the path never reaches the record that number lives on         |
| `depth_exceeded`, `path_too_long` | the traversal is bounded, and this exceeds it                  |
| `service_measure`                 | the number comes from a canonical service this path cannot run |

A hop that is filtered but never referenced narrows to `EXISTS` instead of joining, so
it cannot multiply anything. A hop that _is_ referenced after a fan-out is refused by
name. Money partitions by currency, quantity by unit; no conversion is introduced.

## An empty answer

An empty answer means one of two very different things: nothing matched, or the question
named something no record carries. Only the first is about the business.

Two things keep them apart. A column with a short fixed vocabulary — a type, a status, a
channel — publishes the words this company's records actually use, read from the company
rather than declared, so nobody has to guess one. And when an answer is empty, every
equality filter whose value appears on no record at all is named back to the caller as
`matched_nothing`. Nothing may present an empty result as a fact about the business when
the question itself did not match the data.

## Agent operation

1. Call `graph_catalog` to discover the records, connections and measures this company
   declares, in the reader's language. It also carries each node's identity, so two
   records that share a name can be kept apart, and the vocabulary of every
   short-value column.
2. Call `graph_ask` with a traversal, or with a path string.
3. Read the refusal if one comes back. It names the edge that fanned out or the unit
   that cannot be added; asking the same question again will not help.

## Templates

Six questions worth starting from are declared beside the model — an open delivery
backlog, incoming supply, order intake by customer, order value by month, ordered but
not billed, stock movements by article. They live in the declaration because they name
nodes, edges and measures: one that cannot be resolved stops the model from loading
rather than waiting to be clicked and refused, and every one of them is executed against
real records by a test.

A template carries no absolute date. Where it means a period it names the window —
`this_month`, `last_year` — and whoever adopts it resolves that against their own
calendar, because a template that hard-codes a month is wrong the following month.
Taking one over creates an ordinary private report: same ownership, revision and retry,
and the reader can change it from there.

What is not a template is as deliberate as what is. Order value by currency is a required
axis, not a report. Returns have no authoritative link to their credit yet.

## Web and persistence

The sidebar lists Analytics last under Workspaces, after Master data, with no separate
Analytics group. Its name and tooltip are Analytics in every language (spec 221).
Default links and links naming a retired view open the business graph.

The page opens on the records rather than on an empty builder: picking a record type
shows those records, and the rest happens on the result — a value filters, a column
header sorts, the row count sits under the table. Two things are asked in words, what to
count and what to split it by, and several numbers may stand side by side.

A connection is offered from everywhere the question has already reached, not only from
its last step, because a realistic report branches — an open delivery is asked about by
customer and by article, and both hang off the same promise. A hop says whether it fans
out before it is taken, and an axis a number may not be summed across arrives as soon as
the path can see it rather than as a second refusal.

`analytics_report` stores a saved report: the **question**, never its answer, with the
model version that gave it meaning, its owner, a revision and a retry key. Reopening
one re-executes it, so what comes back is a fresh observation rather than a preserved
number — the only honest thing a report can be when the records underneath it keep
changing. Reports are private to their author, and every change is confirmed
explicitly. Migration 0062 added `kind` and `model_version` additively.

Reports saved by the configured generation are still in the table with neither column
set. Nothing reads them, and nothing writes over them: they belonged to a generation
that was replaced rather than translated.
