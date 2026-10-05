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
- Complete shared scheduler/worker/recovery/projection/case checks passed 73 tests
  on the final implementation. Queue/worker/case/migration checks passed 25 tests.
  A fresh run passed all three
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
- Complete implementation CI at `f88c6b6b73464ac089e26173f5fd1d9899bd5325` passed:
  [Quality gates run 37380117375](https://github.com/Xentral-Labs/reality/actions/runs/37380117375)
  and [Installer run 37380117269](https://github.com/Xentral-Labs/reality/actions/runs/37380117269).
  All four backend shards and the aggregate passed: 6,489 passing tests and 11 skips
  across the shards. Spec policy, documentation, frontend/localization, all seven
  fixture-browser shards and all nine live-browser journeys passed, including actual
  company setup and the full business journey. Earlier month-story and source-starvation
  failures are resolved without weakening their assertions.
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

## Final review and remaining integration gates

Independent final read-only review of `f88c6b6b` found no material defects in claim
fairness, the index/migration, the narrow fixture scope or their regressions.
The current backend collection contains 6,499 tests.

T011 is complete against the implementation commit above. Final diff/whitespace and
spec-policy checks passed; independent review found no material defects. The completion
commit updates only this evidence, task status and specification status, with no runtime,
migration, test or public/generated documentation changes. Its spec-policy and whitespace
checks also pass. GitHub may rerun the unchanged implementation after that evidence commit;
the green full run above identifies the exact tested code.

Simulator runtime stays on its separate branch; the supplied integration
regression explicitly skips when `reality.services.live_company` is absent.
External-runner and multi-day capacity gates remain pending under FR-009. This PR
makes no production deployment or external simulator acceptance claim.
