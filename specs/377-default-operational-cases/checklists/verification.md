# Verification evidence

Base: `main` at `b7a1f16e`; implementation: `feat/default-operational-cases`.
Specification and handoff imported from `feat/company-reference-simulator`.

- Test-first proof: ordinary default acceptance, no-owner discovery, rollout persistence
  and public internal-job refusal all failed before implementation (four failures).
- PostgreSQL case/guard/adapter/migration/tenant-isolation checks: 91 passed. Covers
  canonical acceptance, partial/closed history, raw Sources, rollback/retry, concurrent
  backfill/intake, old manual revisions/bindings/unknown execution, exact handback,
  missing migration, downgrade refusal, exhausted leases and revoked historical owner.
- Canonical-order compatibility checks: 2 passed; automatic serial reservations and
  Copilot approval still require supported order anchors and exact confirmed work.
  Manual orders without a Source have no interpreted Shopify refunds.
- Operational-cases Playwright proof passed: no enable control, incomplete rollout
  status, confirmation, takeover retry, provenance, exact handback and direct discovery.
- `make lint`, `make spec-check` (also against `origin/main`),
  `make business-annotations-check` passed (649 described functions, 115 described tests,
  zero missing root functions or approved tests).
- `make web-build` passed: formatting, executable contracts, localization audits,
  TypeScript and production build.
- `make docs-build` passed: 16 Python reference tests, 145 Node contracts, formatting,
  generated reference and production documentation build.
- `make docs-catalog-check` and `git diff --check` passed.

Broad regression found two HTTP review integration defects: assigning a deterministic
proposal ID after case binding, and overwriting the stored case business review. Both
are corrected before persistence; a dedicated replay/binding/review regression passes.
Playground and migration concurrency fixtures now use canonical supported orders,
retaining their receipt, correlation and rollback assertions. Additional targeted checks:
42 passed plus the corrected full empty migration roundtrip/populated downgrade proof
(1 passed).

Further regressions prove shared scheduler coexistence (10 passed), reporting/catalog
contracts (25 passed), shipment/warehouse/readiness flows (45 passed), adapter flows
(6 passed) and movement readiness (7 passed). Commercial purchasing/finance/order
scenarios passed 97 checks; their three orderless fixture failures were corrected
without relaxing guards. A subsequent focused run passed 23 of 24 checks; the remaining
free replacement was updated to use an observed member for both replacement creation
and shipment, preserving its orderless, zero-price semantics.

The broad run also exposed Numeric scale changes after loading case business state.
Shipment readiness normalizes derived open quantities; delivery reviews load canonical
case records before both snapshots. This avoids false stale-review refusals while
retaining exact current-state and control revision fencing.

Latest case/guard/manual-replacement run: 32 passed; one migration failed because
parallel test schema construction exhausted the local PostgreSQL lock table. The
throwaway container now uses CI's `max_locks_per_transaction=1024`; that migration
proof passed on repeat (1 passed), and the complete suite is rerunning. No application or deployment setting changed.

The Web action-reference fixture now matches default policy and status metadata.
The activity-volume proof counts the shared delivery fixture's accepted order while
still rejecting duplicate import events. Both revised contracts passed (2 passed).

Further current-schema and public-adapter checks passed: email migration (1), MCP
confirmed reservation (1), and complete application catalog/HTTP contracts (51).
Fixed count assertions reflect 207 commands, 102 currently emitted event types and
717 tenant-classified operations. Application-tool reservation fixtures retain their
exact unknown-execution and receipt proofs with canonical order anchors.

The eight-worker local backend run completed 1,564 passing proofs and 10 expected
skips before interruption. Its ten failures were outdated fixtures/counts corrected
above; ten demo setup errors arose from the unchanged 120-second handler deadline
under concurrent local load. The same complete demo-profile proof passed on repeat
without changing deadlines (1 passed). A four-worker continuation retains completed
proofs and runs every remaining collected test, including failures/errors, using only
a temporary local collection filter. No repository assertion or product limit changes.

Final API review found that the old human business-member check also blocked an
owned sandbox's status read (new regression failed with HTTP 404). Status now follows
existing private tenant-surface access and reports can_control=false for sandboxes;
business-member takeover rights and anonymous sandbox refusal remain unchanged.
Default-case, API and job checks passed after this fix (27 passed). Legacy adoption
acknowledgements pass the already verified owner to readiness output, preserving old
stored receipt replay and truthful current control availability.

Full backend (6,492 current collected tests), full fixture browser suite (87 scripts)
and PR CI are running. T011 and complete acceptance remain unchecked until assessed.
The local browser harness maps existing macOS `/private/tmp` screenshot paths to
`/tmp`; it changes only local artifact paths, not assertions or product code.
Google Fonts is blocked in this environment. The OAuth browser script initially failed
on that external asset; its repeat passed with a local empty stylesheet route and the
existing system-font fallback. All consent, grant and error assertions remain intact.

Simulator runtime remains on its separate branch. The imported integration regression
explicitly skips when `reality.services.live_company` is absent. External-runner and
multi-day capacity gates remain pending; no production rollout is claimed.

Current regression evidence before the final CI repeat:

- Explicit delivery business re-review renews its held-state digest only for existing
  CaseProposalLinks. Their control revisions are never rebound. A new regression proves
  that re-review after takeover/handback still refuses the old proposal with
  `case_action_stale` and creates no reservation. The complete targeted case/guard,
  delivery review/holds/reads and Storyline run passed 63 tests.
- Actual-member manual exchange and unannounced-return repair, source coverage and
  canonical stock scenarios passed 66 tests. CLI `--yes` cannot claim an observed human;
  its unsupported exchange confirmation refuses without effects, and subsequent actual
  member confirmation retains the same proposal and exact business review.
- Orders API filters passed 3 tests. Credit blueprint evidence passed 2 tests.
  Captured-basis rollback, fulfillment safety and bounded demo settlement passed 20 tests;
  one unrelated full demo-profile setup exceeded the unchanged 120-second limit under
  concurrent local load and needs a reduced-load repeat.
- All 87 fixture browser scripts are covered: 83 passed in the full run and the four
  local environment failures passed on repeat. The repeat supplies installed Chromium,
  maps artifact paths and uses the existing system-font fallback for blocked Google
  Fonts; it preserves assertions. Current action discovery also passed separately.
- CI at `6c9c4fd6` passed Installer, documentation, frontend, all seven fixture-browser
  shards and eight live-browser journeys. Its backend failures exposed the additional
  historical/canonical fixture updates; live company setup exposed source starvation.
  Independently queued case work is now excluded from the existing source/projection
  alternation. Its regression and a fresh complete CI run are required before acceptance.
- Historical cost/finance migration specimens explicitly retain their predecessor's
  pre-coordination policy in test setup. Their exact data, schema and rollback assertions
  remain intact. Current-schema missing-migration refusal remains covered independently.
- The fixed normal-month story now anchors cancellation to a sales order and records
  the customer's two-unit return at the same instant as its receipt, using the canonical
  announcement/commitment relationship. Its quantities and financial effects are unchanged.
  Fresh CLI, Chat, commitment-action and worker interaction checks passed all 5 tests.
- Latest lint, spec policy (including origin/main), generated catalog consistency and
  whitespace checks passed. Complete backend continuation and final CI remain pending;
  T011 remains unchecked. The current collection includes 6,495 tests.
