# Verification

## Completed checks

- The measurement that opened the feature, taken on a created playground company:
  request 0,044 s / 39 statements, worker 2,72 s (seed 2,36 s / 5.676 statements, live
  setup 0,33 s / 732 statements). The remaining wait was worker poll (up to 5 s) plus
  the screen's first read (2 s) — roughly half the total spent waiting to look.
- New discovery tests failed first for the stated reason (`AttributeError: due_tenants`),
  then passed: only tenants with claimable work, an expired lease counted as work again,
  a future attempt time excluded, the cursor and limit bound enforced, and the sweep
  itself proven not to call the full catalog for the worker role.
- The first draft of the expired-lease test executed the old claim token and hit
  `stale_claim`; the fencing is correct and the test now re-claims, which is what a
  worker does.
- Receipt tests prove the reported state moves queued → preparing → none, and that a
  company nobody prepares reports nothing.
- Web: 9 contract tests over the derived steps and the immediate first read, including
  that a ready company returns after one read in well under a second, that a failed
  receipt reports no steps at all, and that at most one step is ever current.
  181 contract tests in total, four-language audit, TypeScript and Prettier.
- Browser run: the three steps appear, the first is done, the middle one reads
  "Waiting to start" while the run is queued and only then becomes
  "Preparing orders, deliveries and invoices" with exactly one current step. Screenshot
  reviewed.
- One trap worth recording: the four-language audit does not flag a plain object
  property such as `label: "Ready to explore"`, though it flags the same string inside a
  ternary. All three step labels were added to the catalog by hand rather than trusting
  the audit to find them.
- Lint, format and spec coverage policy passed.

## Completion

Full PostgreSQL suite: 2572 passed, 9 skipped in 17:54.

Expected effect on the wait: the worker's poll drops from five seconds to one, and the
screen's first read from two seconds to none, so roughly seven seconds of waiting become
roughly three. The seed itself is unchanged at 2,7 s and is the next thing worth
reducing — sixteen statements per created record, its own specification.
