# Data Model: Safe Proposal Confirmation

No schema change is required.

## Existing records used

- `ChangeProposal.id`: opaque confirmation/action identity.
- `ChangeProposal.status`: `proposed → executing → executed`; `proposed → rejected` remains.
- `ChangeProposal.input`: immutable normalized command input used for receipt verification.
- `ChangeProposal.output`: preview while proposed; stable execution receipt after execution.
- `Reservation.commitment_id` and `Reservation.quantity`: shortest operational relationship/value.
- `BusinessEvent.action_id`: correlation from `reservation.created` to the proposal.
- `BusinessEvent.subject_id`: correlation from event to Reservation.

## Derived verification

Verification compares the stored receipt and proposal input with tenant-scoped Reservation,
Commitment, and BusinessEvent records. It stores no duplicate verification state.
