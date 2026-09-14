# Validation Guide: Learning Playground

## PR #135 integration checkpoint (2026-09-06)

After the first green CI run, PR #136 advanced main to `54450a7` and claimed 095
for `095-a-fee-is-a-charge`. Rebased again without conflicts and moved Playground
to the next free number 096 using `scripts/next_feature_number.py --explain`.
Preserved the newly merged fee documentation/tests. This second integration changes
no Playground runtime behavior. GitHub also reports the existing Code Owner
`@benediktsauter` as invalid; choosing a replacement is an explicit owner decision.

Rebased on main `faee337`; Playground specification moved from 085 to the next free
number 095 because main now owns 085-close-stale-promises. Both sets of business
commands are retained (52 commands, 44 event types, 308 tenant operations).
Six newly integrated core mutations now enforce the shared sandbox boundary before
business validation. The existing catalog-driven denial tests reproduced all twelve
active/archived failures before this fix.

Migration 0041 joins the previously deployed Playground and main histories without
rewriting either revision. Regression tests upgrade from each prior head and preserve
tenant/sandbox data. Platform migration inspection reads literal revision metadata,
including merge parents, without executing scripts.

Focused integration verification: 464 tests passed (migrations, platform overview,
sandbox security and spec policy). Web/site/Docs build gates and all four web locales
pass; 97 web contracts and isolated browser trading/finance/return stories pass.
Full rebased backend rerun: **1,344 passed, seven unchanged skips, 151.68s**.
The site copy assertion now uses its existing whitespace-normalization helper so
Prettier wrapping does not falsely fail the sandbox-discovery contract. All local
build/audit gates pass. All six remote checks passed on `00cc0aa` in Actions run
34060076088, including the complete PostgreSQL suite. PR #135 was marked ready for
review after that result; required human Code Owner approval remains outstanding.
The subsequent owner-requested account-first homepage increment is documented in
Spec 022 FR-027 and receives a fresh CI run. Reviewer-owned checklist markers remain unchanged;
human learning acceptance and future chat/R2R scope are not implied complete.

## Supplier finance and returns checkpoint (FR-022–023, 2026-09-06)

Final verification after all code and catalog changes: **1,199 backend tests passed,
seven unchanged retired-UI skips, 157.00s**. T059–T062 are complete for this increment.
Runtime validation reports 42 commands and 289 tenant operations; API health is OK.

The in-sandbox chooser now supports purchase → partial/final receipt → stated
supplier invoice → allocated supplier payment, and recorded customer shipment →
return → stated credit → allocated refund. Each action has a separate review;
selection and repeated operations preserve the same run. The four cards fit the
1280×800 cockpit. Fresh-sandbox presets remain trading/partial-delivery; the library
labels purchasing and returns as operations available inside the sandbox.

Failing-first outgoing-finance tests demonstrated partial durable payments after
allocation errors, missing action correlation, and refund currency loss. Shared
supplier-payment/refund services now commit atomically and preserve USD as well as
EUR. Supplier invoice/credit evidence uses the common source/document/ledger services.
Credit posting failure after ledger creation also rolls back evidence and events.

Full backend checkpoint: 1,198 passed, seven unchanged retired-UI skips (158.66s).
The subsequently added credit rollback test and final shared-reader refactor passed
the 24-test finance/story subset; the final receipt terminology passed six story
cases. 96 frontend contracts, TypeScript/Vite build, Ruff, spec policy and diff checks
passed. Isolated browser fixtures exercised twenty confirmed operations, supplier
invoice/payment references, historical return selection, credit/refund references,
reload before confirmation and between steps, both themes and the prior partial
delivery scenario. Screenshots were inspected; all four operation cards are visible.
Fixtures intercept HTTP and do not claim live-account end-to-end execution. Browser
discovery returned no connected browser. No user's saved run was mutated or deleted.

These are incremental implementation checks, not complete public-release acceptance:
existing full i18n/human-review/chat/R2R gates and separate fresh-sandbox presets remain
open. No commit, push or PR; reviewer checklists remain unchanged. No extension hooks.

Local API/Web rebuilt and restarted with no migration or user-run mutation. The
served bundle is index-B8_icFtp.js with index-R2MYTQq4.css. The same twenty-step
isolated browser journey passed against localhost:8080; authenticated entry and
health checks passed. The final shared reader was registered in the tenant isolation
aggregate family; forty catalog/isolation tests and an explicit foreign-line denial
passed. Runtime catalog validation excludes test-file existence checks because test
sources are intentionally not packaged in the production image.

## Embedded operation chooser (FR-021, 2026-09-06)

The empty/completed cockpit uses one OperationChooser in the left action slot.
Opening stock returns to the chooser; sale progress no longer includes an earlier
standalone stock operation. No backend commands, run lifecycle or schema changed.
96 frontend contracts and TypeScript/Vite build pass. Isolated browser checks cover
empty entry, zero writes while selecting/cancelling, stock→chooser→sale, repeated
sales, purchase/partial/final receipts→chooser, reload, both themes and the separate
partial-delivery lesson. The chooser screenshot was inspected and duplicate footer
guidance removed to keep the three cards compact. Existing full-release gates remain.

## Purchase/receipt continuation verification (2026-09-06)

FR-020: the full backend suite passed (1,176 tests, seven existing retired-UI skips,
154 seconds). The final expanded purchase regression passed all five parameter cases
separately: purchase/partial/final receipt, replay and missing confirmation, altered
review, excessive quantity, mismatched item, inaccessible commitment, customer instead
of supplier commitment, and handler tampering with quantity/action/from-location/source.
Ten ordered units produce no stock until received; 4 then 6 produce stock 10 and
zero remaining supplier goods obligation without ledger entries. No new domain
command or schema was added; the existing shared commands remain authoritative.

