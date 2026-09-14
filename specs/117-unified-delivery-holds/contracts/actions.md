# Interfaces

Existing delivery-actions prepare accepts commitment_hold {commitment_id, reason_code, note?} and commitment_hold_release {commitment_id}; canonical tool schemas remain unchanged. Hold reasons come from case metadata, not a browser-owned allowlist. Blockers retain id/reason and add scope, note and created_at; customer-wide holds are never treated as releasable own holds.

Review effect keys are holds_set or holds_released (counts, not item quantities); state.holds contains sorted own-hold snapshots. Confirm/review/detail/reconcile retain existing tokens/status/URL semantics. Receipt records use commitment_hold family and may be plural. Inspector proof includes the commitment and action event; optional technical disclosure shows hold identities and original intent.
