# Projection interfaces

- Existing stored list reads return stored rows only; no hidden refresh, queue creation or commit.
- Add a tenant-scoped snapshot response containing `items` and `metadata`: projection name, calculation mode, state, processed event sequence, relevant target sequence, completed_at, and unknown upstream freshness. Return only safe failure classification. Invalid names fail and cross-tenant references are not disclosed.
- Paginated stored APIs add equivalent metadata. Rows/totals/metadata share a completed generation; explicitly live responses remain fully live.
- Inspector marks stored, live view and parameterized pricing modes; uninitialized data says awaiting calculation, pending data retains old rows, failed calculation is distinguished from a failed business action. Refresh reads only.
- Internal registry job `projections.refresh`, version1, validates a bounded unique list of materialized projection names. No user actor, no schedule, no source payloads. Handler returns bounded projection/row counts and no commercial figures. Only internal scheduler service can enqueue; ordinary manual/schedule APIs reject this job type.
- A tenant has at most one unfinished internal run. Frozen inputs and same run ID survive retries. Relevant work committed after snapshot is eligible in a later run. Capacity defers; terminal or unresolved outcomes are visible and are not silently replaced.