96 frontend contracts, TypeScript/Vite build, Ruff, spec policy and diff whitespace
checks pass. Isolated browser fixtures cover sales → purchase → partial/final receipt,
reload with real-shaped summary/detail responses, exact supplier/commitment/location,
incoming obligation display, further sales selection and stock continuation. The
four-step partial-delivery regression and light/dark assertions also pass. Screenshots
were inspected. These are isolated browser fixtures plus real PostgreSQL service
tests, not a mutation of the user's saved sandbox. Supplier finance, returns, chat
and pre-existing complete-release/i18n gates remain open.

## Continuing sandbox verification (2026-09-06)

FR-019: 96 frontend contracts, TypeScript/Vite build, 72 PostgreSQL Playground-step
tests, Ruff and spec policy pass. The shared financial story now executes two
sales in one run: 20 initial pieces, deliveries of 12 and 3, physical balance 5;
the first invoice remains EUR 175 open while the second EUR 75 invoice is settled.
No new backend command or schema is introduced.

Isolated browser fixtures verify two successive sales with distinct commitment,
order-line and invoice IDs, reload after the second order and before shipment/payment,
cancel without mutation, preserved run URL/history, current-operation progress,
additional opening stock and the original partial-delivery exercise. Screenshots
were inspected at 1280x800; shared light/dark contrast assertions pass. Browser
discovery returned no connected browser, so this is not live-account E2E proof.
The local web container was rebuilt separately; existing user data was not modified.
Purchasing, returns, free-form operations and the existing full-release/i18n gates
remain open. Existing step quotas are retained.

## Invoice/payment cockpit checkpoint (2026-09-06)

FR-018 / T048–051: trading histories now continue after shipment with a stated
invoice and an allocated payment. The common sales_invoice_record proposal composes
Source, linked invoice Evidence and receivable postings in one shared transaction.
The ordinary customer_payment_post command handles settlement. Both are narrowly
admitted only through owned reviewed Playground steps; generic mutations stay denied.
Partial delivery still presents four steps. Other scenario families remain disabled.

Failing-first: the real PostgreSQL story stopped at the missing invoice action.
Catalog regression exposed the missing order_line_id description and expected new
command/isolation totals; declarations now retain strict coverage. HTTP replay found
older reservation receipts changing their observed timestamp. The shared confirmation
path now preserves every existing receipt, restoring FR-005's write-once guarantee.

Verification: complete backend suite **1,175 passed, seven unchanged retired-UI skips**
(164.57s); **95 frontend contracts passed**, TypeScript/Vite build, Ruff, spec policy
and diff whitespace checks passed. Shared tests preserve a stated EUR 301 independently
of an order's EUR 300, check invoice rollback, and verify EUR 300 → EUR 175 after a
EUR 125 payment. The authenticated HTTP story verifies preparation without execution,
wrong revision rejection, replay, billing before delivery rejection, excessive payment
rejection, disappearance of the actual shipped_not_billed class and EUR 0 after full
payment. The final stricter exception assertion separately passed after suite collection.

Browser plugin discovery returned no connected browsers. Isolated Chromium fixtures
verified six confirmations, reload before payment, a visible EUR 175 position, all tabs,
inspectors, anchored buttons and both themes; the four-step partial lesson also passed.
Desktop and mobile invoice screenshots were inspected. Desktop fits one viewport;
the existing narrow-screen workspace remains horizontally navigable rather than claiming
complete mobile redesign. Fixture tests do not claim real-account browser execution.

Local API and Web were rebuilt/restarted without mutating any user run. API health and
authenticated Playground discovery passed. The actually served localhost:8080 bundle
also passed the six-step browser fixture journey. New financial copy has DE/NL/ES
translations; the complete multilingual audit remains red on pre-existing cockpit
copy/invariant gaps (DE: six missing/three invalid; NL: 56 missing). Full release,
human review and T044's remaining return/P2P/R2R work remain open. No commit, push,
public deployment or reviewer checklist change. No extension hooks are configured.

## Shared finance prerequisite checkpoint (2026-09-06)

FR-017 / T045–047: customer payment evidence, balanced postings, allocation and
their events now form one shared-service transaction. Child helpers support an
outer transaction; ordinary callers retain commit-by-default behavior. Confirmed
customer payments correlate all three events to the trusted proposal identity.
No schema, financial calculations, sandbox permissions or Playground UI changed.

Failing-first: both injected allocation failures persisted a payment document;
the confirmed-payment test found no action-correlated events. After implementation,
both failure positions leave no payment document, ledger entries, allocation or
events, even when the caller subsequently commits. Independent database sessions
verify durability. Two additional tests verify outer rollback and standalone
payment-document rollback when ledger posting fails.

Verification: 445 focused finance/tool/catalog/isolation tests passed. The complete
backend suite, launched from packages/reality-core, passed 1,165 tests with seven
existing retired-UI skips (142.60s). The two additional rollback tests were added
after full-suite collection and passed in the separate 166-test finance/Playground
run. Ruff, spec policy and diff whitespace checks passed. Diff review confirms
no supplier-payment change, no alternate simulator engine and no permission bypass.
Testing used disposable PostgreSQL databases; no live user run was mutated.
No browser claim, runtime rebuild, commit, push or deployment is part of this slice.
T044 remains open: invoice/payment controls and the other scenario adapters are not
yet enabled. Reviewer-owned release checklist decisions remain unchanged.

