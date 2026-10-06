# Run-local observations

No business schema or persistence authority changes.

- **Spectator snapshot v1**: schema_version, run_id, day, observed_at, run_state, core_status, refs, order_references, released world view, world_events, goals and coverage. Atomic file replacement. Active checkpoints are `unfinished` / `passed_at_checkpoint`; terminal outcomes preserve passed/failed/unknown/awaiting_review.
- **Party observation**: opaque party ID, recorded name/role and optional simulator label. Extracted only from exact accepted create receipts or exported refs.
- **Message observation**: original JSONL row plus explicit party association from its source context or optional journal party_id. Original payload/direction/status retained; absent status remains unspecified. No tool receipt is a mail-send proof.
- **Business event observation**: authored released event, day, kind, related original order/party IDs and evidence. World event count excludes tool proposals/commit duplicates. Older in-progress tool operations are separately labelled.
- **Checkpoint observation**: day, recorded_at, recorded actual/expected values and differences, unchanged. UI never recomputes source totals.
