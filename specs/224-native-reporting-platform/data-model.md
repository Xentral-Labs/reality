# Data Model: The Reporting Graph

Status: proposed declaration only. No new business table, no materialisation, no second
store. Nodes are the typed tables that exist today; edges are mostly the foreign keys
that exist today. The declaration is configuration, versioned and validated.

This is the **reporting graph**, not the Context Graph. See spec.md, "Terminology".

## Why the declaration carries three things

A traversal engine needs exactly what neither SQL nor Cypher can infer:

- **Grain** — what one row of a node is, so a measure is summed once per that thing.
- **Multiplicity** — whether an edge fans out, so the compiler knows when to fold.
- **Unit and additivity** — what a number is, so it is not added to something else.
- **Corrections** — how the node changes when the world corrects itself, because that is
  the second way to count something twice and it has opposite rules per node.

Everything else about a query can be written freely. These three cannot, and that is
the entire boundary between flexible and wrong.

## Nodes

| Node | Table | Grain: one row is | Key | Corrections |
|---|---|---|---|---|
| `party` | `party` | one business partner | `id` | `replace` |
| `item` | `item` | one article | `id` | `replace` |
| `order` | `document` where `type` is a sales order | one retained sales order | `id` | `replace` |
| `order_line` | `document_line` of an order | one order position | `id` | `replace` |
| `invoice` | `document` where `type` is an invoice | one invoice | `id` | `replace` |
| `invoice_line` | `document_line` of an invoice | one invoice position | `id` | `replace` |
| `posting` | `ledger_entry` | one ledger entry | `id` | `compensate` via `ledger_reversal` |
| `allocation` | `settlement_allocation` | one payment-to-invoice settlement | `id` | `replace` |
| `movement` | `movement` | one stock movement | `id` | `compensate` via `movement_correction` |
| `shipment` | `shipment` | one shipment | `id` | `replace` |
| `location` | `location` | one storage location | `id` | `replace` |

Every node also declares its tenant column, which is `tenant_id` throughout.

## Corrections

The schema corrects itself in three different ways, and the rules are opposite, so the
node declares which one applies. See [scale-and-updates.md](scale-and-updates.md) for the
evidence behind each.

| Value | Meaning | Aggregation rule |
|---|---|---|
| `replace` | The row is the current truth; re-import updates it in place | Sum and count are both direct |
| `revise` | An append-only revision table holds the changes; the latest is true | Select the latest revision first; summing all revisions multiplies the promise |
| `compensate` | A correction is itself a row that nets the original out | Measure sums over all rows are correct; a naive `count` is inflated and is refused in favour of a distinct count of corrected events |

A node without a `corrections` value is rejected at load, exactly like a measure without
a unit. `commitment` will declare `revise` when it is added, backed by
`commitment_revision`.

A node whose table is shared by several business meanings carries a discriminating
predicate in its declaration (`order` and `invoice` both sit on `document`). The
predicate is part of the node, not of the query, so a question cannot accidentally mix
orders and invoices into one aggregate.

Extension nodes are backed by `fact` through `subject_type` plus `predicate`. They obey
the same rules and are not aggregable until grain, unit and additivity are declared.
`fact.value` is text, so an extension measure declares its cast explicitly and a failed
cast is an error, never a zero.

## Edges

| Edge | From → To | Multiplicity | Carried by |
|---|---|---|---|
| `ordered_by` | `order` → `party` | n:1 | `document.party_id` |
| `ships_to` | `order` → `party` | n:1 | `document.ship_to_party_id` |
| `contains` | `order` → `order_line` | 1:n | `document_line.document_id` |
| `of_item` | `order_line` → `item` | n:1 | `document_line.item_id` |
| `bills` | `invoice_line` → `order_line` | n:1 | `document_line.billed_document_line_id` |
| `invoiced_to` | `invoice` → `party` | n:1 | `document.party_id` |
| `promises` | `order_line` → `commitment` | 1:n | `commitment.document_line_id` |
| `fulfilled_by` | `commitment` → `movement` | 1:n | `movement.commitment_id` |
| `posted_for` | `posting` → `party` | n:1 | `ledger_entry.party_id` |
| `posted_from` | `posting` → `invoice` | n:1 | `ledger_entry.document_id` |
| `settles` | `allocation` → `posting` | n:1 | `settlement_allocation.invoice_ledger_entry_id` |
| `paid_by` | `allocation` → `posting` | n:1 | `settlement_allocation.payment_ledger_entry_id` |
| `moved_item` | `movement` → `item` | n:1 | `movement.item_id` |
| `moved_from` / `moved_to` | `movement` → `location` | n:1 | `movement.from_location_id` / `to_location_id` |
| `within` | `location` → `location` | n:1, **recursive** | `location.parent_location_id` |

