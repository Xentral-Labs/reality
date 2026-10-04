# Runtime cutover verification

Status: implementation in progress. This evidence does not certify US1 universal
writer enforcement, completed rollout, or a production release.

## Verified focused behavior

- Legacy Shopify/file/financial interpreters refuse direct invocation, including
  an arbitrary executing-action tag: `test_retired_interpreters_cannot_reuse_raw_or_action_id_as_approval`.
- The shared queue prepares a retained proposal without Documents or Commitments:
  `test_pending_job_cutover_is_safe`.
- Continuous synthetic preparation waits without an implicit reviewer:
  `test_unavailable_reviewer_does_not_turn_intake_into_business_effects`.
- A retained named-agent grant can approve the exact synthetic order within its
  actual source, capability, profile, currency and finite limits:
  `test_live_demo_uses_real_decisions`. Evidence is supplied by a controlled client
  fixture; this does not measure a live model's judgment, latency or cost.
- Fixed compact/month definitions require explicit confirmation. A completed
  fixed receipt replays without new effects or confirmation. Unconfirmed setup
  and subsequent unrelated intake remain refused.
- A safe ambiguous Demo Data preparation is separately review-required, rather
  than a failed execution. The actual worker, retained job and status agree.
- Historical completed jobs without a retained proposal preserve their source,
  input, timestamp, attempts and events without inventing decisions or outcomes:
  `test_historical_provenance_is_honest`.
- Explicit supported normalized financial profiles retain the original source
  system; an unknown declared profile remains raw and unmapped. Preparation
  grants no effect authority.
- Unstated order totals remain null in delivery readiness. Prepayment waits for
  a stated required amount instead of recomputing one from price and quantity.

## Executed checks

- Frozen backend regression: 6,178 passed, 10 skipped, one outdated benchmark
  fixture failed (18m34s). The sole failure omitted the newly required named
  reviewer ID in `Company`; the corrected Black Friday scenario passed separately.
  No runtime source was changed after this full run. Final committed-head CI
  must pass all backend shards before this slice is marked complete.
- Focused source/file/rollout regression: 49 passed. Historical and financial
  regression: 70 passed. Demo/security/startup/parity regression: 47 passed.
- Peak benchmark: two passed; its 50 applied orders carry actual executed
  proposal receipts attributed to the fixture's named Owner.
- Final frontend contracts: 462 passed. Final presentation browser: all 16
  language/theme/width combinations passed, including awaiting-decision and
  review-required states without implicit acceptance or reviewer enrollment.
- Actual PostgreSQL company-setup/worker/browser proof passed (93.35s): the
  creation receipt selects the new owned Sandbox, a generated source remains
  unapplied, its complete original and canonical digest are checked, the user
  confirms in the actual review dialog, and exactly one source becomes applied.
  The database proof checks original payload equality and actual decider identity.
  This proves pipeline behavior, not live-model judgment or provider cost.
- Actual bulk browser proof passed (83.56s), including lost-response replay and
  retained exact source receipts. The business, file-import and finance browser
  journeys passed. History/engine-room business assertions passed locally; their
  strict console-error checks failed on blocked Google Fonts and a default
  favicon request in the local system Chromium. The committed-head CI must
  run both journeys with its installed Playwright browser.
- Final language audit: 2,738 keys in all four languages, zero missing or invalid
  entries. Final frontend build passed. Standardized refusal gates: 29 passed.
- Specification policy, business annotations, Ruff and generated references
  passed. Final contracts passed again after translating the dedicated bound-source
  refusal into German, Dutch and Spanish; the final build passed.

## Remaining completion gates

Complete the final browser runs and committed-head CI, including all backend
shards, generated documentation and frontend/browser gates. The local full-run
fixture failure is recorded above rather than represented as a passing full run.
The required final CI verifies the corrected committed test.

The 507 baseline AST candidates remain an inventory, not semantic coverage. Public
canonical writers outside intake/setup authority and their non-core callees still
require the US1 guard, explicit exception classification and direct-call refusal
proofs. No task requiring that universal boundary is marked complete here.

## Worker/control concurrency regression

The live company-setup proof reloads the current Demo Data revision before its
explicit pause request. It retries only the documented `unfinished_run` refusal,
with the same request key, refreshed revision, a 500 ms polling interval and a
60-second deadline. An already claimed worker run must finish before its queue
can be cancelled; five immediate retries did not establish that condition.
Other refusals still fail the proof. The actual PostgreSQL/worker/browser journey
passed again under concurrent backend-suite load (109.86s),
including exact original payload, digest, decider and one applied document.

## Disposable CI database capacity