## Scenario library checkpoint (2026-09-06)

FR-014–016 / T041–043: the library opens before any new run. Seven localized learning
goals are grouped into sales, purchasing and accounting. Only trading-v1 (through
delivery) and partial-delivery-v1 are runnable. Planned invoice/payment, return,
purchase and accounting adapters stay disabled; T044 is not complete.

Failing-first tests rejected the missing selected-preset restart argument. The next
run exposed the legacy single-preset initialization guard; both start and seed now
validate the same versioned catalog. Replayed confirmed restarts use the owner's
request key and preserve the replacement after a lost response. Invalid scenarios
and unconfirmed switches do not archive the current run.

Verification: 161 focused run/API/step tests and 382 isolation tests pass against
temporary PostgreSQL databases; 94 web contracts and the production build pass.
Isolated Chrome fixtures exercise both choices, seven goals/five disabled choices,
selection cancellation, explicit setup and four action confirmations, scenario
context after reload, five-unit partial-delivery suggestion, inspectors, fixed
action position and both themes. A library screenshot was visually inspected.
These are fixture-based browser tests, not live-account end-to-end execution.
Ruff on changed Python files, spec policy and diff whitespace checks pass.

Local API/Web were rebuilt; read-only authenticated GET confirms two supported
presets and the existing 1,000/day and 2,000-retained configuration. No existing
user run was started, archived or deleted during verification. No public deployment,
commit or PR was performed. Full multilingual/human/performance release gates remain
open; the Spec Kit reviewer-owned checklist markers were not changed. No extension
hooks are configured.

Full regression result: 1,153 passed and seven unchanged retired-UI skips. Nine
migration tests failed because the command was launched from the repository root,
where their relative `alembic.ini` is absent. Repeating `tests/test_migrations.py`
from `packages/reality-core` passed all nine (4.13s), with no code changes. Thus all
1,162 backend checks passed across the full run and corrected migration invocation.
The final locally served Web build (`index-Ii9cQUFs.js`) also passed the isolated
partial-delivery browser journey with all API traffic intercepted; no live run mutated.

Implementation approved on 2026-09-06. Commands below are acceptance instructions;
only results explicitly recorded in the review record have been executed.

## Preconditions

Use the repository PostgreSQL test setup, installed locked frontend dependencies and an isolated
local deployment. No production credentials, tenants or customer data. Set feature enabled only
in the test deployment. Account A verified/active, B verified/pending production admission,
C verified unrelated owner, plus unverified/disabled negative identities. Keep a normal company
for A with distinctive records to prove there is no leakage. Use fake provider responses for CI.

## Core acceptance

1. B enters from Docs through login without company setup. Confirm run creation; production
   company creation stays denied. Check preset Party/Item/Location records and zero stock.
2. Repeat same creation key concurrently: one run, one seed. A/C cannot read B's run by guessing IDs.
3. Follow the five golden steps in contracts/playground.md without AI. Check every exact quantity,
   stored record, automatic event and unchanged assertion. Inspect from each receipt.
4. Prepare then reject a mutation: no domain changes. Propose a shipment exceeding open demand:
   explicit error, never manufactured success or record. Capture actual Exception identities.
5. Create an article through chat; confirm it. Stock remains zero until separate stock proposal.
   Introduce two similarly named customers; choose deliberately, never resolve by order of results.
6. Lose connection after domain commit and before proposal settlement. Reconfirm/poll; no duplicate,
   recover from correlated evidence or show blocked unknown. Crash before commit also stays honest.
7. Force projection/verification failure after success. Domain success stays separate from unavailable
   current-picture verification. Reads/recovery do not execute the action again.
8. Restart. New ready run has distinct IDs and zero stock; old run retains receipts and permits only
   reads, including through generic APIs. Seed failure leaves prior active run available.
9. Provider unavailable/turn quota exhausted: lesson buttons, inspection and current views still work.
10. Attempt invitation, secret/token creation/resolution, custom provider, connector setup and production
    target IDs through new/generic HTTP, tools, CLI/MCP and direct services. All forbidden effects denied.

## Required automated gates

```sh
make spec-check
make lint
make test
make web-build
cd apps/web && npm run test:contracts
```

Run make site-build and make docs-build from repository root when public integration lands.
Migration tests cover latest PostgreSQL head, existing business defaults, new constraints,
tenant table registry and disposable downgrade. Keep original normal-month expectations unchanged.
Detailed test filenames and failing-proof order are in tasks.md.

## Human and performance acceptance

Browser: fresh account/pending admission, desktop 1280px and mobile 390px, keyboard-only selection,
focus after confirmation/error, screen-reader labels, four UI languages and two Docs editions.
No browser unavailable condition may be recorded as passed visual acceptance.
Profile: local API + PostgreSQL, no external provider in timed guided flow, ten concurrent runs
using the 3-item/4-party preset and at most 50 steps/run. Record hardware, warmup, 100 measured
starts/actions and p95 separately. Targets: start 5s, post-action verification 2s (SC-003).
Moderated learning: five new users, five-minute guided task and explain-reservation question;
at least four succeed unaided (SC-001). Record anonymized observations, not invented results.

## Review record

The owner approved the specification, schema and security design with "freigabe" and
explicitly confirmed proceeding despite the 14 unchecked reviewer-owned security/UX
checklist items. Those markers remain unchanged; no security or release test was waived.

