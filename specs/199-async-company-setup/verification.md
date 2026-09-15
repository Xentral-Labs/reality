# Verification

## Completed checks

- The measurement that opened the feature, taken on a created playground company:
  `TOTAL=6447` SQL round-trips in the one creation request, 3.2 s against a loopback
  database. The hot spots are per-operation authorization re-reads — 1,231 tenant rows,
  791 playground runs, 287 tenant ids, against roughly 700 inserts — which is why this
  feature moves the work instead of batching it.
- New service tests failed first for the stated reason (`assert 'ready' ==
  'initializing'`, then "the queued initialization must be claimable"), then passed.
- Fourteen existing tests across seven suites stated the old contract and were rewritten
  to run the queued work the worker would run (`conftest.seed_company`). Each one now
  asserts both halves: the request answers `initializing`, and the receipt reports
  `ready` after the worker has run.
- Two refinements came out of those suites rather than from the plan: an already failed
  initialization is recovered in the request instead of re-queueing a run that would
  never be claimed, and the two-order execution fixture is small enough to stay
  immediate, so only the international profile is deferred.
- A security check that the plan did not anticipate: `_owner` is consulted from several
  queue entrypoints, so the job type's ownership rule had to be as strong as the shared
  one. `require_setup_owner` resolves the run from the tenant and the actor and then
  applies `require_playground_run` in full; the test asserts the owner passes and a
  stranger, an anonymous actor and a foreign tenant are all refused.
- Web: 5 new contract tests for the followed receipt, its bound and its retry of failed
  reads; 177 contract tests, the four-language audit, TypeScript and Prettier.
- Browser run passed with a seed deliberately outliving the request: the preparing
  screen keeps showing progress with no alert, the company opens when its receipt
  reports ready, and exactly one creation request was made.
- Lint, format, spec coverage policy and the proxy contract test passed.

## Completion

Full PostgreSQL suite: 2559 passed, 9 skipped in 13:47; after rebasing onto feature 198
(the two offered starts, merged meanwhile) the suite ran again at 2563 passed, 9 skipped
in 8:52, and the browser run covers both features in one flow: a start is chosen, the
slow seed keeps showing progress, and the company opens without a second creation.

Known bound, stated in the spec: the worker executes the handler in a child process
with a 30-second wall-clock budget. The measured seed is 3.2 s locally and stays inside
that for a database in the same region; a handler that exceeds it is terminated and
retried, after which the explicit retry still initializes the company in the request.
Rollback is a code revert: queued runs are ordinary rows and the retry path completes
any company left initializing.
