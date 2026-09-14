# Research: Safe Proposal Confirmation

## Decisions

- Use a tenant-scoped conditional update from `proposed` to `executing` as the single-winner claim.
- Commit `executing` before invoking a handler. This favors required at-most-once safety and explicit unknown outcome over automatic retry.
- Correlate reservation execution with existing `BusinessEvent.action_id`; do not add a duplicated proposal FK to Reservation.
- Treat an executed replay as idempotent retrieval of the stored receipt. Never invoke the handler.
- Separate discovery from exposure: guidance may describe confirm, while default model schemas continue to include only read/propose access.

## Rejected Alternatives

- `SELECT ... FOR UPDATE` held across the handler: current handler commits release the lock.
- A generic idempotency table/workflow engine: larger than the proven reservation use case.
- Automatic retry of `executing`: can duplicate an effect after response/process interruption.
- Verifying by exception disappearance or aggregate inventory alone: not correlated to this action.
