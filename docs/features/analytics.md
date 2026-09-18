# Analytics and private reports

Specs: [224](../../specs/224-native-reporting-platform/spec.md) (reporting platform), [228](../../specs/228-guided-analysis-builder/spec.md) (guided builder and catalog). It replaced the
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
- a Cypher-near path syntax, reachable through tools, CLI and the builder's Cypher tab.
  `graph.format` produces editable text with separately bound parameters. Expert clauses
  remain in the checked question even when sentence controls cannot represent them.

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

Seven questions worth starting from are declared beside the model — an open delivery
backlog and the billing backlog that pairs with it, incoming supply, order intake by
customer, order value by month and by article, stock movements by article. Each is named
after what it counts rather than what somebody might wish it meant: order value by
article takes the line's amount, not the order's, because one order reaches many lines. They live in the declaration because they name
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
Default links open My reports. Legacy retired-view links open Analysis; template links
open the template choices inside Analysis.

The Analysis Builder starts directly with a compact configuration toolbar and an
editable sentence. The separate heading, status badge and question/examples panel are
omitted by owner request. Builder and Explore data use the shared flat application
surfaces, controls and theme-aware semantic colors. Result, Connections and Cypher are presentations of the same checked
question. Results retain value filters, column sorting, limits and SQL derivation. The
summary cards describe returned rows, selected measures and the last successful read;
they are not invented financial totals or upstream completeness claims.

The retained shared interpretation tool `graph.interpret` supports free text: active membership, tenant provider policy and existing
managed-question reservation apply before provider dispatch. Only the declared model
and the user's question are sent, without catalog record-value lists. Provider output
is validated and compiled before returning a question; `graph.ask` remains the executor.
Unavailable providers and ambiguous/unsupported questions explain the next step. Exact
example labels and sentence controls work without AI. Managed provider failures consume
the already-reserved question, consistently with existing usage accounting.

Explore data provides catalog search, object/edge/field counts, field and relationship
lists, and bounded previews. Fields and paths open unsaved analyses. Browsing the catalog
does not discard the current builder draft. It does not revive spec185's fixed datasets.

Unexecuted expert text survives view switches and failed execution. It disables sentence
edits and saving until a successful execution; explicit reset starts another analysis.
Advanced clauses are preserved in expert mode. Pending/failed/edited queries never show
an old answer as current, and obsolete requests cannot overwrite newer state.

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

Analytics shared-component refinement (spec228 FR-014): all four views use the common
RegisterWorkbench and single-row tabbed header. Save analysis and Use in analysis
are page actions in the shared More actions menu, scoped to the active view. Local
analysis/catalog tabs use the shared local navigation, tables use ERP register geometry,
and templates/private reports use compact flat lists. No duplicate page titles appear
inside these views. Mounted Builder drafts survive view switches without leaking header actions.

## Analysis entry and chat handoff

The navigation is My reports → Analysis → Explore data. My reports is the default and
its empty state offers Create your first analysis. Analysis offers chat, templates or
manual construction; choosing a template opens an unsaved draft, not a stored report.
The builder remains mounted while browsing other tabs.

Create with chat/Adapt with chat use the existing global chat with an editable prompt
and removable query-only context. No message is sent automatically. The existing
4000-character message limit applies to text plus context; oversized attachments are
explained, never truncated. Context is untrusted message content and grants no authority.
The chat's graph report proposals offer Open in analysis for create/update definitions,
loaded through the existing owner/tenant-scoped proposal API and executed as unsaved
drafts. Confirmation remains necessary for chat saving; opening a proposal never confirms it.


### Question hierarchy (spec228 FR-018)

The analysis editor has one locally bordered question section headed “How Reality
understands your question”, with Adapt with chat beside it. Larger editable tokens
form the primary sentence; aggregate queries lead with their measures. A labeled
Conditions row follows. The period appears once in the sentence and can be removed
there as a whole, preserving unrelated filters. Measures and columns, record paths,
and sorting remain editable in an initially collapsed disclosure. This local frame
is intentional; result tabs and tables retain the shared flat register design.
Currency and identity axes remain in the canonical query even when technical identity
is omitted from the readable sentence. No additional page hero or question input is added.

