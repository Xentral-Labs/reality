# Research decisions

Read-only planning agent and local inspection agree:

- Reuse commitment_hold and commitment_hold_release. Existing reasons are canonical; release targets all active own holds. No partial or customer-wide release is inferred.
- Existing services lack action attribution. Add optional action_id using existing event/proposal fields; do not invent a parallel receipt store.
- Snapshot the entire active own-hold set, not only the latest hold. Reject no-op reviews while preserving direct service compatibility.
- Verify event subject commitment plus payload hold IDs and exact tenant records; creation proof survives later legitimate release. Reconciliation may return several hold records.
- Distinguish customer-wide holds in case data. Existing tenant mutation lock already covers all hold/fulfillment writers.

Alternative separate form/proposal engine rejected: existing delivery card has edit/review/confirm/recovery. Separate release reason rejected: no existing storage/command use case. No unresolved question or constitutional exception remains.
