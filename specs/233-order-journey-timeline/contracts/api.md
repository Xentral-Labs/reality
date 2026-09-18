# Order journey read contracts

GET `/api/tenants/{tenant}/order-journeys?q=...`: existing tenant session authorization; bounded search (30) over sales order number/customer; returns `{orders:[{id,number,party}],has_more}`. Empty query returns recent orders by opaque stable tie-break after available date. Search is a selector, never a total.

GET `/api/tenants/{tenant}/order-journeys/{order_id}?limit=100&before_sequence=...&after_sequence=...`: shared read, sales-order and tenant validation, 404 for absent/foreign/non-sales root. Limit 1–250. Cursors are mutually exclusive. Returns `{order,events,edges,has_more}`; event projection and sequence semantics match timeline_activity. Edges use `{from:{kind,id},to:{kind,id},label}`. No writes.

All-activity mode uses existing `/timeline?hours=0`. Only supported subject types become chart points; every loaded event is retained in the chronological detail list. Order mode uses the exact server membership read. 15-minute/hour/today controls do not redefine API hours semantics.

Posting-group events retain their subject identity. Up to 250 held ledger-entry links per page are returned; `links_truncated` explicitly reports additional entry links. Their original posting payload remains available in the event Inspector.