The full declaration is drafted in [reporting-graph.draft.yaml](reporting-graph.draft.yaml)
and every table, column and carrier in it was verified against `db/core.py`. Three edges
above were corrected in that pass: billing is carried on the invoice line and points back,
so its direction is `n:1`, not `1:n`; postings reach party and invoice through their own
columns rather than through a posting-group construction; and there is no direct column
from an order line to a movement — the path runs through `commitment`, which is what
actually links a promise to its fulfilment.

Two edges may connect the same pair of nodes with different meanings (`ordered_by` and
`ships_to`). A path therefore names its edge, never merely its target node.

An edge declaration records: direction, multiplicity, nullability of the carrying
column, whether it is recursive, and for a recursive edge the maximum depth and the
cycle policy. An edge is carried either by a column that already holds the
link (`via`) or, where no column holds it, by `fact` rows that somebody creates
(`fact`, optionally `writable`). Both kinds are traversed identically; only their
storage differs, and a declared column edge stores nothing at all because the link is
already there. A writable fact edge additionally declares who may assert one. `within` is the only recursive edge in the schema today. Bills of material,
nested handling units and party hierarchies are new rows in this table when they arrive,
not a redesign and not a compiler change.

## Measures

| Measure | Node | Source | Unit | Additive over | Never additive over |
|---|---|---|---|---|---|
| `stated_order_amount` | `order` | `document.gross_amount` | `document.currency` | time, party, channel | currency |
| `line_amount` | `order_line` | `document_line.gross_amount` | order `currency` | time, item, party | currency |
| `quantity` | `order_line` | `document_line.quantity` | `document_line.unit` | time, per single item | item, unit |
| `invoiced_amount` | `invoice` | `document.gross_amount` | `document.currency` | time, party | currency |
| `allocated_amount` | `allocation` | `settlement_allocation.amount` | `settlement_allocation.currency` | time, party | currency |
| `open_balance` | `party` | canonical finance service | `currency` | party | **time** — it is a state, not a flow |
| `order_count` | `order` | distinct `document.id` | count | time, party, item | — |

Measures bind to canonical services where one exists, so a number here and a number in
the Finance register cannot drift. A missing `gross_amount` stays unknown; it is never
reconstructed as `unit_price * quantity`, and never coerced to zero.

`open_balance` is the worked example of non-additivity: summing it across months is
meaningless and is refused, while grouping it by party is correct. Declaring this once
prevents the class of error that no amount of query review catches reliably.

## Traversal semantics

A query is a path plus filters plus measures plus grouping.

1. The compiler resolves the path against the declaration and rejects an undeclared hop.
2. It computes the **effective grain** of the path: the coarsest node whose rows are not
   multiplied by the hops taken.
3. For each requested measure it compares the measure's declared grain to the effective
   grain. Equal: aggregate directly. Coarser: fold to the measure's grain first, using
   the node key, then aggregate. Incompatible: refuse, naming the edge that fanned out.
4. It checks units across the requested grouping and refuses a mixed-unit aggregate.
5. It checks additivity against each grouping axis.
6. It emits one statement with the tenant predicate on every node and bound parameters
   for every literal.

Recursive edges emit a recursive common table expression with the declared depth bound
and a visited-set cycle guard. An unbounded depth request is refused rather than
executed.

Independent branches — order value against invoiced amount against allocated amount —
are compiled as separate aggregates joined on the grouping keys, never as one join chain,
because a chain would multiply all three against each other.

## Storage

Reuse `analytics_report` and `analytics_report_draft` from spec 222. Drafts stay
immutable and store the definition and observation metadata, not result rows. Proposals
seal an exact selected definition; confirmation remains the mutating step.

The stored definition is the traversal query in its typed form, plus the model version
that interpreted it. It contains no SQL and no dialect, which is what makes a different
execution backend a compiler change rather than a migration of saved artifacts.

Existing v1 SQL definitions keep their stored envelope and are read through an explicitly
tested mapping. Stored drafts are never silently rewritten.

## Observation contract

Record the query fingerprint, model version, UTC observation time, resolved business
periods and timezone, traversal path, available temporal coverage and explanation
capability. A current read has a consistent local transaction snapshot; that is not a
claim about upstream freshness. Continuation and later reads are fresh observations and
say so.

Temporal descriptors distinguish current retained state, business-dated activity,
effective-time as-of and knowledge-time as-of. The last two remain unsupported and fail
explicitly; see `temporal-coverage.md`.

## Not database objects

The declaration creates nothing in the database. No view, no role, no grant, no
materialisation, no index is introduced by declaring a node or an edge. Indexes may be
added later as ordinary performance work, justified by measurement, and are not part of
the model's meaning.