Baseline: local branch and origin/main at a9e7101 (#123); migration head
0038_return_resolution. Existing inventory/fulfilment suite: 7 passed against isolated
local PostgreSQL. The initial sandboxed connection was denied; the approved local-test
invocation succeeded. No production database was used.

Static analysis: 17 FR/DR requirements, 39 tasks, 100% mapped; no critical findings.
Performance and human acceptance have explicit tasks rather than claimed results.
Verified V1 tool names: party_create, item_create, location_create, order_create,
movement_create, reserve, reservation_release. Sales/movement subtype restrictions
must still be enforced below these generic tools.

Security implementation inventory: generic web/api.py, web/cli_console.py,
cli/app.py and mcp/server.py can reach services outside the proposal path. Guard
core mutators, proposals, reality_gaps, master-data/pricing and import processing;
include memberships create/accept/resend/remove, notifications enqueue and
deliver_next_invitation (including previously queued deliveries), secrets put/resolve/
replace/revoke, AI settings/key selection, MCP token issuance/authentication and
source-system/capability/connector setup. Account mail is separate from business mail.
Provider calls in agent/mcp_chat.py require the later managed-only sandbox context.
This inventory is implementation input, not a claim that the guards exist.

Implementation, migration, benchmark, usability, provider readiness and browser release
evidence remain pending unless recorded below.

### Storage foundation verification (2026-09-06)

- T003/T004: tenant purpose, run/step metadata, migration 0039, bounded JSON objects,
  database-enforced same-tenant run/proposal links and unique request/sequence constraints.
  Existing tenant purpose defaults to business even when its name contains Playground.
  A PostgreSQL trigger prevents conversion, including bulk SQL updates.
- Failing-first evidence: missing PlaygroundRun import; migration failed on absent purpose;
  new registry and JSON-bound tests failed before their implementation.
- Focused schema/migration/catalog suite: 25 passed, including lifecycle/version constraints
  and refusal to downgrade with retained Playground data. No production migration executed.
- Full backend regression at the preceding storage checkpoint: 628 passed, 7 skipped
  (123.64 seconds). The subsequent additional five lifecycle cases also passed in the
  focused suite. Skips are not claimed as executed acceptance evidence.
- make lint, make spec-check and git diff --check passed after fixing import order and
  registering the new concepts/test family in the central coverage matrix.
- No runtime entry, service isolation policy, seed, proposal executor integration, lesson,
  chat or UI is implemented yet. T005 onward remains open. Do not create interactive runs
  or expose public links on this storage-only foundation. Frontend/browser/human/performance
  release checks remain pending; this is not a completed Playground or releasable PR.

### Business-only boundary checkpoint (2026-09-06)

T005/T006 partial implementation: persisted-purpose checks now precede vault access,
generic AI settings/key/client use, MCP token creation/authentication, connector/source
configuration, membership changes, invitation enqueue and actual delivery. Already queued
forbidden deliveries become terminal failures without creating tokens or calling senders.
HTTP policy exceptions return 403 and a stable safe code even with local auth disabled.
The existing provider test now uses an actual business tenant/session so it exercises
the new boundary instead of supplying an untyped object as a fake session.

Failing-first evidence: the first negative service suite failed before guards existed;
14 additional connector/provider bypass cases then failed before their guards; four
HTTP cases exposed 500 responses before the dedicated 403 handler. Final focused
security suite: 46 passed. Lint and spec policy passed. Full backend regression:
679 passed, 7 skipped in 111.93 seconds. All seven skips are existing retired
server-rendered UI tests, not skipped Playground checks. External clients and mail
senders were mocked; no external delivery
or production credentials were used. No interactive entry or public link was added.

Complete mutation/admission policy and direct CLI/tool execution coverage remain open;
this partial egress boundary must not be described as complete sandbox isolation.

### Run ownership and closed mutation boundary (2026-09-06)

The shared resolver checks current persisted run ownership, tenant purpose, owner
membership, account status and email verification. Foreign or missing runs are not found;
admin status does not override ownership. Verified pending-production accounts can resolve
their own runs. Write eligibility requires an active run and non-archived tenant, but does
not grant execution permission.

All 80 core mutations in the existing isolation catalog now reject sandbox calls before
business validation/writes; the policy remains deliberately closed until confirmed run-step
execution exists. Generic proposals (all 62 mutating tools), decisions, company lifecycle,
demo seeding, nine rule-workflow mutations, staging and interpretation are also guarded.
Tests exercise actual CLI and MCP paths, not just helpers. Derived-cache reads are unchanged.

Failing-first evidence: missing owner resolver and unguarded core operations; then 134
generic lifecycle/proposal cases; then 20 direct rule/upload cases failed before their
guards. The CLI initially asserted only stdout; its real policy error is on stderr, so
the test now checks combined output and still requires the specific Playground denial.
Latest focused security/hold/rule suite: 414 passed.

An intermediate full regression had one failure: an unknown-tenant Hold expected the
old downstream "Commitment not found" instead of the new earlier "Company not found".
The test now expects the explicit earlier rejection and additionally verifies a genuinely
existing foreign tenant still cannot access the Commitment. No permission assertion was
removed. A complete rerun is required after this correction; record its result below.

Final complete rerun: **1015 passed, 7 skipped in 123.73 seconds**. The seven skips
are unchanged retired server-rendered UI checks. No Playground security test was skipped.
Lint, spec policy and diff whitespace checks also passed. No deployment or public activation.

T005/T006 are still not complete: generic HTTP read/admission wiring and the remaining
entrypoint audit are pending. No interactive entry, successful sandbox execution or public
release is claimed by this checkpoint.

### Private generic HTTP inspection (2026-09-06)

Implemented the next FR-001/FR-003 boundary using the existing shared owner resolver.
The tenant router independently requires a real authenticated owner for sandbox reads,
including local auth-disabled mode and platform administrators. Only explicitly listed
read routes and Inspector kinds are admitted, for active or archived runs. Configuration,
generic writes and unknown surfaces remain closed. Pending-production owners can inspect
their run without gaining access to their own business tenant or company creation.
Bootstrap/company selectors and the platform company overview exclude sandbox identities.

Failing-first evidence: 10 of the initial 13 HTTP tests failed, showing anonymous local
reads, foreign-admin access, missing pending-owner admission and company-list disclosure.
After the boundary change, 395 focused HTTP/security tests passed. Additional cases cover
unverified/suspended accounts, not-ready runs, archived writes and foreign record IDs.
One test fixture initially used an invalid run status (`failed`); corrected it to the
actual `initialization_failed` vocabulary, without weakening its expected denial.
The platform overview non-disclosure test also failed before its purpose filter was added.

Complete backend run: **1037 passed, 7 skipped in 121.77 seconds**. The skips are the
existing retired server-rendered UI checks. Final API/foreign-record and platform-overview
changes were then verified together: **32 passed in 1.34 seconds**. Lint, spec policy and
diff whitespace checks passed. No deployment, commit or public activation.

Review: authorization is attached to the entire tenant router (new routes default to
denied for sandboxes); production admission is deferred only for tenant routes and
rechecked there. The development business-mode behavior remains unchanged. No new
execution permission is granted. The all-entrypoint drift audit, scoped execution,
run lifecycle endpoints, seed, lesson, chat and UI remain open in tasks.md.

### Causal recorder prerequisites (2026-09-06)

T007/T008 implementation threads the confirmed proposal ID through the seven V1 handlers
and their shared services. Master-data batches, order Source/Document/Commitment records,
movements and reservation release retain their existing tool outputs. Manual document
events include their actual line IDs and source link. A newly stored source version from
a confirmed action emits `source_record.stored`; duplicate source reuse does not claim
another creation. No mirror Facts or operational schema fields were added.

Shipment events co-commit with actual consumption, active remainders and newly fulfilled
Commitments. Their `causation_id` names the Movement event; `action_id` identifies the
confirmed proposal. Partial consumption records both original and consumed quantities,
and remainder creation is explicitly labelled automatic. Correction internals retain
their dedicated event path; returned goods do not duplicate an already fulfilled transition.

Failing-first evidence: missing opening-stock/release attribution failed two tests; then
three master-data handlers and manual order attribution failed four more. The resulting
eight recorder tests verify IDs, partial/final quantities, repeated confirmation without
duplicate effects, foreign action rejection and rollback of records plus automatic events.
The original inventory/identity regression suite remained green (15 tests with the first
two recorder tests). Expanded recorder suite: 8 passed in 0.51 seconds.

The first complete run exposed 27 catalog-dependent failures: the three newly emitted
types were not registered. Registered them in business_event_catalog.yaml, updated command
event guidance and exact event-count assertions (39 to 42), preserving strict drift checks.
Focused catalog/recorder rerun: 38 passed. Final complete rerun evidence follows below.
No sandbox execution permission, run initialization, UI or deployment is claimed here.

Final full backend rerun: **1048 passed, 7 skipped in 189.47 seconds**. The seven
skips remain the existing retired server-rendered UI checks. Lint, spec policy and
diff whitespace checks passed. T007/T008 are complete; T005/T006 still retain the
entrypoint-audit/scoped-permission work and no user-facing execution is enabled.
Review confirmed unchanged quantities and tool outputs, same-tenant action lookup,
transactional automatic events, no duplicate fulfilment event on returns, and separate
correction evidence. No commit, PR, deployment or migration against production was made.

### Owner-private initialization (2026-09-06)

Implemented the internal start service and fixed trading-v1 reference catalog. Start requires
an enabled feature flag, explicit confirmation and a currently verified active/pending account.
It creates a fresh sandbox rather than accepting a tenant target. The owner row serializes
request-key lookup, capacity reservation and initialization. A durable empty run survives an
interruption; the second transaction atomically writes eight references, their events, the ID
map and ready status. All nested master-data calls use `_commit=False`.

Seed permission is internal and bound to owner, run, tenant, Session and transaction. It takes
the owner lock, rejects partial commits and permits only reference setup/event operations.
Business-only services remain denied, including when a buggy setup call targets a production
tenant. Normal core operations outside this scope retain the existing purpose policy.
No HTTP/UI/CLI/MCP start endpoint or lesson execution has been exposed.

Failing-first evidence: ten lifecycle cases initially failed because the service was absent.
The initial lifecycle/security implementation passed 406 tests. An adversarial internal commit
then demonstrated a partially retained Party; the before-commit guard now prevents that and the
whole preset rolls back. Separate-connection concurrent starts (same and different keys) pass.
Additional cases cover metadata-commit interruption/retry, archived replay, request-key bounds,
quota exhaustion and retries at capacity. Expanded run suite: 35 passed in 3.23 seconds.
An explicit wrong-production-tenant case failed before the seed-context business-operation ban.

The new account-scoped start service is an explicit isolated boundary in the catalog, not
global-admin access. Its required reason and exact registry counts were updated (7 families,
276 operations). Intermediate catalog failures were declaration/count mismatches, not waived
checks. The next full backend run is the release-evidence checkpoint for this internal slice.
Default start flag remains off; run limits are 5 new runs per UTC day and 20 retained runs,
with failed runs counted and same-key retries consuming no additional slot.

Final full backend rerun: **1069 passed, 7 skipped in 139.74 seconds**. The skips
are unchanged retired server-rendered UI checks. The preceding complete run had one
remaining legacy operation-total assertion (275 rather than 276); it is corrected,
and all strict declaration/coverage checks remain enabled. Lint, spec policy and diff
whitespace checks passed. T009/T010 are complete for internal initialization only.
T005/T006 remain open for the full entrypoint audit and scoped lesson execution;
HTTP/CLI/MCP account-aware entry, user-facing controls, restart and lessons remain pending.
Review: no production tenant conversion, no source fabrication, no initial stock,
no per-record commits, no quota consumed by replay, no archived reseed and no new
dependency or schema expansion. No commit, PR, deployment or production migration.

### Authenticated entry API checkpoint (2026-09-06)

Implemented the T011/T012 HTTP slice: owner-only bounded run listing, run setup detail and
confirmed start, all through shared services. A real session is mandatory even with local auth
disabled. Pending-production users enter only this lane; production admission is unchanged.
The dependency rechecks account verification/status, and reads require current owner membership.
Unknown and foreign runs have identical not-found responses, including for platform administrators.

Not-ready runs expose no partial reference map or inspectable tenant ID. Run detail includes the
original request key so setup can resume explicitly after reload. Start rejects supplied actor/
tenant IDs, truthy string confirmations and unknown versions. Quota errors include remaining
capacity and the next UTC-day reset; disabled entry and exhausted quotas do not block history.
Shared run reads are explicitly classified in the isolation catalog (8 families, 278 operations).
Chat availability is false, not inferred from a production provider setting.

Failing-first evidence: 18 of the new HTTP cases failed on absent routes or pending-account
admission before implementation. The initial focused API/run/catalog suite passed 109 tests.
Expanded coverage includes revoked/expired sessions, removed memberships, bounded pages and
safe setup failure/retry after reading saved detail. Final focused rerun: **114 passed in
43.78 seconds**. Lint, spec policy and whitespace checks passed. Complete backend evidence
is recorded below when finished; no unchecked review criterion is marked passed by these tests.

Review: adapters never choose a tenant from input or write ORM records; the new account reader
is reused under the existing start lock. Authenticated reads remain available when entry is off.
No new schema, dependency, lesson mutation, provider call, UI, public link or deployment.
T012 remains partial for account-aware tool/CLI access; T005/T006's drift audit and scoped lesson
policy, T013 UI and later lesson/chat/restart/release gates remain open.

Complete backend regression: **1093 passed, 7 skipped in 213.24 seconds**. All skips remain
the existing retired server-rendered UI checks; no Playground test was skipped. The final
saved-request-key/detail addition was also checked in the 114-test focused rerun above.
Lint, spec policy and diff whitespace checks are green. T011 is complete; T012 stays partial.
No frontend build/browser acceptance is claimed because no frontend implementation changed.
No commit, PR, deployment, public activation or production migration was performed.

### Private browser entry checkpoint (2026-09-06)

Implemented the T013 internal entry/reference slice at `/playground` and owned run URLs.
The account gate admits active/pending users to this separate workspace without mounting
ProductApp, querying bootstrap or reading the production tenant preference. Login, signup
and verification preserve only an allowlisted local Playground destination. Existing
invitation precedence is retained. No public Site/Docs discovery link was added.

Entry uses the existing PageHeader renderer and Tailwind primitives. It provides sandbox
identity, saved-run pagination, explicit inline review/confirmation, setup/loading/error/
archive states and actual run-local reference reads. No initial-stock constant is displayed
as current Reality. Business labels/IDs retain original-content localization protection.
All entry copy and statuses use en/de/nl/es; Playground is a documented stable product name.
Mobile places the selected run before saved history. Lesson/chat controls remain unavailable.

Failing-first evidence: all four initial UI/routing contracts failed on absent components.
The localization audit initially identified missing new copy; translations and dynamic status
coverage are now complete. Browser recovery testing found that a lost POST response left
the review open. The UI now returns to a new explicit review while retaining the original
request key across reload, including retries at exhausted creation capacity. A later signup
test used an exact password label that omitted existing help text; corrected its accessible
selector without changing the signup form or weakening the destination assertion.

`make web-build` passed: formatting, **86 frontend contracts**, **1063/1063 copy entries**
covered in each of en/de/nl/es, TypeScript and Vite production build. Vite retains its
non-blocking large-chunk warning. Lint, spec policy and diff whitespace checks passed.

The Browser plugin reported no connected browser after its prescribed discovery check.
Used the installed isolated headless Chromium instead, with a fresh context and synthetic
HTTP fixtures only; no real account, production session or external provider was used.
`scripts/playground-browser.mjs` passed **12 cases**: four languages at 390/1280px (review/
keyboard confirmation, focus return, ready references, reload without mutation, archived and
disabled-entry reads, no production API requests), two failure/lost-response recovery cases,
and pending-account login plus signup/verification deep-link return. Screenshots were written
to `/private/tmp/reality-playground-qa`; German desktop/mobile images were inspected, then
mobile content order and the untranslated Ready label were corrected and reverified.
This is UI-fixture evidence, not a substitute for the PostgreSQL ownership tests, real integrated
acceptance, full lesson checks or the five-person learning evaluation. Those remain pending.

The complete backend rerun result follows below when available. No release checklist was changed.
T012's remaining adapters and T005/T006's full audit/scoped lesson execution are still open;
this internal entry is not public release approval or completion of the learning Playground.

Final verification: **1093 backend tests passed, 7 unchanged retired-UI skips, 457.71 seconds**.
No new backend failure or skipped Playground check. After aligning mobile DOM reading order
with visual content order, all **86 frontend contracts**, four language audits, production
build and all **12 browser cases** passed again. Final desktop/mobile screenshots were reviewed.
The local Vite server and isolated browser were stopped; screenshots remain in the temporary
QA directory. T013 is complete for the internal entry only. The 14 reviewer-owned markers,
full integrated/human acceptance and public release gates remain unchanged. No commit, PR,
deployment, public activation or production migration was performed.

### Pinned run serialization checkpoint (2026-09-06)

Added the internal `_mutation_session` prerequisite for T014/T015. It uses a dedicated
PostgreSQL connection and nonblocking, namespaced advisory lock bound to the operation Session.
The connection remains pinned across ordinary service commits/rollbacks. Ownership is rechecked
after acquisition, unknown/foreign/unavailable runs fail closed, and the Session cannot be
reused after exit. This grants no core/proposal mutation permission and has no adapter yet.

Failing-first proof: the first new lock test failed on the absent helper. Failure injection
later found that SQLAlchemy invalidation of a pool-detached connection drops its driver
reference without closing it; a lost acquisition reply could leave the lock held. The dedicated
connection now retains and explicitly closes the physical driver in final cleanup. Lost lock
acquisition/release replies, application/SQL failures and invalidation are covered. One test
fixture was also corrected to set the required archived_at when archiving its test run.

All **26 step tests passed**, including **18 new locking checks**, on actual temporary
PostgreSQL databases with independent connections and real commits. Coverage also includes
continued reads, independent run locks, rejected generic mutations, account/membership/archive/
flag denial, post-lock revocation, rollback of uncommitted metadata and closed-session reuse.
The full backend regression is being run separately; its final result is recorded below.
T014/T015 remain partial: preparation, exact confirmation, stale previews, quota enforcement,
execution policy and reconciliation/receipts are not yet implemented. No UI, schema, public
entry, deployment or release-checklist change is included in this increment.

Final verification: **1111 backend tests passed, 7 unchanged retired-UI skips, 129.70 seconds**.
`make lint`, `make spec-check` and `git diff --check` passed. The existing frontend was not
changed in this increment; no new browser acceptance is claimed. Final review confirmed that
the lock helper has no public caller and does not widen the business-only operation policy.
No extension hooks are configured. Reviewer markers and the remaining task gates are unchanged.

### Atomic opening-stock proposal checkpoint (2026-09-06)

Added internal `prepare_step` for movement_create/opening_stock only. It resolves the verified
owner's run under the pinned lock, validates bounded typed inputs and owned active untracked
stock references, and calls the common proposal factory with `_commit=False`. One proposal and
one step commit atomically. The temporary capability is restricted to the exact Session,
transaction, tenant, tool and arguments, forbids intermediate commits, and cannot grant core,
execution or business-tenant access. Generic confirmation remains denied.

The preview identifies actual item/location names, IDs and unit, the resolved timestamp and
which default was supplied. Normalized requested intent is separate from resolved tool input;
same-key replay preserves identity and defaults, while changed requests conflict. Before any
future execution replaces proposal.output, claim metadata must retain that original request
identity. Missing identity fails closed. No execution/receipt engine is added by this slice.

Preparing a step creates no Movement, Fact, Commitment, Reservation, Document, SourceRecord or
additional BusinessEvent. Pending before/receipt observations stay null. An unresolved executing
proposal blocks new preparation. The applied-step preparation cap defaults to 50 with
REALITY_PLAYGROUND_STEP_LIMIT; checking it again at execution remains mandatory future work.
The tenant-isolation catalogue now registers 279 operations in nine families.

Failing-first evidence: opening preparation failed on the absent service. The initial focused
run passed **483 tests** (steps, security, runs and catalogue). Expanded preparation/scope tests
then passed **48 tests** in the step file; one additional production-target capability test and
explicit default-label assertions were added for final verification. Cases cover rollback when
step persistence fails, original timestamps, changed keys, foreign owner and real production
item IDs, precision/NaN/timezone/extra-field rejection, busy/unresolved/quota state and capability
misuse across arguments, tools, sessions, transactions and direct core writes.

No adapter, confirmation/rejection flow, further lesson action, UI, provider or schema change.
T005/T006 and T014/T015 remain partial. This is not completion of the guided learning workspace.
Reviewer/release markers are unchanged. Full regression and final gate results follow below.

Final verification: **1134 backend tests passed, 7 unchanged retired-UI skips, 150.84 seconds**.
The final focused run passed **49 step tests**, including the production-target and default-label
assertions. `make lint`, `make spec-check` and `git diff --check` passed. Review confirmed no
direct domain write, adapter exposure or alternate execution engine. The new proposal-factory
commit option defaults to existing behavior; sandbox execution remains denied. No extension
hooks are configured. No commit, PR, deployment or public activation was performed.

### Confirmed opening-stock checkpoint (2026-09-06)

Added internal confirm_step/reject_step/read_step for opening_stock only. Confirmation binds
the displayed revision and rechecks relevant reference/physical-stock state under the pinned
connection lock. Before-state and original request identity commit before calling the existing
approve_and_execute_proposal CAS/executor. Rejection uses the ordinary proposal lifecycle;
both decisions attribute the verified human owner. The private HTTP adapter is covered below;
there is no browser UI yet.

The narrow decision capability is bound to the Session, live connection, owned run, existing
step and proposal. It permits one exact Movement and its movement.recorded event only after
the ordinary executor claims executing. Shared services reject altered quantity/time/identity,
extra source/tracking fields, unrelated core writes/events and a second Movement in the same
scope. Generic tool/HTTP/CLI/MCP mutation paths remain denied. Production behavior is unchanged.

The shared proposal_execution_status reader verifies a unique correlated opening event and
its exact Movement instead of inferring success from status or sequence ranges. An interruption
before/after the domain commit remains executing/unknown or effect-observed-but-unsettled,
never automatically reexecuted or marked settled. New mutations wait; owner reads remain open.
The executed action's explanatory observation can fail/recover independently of execution.
Before/after values come from stock_at; write-once snapshots remain historical after subsequent
actions and in archived runs. Full Facts/Exceptions/current-picture reporting is still pending.

Failing-first confirmation tests detected the absent service; initial integration then exposed
an incorrect read-dispatcher import, corrected to the existing run_read_tool. **54 step tests**
passed for the initial decision slice. Expanded steps/security/application-tool/catalogue checks
passed **487 tests**. Tightened exact-execution and independent-thread double-confirmation
checks then passed **68 step tests**. Final tests add historical/archived observations,
execution-time applied quota, required event attribution and mismatched replay revision.
The catalogue registers 282 operations in nine boundary/read/write families.

T005/T006 and T014/T015 remain partial: the full entrypoint audit, other lesson actions, explicit
settlement of interrupted proposals, complete read models and all lesson adapters remain open.
No schema, frontend, public discovery, provider configuration or release-checklist change.
Full regression and final review results follow below. Reviewer markers remain unchanged.

The final catalogue-evidence refinement initially reused one test ID in two families; the
focused run correctly rejected both catalogue checks. Split read ownership into its own
executable test/evidence ID, retained decision coverage, and reran the complete suite.
Final verification: **1156 backend tests passed, 7 unchanged retired-UI skips, 199.81 seconds**.
This includes 71 step tests, final revision binding, historical/archive reads, capacity,
evidence attribution and the corrected catalogue. Lint, spec policy and diff whitespace checks
are green. Review confirmed only the owned opening action is permitted by the internal scope;
generic mutations and all other lesson tools remain denied. No extension hooks are configured.
No frontend/build acceptance is claimed for this backend-only increment. No commit, PR,
deployment, public activation or production migration was performed.

### Private step HTTP checkpoint (2026-09-06)

Added authenticated owner-scoped HTTP routes for step prepare, detail, confirm and reject.
Pydantic payloads reject unknown fields and require strict booleans for decisions. Routes resolve
the run from the signed-in account and pass the request-scoped database connection to the same
service methods; they never accept a tenant ID. Responses preserve proposal status, preview
revision, correlated Movement evidence, historical receipt and verification state. HTTP replay
returns the original step, confirmation creates one Movement, and rejection remains domain-no-op.
Foreign users receive the same not-found boundary as other run records; unconfirmed rejection
is denied. No production routes, generic tools, CLI/MCP/chat adapters or UI controls are opened.

Focused HTTP regression: **51 tests passed** after isolating seeded run-local references in the
new cases. The initial adapter run exposed that the test fixture's synthetic active run had no
references; this was corrected without changing the normal fixture's zero-data read assertions.
The adapter now reuses the request session for its pinned lock and mutation, so the fixture's
outer transaction remains intact and the final run completed without SQLAlchemy warnings.

### Opening-stock browser checkpoint (2026-09-06)

The private Playground page now exposes the first guided action: choose a prepared item and
location, enter a quantity, request a server preview for `movement_create/opening_stock`, then
explicitly confirm or reject the returned step. The browser only submits typed step commands and
renders the server preview/status; it does not calculate stock or write Reality records itself.
The API client covers detail, confirmation and rejection, and the browser contract test asserts
the explicit confirmation boundary. Web verification: **87 contract/i18n tests passed**, Prettier
and the production TypeScript/Vite build passed. The action is still intentionally limited to the
private sandbox and one lesson action; step history, complete live reads and the remaining lesson
actions are not yet implemented.

The run detail now also returns the ordered historical step previews. The browser restores the
latest step after reload instead of losing the visible recorder state. This remains a bounded
read model: verification receipts and current Reality projections still come from their dedicated
step/read services and are not recomputed in the client.

### Server receipt checkpoint (2026-09-06)

Reloading a run now fetches the latest step detail through the existing read endpoint and renders
its server-produced Reality receipt when available: before/after physical state, recorded Movement
ID and correlated event ID. The browser remains presentation-only; it does not derive a balance or
invent Fact, Exception or View rows. The receipt is deliberately honest when observation is still
unavailable after an execution boundary.

### Current Reality read checkpoint (2026-09-06)

The private run now exposes a bounded `/reality` read through the same application read tools:
inventory projection rows, current operational exceptions and the last 50 journal events with
their sequence and payload. The browser renders these three server-owned sections as Current
Reality; it does not calculate physical/available values or synthesize exceptions. The route is
owner-scoped to the playground run and returns no production tenant data.

### HTTP confirmation policy fix (2026-09-06)

The first browser confirmation exposed an adapter-only policy mismatch: a request Session was
bound to an Engine while its active operation used the pinned Connection, so the decision scope
correctly—but incorrectly for this adapter—returned 403. The policy now validates the Session's
active connection, preserving the same run/proposal/intent identity checks. Focused service/API
regression passed **122 tests**; the local API was rebuilt with the fix.
