# Implementation Review and Verification

## Scope and source boundary

The owner's "Ok mach" authorized the proposed local harness and reference-day-first
implementation, with week continuation. The implementation has no business schema,
production catalog, web, Shopify, AI authority, mailbox or scheduler changes.
It calls confirmed existing application tools in a new independent practice Sandbox.
All ORM access in the new observer is read-only and tenant-scoped.

The fixture is literal and independent of Reality's observed numbers. Expected
quantities, per-line status/amounts, master/order counts and warehouse stocks are
compared after every event. The return arrival uses the opaque preceding announcement
ID; outstanding announced return quantities are measured separately from fulfillment.
Prepared proposals are inspected before acceptance and must have zero accepted effect.
Errors preserve logs and stop without automatically redispatching any effect.

## Verification evidence

- Initial test-first proof: collection failed on the missing runner module.
- Initial day/week, mismatch/stop, repeat/isolation and no-write observations: 6 passed.
- Extended launch/configuration acceptance: 8 passed.
- First parallel full suite: 6,358 passed, 10 skipped, 4 failures and 3 setup errors.
  PostgreSQL logs recorded `out of shared memory` at those failures. All affected
  cases passed in a targeted sequential recheck (8 cases including parametrization).
- Local test PostgreSQL was configured with `max_locks_per_transaction=1024`, matching
  the existing CI workflow; no business code was changed to address those failures.
- Full suite recheck: **6,367 passed, 10 skipped**, in 1,295.50 seconds.
  Evidence: ignored `artifacts/reference_week/full-suite.log` and `full-suite.xml`.
- Final return-link proof was first observed failing before implementation. Its
  scoped final acceptance and return-related regressions are recorded below.
- Ruff (`make lint`), specification policy (`make spec-check`) and whitespace checks
  pass. No frontend, migration or generated-catalog changes: those checks do not
  apply. No remote CI run, merge or deployment is claimed.

Final scoped acceptance: **59 passed** in 55.43 seconds, covering the final
reference-day/week fixture, multiline order entry, Sandbox read parity and return
announcement/adapters. Evidence: ignored `artifacts/reference_week/final-acceptance.log`
and `final-acceptance.xml`. This scoped check followed the full-suite pass and the
final simulator-only return-link correction; no core business code was changed.

## Practical limitations

The runner is trusted local developer tooling, not a remote account/permission
boundary. Actual application booking time stays real; authored dates are scenario
inputs. Reads prove authoritative state, not materialized projection catch-up.
Raw external source replay, payments/payouts and AI decisions need separate adapters
and oracles. Test-company reports identify disposable, rolled-back companies; only
explicit local command-line runs retain a company in the configured local database.