Quality run 37168058421 exhausted PostgreSQL's default shared lock table in
parallel full-schema migration tests (`test_all_migrations_on_disposable_postgresql`
and `test_target_migration_preserves_ledger_and_refuses_history_loss`). The
backend-test job now explicitly sets and verifies `max_locks_per_transaction=1024`
in its own disposable service container before testing. Deployment configuration
is unchanged. Both affected migration proofs passed concurrently against the
local disposable database configured at that capacity (13.60s). Required
committed-head CI remains the completion gate.

## Canonical master decision slice (qualification in progress)

- Valid direct create/update and unconfirmed REST requests fail without accepted
  effects in both authentication modes. Changed/repeated canonical callbacks and
  premature root commits refuse atomically; confirmed company creation is limited
  to its exact creation receipt.
- Fixed compact/profile master callbacks are frozen: two valid changed/repeated
  callbacks failed before enforcement; 40 fixed/setup/playground checks passed
  afterward.
- Current confirming token revocation and loss of confirmation permission each
  produced `DID NOT RAISE` before enforcement. Both now refuse accepted masters;
  token attribution remains distinct from human attribution.
- Focused history, migration, isolation, reference and CSV checks: 97 passed,
  four fixture expectations corrected. A second batch passed 32 checks; remaining
  expectation/fixture errors were corrected. The final affected batch passed all
  38 checks, including CLI, MCP, web interaction attribution, token refusal,
  delivery locking, exchange previews and fixed/canonical master attacks.
- Real small single/bulk volume setup: six checks passed. Catalog generation and
  specification policy passed. Full regression and committed-head CI remain
  required; no result from an earlier source snapshot certifies this slice.

Historical fixture rows explicitly preserve retained creating relationships or
unknown attribution. Test-only reflected migration inserts grant no runtime
permission. No unrelated writer family is marked complete by this slice.

### Master committed-head CI follow-ups

The first CI head passed three backend shards, all seven browser contract shards,
six real browser workflows, docs and spec policy. The remaining backend failure
was a fixed-profile cross-company refusal being masked by the newly earlier intent
check in `create_item`; company-purpose/profile checks now run first. The fixed
profile also explicitly refuses a foreign session/root/company before operation
acceptance. All 50 directly affected security/canonical/fixed proofs passed.

The engine-room browser now sends actual confirmation for its explicit member
save; local real-stack verification passed all 27 functional checks, with its
strict console check failing on unavailable font/network resources. Committed-head
CI remains the required complete browser proof. The optional demo-payment harness
has been formatted; its two-hour soak is not claimed executed.
## Finance configuration slice (qualification in progress)

The existing Finance branch retains its proposed-state row lock and atomic effect /
executed receipt. A private scope binds actual confirmation, retained command,
current root, principal/token and policy; it never creates an executing claim.
Direct arbitrary account configuration and direct finance dispatch refuse.

- Six valid direct/tag cases and direct proposed dispatch/absent confirmation
  produced `DID NOT RAISE` before enforcement. Changed account input also applied
  previously; repeat/early commit are now refused by canonical invocation/root
  checks, rather than a later incidental stale preview.
- Initial combined canonical/finance/master checks: 24 passed.
- Finance regression: 431 passed, 16 failed; missing actual confirmation in positive
  HTTP fixtures and missing existing roles in the account catalog were resolved.
- Existing exchange-difference/down-payment role proposals failed validation
  before catalog parity was repaired. A genuinely demoted Owner in another
  transaction produced `DID NOT RAISE` with a cached membership; canonical checks
  now reread its current role and serialize later changes through settlement.
- Final affected finance/account/foreign-currency/HTTP-MCP checks: 59 passed.
- Test fixtures use retained existing finance commands and a real named Owner;
  no current actor/approval is added to historical migration fixtures.

Full regression and committed-head CI remain required. Other canonical writer
families and final semantic inventory closure remain pending.

Final parent integration: 29 canonical finance/master/profile/token checks passed on the master CI correction parent. Frontend contracts passed all 462 checks and the production build passed; catalog generation, Ruff and spec policy passed. Full committed-head regression and CI are still pending.

Account-only operation closure: valid callbacks admitting an unrelated Document
or stock receipt each produced `DID NOT RAISE` before the operation filter. The
confirmed account transaction now grants account maintenance/audit only, while
lossless raw source capture remains an explicit non-business-effect exception.
All 55 affected account/canonical/intake checks passed; the final 17 configuration
proofs also passed, including raw preservation without accepted Documents.

Finance CI integration correction: the original committed-head run found explicit
confirmation missing in Finance Web forms and positive browser/story fixtures,
and fixed initial profile account configuration was incorrectly refused. Finance
forms now send confirmation only after the user's confirmation action; rejecting
still sends no approval. The fixed setup path retains its actual company/run/root
and closed authored account definitions plus frozen, single-use invocations. Its
profile finance dispatcher checks the exact retained proposed command and authored
intent instead of manufacturing an executing claim. The meaningful pre-fix proof
refused two valid preset account calls; all 31 canonical/configuration/execution/
profile-security checks passed after correction. Other CI failures and the complete
regression remain under investigation.