## Expanded business catalog (spec 229)

The catalog exposes 55 named objects grouped in this order: Sales, Purchasing,
Payments and accounting, Warehouse and shipping, Partners and items, Prices and
terms, Evidence and facts, Additional objects. Groups collapse in the explorer;
search matches declared names, synonyms, categories and fields and opens matching groups.
The same category metadata groups the builder's record selector.

Dedicated sales invoices/customer credits, purchase orders, supplier invoices/credits,
their positions, payments/refunds and settlement adjustments are additive nodes. The
old `invoice`/`invoice_line` keys remain combined customer invoice/credit views with
explicit labels. Stored `sales.1` definitions are not rewritten. Position roots and
joined positions enforce their parent document type through tenant-scoped EXISTS.
Observed catalog values use that exact scope. Reverse same-table relations use the
FK carrier implied by multiplicity/direction, including deductions and target filters.

Reservations follow commitments and existing item/location/lot/serial/handling-unit
references. Holds retain release timestamps. Packages connect movement to shipment;
event history exposes supersession references and never claims to be current shipment
status. Price lists/tiers/assignments, payment terms, partner roles/groups and accounts
are queryable. Received financial components and opening scopes/items are browsable;
component header and line amounts are not offered as a combined additive measure.
Generic documents/positions and source-version metadata preserve evidence access.
Additional facts are explicitly historical records, not inferred current attributes.

Recorded document amounts preserve the source's sign and currency. They are not net
revenue, cash flow or open balances. Reservation quantities are retained snapshots,
not available stock; status filters distinguish active rows. Text document dates remain
text and cannot acquire date-bucket semantics through their label.

Remaining boundaries: operational stock/availability/aging and service-backed balance
execution are not new graph implementations; use their canonical operational views.
Finance target/component assignment histories remain outside this catalog. Full raw
source payloads remain in the Inspector. The existing fact-backed campaign example
still has no supported preview fields and is not presented as a new capability.

## Finance and calendar analysis (spec 230)

Customer and supplier financial-position nodes derive current remaining amounts,
due dates, days overdue and overdue amounts through the same aging service as Finance.
They include opening debts and retain paid/reversed positions with their canonical
status; unposted evidence is not a financial position. Document and party links
preserve traceability. Amounts remain grouped or filtered by currency. Current
positions are not historical time series; state measures reject bucketed trends.
Unused credits and net party balances remain in Finance, separate from invoice debts.

Registered finance paths perform bounded canonical bulk reads plus one SQL aggregate;
the response reports measured SQL reads. Ordinary paths retain one aggregate statement.
A tenant with more than 20,000 debt documents receives an explicit refusal, not a
partial total. The statement timeout applies before derivation; data stays ephemeral.
This narrowly supersedes spec224's one-statement rule for registered service nodes.

Ledger sums apply debit-positive/credit-negative signs. Explicit document calendar
dates support filters and buckets without changing lossless source text. Invalid
calendar dates become unknown; date-only UI bounds retain calendar days across
time zones. Timestamp fields retain instant semantics.

## Current stock and starting templates (spec 231)

Current article stock is a separate item-backed analysis node. Physical, reserved and
available quantities come from core.inventory_rows at one article across all locations
and lot/serial/handling identities. Internal transfers cancel; movement corrections
and active reservation status are respected. Articles without movements remain zero;
negative availability is retained. Available means physical minus active reservations,
not shipment permission, ATP, or expiry/hold-adjusted stock.

Stock measures require unit grouping or a single-unit filter and reject time-bucket
trends. Following movement/reservation history retains the ordinary fanout guard.
Stock→article links preserve identity and the existing paths to evidence and Reality.
The registered service adapter refuses more than 20,000 articles or open supplier commitments, or 100,000 movements
or commitment revisions before materializing its inputs.
No result limit truncates an aggregate. Registered service reads are counted honestly;
plain article queries do not trigger stock derivation.

