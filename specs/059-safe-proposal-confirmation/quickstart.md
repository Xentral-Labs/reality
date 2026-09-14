# Quickstart: Atlas Confirmation

1. Read `capability_describe` for `proposal_approve_and_execute` and the proposed capability.
2. Read the pending proposal and show its exact preview to an accountable human.
3. On explicit approval, call confirmation once with `approved=true`.
4. If a receipt returns, call `proposal_execution_status` and re-read the Reservation and Commitment named by the receipt.
5. If transport fails or status is `executing`, do not confirm again; reconcile by proposal ID.
6. Treat verified allocation as operational evidence only, not fulfilment or customer outcome.

## Verification record

Verified on 2026-09-03:

- `make spec-check`: passed.
- Ruff (`src` and `tests`): passed.
- Complete PostgreSQL backend suite: 400 passed, 7 skipped.
- Documentation contract suite: 19 passed.
- Documentation production build: passed.
- Prettier check and `git diff --check`: passed.

No database migration or schema expansion is part of this feature. An `executing` proposal is never
retried automatically: callers use `proposal_execution_status` to find a correlated effect and
escalate an unresolved outcome for reconciliation.
