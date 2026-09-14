# Public Confirmation Contract

## `proposal_approve_and_execute`

Input: opaque `proposal_id` and literal `approved=true` after explicit human approval.

Outcomes:

- `executed`: returns the stable stored receipt; replay returns the same receipt.
- `executing`: outcome may be unknown; do not retry, call `proposal_execution_status`.
- `rejected` or failed/invalid/foreign: bounded refusal, no handler execution.

For reservation execution the receipt identifies proposal, `reserve` capability, Reservation,
Commitment, requested/applied/shortage quantities, and correlated event.

## `proposal_execution_status`

Input: opaque `proposal_id`.

Returns tenant-scoped lifecycle, stored receipt when available, and three distinct conclusions:

- execution evidence: whether a correlated committed event proves handler effect;
- operational state: whether Reservation/Commitment/quantity match the receipt and input;
- business outcome: always `not_proven` for reservation alone.

Discovery grants neither confirmation permission nor authority. The confirmation tool remains
excluded from model-selectable schemas.
