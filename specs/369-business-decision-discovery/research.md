# Research
## Decision
Extend existing business discovery with executed_decision and existing document_id scope. Use ChangeProposal status plus tenant-scoped BusinessEvent.action_id and exact order-member selections.
## Rationale
The independent planning research confirmed the physical action table represents ChangeProposal, with no separate ActionLog. Existing order_journey demonstrates authoritative line-first commitment membership. Reservation execution emits a reservation subject event and action_id. SQL EXISTS prevents duplicate effects multiplying records. Shared service selection preserves all transports.
## Alternatives considered
New daily/report command rejected by owner intent. Raw proposal input/output JSON substring and shared numbers/items rejected as non-authoritative. New relationship table rejected because existing event FKs establish the acceptance case. Pending/failed/rejected association and broader source/party/invoice membership deferred to independently specified evidence requirements.
## Unknowns
None. Privacy: payload-free metadata mirrors existing pending summaries; exact review remains responsible for contents and existing policy. Absence never establishes full history.
