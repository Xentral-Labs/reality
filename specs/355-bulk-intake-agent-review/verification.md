# Verification checkpoint: fixed bulk decisions and durable chunks

The selected manifest and shared database-only queue path are implemented. This
checkpoint is not completion of delegated review, Web selection/recovery, all
intake adapters or performance acceptance.

Observed PostgreSQL results:

- 69 tests passed across bulk admission, application/tool catalogs, annotation
  regression and tenant isolation before the final queue-volume additions.
- 19 bulk/shared-queue tests passed, including actual queue claim/execution and
  atomic run success with child receipts.
- 500 five-line orders prepared without accepted documents, then applied through
  20 real queue deliveries of 25 units: 500 documents and 2,500 lines, no duplicate
  continuation, exact 500 retained dispositions across five result pages. The
  queue configuration stays below 15,000 bytes and each result below 3,500 bytes.
  This correctness test took 40.51 seconds on the session's local PostgreSQL; it is
  not the three-run comparative throughput benchmark required by FR-013.
- Final combined PostgreSQL verification: 81 tests passed in 91.79 seconds across
  all bulk admission cases, application/tool catalogs, shared scheduling, annotation
  regression and tenant isolation, including the full 500-order queue workload.
- Spec policy, Ruff, catalog generation, business annotations and Web build pass.

The worker preserves the original reviewer, rechecks current child authority,
retains revoked/stopped/stale no-effect results, and aborts the whole provisional
chunk on infrastructure failure. Immutable manifest membership excludes later
arrivals. Every accepted child keeps its own decision and parent authorization.

Pending: AgentMandates and structured external verdicts; Web/CLI selection and
stop/recovery flows; financial independence; real competing claims/crashes and
three-run query/time/memory measurements including 5,000 items. Full repository
and PR gates must pass before this checkpoint is described as verified globally.

## Named-agent single-unit mandate slice

A separate, confirmed current-owner proposal grants finite authority to one actual
manual MCP token. Its retained mandate binds source system/capabilities, closed
profiles/effects, rows, UTC-day units, source-stated per-unit/daily amounts and
currency, expiry and revision. Review fetch and settlement refresh the token,
issuer, owner membership, source and capability activation under database locks.
Built-in Chat and missing/foreign authenticated agents cannot use that authority.

Original payload/artifact bytes are available in fixed 64 KiB pages outside the
worker. Evidence binds exact plan/source hashes, every original byte range and
original row/line references, six deterministic checks and a bounded verdict and
reasons. Coverage claims do not establish cognitive understanding. Uncertainty
retains review evidence without accepted effects. Accepted receipts name the
actual token and mandate revision and do not fabricate human approval.

Observed PostgreSQL checks:

- 66 tests passed in 38.15 seconds across initial mandate/tenant refusals and
  executable application/tenant catalogs.
- 23 final targeted mandate and migration tests passed in 7.02 seconds, including
  confirmed revocation, expiry, token revocation, issuer deactivation, owner
  demotion, currency and amount limits, effect scope, free exact replay, original
  byte reconstruction and refusal to erase retained mandate history.
- Ruff passes. The complete repository backend suite is running; no full-suite
  success is asserted by this checkpoint.

Pending for this feature: queued delegated bulk with per-child retained verdicts
and execution-time mandate/quota checks, concurrent quota proof, full bulk
Web/CLI controls and comparative volume measurements.
