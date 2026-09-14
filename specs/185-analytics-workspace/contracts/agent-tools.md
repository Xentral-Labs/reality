# Agent analytics tool contract

Contract version: 1. Implemented tool names and input shapes.

## Workflow

1. Call `analytics_catalog` to discover perspectives, dimensions, measures, filters, relationships and starter definitions.
2. Resolve product/customer identity using existing scoped discovery. Display names and SKUs are not query identity.
3. Call `analytics_query` with a structured definition. Refine the definition for follow-up questions.
4. Call `analytics_contributors` for the selected group/measure, or `analytics_export` for complete bounded tabular output.
5. Offer `open_in_reports` handoff from the returned definition. Do not invent an app URL with arbitrary query parameters.
6. Authenticated personal-report callers can list/get private definitions and propose changes. Anonymous or tenant-only callers cannot supply an owner ID to impersonate a person.

## Public tools

| MCP name | Application name | Input | Authority / result |
|---|---|---|---|
| analytics_catalog | analytics.catalog | optional dataset | Authorized tenant read; full versioned metadata and starter definitions |
| analytics_query | analytics.query | definition, page_size=50, cursor? | Authorized tenant read; values/definitions/coverage |
| analytics_contributors | analytics.contributors | definition, group, measure, page_size=50, cursor? | Fresh scoped observation of contributors |
| analytics_export | analytics.export | definition, expected_fingerprint? | Fresh bounded CSV result plus observation context |
| analytics_reports_list | analytics.reports.list | query='', limit=50, cursor? | Authenticated Principal required; own active definitions only |
| analytics_report_get | analytics.reports.get | report_id | Authenticated Principal required; own active definition |
| analytics_report_change_propose | analytics.reports.change | operation, request_id, report_id?, expected_revision?, name?, definition?, presentation? | Authenticated author required; proposal only, confirmed before mutation |

Operations: `create`, `update`, `rename`, `duplicate`, `delete`. Create requires name/definition; others require report_id/expected_revision. Update replaces a complete validated definition/presentation (and optionally name), rather than applying arbitrary JSON patches. Duplicate uses a new name and retry key. Delete names the report in confirmation. Unknown/irrelevant fields are refused.

The existing proposal approval/receipt tool performs confirmation, with original author and current membership checked again. A company owner cannot approve another user's private report. Web chat carries its authenticated user outside JSON arguments. Tenant-only MCP and current local CLI can query/export/open unsaved definitions but receive `user_context_required` for private reports; no MCP auth expansion is included.

## Concrete query example

After resolving the product identity and confirming that the catalog offers these keys:

```json
{
  "definition": {
    "version": 1,
    "dataset": "sales_order_lines",
    "dimensions": ["customer_id"],
    "measures": ["ordered_quantity", "order_count"],
    "where": {
      "all": [
        {"field": "product_id", "op": "eq", "value": "itm_example"}
      ]
    },
    "time": {
      "field": "ordered_at",
      "timezone": "Europe/Berlin",
      "window": {"kind": "iso_week", "year": 2026, "week": 7}
    },
    "cancellation": "all_recorded",
    "sort": [{"field": "customer_id", "direction": "asc"}]
  },
  "page_size": 50
}
```

`itm_example` is illustrative and must be replaced with an actual scoped opaque ID. This is an input contract example, not a runtime demonstration.

To answer weekly product trends, use dimensions `product_id` and `ordered_week`, measures `ordered_quantity`/`stated_line_amount`, and a window such as `last_complete_weeks` with `count:12`. Currency and unit are mandatory partitions automatically included by execution for those measures. The normalized definition shows them explicitly.

## Definition grammar and limits

- Pydantic models forbid extra fields, SQL strings, tenant/owner selectors and arbitrary expressions.
- Dataset is a catalog key. Maximum 4 selected dimensions and 4 measures.
- Predicate is a typed leaf (`field`, `op`, `value`/`values`) or `all`/`any` group; maximum depth 3, 32 leaves, 100 values per `in`/`not_in`, 200 characters per text term. Null is tested only through `is_missing`/`is_present`.
- Operators: `eq`, `ne`, `in`, `not_in`, `contains`, `gte`, `gt`, `lte`, `lt`, `is_missing`, `is_present`; supported subsets come from each field's type/catalog. Text matching is parameterized and documented as case-insensitive literal substring, not regex.
- Cataloged `exists`/`not_exists` relationship predicates carry their own filter/time scope. Example: customer bought A within the requested window but has no B purchase within the same explicit window. The compiler owns all join predicates and tenant constraints.
- Time windows: absolute `[start,end)` local dates, ISO week/year, last N complete weeks/months, current month/quarter/year, last N calendar days including today. Counts/ranges are bounded to 10 years. Resolve local boundaries to UTC with the specified IANA timezone. Comparison accepts explicit dates or immediately preceding equal-length calendar period with displayed boundaries; no hidden partial-quarter equivalence.
- `cancellation`: `all_recorded` or `exclude_fully_cancelled`. Partial cancellation keeps original evidence quantities/amounts. Commitments expose separate effective/open measures.
- Presentation is table/bar/line/pivot; pivot supports two row dimensions, one column dimension and two measures. Presentation cannot smuggle new expressions into execution.
- Definition plus presentation: maximum 16 KiB. Query page size 1–200; contributor page size 1–100. Result group limit 10,000, chart categories/series 50, pivot columns 50 and cells 5,000, export rows 10,000 and bytes 10 MiB. Overflow is explicit; export refuses rather than truncates.
- Order-pair preflight: at most 100 distinct products per order and 1,000,000 candidate pairs per request, otherwise `query_too_broad` with narrowing advice. Basic order aggregation supports the 100,000-line acceptance benchmark. Existing canonical derived perspectives admit at most 20,000 relevant source records after a bounded scoped preflight; over-limit requests are refused, not approximated.
- Execution deadline 30 seconds total, not 30 seconds per statement. DB and CPU/cancellation checks share the deadline. No background job is created.