The complete company setup/international demo/order-to-cash affected scenarios passed: 30 tests in 155.53 seconds. The initial Finance CI backend shard also identified positive allocation and owner-refusal fixtures missing their intended explicit confirmation; those inputs are being corrected without changing permissions.

Final affected positive Owner/allocation and initialization follow-ups: 18 passed.
All four previously failing real browser journeys passed locally with actual Web/API/
worker/PostgreSQL: company setup, Finance rollout, unified business journey and bulk
intake (514.29 seconds). All 462 frontend contracts and the production build passed.
The bulk browser failure did not reproduce; committed-head CI still must prove it.
The existing attribution instrument now names the frozen dispatcher parameters and
recognizes that actual dispatcher call inside its executing-proposal context. The
account-initialization annotation is attached to the invocation, not its import.

Final attribution, opaque-ID MCP boundary and repository annotation audit: 15 passed. Catalog generation and spec policy passed. The original complete regression remains running on its frozen source; its discovered profile/confirmation/instrumentation issues have the affected passing proofs above. Final-head CI is still required.

The complete frozen pre-correction regression finished with 42 failed, 6,158
passed, 10 skipped and 19 setup errors in 1,570.32 seconds. Its failing set matches
the original four CI shards: fixed preset setup, missing positive confirmations,
probe keyword/AST instrumentation and the misplaced annotation. This is a failed
pre-correction run, not a passing final qualification. The corrected committed
source still requires its complete regression and all CI jobs.

The bulk browser failure reproduced twice in CI. The downloaded final-head CI
artifact showed 24 earlier cold projection jobs across the two owned test tenants,
zero batch members settled at the browser deadline, followed by the queued batch
run succeeding in 2.853 seconds as stack shutdown waited for it. This was a queue
wait race, not an authorization failure or duplicate effect. The harness now waits
at most 120 seconds for the real cold queue, with a 240-second whole-script limit;
execution/volume budgets and all receipt/duplicate/source assertions are unchanged.
Failure artifacts include scoped queue types/statuses/errors, without payloads.

The bounded cold-queue bulk browser qualification passed locally in 86.21 seconds. The final queue-harness correction changes no production Python or default backend tests; the complete production regression remains running on identical production source at 14ca6637. Committed-head CI remains required.

### Normalized evidence qualification in progress

Three meaningful direct/absent-confirmation proofs produced DID NOT RAISE on the
pre-boundary source. The normalized writer now requires the actual current
confirmed existing command family or exact intake/fixed setup. document_create
freezes and consumes its invocation once, owns evidence plus receipt atomically
and permits no unrelated header/stock/commitment effects. Its public proposal
cannot claim private action/commit/source-absence fields. Other order/invoice/credit
root ownership, header-only and correction boundaries remain tracked separately.

Legitimate fixture documents, orders, invoices and credits use retained existing
commands and actual named Owner confirmation plus the actual retained review token.
No Source amount/line/actor/approval is invented to bypass a guard. Initial affected
regression: 89 passed, 25 failed because order review tokens were not forwarded;
after forwarding actual tokens, 112 passed with two remaining direct invoice
fixture failures. The subsequent invoice/HTTP pass had 146 passed and one expected
earlier catalog input-refusal text mismatch. Final/full/CI qualification is pending.

Approved import callback qualification found a further real gap: a valid repeated
normalized-document callback produced DID NOT RAISE and accepted duplicate
evidence. The analogous commitment repeat hit a later database uniqueness error
instead of admission refusal. Each actual effect scope now consumes frozen
canonical invocation nonces once; separate planned package commands retain their
separate nonces. No extra SQL/state/actor is manufactured. Full source/profile/bulk
regression and final volume qualification remain required.

The Finance parent de4d4218 passed all 23 CI jobs. Its identical production/backend source completed the full regression with 6,221 passed and 10 skipped in 1,637.74 seconds. Normalized document single-use, import, bulk, mandate and calendar follow-ups passed all 112 checks in 75.74 seconds; complete document qualification is pending.

Normalized document adapter follow-ups: 50 focused document/API/annotation checks,
462 frontend contracts and the production Web build passed. Both real backend
business/bulk browser journeys passed in 360.81 seconds. The frozen complete run
found positive catalog document confirmation calls missing their explicit flag,
an obsolete API-only order spy, and source attribution checks not following the
new canonical normalizer. Corrected catalog/drop-ship/finance/order/purchase/HTTP
cases passed all 104 checks; return and source-attribution cases passed all 21.
These changes are test adaptation only; absent confirmation remains refused.
Full regression and final committed-head CI remain required.
