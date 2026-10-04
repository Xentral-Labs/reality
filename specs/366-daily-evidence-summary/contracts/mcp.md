# Existing MCP read extensions

`business_records_discover` page mode retains records/next_cursor/has_more/metadata and
adds summary. All families have shown count and coverage; movement pages additionally
have counts_by_type and labelled movement observations. Legacy format retains bare lists.
No new input or permission is introduced. Query return still substring-matches both
return and supplier_return. Summaries never silently count unshown records.

`order_explain` retains existing canonical fulfillment fields and adds per-line
unfulfilled_cause; missing cause remains unknown. Current blocker codes are preserved,
not invented from document/object absence. Source payloads stay lossless.

Tools are read-only. Both native and external MCP clients receive service-owned output.
No scheduling, confirmation or external transport changes.
