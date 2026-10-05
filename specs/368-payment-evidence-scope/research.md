# Research
**Language**: English
## Decision: Explain the existing payment branch
Standard readiness carries stated gross plus zero received/remaining because settlement was not evaluated. Preserve them and expose not_evaluated plus null interpreted values. For prepayment, expose only canonical qualified evidence, with missing/ambiguous/unstated boundaries. An owner release changes the constraint, not payment evidence.
**Rationale**: Avoid inventing customer balances or replacing canonical qualification rules.
**Alternatives considered**: Rename/remove old fields (break compatibility); query all payments (different semantics and extra queries); new report tool (unnecessary).
## Decision: Shared transient helper
Use the same helper for direct/exact reads and cached queue decoration. Keep persisted derivation and review payloads interpretation-free.
**Rationale**: Existing cache reconstruction and tokens require identical raw values.
**Alternatives considered**: Persist metadata (new authority/cache drift); adapter-only rendering (inconsistent surfaces).
## Decision: Known selection size only for complete first response
Expose null for any omitted keys, including final cursor pages. Movement records are not Shipment consignments.
**Rationale**: Live cursor pages do not form a consistent snapshot.
**Alternatives considered**: Sum page counts or issue separate aggregate (scope and snapshot mismatch).
## External acceptance boundary
Claude's existing paused routine targets the older test company. No next active run or separate timezone/checkpoint is established by that UI. Inspect client state separately from Reality capability discovery. No scheduling change.
