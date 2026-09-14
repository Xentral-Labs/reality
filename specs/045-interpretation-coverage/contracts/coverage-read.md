# Contract: Interpretation Coverage Read

Read-only application/MCP capability: `interpretation_coverage`.

Optional `source_record_id`; absent lists the tenant's sources newest first, present returns one tenant-owned source or not found. Rows include safe source identity metadata, job state, current classification, and ordered outcomes with interpreter identity, reason, completion time, and produced `{record_type, record_id}` references. Never return payloads, job inputs, credentials, or stack traces. Cross-tenant IDs behave as not found.