Six additional localized starting templates open unsaved editable analyses: stock by
article, reserved stock, shortages, customer outstanding, supplier outstanding and
customer overdue. Stock templates retain article identity/unit; finance templates
retain partner identity/currency. Existing templates and save confirmation remain.

## Balances, exact stock dimensions and effective-date snapshots (spec 232)

The graph exposes unpaged customer/supplier net balances at party × currency grain,
using the same canonical open-item and unused-credit readers as Finance. Negative
balances remain negative. A derived position has a stable opaque identity separate
from its backing party or article identity; joins retain ordinary fanout safeguards.

Stock detail groups movement legs and active reservations by article, location, lot,
serial and handling unit. Missing dimensions form exact null buckets, never wildcard
matches. Internal transfers conserve the article total. Current availability means
physical minus active reservations, not permission to ship.

Historical balance and physical-stock nodes require an explicit `snapshot_date =
YYYY-MM-DD` input, through the end of that UTC day. Templates ask for the date before
adoption; the sentence editor exposes a date control. Chat, saved questions and the
path editor retain the same filter. Finance restricts posting effective times,
allocation times and both endpoints, and reversal times consistently. Stock uses
retained movement timestamps, including compensations. Queries before relevant
opening coverage, future or conflicting dates are refused. Names and units remain
current master data. Historical reservations, availability, aging and knowledge-time
reconstruction are deliberately unavailable because their required history is absent.

Position readers enforce a 20,000-row cap per input family before materialization,
exact Decimal arithmetic, tenant scoping, statement deadlines, currency/unit grouping
and read counts. They never truncate totals to register pages. No persisted snapshots,
schema changes, external writes or alternate chat calculation paths are introduced.

## What a question costs (spec 234)

A question is answered in one of two ways, and the difference is large. An ordinary
path compiles to one SQL aggregate. A path reaching a derived position first runs a
canonical service, ships its rows back into PostgreSQL as one bound JSON value and
aggregates that. Measured on a 10,233-document company, the first shape costs single
milliseconds and the second hundreds.

Before the canonical service runs, the compiler works out which anchor rows the
question can still reach and passes them in. The identity query is built from the same
frame as the answer, so both agree about what the path means; conditions the plain
anchor table cannot express — the derived amounts themselves — are left out, and any
existence test that loses a condition is dropped whole. The set can therefore only be
too generous, never too small, and every condition is conjunctive, so a row it excludes
is one the final `WHERE` would have dropped. Where nothing narrows, or the set exceeds
the binding limit, the derivation reads the company exactly as before: push-down is an
improvement that can always be declined.

The canonical readers take the narrowing as an optional identity filter — `party_ids`
on the open-item, aging and credit reads, `item_ids` on both inventory reads. Each
selects rows and changes no arithmetic, because every position is summed within one
party, article or document and never across them.

`document.document_date` is a calendar date. Every surface still sends and receives ISO
text, with an absent day spelled `""` outside and NULL inside; `reality.domain.calendar`
holds the two conversions. An unreadable day — an impossible calendar date, or free text
such as a period label — is refused where it is written rather than stored and judged
again by each reader. That distinction matters beyond cost: a document stating no date
and a document stating a date that does not exist used to be the same row to every
report. What a source sent is still kept verbatim in its payload, which is the record
that is meant to be lossless. `document` is indexed by tenant, type and day,
and `document_line` by tenant and document, because sixteen and eight analysis objects
respectively share those tables and otherwise pay for each other's rows.

`statements_per_traversal` states what an ordinary path costs; the new
`statements_per_derivation` is the ceiling one canonical bulk read may reach before the
traversal is refused as a regression rather than served slowly. It sits far above what
any declared derivation costs today, and exists to catch a derivation that quietly
becomes a read per row.

Cost is pinned in tests by statement counts and derivation inputs, not by wall-clock,
which varies by an order of magnitude with the company's history and the machine's load.
