# Analytics and private reports

Spec: [185](../../specs/185-analytics-workspace/spec.md). Verification and remaining
checks: [evidence](../../specs/185-analytics-workspace/verification.md).

## Shared capability

PostgreSQL remains the only database. The Explorer, command line and agents use
`services/analytics/` through the same application tools. Callers submit a versioned
analytical definition, never SQL. The catalog declares datasets, source grain,
dimensions, filter operators, measures, compatible partitions, relationships,
starter definitions and restricted business meanings.

The main perspectives cover stated sales/purchase order evidence, retained customer
purchase history, co-ordered product pairs, current delivery commitments, stock,
stock versus open demand, effective movements/returns, observed suppliers, canonical
billing observations, invoice open items and recorded payments. These are read-time
observations. They do not create new financial or operational authority.

## Agent operation

1. Call `analytics_catalog` to discover the supported vocabulary and limitations.
2. Resolve customer/product references with existing reference tools. Human names and
   SKUs are search inputs; use returned opaque IDs in filters.
3. Call `analytics_query` with a definition. Example: distinct retained orders by
   customer for a resolved product in ISO week 7 of 2026:

```json
{
  "definition": {
    "version": 1,
    "dataset": "sales_order_lines",
    "dimensions": ["customer_id"],
    "measures": ["order_count"],
    "where": {"field": "product_id", "op": "eq", "value": "<resolved-item-id>"},
    "time": {
      "field": "ordered_at",
      "timezone": "Europe/Berlin",
      "window": {"kind": "iso_week", "year": 2026, "week": 7}
    }
  }
}
```

4. Interpret exact typed values with the returned period, missing-value and history
   metadata. Return the supplied `open_in_reports.url` for an editable Explorer
   handoff. Never describe retained data as complete upstream history.
5. Use `analytics_contributors` with the executed definition, group and selected
   measure to inspect counted identities or underlying records. Continuation is a
   fresh observation, not a frozen snapshot.
6. Use `analytics_export` for a complete bounded CSV. Monetary and quantity strings
   retain decimal precision; potentially executable spreadsheet text is escaped.

Private tools are `analytics_reports_list`, `analytics_report_get` and
`analytics_report_change_propose`. The latter prepares create/update/rename/duplicate/
delete changes; the shared approval tool requires explicit confirmation. Trusted
user identity is outside model arguments. Tenant-only MCP credentials can query
business analytics but cannot claim a private report owner. Private proposal payloads
are encrypted with the existing secret mechanism and generic action results are
redacted. Names, definitions and report IDs are not tenant-wide storyline entries.

## Observation and numeric semantics

Each production query/contributor/export request owns a repeatable-read, read-only
PostgreSQL transaction and rolls it back. Statement interruption, cancellation and
cooperative CPU checks share the request deadline. Limits: 30 seconds, 10,000 groups,
200 result rows per page, 100 contributors per page; bounded operational providers
reject populations above their stated admission limits. A broad request fails without
partial success or a hidden sample. Read transport telemetry can still be recorded
outside the analytical transaction.

Money partitions by currency; quantity by unit; prices by currency and unit. No FX,
new conversion policy or source amount recomputation is introduced. Order totals are
aggregated at order grain, separately from stated line amounts. Missing source amounts
remain unknown even if an intake stores a default zero. Distinct counts and pivot
totals are reaggregated from contributors, never summed from displayed pages.

Absolute date ranges are half-open local calendar intervals. ISO weeks require a year
and timezone. Previous-period comparisons expose absolute and relative changes;
percent change from zero is unknown. First purchase means first observed retained
purchase. A newer pending source version does not erase already interpreted evidence.

## Web and persistence

Analytics keeps Overview and adds Explore and My reports. Editing changes a draft;
Run replaces the successful result only when the current request succeeds. Errors and
cancellation retain previous results. Tables, bar/line charts and service-generated
pivots show the executed result; supporting values open the existing Inspector.

"Start new chat about analysis" creates a new conversation through the shared chat
service and opens it in the dock with a visible, removable typed analysis attachment.
It sends no automatic message and preserves the previous conversation. Creation
failure retains the existing draft/context. Attachments belong to the new session
and are cleared when navigating to another conversation.
Open in Reports validates version and company and opens a draft for review. Switching
company clears private report and composer context.

`analytics_report` is the only new table. It stores a private versioned definition
(including presentation), tenant and authenticated owner, revision and retry metadata.
It never stores result rows. Replacement updates use expected revisions, request keys
are payload-bound, and tombstones prevent a lost create response from resurrecting a
deleted report. Migration 0060 upgrades additively; downgrade refuses a populated table.

Grouped charts immediately show the first available currency/unit partition.
Buttons above the chart switch between loaded partitions without another query;
tables and totals keep all partitions. Values are never converted or combined.
Missing grouping retains actionable guidance. Editing query settings still requires
explicit execution. Partition selection precedes the 50-row chart display limit.

Explorer selectors and inputs use shared bordered controls with full-size click
targets. Native dropdowns retain keyboard selection and visible chevrons; Filters
is a bordered disclosure. Date controls adapt to the available container width.
