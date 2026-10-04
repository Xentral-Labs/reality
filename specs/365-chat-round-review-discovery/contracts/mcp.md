# MCP Contract

`business_records_discover(family="movement", query="shipment", limit=5)` selects
matching held movement types before limiting. Substring and case-insensitive search
are existing query semantics. `record_id` remains the stronger exact identity.
Empty query is unchanged. Paging, metadata, tenant scope and legacy/page parity remain.
Neither this sample nor an empty Shipment-object list proves whole-company or
exact-order delivery absence.

`capability_catalog(topic="review")` exposes a standalone generic
`proposal_approve_and_execute` entry with access confirm and the actual caller's
callable/reason. Existing intake presentation remains. No grant or approval is
inferred from catalog presence.

No native Reality MCP timer, provider-job, persisted mission/checkpoint or generic
next-run/pause control is added. A client-owned recurring test must prove its own
controls and preserve exact human approval boundaries.
