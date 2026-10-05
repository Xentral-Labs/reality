# Verification evidence

Base: `main` at `b7a1f16e`; branch: `feat/default-operational-cases`.
Specification and handoff imported from `feat/company-reference-simulator`.

## Default policy and safety

- Four test-first failures proved missing default acceptance, no-owner discovery,
  rollout persistence and public internal-job refusal before implementation.
- 91 PostgreSQL case/guard/adapter/migration/isolation checks passed: canonical
  acceptance, partial and closed history, raw Sources, rollback/retry, concurrent
  intake/backfill, existing manual control, old bindings, unknown execution,
  exact handback, missing migration, downgrade refusal and revoked legacy owners.
- Fresh case/guard, delivery review/holds/reads and Storyline checks: 63 passed.
  Business re-review updates existing business digests only; the old control revision
  survives takeover/handback and still refuses execution without reservations.
- Observed-member exchange/unannounced-return repairs, source coverage and canonical
  stock scenarios: 66 passed. CLI `--yes` never becomes an observed human. Its
  unsupported automated repair refuses without effects; an actual member can confirm
  the retained proposal with the existing business review.
- Canonical-order fixtures retain their original quantities, financial effects,
  concurrency, rollback and unknown-execution assertions. Historical migration
  specimens explicitly preserve pre-coordination fixture policy only while pinned
  to the old schema; current missing-schema refusal is independently covered.
- Confirmed fixed-month setup preserves its deliberately unexplained return through
  a scope around that one original movement, after `_require_fixed_setup` validates
  the exact immutable approved definition/session/transaction/tenant. No invented
  announcement or human principal remains. All 41 month/intake/default checks passed;
  an additional regression passed, proving automatic context restoration and refusal
  of an ordinary unanchored return immediately afterwards. Independent review accepts
  this narrow preservation; generic guards and takeover checks remain authoritative.

## Shared queue, migration and real source activity

- Initial shared claim fairness regression failed with more than 100 older internal
  runs before an ordinary source/manual job. Claims now alternate preferred classes
  using actual `started_at` history, with bounded per-class candidates and locked-row
  fallback. New enqueue is not a claim. Future retries and unresolved runs remain
  excluded; expired leases retain their run identity, attempts and fencing token rules.
- Queue/worker/case/migration checks passed 25 tests. A fresh run passed all three
  fairness regressions, the annotation audit and both credit-graph checks (6 total).
- Fresh full migration roundtrip/populated downgrade proof and ten real demo-worker
  occurrences passed (2 tests). The partial claim-history index is verified against
  current metadata and absent after downgrade. Original deadlines remain unchanged.
- Real live company setup passed (1 test, 104.61 seconds): browser login and company
  creation, new retained sources, actual review/decision and original payload audit.
  The source wait retains its original 60-second limit. Earlier failures showed
  unclaimed source runs behind internal backlog; no source handler failure was inferred.

## Regression and public surfaces

- Full local backend execution retained 1,564 passing tests and 10 skips before the
  eight-worker interruption. A four-worker continuation executed every remaining
  item: 4,866 passed, 2 skipped, 44 failed and 7 errors. Workers had loaded earlier
  source versions; all discovered failures were corrected and rechecked in targeted
  runs. These are broad execution evidence, not a claim of one green full-suite run.
- Current CI at `0ae677c8`: backend shards 0, 2 and 3 passed; shard 1 failed solely
  on the fixed month's exact exception story. Installer, specification, documentation,
  frontend, all seven fixture-browser shards and eight live journeys passed; live
  company setup failed on source starvation. Both remaining failures are fixed above.
  A fresh complete CI run is required before T011/acceptance completion.
- All 87 fixture browser scripts are covered: 83 passed in the full local run and
  four local environment failures passed on repeat. Default-case takeover/handback
  and current action discovery passed. Local harness supplies installed Chromium,
  maps macOS artifact paths to `/tmp`, uses system fonts for blocked Google Fonts,
  and reattaches an intermediate auth navigation within the same original deadline.
  No repository assertions, browser source or product deadlines were relaxed.
- `make web-build` passed formatting, executable contracts, localization, TypeScript
  and production build. `make docs-build` passed 16 Python and 145 Node contracts,
  generated references, formatting and production documentation build.
- Latest lint, spec policy, generated catalog consistency and annotation audit passed.
  Annotation coverage has zero missing roots or approved described tests. The fresh
  migration and reduced-load demo repeat passed without changing production settings.

## Remaining gates

T011 remains unchecked until the complete final PR CI is green and diff review is
recorded. Simulator runtime stays on its separate branch; the supplied integration
regression explicitly skips when `reality.services.live_company` is absent.
External-runner and multi-day capacity gates remain pending under FR-009. This PR
makes no production deployment or external simulator acceptance claim.