## Dataset catalog

| Key | Grain | Important capability |
|---|---|---|
| sales_order_lines / purchase_order_lines | Interpreted evidence line | Product/party/date quantities, stated line value, agreed price, distinct orders |
| sales_orders / purchase_orders | Interpreted evidence header | Stated order value without line multiplication; product existence filters |
| customer_purchases | Customer over scoped retained order history | First/last observed purchase, active/inactive filters, exists/not-exists products |
| order_product_pairs | Distinct unordered product pair per order | Co-order counts and support; no duplicated same-product pair |
| delivery_commitments | Effective current commitment | Original/effective dates, open/fulfilled/reserved quantities, cancellation counts |
| inventory | Current item/location | Physical/reserved/available, current demand at compatible grain, effective outbound absence |
| order_billing | Agreed order line | Canonical received/shipped/billed/remaining quantities and discrepancy reasons |
| open_items | Current booked invoice/opening item | Due date, side, currency, original/settled/open/overdue |
| payments | Recorded payment | Effective date, party, allocated/unallocated, currency; not allocation date as payment time |
| returns | Effective physical return movement | Product/party/time quantity; announcements remain separate |

Each catalog entry declares an available subset, not a promise that every measure can combine with every other dataset. Derived inventory demand must never be repeated across locations and summed as if allocated there. Tax/price basis that cannot be established stays unknown. Catalog labels are localized; stable keys remain English.

## Result contract

Return `version`, `executed_definition`, `definition_fingerprint`, `columns`, `rows`, `population_totals`, `comparison`, optional `pivot`, `page` and `metadata`. Money/quantity values are decimal strings; counts are integers; dates ISO; missing values null. Column descriptors include type, unit/currency field, measure meaning and contributor capability. IDs and display labels are separate.

Metadata includes observation ID/time, tenant, resolved window, `consistency: repeatable_read_request`, `history_scope: matching_interpreted_retained_records`, unknown upstream completeness/freshness, exclusions/missing counts, display limits, duration and persistence facts. It explicitly distinguishes the read-only analytics transaction from possible authentication/chat/storyline telemetry outside it. No event sequence is presented as a reusable snapshot.

Continuation binds tenant, caller scope when needed, normalized definition hash and deterministic ordering. It is revalidated on every call and states `fresh_observation` across requests. Exact totals are recalculated for each observation. The client cannot treat multiple live pages as a frozen export; export runs the whole bounded result in one fresh transaction.

Contributor requests carry typed group values, selected measure and full definition, not SQL or trusted record lists. Zero/anti-existence results explain the included population and missing relation; they never fabricate a missing source record. Distinct-count contributors preserve distinct identity grain. Every exposed record is tenant-validated.

## Errors

Stable codes: `invalid_definition`, `unsupported_combination`, `unsupported_meaning`, `query_too_broad`, `query_timeout`, `query_cancelled`, `invalid_cursor`, `not_found`, `user_context_required`, `revision_conflict`, `idempotency_conflict`, `definition_upgrade_required`. Responses include a localized business explanation and actionable field/context, without raw SQL or foreign record details. No rows/totals are returned as successful output after an execution failure.

## HTTP and CLI mapping

Existing GET `/api/tenants/{tenant}/analytics` and `/analytics/contributors` remain the operational Overview API.

New `/api/tenants/{tenant}/analytics/` routes: GET `catalog`; POST `query`, `query/contributors`, `export`; GET `reports`, `reports/{id}`; POST `reports/changes` and scoped recovery. Direct Web changes use the same validation/lifecycle services under authenticated Principal; agent changes pass the existing proposal confirmation. Recovery keys are owner/tenant-bound. New POST reads must be classified explicitly in existing protected-company read policy; no generic POST bypass.

CLI subcommands: `reality analytics catalog`, `query --file definition.json`, `contributors --file request.json`, `export --file definition.json --output result.csv`. File inputs are validated through the same tools. Private report commands require a trusted authenticated Principal; the existing tenant-only CLI does not gain impersonation flags.

## UI/chat handoff

`open_in_reports` contains a versioned normalized definition and presentation (maximum 16 KiB), never result rows or credentials. Web uses a typed chat-result/context payload. URL fragments can carry a base64url definition for an unsaved handoff; the route owns company selection and all fields are revalidated. No private report name or customer data is placed in an HTTP query string. Saved report navigation uses its opaque ID and authorization.

Discuss attaches visible typed context to the existing composer and sends through the normal chat submit flow. Agent output rendering recognizes only this supported analytics payload; arbitrary model links do not become executable navigation. Reload/back restores the definition, not a claimed old snapshot. A company switch clears pending context, execution and saved selection.
