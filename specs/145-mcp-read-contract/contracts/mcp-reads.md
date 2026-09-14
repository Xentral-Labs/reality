# MCP Read Contract v2

Affected lists: business_records_discover, inventory_read, commitments_list, fulfillment_queue, fulfillment_blockers, item_supply_demand.

Inputs: response_format page (MCP default) or legacy, limit 1..100 (default 25), cursor optional. Discovery retains family/query/record_id. Inventory adds view aggregate (default) or location, item_id and location_id; location_id selects location scope. No new permissions or tool names.

Page output: records array, next_cursor string/null, has_more boolean, metadata object. Empty/final pages use null/false. No total required. Changing tenant/tool/filter/view with a cursor is invalid. Limits may change between pages. Opaque IDs/record keys sort ascending; live mutations may alter later rows, and inserts before the cursor require restarting. This is not an atomic snapshot or proof of external-source completeness.

Metadata: contract_version 2, tenant_id, filters, observed_at, projection_version (known derived version or null), event_sequence (observed local value), upstream_freshness unknown, consistency live_keyset (pages) or live_read (details), persistence {business_writes:false,projection_writes:false,authentication_telemetry:possible}. No cache rows created or committed in page mode. Legacy operational lists can refresh/commit cache; legacy discovery remains bounded and is not a complete export.

Finance: balances array sorted by currency, each containing currency/receivables/payables, plus metadata. Negative and zero balances retained; no false single-currency fallback. Ledger discovery includes canonical debit_credit and matching side compatibility alias.

Order: existing fulfillment/reservations/movements/source keys retained; document and document_lines plus metadata added. Resolve IDs before display references; fail ambiguous display references. Open and closed commitments and effects remain visible; closed cases are not actionable. This is current retained evidence, not an arbitrary historical snapshot.
