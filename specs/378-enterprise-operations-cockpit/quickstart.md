# Validation: enterprise operations cockpit

**Language**: English
**Date**: 2026-10-06
**Status**: The approved optional first increment is implemented. Functional, frontend and ordinary backend/browser proofs are green with explicit corrections/reruns recorded below. The full declared backend/JSON enterprise workload now passes. Aggregate rollout acceptance, enterprise DOM timing and pilot readiness remain separate. The separate pre-pilot eight-hour real-time soak is unrun. No pending criterion is represented as passing.

## Authorization and environment

The owner approved the optional cockpit, three input tables, completion-slot-v1, all-day observation and named Agent/access panel; see [review](review.md). All persistence proofs use isolated temporary PostgreSQL databases. No live company was seeded, migrated, adopted or enabled. Home remains the default. The hosted enterprise reference is unchanged.

Python 3.12.4, macOS 27.2 arm64, eight CPUs and 24 GiB memory; the isolated database is PostgreSQL 17.10 arm64 Alpine, shared_buffers 128 MB, work_mem 4 MB, max_connections 100 and max_parallel_workers_per_gather 2. Playwright uses the installed Chromium headless shell. Existing scheduling/worker services run only in each disposable real-browser fixture.

Controlled regression retries additionally use an independently owned disposable
PostgreSQL container, with `max_locks_per_transaction=1024` matching CI rather than
the pre-existing local server's 64. Its version/buffer/work-memory/parallel settings
match those above. Docker has eight CPUs and 8,218,251,264 bytes of VM memory;
the container has no additional CPU/memory limit and 64 MiB shared memory. Database
isolation does not isolate host CPU contention. No existing server, company or
other operator process was reconfigured or stopped.

## Executed functional proof

| Proof | Latest executed result | Meaning |
| --- | --- | --- |
| Canonical shipping/readiness/revisions/delivery policy/cases/retries/snapshots | 91 passed in 51.39 s | Exact quantities, blockers, source meaning, controls and current access remain canonical |
| Narrow stored-value scalar/batch parity | 2 passed in 3.90 s | Standard and prepayment readiness retain exact representation and hold evidence |
| Final shipping/source-priority/story/HTTP-tool parity | 44 passed in 27.78 s | Daily plan and collection confirmation sources remain visible before the order-source preview |
| Earlier input/domain/migration foundations | 71 passed in 62.89 s | Closed input validation, original Sources/versioning, reviewed acceptance/replay, tenant FKs, DST and migration safeguards |
| Exact large ID membership/source/case regression | 84 passed in 32.47 s | Empty/nullable/unusual opaque IDs and 70,000-ID cohorts remain exact with one safe bound value |
| Full frontend gate | 478 passed, zero failed; final nullable-count guard build 7.00 s | Formatting, TypeScript, production bundle and all 2,964 used strings in four languages pass |
| Specification policy, Ruff and business annotation audit | Passed | 666 described functions, 115 described approved tests and zero unresolved roots |
| Generated executable vocabulary | Generation passed | Six new reads, reviewed planning proposals, German ERP labels and generated references are retained |

These focused runs overlap and are not added together as a full-suite count. The full backend gate excludes only the separately measured enterprise benchmark; both parts must pass before complete runtime acceptance.

## Independent populated shipping oracle

[Shipping contract](contracts/shipping.md) and `test_shipping_performance_story.py` establish a fixed-time two-site oracle independently of the evaluator: one confirmed company completion, three forecast company completions, four due company orders; split-site C is counted once at company level. Venlo has three due/three forecast orders; Leipzig has two due/one forecast order. Requested extra collection and repeated reports add no confirmed baseline capacity or physical contents.

Domain/service variants prove partial quantities, event supersession, contradictory/missing/future handover time, cancelled/revised commitments, accepted versus unresolved Sources, company/site calendars, DST folds, original-period completion pace, adjacent-window boundary accounting and forecast day-end limits. Missing plans or capacity remain unknown; a known cancelled cohort may correctly be zero. Unplanned open work has no invented dispatch site/deadline. More than 200 supporting orders and 205 adopted cases retain full totals across pages.

Full fingerprint inputs are calculated before a disclosed 50-record evidence preview. All planning-source identities remain in the basis; their metadata is prioritized across sites ahead of sampled order sources. Full work, quantity revisions, source checks, readiness and physical coverage still determine every total and curve. No forecast or operational Document status is stored.

## Browser and real database-to-browser proof

The fixture component and full Shell proofs cover populated three-series shipping, two-site counts, exact blocker detail and evidence links, unknown/stale states, reviewed takeover and handback, retained reason/revision/request key, human-owned discovery, explicit return context, default Home, optional capability, on-demand chat and company reset. Existing operational-case browser behavior passed separately. Final review identified that the initial three-action proof reached case discovery, while opening takeover review required a fourth click. The strengthened full Shell proof failed against that collapsed disclosure, then passed after selected orders entered from the cockpit open their existing case disclosure. Risk → order → takeover review now uses three navigational actions; ordinary entry remains collapsed. The final real-browser journey passes this corrected SC-003 path. Document, commitment and original Source links in specialist case detail and the full Inspector preserve the same validated company/filter origin; the strengthened integrated proof also passes all three evidence links.

The initial isolated API/PostgreSQL/browser journey passed **1 test in 32.72 s**, with an actual committed hold visible after **3,422 ms**. Its final rerun after the three-action correction also passes, with the actual committed hold visible after **1,700 ms**. It creates three orders through canonical services, accepts current-day planning through the existing reviewed proposal service, records physical contents/handover, registers a named manual access and adopts new cases explicitly. It navigates risk → exact order → takeover review in three actions, confirms takeover through the real UI, verifies the stored exact reason and discovers human ownership. It uses neither HTTP response fixtures nor an accelerated clock.

Paths:

- `packages/reality-core/tests/browser/unified_operations_cockpit.py`
- `apps/web/scripts/operations-cockpit-live-browser.mjs`
- CI `live-browser` matrix journey `operations-cockpit`
- Final temporary proof directory: `/private/var/folders/y5/px944wdj1tl6g6w9lc54gbwh0000gn/T/pytest-of-benediktsauter/pytest-48/test_live_cockpit_shows_commit0/operations-cockpit/`

The first live fixture declared exactly two slots from its setup instant. Real setup time correctly made the final slot miss the cut-off. The fixture now states three slots, preserving the approved original-period pace; the calculation was not changed to hide that delay.

Final presentation review also found two case-responsibility totals bypassing the
existing display-number formatter. The strengthened component proof first failed
on a valid paged fixture containing 12,345 automated and 3,456 human-owned cases,
then passed with an independently chosen German display locale after both totals
reuse `formatNumber`. No count, case control or backend calculation changed.
Logs: `/private/tmp/reality-378-count-format-before.log` and
`/private/tmp/reality-378-count-format-after.log`. TypeScript caught the first
formatting guard's omission of the existing `counts=null` state for unadopted case
coordination. The corrected guard preserves unknown responsibility as an em dash;
the strengthened component proof also exercises this genuine missing-coverage
state. Final component proof passes in
`/private/tmp/reality-378-count-format-final-browser.log`; the complete web gate
passes in `/private/tmp/reality-378-web-build-final-count-guards.log`.

The final full Shell rerun exposed a fixture assertion that waited for a transient
hidden chat while a company without cockpit capability falls back to Home. Home
already shows its general chat on desktop, as required by the unchanged-entry
contract. The strengthened proof waits for the final company/Home URL, checks the
new company's empty draft, returns to the first company's cockpit and verifies
closed-on-demand chat with no restored old draft. No product chat behavior or
timeout changed. It passes in 6.77 s in
`/private/tmp/reality-378-company-chat-shell-final.log`; its CI estimate is seven
seconds. The earlier failing assertion is retained in
`/private/tmp/reality-378-count-guards-shell.log`.

Populated 1440/390 screenshots and all English/German/Dutch/Spanish light/dark mobile variants have been captured without page overflow. Temporary files `/private/tmp/reality-378-cockpit-1440.png`, `/private/tmp/reality-378-cockpit-390-populated.png` and `/private/tmp/reality-378-cockpit-{en,de,nl,es}-{light,dark}-390.png` are acceptance images, not deployed company data. `/private/tmp/reality-378-cockpit-390.png` records the unavailable-state variant. Final complete-browser reruns regenerate applicable images.

## All-day observation

Nine deterministic lifecycle tests prove the five-second start cadence, eight-second read timeout, capped 5/10/20/30-second failure backoff, non-overlap, cancellation, hidden/resume, stale retention, old-response rejection and access-loss clearing. A controlled eight-hour lifecycle performs 5,761 reads.

The final fixture-backed controlled browser session also passed eight virtual hours on the frozen final navigation/UI: 5,786 shipping reads and 5,791 reads each for activity, access and register (all below 5,800 per endpoint), at most 61 graph buckets and 50 recent events, quiet windows, outage/recovery, hidden-tab resume, stable case inspection and unconfirmed takeover reason. Today rolls over in company time; a pinned date and an opened supporting-order business day remain fixed. Company switching and revoked access clear prior observations/reviews. Pausing activity following is presentation only and creates no business mutation. The final log is `/private/tmp/reality-378-controlled-session-final.log`.

This controlled proof is distinct from the real-time eight-hour soak. That soak remains a separate pre-pilot gate and has not run. Do not mark it complete or enable a pilot on the strength of virtual time.

Agent proofs cover qualified manual/OAuth identities, repeated names, complete matching totals before keyset paging, effective access, never-used/revoked records, exact manual interaction attribution, owner-only disclosure and secret redaction. An OAuth name or last use is not a current runtime observation. Ordinary members retain other cockpit panels and receive a restricted access panel.

## Enterprise workload: still pending

`tests/test_operations_cockpit_performance.py` retains 10,000 planned daily orders, 100,000 historical fulfilled orders/cases, 500,000 shipment observations, two sites and ten observers. Its explicit distribution is one item, one-unit partial-allowed EUR orders, 1,000 completed and 9,000 ready active orders, no prepayment. This does not establish throughput for every business mix or from annual revenue alone.

The test uses existing pool settings of 80 connections plus five overflow, allowing caller authority and independent snapshot connections for ten browsers' four simultaneous reads. Deployment defaults are unchanged. It records a first application read after fixture ANALYZE; PostgreSQL OS/shared buffers are not flushed. Twenty simultaneous opening/site-filter samples, exact company/site/case totals, serialized payload bytes, query counts and committed hold visibility are measured without profiling overhead.

The sustained stage schedules twelve canonical new orders concurrently with twelve forty-read batches at five-second intervals. Each snapshot must match exactly the prior or current committed count; every next cycle includes the previous commit. The last committed order is independently verified. The complete cycle includes both writer and all observers, and records write duration, read p95, queries, payload size and commit-to-verified-observation time. Required limits remain three-second p95, five-second cadence, ten-second committed-change visibility and 250 queries per observation.

Important measured history:

- Initial complete profile: 25,849,349 response bytes, 16.984 s cold and 110.715 s warm p95 — red.
- Full SQL case aggregation and bounded evidence transport: 370,800 response bytes and 8.162 s cold; timing still red.
- Safe single-evaluation PostgreSQL array membership and exact in-flight observation joining reached 2.991 s opening/site p95, then failed sustained cycle ten at 5.919 s; this was not a complete performance pass.
- Narrow read-only canonical inputs and same-call case-term reuse reduce the cold query count to 154, but the latest complete opening measurement remained red: 2.661 s cold, 4.713 s warm p95 and 6.603 s committed-hold observation. The enterprise gate remains unresolved and must be measured again after the full regression workload stops. No threshold or cohort is reduced.
- Subsequent isolated PostgreSQL 17.10 container run (no other owned heavy checks) also remains red: 5.268 s cold, 7.831 s opening/site-change p95 and 6.456 s committed-hold observation. Complete quantities and case totals pass; the sustained stage is not reached because the unchanged three-second opening gate fails. The cold read uses 154 queries and a 370,870-byte response. The Docker VM has eight CPUs and approximately 8.22 GB RAM; PostgreSQL uses 128 MB shared buffers, 4 MB work memory and two parallel workers per gather. Hardware/distribution and all twenty samples are recorded in `/private/tmp/reality-378-performance-isolated-final.log` (one failed in 294.17 s). Profiling and targeted optimization continue; this measurement supersedes the shared-server timing for acceptance.

Source/quantity/readiness/state meanings stay canonical. Exact in-flight sharing never keeps a completed result; every observer independently checks current access before/after its detached JSON response. Normal sessions preserve pending identity-map values and existing Decimal representation. Caller-owned connections retain the original source/watermark drift guards.

## Complete gates in progress

- Complete backend: `pytest -n 2 --dist worksteal --ignore=tests/test_operations_cockpit_performance.py --tb=short`, 6,673 collected. The first run was deliberately interrupted after 305 passes for the final planning-source preview refinement; its partial result is not completion. The restarted run completed with 6,644 passed, 11 failed, 11 skipped and seven setup errors in 6,709.61 s. Six failures were concrete integration gaps (coded readiness refusal, explicit analytics deferral, later migration index inventory, generated action fixture, structured read schemas and diagnostic reader boundary). Five failures and seven setup errors were demo initializer handler deadlines. This red run is not a complete acceptance pass; controlled corrections/reruns are recorded below.
- Complete fixture browser suite: all 91 registered scripts executed, 88 passed initially in 3,633 s (including planned parent pauses). Settings and Analytics fixtures did not recognize the new default-off capability GET; the shared exact background-read fixture corrects that omission. The populated component initially selected a hidden site option instead of its visible row header. All three corrected scripts pass their targeted reruns; final component/source-return/three-action proofs pass. The controlled final live session passes separately. Paused/inflated durations are not used to revise normal CI estimates.
- Final real-backend browser regressions: all nine journeys executed, five pass (business journey, CSV import, history table, cockpit and finance rollout), four fail (payment projection refresh, bulk intake execution state, Engine Room change detail and demo calculation completion), 1,800.66 s including controlled parent pauses. These failures require targeted controlled reruns and diagnosis; they are not waived as load. The corrected real cockpit journey passes with 1,700 ms committed-change visibility.
- Controlled own-container rerun: payment refresh, bulk intake, Engine Room and the complete business journey pass; the latter additionally proves all 18 register title counts and page introductions as in CI. Result: four passed, one failed in 1,118.41 s. Demo setup now proves its calculation/ready phases, but no initial reviewable source appears within its unchanged 60-second limit. The initializer's recorded worker duration is 105.602 s. Repeat this remaining journey alone after the complete backend run, then diagnose any remaining failure; neither isolation nor timing is a blanket waiver. Log: `/private/tmp/reality-378-real-browser-isolated.log` and `pytest-49` artifacts.
- Final isolated enterprise measurement and diff/FR/DR/SC/reference review: pending.
- `make docs-catalog-check`: passed against an isolated temporary Git index/object baseline containing the final generated files. The real index remains untouched.

Earlier partial four-worker backend execution found an existing demo initializer's handler deadline (3,252 passed/four skipped); its isolated serial rerun passed in 41.86 s. That does not replace the complete final gate or waive future failures.

## Migration and rollback

Original proof used the predecessor head `0144_operational_cases`; PR integration rebases `packages/reality-core/migrations/versions/0146_shipping_plan_inputs.py` onto `0145_default_operational_cases` and reruns the combined chain. Isolated upgrade/empty downgrade, tenant composite FKs and retained-evidence downgrade refusal pass. Only three approved input tables are added. No startup path migrates, no history is backfilled and no live-company table was changed. Presentation rollback disables the capability while preserving planning inputs, Sources and case responsibility. Dropping retained planning evidence is not rollback.

The archived reference remains byte-exact: 70,071 bytes, SHA-256 `c5bee6395b7a63f00b2a22c9d26ac3bb479b2ceea8290ae2b8789a8ca39eb03e`. [Reference metadata](reference/README.md) and [migration map](migration-map.md) protect C01–C25, including individually deferred commercial KPIs, SLA pages and additional case families. The production Site and current company entry are unchanged.

## Reproduction

Use the repository runtimes and isolated PostgreSQL setup from `docs/TEST_STRATEGY.md`:

```bash
cd packages/reality-core
../../.venv/bin/pytest tests/test_shipping_performance_domain.py tests/test_shipping_plan_inputs.py tests/test_shipping_plan_migration.py tests/test_shipping_performance.py tests/test_shipping_performance_story.py tests/test_operations_cockpit.py tests/test_operations_cockpit_adapters.py tests/test_operations_cockpit_snapshots.py
../../.venv/bin/pytest -n 2 --dist worksteal --ignore=tests/test_operations_cockpit_performance.py
../../.venv/bin/pytest tests/test_operations_cockpit_performance.py -s
../../.venv/bin/pytest tests/browser/unified_operations_cockpit.py
```

From root run `make spec-check`, `make lint`, `make business-annotations-check`, `make web-build`, `make docs-generate` and `make docs-catalog-check`; from `apps/web` run the complete fixture browser runner with the installed Playwright module/executable. Inspect [tasks](tasks.md) and [review](review.md) for actual completion and remaining gates; no real-company pilot or default-route switch is authorized by these commands.

## Final integration and freshness corrections

The first targeted integration rerun passed 89 tests and skipped two in 114.64 s; its remaining MCP schema failure came from the schema imported before the correction. The subsequent frozen shared-boundary rerun passed 66 and skipped two in 96.63 s, including structured MCP schemas, existing Engine Room reads, the architecture boundary, full migration index coverage and canonical readiness. These overlapping counts are not a new full-suite count. Logs: `/private/tmp/reality-378-integration-corrections.log` and `/private/tmp/reality-378-shared-boundary-final.log`.

The case register now returns its own transient read-snapshot `observed_at`, including unknown/unadopted coverage. Its new PostgreSQL test first failed on the missing field, then passed without creating business events. Independent Agent and register panels display their own last successful observation timestamps and retain those times on failed refreshes; the new browser assertions first failed on the absent display and then passed. Full control attribution displays its date and explicit business-zone offset rather than a time-only historical label. Diagnostic and live activity clocks retain the user's independent display-zone preference and explicitly disclose the offset; business-day shipping and collection clocks keep their stated company/site zones. No timestamp becomes a new stored authority.

Manual-access attribution is now redacted exclusively by `services/interactions.py::latest_manual_actions`. The owner-only observation adapter consumes DTOs without importing or querying the telemetry model. An architecture test names this single diagnostic consumer and separately prohibits its direct model access; shipping and execution remain independent of telemetry. The first isolated architecture-test launch was prevented by sandbox networking, not counted as a failing semantic proof. The complete backend run had already demonstrated the original direct-access violation.

The action reference fixture was regenerated from executable catalogs; its frontend unit tests and action-directory browser proof pass with zero business writes. Two local browser launch attempts used incorrect address-variable names and failed before loading the product; the final documented `BASE_URL` run passes. Two interim controlled-session attempts were invalidated by development hot reloads while timestamps were still being edited; they are not used as final session acceptance. The final frozen display-zone component/Shell/session and web build are measured separately.

Serial initializer regressions and the final isolated enterprise workload remain pending. Required runtime deadlines, complete cohorts and performance thresholds are unchanged.

### Frozen final frontend result

`make web-build` passed all 478 frontend tests (267.74 s), all four languages at 2,964/2,964 audited strings, TypeScript and the production bundle (9.94 s). The existing large-bundle advisory remains; no build errors. Final populated component proof passes desktop/mobile, four languages/themes, timestamp retention and the independent Tokyo display-zone case. Final Shell proof passes serially after a concurrent local attempt exceeded its unchanged ten-second navigation wait. The action-directory proof passes with zero writes. These results retain failures/launch mistakes above rather than claiming a clean initial run. Logs: `/private/tmp/reality-378-web-build-frozen-display-zones.log`, `/private/tmp/reality-378-operations-cockpit-browser-frozen-display-zones.log`, `/private/tmp/reality-378-shell-display-zones-serial.log`, `/private/tmp/reality-378-action-discovery-browser-confirmed-url.log`.

The final frozen controlled eight-hour session passes bounded chart/event history, stable case inspection/reason, quiet time, outage/recovery, hidden/resume, business-day rollover, pinned dates, preserved supporting-order day, company clearing and revoked access. Every endpoint remains below 5,800 reads at the end of the eight-hour rate assertion; the receipt after subsequent pin/company/revocation checks records 5,794 shipping and 5,801 reads each for activity/access/register. Final extra interaction reads are not part of the eight-hour rate assertion. Log: `/private/tmp/reality-378-operations-cockpit-session-browser-frozen-display-zones.log`. The separate actual real-time soak remains unrun. Owned Vite test server is stopped and port 54378 is closed.

The canonical initializer still exceeded its unchanged handler limit during a concurrent local run. After all other owned heavy checks ended, the exact canonical test passed under cProfile: one passed in 41.87 s (47.62 s whole process). No runtime deadline, fixture quantity or business rule changed. This is diagnostic evidence, not a waiver for the other affected tests. The complete affected initializer scenarios are now rerun with only the normal two backend workers active in the disposable container.

### Controlled initializer regression result

All thirteen affected/canonical initializer scenarios pass with the normal two backend workers, no other owned heavy test workload, unchanged input quantities and unchanged 120-second job deadlines: **13 passed in 266.06 s**. This includes every one of the five initializer failures and seven setup errors from the complete backend run. No initializer or scheduling code changed. Log: `/private/tmp/reality-378-initializers-isolated-only.log`. Together with the six corrected integration failures and their targeted regressions, this resolves all recorded complete-backend failure identities; it is a complete original run plus explicit corrections/reruns, not a fabricated clean 6,673-test invocation. The separate enterprise benchmark and final real demo/browser journey remain pending.

### Final real-stack browser result

Both final real PostgreSQL/browser journeys pass, serially with the final code and unchanged deadlines: **2 passed in 237.62 s**. Actual demo setup shows data/calculation/ready, produces the first pending Source without automatic business approval, pauses the source with settled execution, preserves/downloads exact original payload bytes and confirms the actual reviewed intake. The final cockpit uses canonical populated two-site inputs, observes an actual HTTP-committed hold, reaches takeover review in three navigational actions and verifies the confirmed retained control/reason in the database and human-owned register. Log: `/private/tmp/reality-378-real-browser-isolated-final.log`; owned artifacts: `pytest-53/test_live_demo_company_setup_r0/company-setup-live` and `pytest-53/test_live_cockpit_shows_commit0/operations-cockpit`. All nine originally executed real-browser journey identities now have passing final or controlled rerun evidence. The separate enterprise measurement is now running alone.


### Read-path refinement and selected-day caption

Two diagnostic profiler runs remain red: 7.224 s cold / 17.643 s opening p95 / 14.227 s committed-hold observation (539.09 s total), then 10.721 s cold / 13.898 s p95 / 10.688 s committed-hold observation (597.33 s total). The second diagnostic additionally records read-only EXPLAIN plans for twelve slow reads, without storing parameters or payloads. These diagnostic runs do not supersede a standard acceptance run. Logs: `/private/tmp/reality-378-performance-isolated-profile.log`, `/private/tmp/reality-378-performance-query-plans.log`; summarized plans: `/private/tmp/reality-378-cold-query-plans.json`. Thresholds, cohorts and exact totals are unchanged; sustained acceptance remains unreached in these runs.

Clean snapshot reads now use original planning headers, source identities/version/action references and the exact reviewed proposal basis, without hydrating full Source payloads or unused proposal previews. Original payloads remain unchanged and inspectable. The new parity test's first attempt compared pending versus stored Decimal representations; after correcting the setup to the same stored values, it failed specifically on loading SourceRecord/ChangeProposal objects. The metadata refinement then passed 88 targeted tests in 149.93 s. Canonical statement selection, source/version guards and full fingerprint inputs are unchanged.

Original scoped order/commitment rows are then reused only within the same clean observation by canonical terms, readiness and delivery-policy readers. The complete-result/query-budget proof first showed three reads of each cohort, then passes with one of each. Ordinary sessions retain their original ORM behavior. A new foreign-input policy proof caught an unintended fallback from the real customer's ship-complete rule to the default; incomplete/foreign reusable customer metadata now falls back to the canonical tenant-scoped order read. No new business refusal, schema, cache or authority is introduced.

The first broad affected run produced 145 passed and two direct-reader parity failures in 185.17 s: directly batched narrow order rows lacked their original tenant column. The original tenant columns were added, both standard/prepayment readers and all three new regression scenarios passed (five passed in 9.78 s), and the complete final affected set passes with the normal two workers: **147 passed in 147.45 s**. This covers shipping inputs/observations/stories, snapshots/authority, readiness/prepayment, delivery rules/shipments/exceptions, revisions, stock blocks and movement corrections. Log: `/private/tmp/reality-378-cohort-reuse-final-regressions.log`. An earlier launch referenced a nonexistent test filename and ran no tests; it is not counted as acceptance.

Pinned-day metrics/site headers now say Due on selected day; Today keeps Due today. This restores FR-003 wording rather than calculating dates in the browser. The component test first failed on the old caption and then passed the pinned/Today transition plus the existing populated, source, control, four-language and responsive proof. The first build stopped on required formatting; after formatting, the final frontend gate passes **478 tests in 128.91 s**, all four languages at **2,965/2,965** strings, TypeScript and the production bundle (**9.44 s**, existing size advisory only). Logs: `/private/tmp/reality-378-selected-day-browser-final.log` and `/private/tmp/reality-378-selected-day-web-build-final.log`. Spec policy, lint and business annotations pass after the read refinement; the latter reports 667 described functions, 115 described tests and no missing approved descriptions. These are not new aggregate release or enterprise-performance claims.


After the final read refinement, the real API/browser cockpit journey passes again:
**one passed in 53.72 s**, with an actual committed hold visible in **1,983 ms**,
three navigational actions to takeover review, confirmed stored reason/control and
the human-owned register. Log: `/private/tmp/reality-378-real-browser-after-reuse.log`;
artifacts: `pytest-57/test_live_cockpit_shows_commit0/operations-cockpit`.
This small populated real-stack proof is not an enterprise-rendering measurement.
All owned frontend/ordinary backend/browser checks ended before the next standard
enterprise run, which has no profiling/EXPLAIN flag. The owned preview on port
54378 is stopped and the port is closed. Real-time soak remains unrun.

### Bounded canonical case explanation inputs

The standard enterprise run after shipping cohort reuse remained red:
5.337442 s cold, 5.204537 s opening/site-filter p95, 7.507750 s committed-hold
observation, at most 153 queries and 370,870 bytes. Full company totals were
10,000 due / 1,000 handed over / 10,000 forecast / zero risk; each site had
5,000 / 500 / 5,000 / zero. The committed hold produced exactly one risk and
9,999 forecast. Sustained acceptance was not reached. This standard run took
292.65 s; log `/private/tmp/reality-378-performance-after-cohort-reuse.log`.

The new stored canonical case-DTO/query-budget proof first failed specifically
on 184 reads for seven cases, with result parity already green. Bounded
read-only original-input batching then passed the same proof. Expanded coverage
adds a separate related return, completed order, source interpretation gap,
exact takeover actor/reason, obsolete proposal and 51 executing actions with
complete totals independent of the 50-item preview. Its first setup lacked
physical shipment evidence required by the canonical return service; actual
opening-stock/shipment services corrected the fixture, after which the expanded
proof passed in 3.36 s. The canonical source-gap function serves both scalar and
batched reads. A further scope refusal test initially used incorrect message
capitalization; it now checks the stable `case_not_found` code. Neither failure
waived a production guard or changed a refusal. Final affected suite and the
unchanged enterprise measurement remain to be recorded.

Final bounded case-input regression is green: **53 passed in 46.48 s**
(`/private/tmp/reality-378-case-input-complete-regressions.log`). Full scalar
versus snapshot DTO parity includes independent related returns, completed work,
source gaps, exact control attribution, obsolete proposals, complete executing
counts and company/limit fallback. The actual browser proof is also green:
**one passed in 33.59 s**, an HTTP-committed hold displayed in **4,029 ms**,
three navigational actions to takeover review, retained confirmed reason/control
and the stopped-case register. Log:
`/private/tmp/reality-378-real-browser-after-case-input.log`. This small
populated proof does not measure enterprise DOM rendering. Spec policy, lint,
annotations and whitespace checks pass. No caller-owned transaction, business
review/control mutation, schema or authority was changed. The unchanged
enterprise measurement and separate pre-pilot real-time soak remain pending.

### Final complete calculation / overview projection proof

The standard case-batched benchmark passes opening/site-filter p95 at
**2.437429 s**, first application read **3.269016 s**, at most 73 queries
and a 370,870-byte response. The committed hold observation is **2.993377 s**.
Its sustained phase now executes all **480 requests**, twelve concurrent canonical
commits and all five-second cycles (maximum **4.146074 s**). Complete old/new
snapshot parity and next-cycle visibility pass; the final new-order verification
is **4.478221 s** after commit. Continuous-read p95 remains red at **3.327774 s**
against the unchanged three-second threshold. The run fails only that final gate
after **204.47 s**; log `/private/tmp/reality-378-performance-after-case-input.log`.

The next refinement allocates full order-detail DTOs only for the overview's
exact already calculated deviations inside the clean snapshot. All work, full
source/physical/readiness basis, fingerprint, aggregates, cut-offs and curves
remain complete before this projection. Ordinary/caller-owned and supporting
reads retain all detail rows. Three stored healthy/held/source-gap proofs first
failed on the absent projection; they now pass with complete observation/terms
and exact filtered-detail parity. A 63-order proof initially lacked confirmed
capacity and then reservations; canonical source confirmation and reservation
services completed the intended ready-work setup without changing any guard.
The final four proofs pass in **6.24 s**, preserving **63 due / 2 forecast /
61 risk**, all **61** projected deviations before a **50**-row overview, and
all **63** supporting orders. Log:
`/private/tmp/reality-378-detail-projection-canonical-ready.log`.

The full affected final shipping/readiness/policy/revision/stock/source/case/
control/replay/snapshot/adapter set passes **183 tests in 63.37 s** with two
workers (`/private/tmp/reality-378-final-read-projection-regressions.log`).
Skipping only known-empty optional case-input queries then retains all
**53** affected case/control/source/company regressions (**25.72 s**,
`/private/tmp/reality-378-empty-cohort-final-regressions.log`); executing totals
are queried independently whenever any case link exists, including actions
outside the bounded preview. The final actual browser is green: **one passed
in 28.66 s**, committed change displayed in **3,440 ms**, three actions to
takeover review and verified retained control/reason/human-owned register. Log:
`/private/tmp/reality-378-real-browser-final-projection.log`; owned artifacts:
`pytest-61/test_live_cockpit_shows_commit0/operations-cockpit`. These browser
measurements use the small populated scenario, not enterprise DOM rendering.
The unchanged final enterprise run is pending; the real-time soak is unrun.

### Original source metadata cohort refinement

The first standard detail-projected benchmark measured **2.538228 s** first
read, **3.196917 s** opening/site p95, **2.614888 s** committed-hold observation,
at most 69 queries and the same 370,870-byte response. Opening acceptance stayed
red and sustained acceptance was not reached. This run took **112.84 s**; log
`/private/tmp/reality-378-performance-final-projection.log`. It finished before
the subsequent documentation generator started, so no owned documentation or
browser job overlapped its measurements. No target, cohort or total was reduced.

Clean snapshots now read original source/current-version/current-intake metadata
once for the union of the accepted site statement references. The canonical
validator still checks each statement's exact required IDs independently. Missing
evidence for one selection neither contaminates nor excuses another; inputs are
bound to the same session, company and explicit source scope. Normal reviews and
mutations ignore private reuse. The new proof first failed on the absent loader;
normal/batched result, exact missing/unresolved errors, foreign-company and
outside-snapshot freshness then pass with the four previous projection proofs
(**five passed in 6.81 s**). All **184** affected shipping/source/version/review/
control/readiness/policy/snapshot regressions pass (**192.28 s**, two workers),
log `/private/tmp/reality-378-source-cohort-final-regressions.log`.
The final real browser also passes (**one passed in 40.60 s**), log
`/private/tmp/reality-378-real-browser-source-cohort.log`. The unchanged enterprise
measurement is pending; enterprise DOM timing and real-time soak are not claimed.

### Final declared enterprise read workload — PASS

The unchanged final isolated profile passes **one test in 238.12 s**.
First application read: **2.388088 s / 63 queries / 370,870 bytes**.
Opening/site-filter p95: **2.792587 s**, maximum **69** queries. An actual
committed hold is observed in **2.013683 s**, with exactly one risk and 9,999
forecast. All company/site due, handover, forecast, risk and complete case counts
remain exact. Hardware, database settings, distribution, cold method and twenty
samples are printed in `/private/tmp/reality-378-performance-source-cohort.log`.

The sixty-second continuous phase passes **480 requests** from ten simultaneous
observers refreshing overview/register/activity/Agent panels, with **twelve
concurrent canonical order commits**. Read p95 is **2.823270 s**; maximum
cycle time **3.511253 s** meets the unchanged five-second cadence. Maximum
queries **84**, maximum payload **373,207 bytes**, final committed-order
verification **4.056409 s** meets the unchanged ten-second visibility gate.
Complete old/new snapshot parity, mandatory next-cycle visibility and all twelve
new orders are verified; no write duration is subtracted. All owned browser,
regression and documentation jobs ended before this standard run began.

This passes the declared service/JSON workload boundary. It does not infer
capacity from annual revenue or establish enterprise DOM/network rendering:
the real end-to-end browser uses the separately described populated small
scenario. The deterministic eight-hour browser proof remains green; the separate
eight-hour real-time soak is **UNRUN** and remains a pre-pilot gate. No real
company, primary route, history adoption, migration, transport, merge or
deployment is enabled by these results. Aggregate rollout review stays open.

### Final integration handoff

`make spec-check`, `make lint`, business annotations (667 described functions /
115 approved described tests / zero missing) and `git diff --check` pass.
`make docs-generate` and `make docs-catalog-check` pass with 232 sources, 446
evidence units, 39 capability routes and 228 journeys. Catalog freshness uses an
isolated temporary Git index/object directory containing only the prepared
generated-file changes; the actual index and Git history are untouched. Log:
`/private/tmp/reality-378-docs-catalog-final.log`. No staging or commit is claimed.
The archived reference remains byte-exact: 70,071 bytes, SHA-256
`c5bee6395b7a63f00b2a22c9d26ac3bb479b2ceea8290ae2b8789a8ca39eb03e`,
including its sandbox/CSP. Desktop/mobile acceptance screenshots remain in the
owned visualization workspace; the default Today layout has not changed during
read refinements.

The optional first implementation is ready for source/UI review. T003–T035 have
verified evidence; T036 and aggregate rollout tasks stay open because backend/
JSON timing does not establish enterprise display timing. The separate real-time
soak is unrun. The existing default entry, real companies, migrations, adoption,
provider effects and hosted reference remain outside this rollout.

## Usability follow-up verification (2026-10-06)

T043–045 are verified: test-first browser evidence, **478/478 frontend contracts**, complete frontend formatting, **2,976/2,976 localization entries in each of four languages**, frontend production build and actual fixture browser proof pass. Browser coverage includes dense cutoff/deviation previews, full disclosure, focused adjacent shipping drilldown and return focus, paging, takeover/handback, stale/revoked states, live refresh, themes, desktop and mobile. The final reviewed web image was rebuilt and activated on the existing local port 8080.

The real retained company cockpit independently showed four default deviation previews, business-readable activity names, registered operator use, six compact cases with complete totals, and the filters Still open / Taken over manually / All cases. Shipping handover counts advanced automatically from 29 to 34; the service read at 18:03:39 UTC confirmed 853 due, 34 handed over, 406 forecast and 819 at risk. Screenshots: `/private/tmp/reality-cockpit-live-final.png` and `/private/tmp/reality-cockpit-ux-final.png`. Existing exact action guards, source links and live observation semantics remain intact. No frontend business formula, source reinterpretation, historical handover backfill or new execution mandate was added. Aggregate enterprise-display timing, eight-hour real-time soak and rollout review remain open.

## Operating flows verification (2026-10-06)

FR-028–033 now have independent PostgreSQL and UI evidence. The final affected backend group passes **55 tests in 120.45 s**, covering local reply/ack lineage, duplicate and foreign replies, complete cohorts, partial/corrected receipts, physical return disposition, canonical stock risk, access/snapshot adapters and no implicit adoption. Log: `/private/tmp/reality-flows-backend-reviewed.log`. Frontend contracts pass **478/478**; final cockpit browser proof passes across desktop/mobile, four languages, themes, evidence links, unknown/stale states and retained shipping/deviation/case controls. Logs: `/private/tmp/reality-flows-contracts.log`, `/private/tmp/reality-flows-browser-reviewed.log`. Formatting, **2,994/2,994** localization keys in each language and production build pass. Local pending queues are labelled pending work rather than active execution; backlog curves disclose their displayed range and missing history stays unknown.

`make lint`, `make spec-check`, business annotations (668 described functions / 115 approved tests / zero missing), `git diff --check`, generated reference freshness and Docker API/MCP/web builds pass. Documentation freshness uses an isolated temporary index and object directory against prepared generated files; the real index/history/objects stay untouched. The plain working-tree check compares against the committed version and therefore reports the intentionally uncommitted generated changes; the isolated-index run proves regeneration introduces no further changes. Logs: `/private/tmp/reality-flows-quality-final.log`, `/private/tmp/reality-flows-docs-final.log`, `/private/tmp/reality-flows-compose-reviewed.log`.

The first per-message correlated reply query was rejected by local timings near 190 s and replaced with grouped same-company/system first-reply and acknowledgement joins. Canonical commitment terms are batch-read. The final independent complete cockpit observation at 18:30:09 UTC took **1.908 s** on the retained local demo; this is local verification, not a repeated enterprise workload or production capacity claim. It observed 501 open orders, 75 first-recorded orders and 48 physical dispatch records in the hour; 1,942 messages without recorded replies, 1,864 unacknowledged, 54 first replies and a **+21** reply-backlog change; two supplier promise lines still expected (both dates unknown), 21 fully received supplier lines; two canonical oversold-item risks; zero recorded physical return positions or announcements. Return counts do not infer return processing from customer messages. The fixed shipping cohort remains 853 due and 34 handed over; newer orders outside that reviewed plan remain separately inspectable rather than silently enlarging the authority.

The existing simulator and Claude supervisor remain running, without a new operator, credential, mandate, recurring queue, migration or history adoption. API/MCP/web activation on local port 8080 preserves the background workers. Expanded enterprise DOM/query load, separate eight-hour real-time soak and rollout review remain open. Final real-browser refresh and screenshot evidence follows below.

### Final live UI and layout receipt

All five cards are visible in the real retained company. Without navigation/reload, the observed time advanced from 20:31 to 20:32 Europe/Berlin, open orders changed from 504 to 503, dispatch records from 48 to 50 and unanswered messages from 1,945 to 1,946. Named access showed the retained Claude operator's recent approved tool use; four default shipping-deviation previews and all three shipping series remained present. The final layout uses three/two equal groups at 1440 px, all five cards side by side on wide displays, and a single column at 390 px. Both real desktop and mobile reads confirm five cards and no horizontal page overflow. The final fixture browser proof also asserts the grouped layout and passes (`/private/tmp/reality-flows-browser-layout-final.log`). Final web image build/activation pass (`/private/tmp/reality-flows-web-image-final.log`, `/private/tmp/reality-flows-web-final-activation.log`). Screenshots: `/private/tmp/reality-cockpit-flows-desktop-final.png`, `/private/tmp/reality-cockpit-flows-mobile-final.png`. Temporary viewport overrides were reset; the test-only port 5177 server was stopped. User-facing port 8080, simulator port 8768 and the existing Claude supervisor remain running. T046–049 are verified within this local increment; earlier enterprise/soak/rollout gates remain open.

The actual 1920 × 1080 responsive check also confirms all five flow cards on the same row and zero page overflow. Wide live screenshot: `/private/tmp/reality-cockpit-flows-wide-final.png`; retained artifact: `/Users/benediktsauter/.codex/visualizations/2026/10/06/01a10ffd-6b60-7800-bb0e-c8f98d6a29f1/operations-cockpit-live-wide.png`. The temporary viewport override was reset after capture.


## Visual consistency verification (2026-10-06)

FR-034–036 and T050–052 are verified within this local presentation increment. The test-first browser run failed on offset order/message charts; a second independent narrow-content assertion failed because viewport-only breakpoints did not accommodate a docked panel. Shared content-sized grid tracks, common chart/note/evidence/footer slots, container-aware layout and unified selection/navigation styling resolve both failures. No fixed whole-card height, placeholder business metric, fabricated stock history or alternate business rule was added. An independent read-only UX review of the implementation and desktop/mobile screenshots found no blocking issue.

The final complete cockpit browser regression passes at 1440/1920/390 px, narrow 720/440 px content, all four languages and themes, keyboard selection, expanded evidence, stale/unknown states, source inspection, shipping series and existing takeover/handback guards. Log: `/private/tmp/reality-cockpit-polish-browser-final.log`. Frontend contracts pass **478/478**, formatting passes, localization covers **2,995/2,995** keys in each language, and production build passes (`/private/tmp/reality-cockpit-polish-web-gates.log`). Lint/spec/annotations pass with 668 described functions, 115 described tests and zero missing (`/private/tmp/reality-cockpit-polish-quality.log`). Generated documentation was regenerated and freshness passed using the isolated temporary index/objects baseline; the actual index/history/objects remain untouched (`/private/tmp/reality-cockpit-polish-docs.log`).

The final local web image build passes (`/private/tmp/reality-cockpit-polish-web-image.log`); only web was recreated with `--no-deps`, and port 8080 returned HTTP 200. API/MCP, scheduler/workers, the simulator and sole Claude supervisor were not restarted. The retained real-company browser confirms identical primary-metric starts and chart slots across all five wide-display cards (0 px difference); the three desktop SVG chart starts also match exactly. Both selection groups are 44 px high. At 390 px all five cards use natural-height single-column layout, with no card or page horizontal overflow. Actual lower-page inspection confirms grouped filters, bounded deviations and six-case paging.

Automatic observation remained active: without another reload the local observation advanced from 20:44 to 20:45 Europe/Berlin, open orders changed from 506 to 507, recorded first replies from 43 to 44 and recent business-object activity from 53 to 54. Shipping still exposes its reviewed plan, 34 confirmed handovers and live forecast. Saved actual UI evidence: `/Users/benediktsauter/.codex/visualizations/2026/10/06/01a10ffd-6b60-7800-bb0e-c8f98d6a29f1/operations-cockpit-polished.png`, `/private/tmp/reality-cockpit-polish-wide.png` and `/private/tmp/reality-cockpit-polish-mobile.png`. Temporary viewport overrides were reset and the fixture-only port 5177 server stopped. Business scope, data semantics, action permissions and live lifecycle are unchanged. Earlier enterprise-display/soak/rollout gates remain open.


## Central status overview verification (2026-10-06)

FR-037–038/T053–055 are verified for this local presentation increment. Test-first browser proof failed on the absent central overview (`/private/tmp/reality-status-red.log`). The final complete cockpit browser proof passes placement before shipping, all five canonical states, exact primary-metric parity, keyboard anchors, stale/missing unknown status and absent metrics/no dead links, four-locale/theme desktop/mobile/narrow layout, existing shipping/case/evidence behavior and exactly the original two reviewed test mutations. Log: `/private/tmp/reality-status-browser-final.log`. The fixture restores its explicit harness URL for isolated state resets rather than reloading an application URL generated by existing navigation.

Frontend formatting, **478/478** contracts, **2,999/2,999** audited localization entries per language and production build pass (`/private/tmp/reality-status-web-gates.log`). Lint, spec and business annotations pass (668 described functions, 115 described tests, zero missing; `/private/tmp/reality-status-quality.log`). Generated references are fresh against the prepared changes using temporary index/objects, without touching the actual Git index/history/objects (`/private/tmp/reality-status-docs.log`). The final web image build and web-only activation pass (`/private/tmp/reality-status-web-image.log`, `/private/tmp/reality-status-web-activation.log`); port 8080 returns HTTP 200.

Actual retained-company inspection confirms five prominent status tiles immediately under the live observation and above shipping: orders critical with 509 open orders, messages ordinary pending work with 1,956 without recorded reply, supply unknown with two expected lines, stock critical with two uncovered-demand items, and returns no finding in the evaluated scope with zero pending physical positions. Status is accompanied by text and uses the exact existing service signal, not a new company-health or agent-quality score. The native keyboard message link focuses `cockpit-flow-messages` at the 80px header offset and retains the cockpit context. The 390px real page and all five tiles have no horizontal overflow. The reviewed plan/confirmed-handover/forecast shipping panel remains present (853 due, 34 handed over, 346 forecast at this observation).

Actual desktop screenshot: `/Users/benediktsauter/.codex/visualizations/2026/10/06/01a10ffd-6b60-7800-bb0e-c8f98d6a29f1/operations-cockpit-status.png`; mobile: `/private/tmp/reality-status-mobile.png`. Temporary viewport override was reset. Only web was recreated; the existing simulator, sole Claude supervisor, API/MCP and background roles remain running. No additional timer, request, business computation, mutation, schema or mandate was introduced. Final review against FR-032/037/038 and the Constitution finds no scope or authority conflict. Earlier enterprise/soak/rollout gates remain open.


## Permanent Control Tower navigation verification (2026-10-06)

FR-039–040/T056–058 are verified in the local frontend increment. A complete root-entry fixture first restores the existing playground-entry read; the meaningful pre-implementation proof then fails with zero permanent Control Tower links (`/private/tmp/reality-tower-red.log`). The revised full-shell browser proof passes root/Home discovery, same-company capability gating, enabled-company operational navigation, unchanged Home, on-demand chat and cleared company context, disabled/failed availability without operational reads, a permitted Inbox return and unchanged order/case/source/return context (`/private/tmp/reality-tower-shell.log`). The complete cockpit browser regression also passes, including its four-locale/themes/responsive/traffic-light/alignment/control/source/stale/unknown scenarios (`/private/tmp/reality-tower-cockpit.log`).

All **478 frontend contracts** pass in `/private/tmp/reality-tower-web-gates.log`. The initially unregistered invariant English workspace name was correctly rejected by the audit. Control Tower is now explicitly registered with its FR-040 product-name reason in the existing invariant catalog; no generic translation rule was relaxed. The final affected audit tests pass **5/5**, all four languages cover **3,002/3,002** audited entries, complete formatting and production build pass. Final repair command exit 0; build log `/private/tmp/reality-tower-build-final.log`. Lint, spec and business annotations pass (668 described functions, 115 described tests, zero missing; `/private/tmp/reality-tower-quality.log`), and generated references are fresh against prepared changes using isolated index/objects (`/private/tmp/reality-tower-docs.log`). The actual Git index/history/objects remain untouched.

Docker web build and web-only activation pass (`/private/tmp/reality-tower-web-image.log`, `/private/tmp/reality-tower-web-activation.log`), and fresh port 8080 returns HTTP 200. Actual root entry still selects Acme Bikes GmbH (`ten_fb7f9595f3`) and now immediately displays the permanent Control Tower destination. Opening it displays the truthful unavailable-current-company explanation with the existing company menu and Inbox return. Choosing the exact retained Live Company Simulator (`ten_29a7b31670`) through that menu opens its operational view, with Control Tower in both shell/page titles, all five flow areas, the status overview and protected shipping/case/agent panels. No default company, company purpose, membership, mandate or persisted preference was changed.

Actual desktop screenshot: `/Users/benediktsauter/.codex/visualizations/2026/10/06/01a10ffd-6b60-7800-bb0e-c8f98d6a29f1/control-tower-navigation.png`; unavailable-company screenshot: `/private/tmp/reality-tower-fresh-unavailable.png`; actual 390px mobile screenshot: `/private/tmp/reality-tower-mobile.png`. Mobile retains the new title and destination with zero page overflow; temporary viewport override was reset and the extra root-review tab closed. The retained live observation advances automatically (19:02 to 19:03 UTC); simulator/Claude/API/MCP/background roles were not restarted. Only the fixture-only port 5177 server was stopped after verification. Final review finds the permanent discovery change within owner-authorized scope, with canonical availability and tenant boundaries intact. Earlier enterprise/soak/rollout gates remain open.


## Workspace surface verification (2026-10-06)

FR-041/T059–061 are verified for this presentation-only follow-up. The test-first computed-style proof failed with the Light canvas `rgb(248, 250, 252)` against the common workspace surface `rgb(255, 255, 255)` (`/private/tmp/reality-surface-red.log`). Changing only `.operations-cockpit` from `--bg` to `--surface` resolves the mismatch. The complete existing cockpit browser proof passes, including four languages, light/dark, responsive geometry, neutral selection/explanation surfaces, expanded calculation basis, all shipping series, source links and reviewed case controls (`/private/tmp/reality-surface-browser.log`). All 478 frontend contracts, complete Prettier validation, production build, lint, spec policy and diff whitespace checks pass; build log `/private/tmp/reality-surface-build.log`. No localization key, business read/tool, schema, scheduling, global theme token or control policy changed, so generated tool reference content is unaffected.

The existing Docker web image was rebuilt and only web was recreated with `--no-deps` (`/private/tmp/reality-surface-web-image.log`, `/private/tmp/reality-surface-web-activation.log`). Real port-8080 Light inspection shows identical white canvas/header/cards; Dark inspection shows identical `rgb(16, 24, 40)` canvas/header. All five operating areas and all three shipping series remain present. The observation advanced from 19:14 to 19:15 UTC, with open orders from 518 to 519 and unanswered messages from 1,959 to 1,960. Light screenshot: `/Users/benediktsauter/.codex/visualizations/2026/10/06/01a10ffd-6b60-7800-bb0e-c8f98d6a29f1/control-tower-light-consistent.png`; Dark screenshot: `/private/tmp/reality-surface-dark-live.png`. The temporary Light choice was restored to the original System preference. The retained cockpit tab remains available; the fixture-only server is stopped. Simulator, Claude, API/MCP and background roles were not restarted. Final review confirms the single surface-role change and preserved neutral detail/selection roles; earlier enterprise/soak/rollout gates remain open.


## Case takeover discoverability verification (2026-10-06)

FR-042–044/T062–064 are verified for the owner-authorized frontend refinement. Test-first placement failed because takeover followed shipping (`/private/tmp/reality-case-entry-red.log`). The existing register now appears once between status and shipping as a bounded, initially collapsed entry. The density proof explicitly restores this new routine collapsed state after exercising the keyboard/count shortcuts. Full cockpit browser proof passes compact placement, keyboard disclosure, human/open-work shortcuts, bookmarked context, preserved draft on close/reopen, original exact takeover/handback, four-locale/theme/mobile/narrow geometry, all shipping/evidence/deviation/flow behavior (`/private/tmp/reality-case-entry-browser.log`). The complete shell regression passes (`/private/tmp/reality-case-entry-shell.log`). Eight controlled hours pass with bounded requests and retained inspection/review through quiet intervals, rollover, hidden/recovery/failure and company changes; zero browser errors (`/private/tmp/reality-case-entry-session.log`). This remains simulated-time proof, not the outstanding real-time rollout soak.

Complete Prettier validation, all 478 frontend contracts, 3,005/3,005 audited entries per language and production build pass. Final affected-file formatting passes (`/private/tmp/reality-case-entry-final-format.log`), as do lint/spec policy and diff whitespace (`/private/tmp/reality-case-entry-lint.log`, `/private/tmp/reality-case-entry-spec.log`). No service, tool/schema, polling, mandate or mutation contract changed; generated tool references are unaffected. The existing web image build and web-only `--no-deps` activation pass (`/private/tmp/reality-case-entry-web-image.log`, `/private/tmp/reality-case-entry-web-activation.log`).

Actual port-8080 observation confirms the collapsed entry before shipping, 827px entry width at the natural 915px viewport, no page overflow, all five operating areas and all three shipping series. It shows 184 automatic cases and one existing manually owned case. The human shortcut returns `LIVE-f1ad500666008054` with manually owned/automation stopped and open work; this verification performs no takeover or handback. The default outstanding-view disclosure was collapsed again, and the retained tab remains available. Screenshot: `/Users/benediktsauter/.codex/visualizations/2026/10/06/01a10ffd-6b60-7800-bb0e-c8f98d6a29f1/control-tower-case-entry.png`. Observation advanced from 19:24 to 19:25 UTC during this read-only check. No appearance preference/viewport changed, and simulator/Claude/API/MCP/background roles were not restarted. The fixture-only server is stopped. Final scope review confirms truthful existing counts, existing supported case scope, full confirmation safeguards and preserved Source/Evidence/Reality links. Earlier enterprise/soak/rollout gates remain open.

## Combined current-main PR verification (2026-10-06)

The isolated PR checkout is based on main `bb74d120` and preserves spec 377 default
coordination and spec 379 source-completeness rules. Migration 0146 follows 0145;
no running local company database or operator checkout is changed by this review.

The new no-activation register regression first failed with hidden accepted work,
then passed. It checks known counts, platform readiness, read-only event history,
absence of fabricated legacy adoption and readiness after canonical reconciliation.
The existing scalar/batched parity proof includes current consumer sequence values.

`make spec-check`, `make lint`, business annotations, frontend formatting/build,
all **478 frontend contracts**, and **3,003/3,003 localization keys** in each of the
four languages pass. Chromium passes populated shipping/flows/evidence/control
presentation, permanent shell navigation, shared selects, existing case controls
and analytics-save clarity. Documentation formatting, **145 Node contracts**,
**16 generator tests**, **16 repository-script tests** and the documentation build
pass. Public references are regenerated with the documentation's actual Prettier
runtime; raw generation without that runtime is not the CI representation.

The controlled browser session previously allowed host wall time to advance in
addition to its explicit eight simulated hours. On a heavily loaded local host this
exceeded the unchanged request-budget assertion. The revised harness pauses its
clock before opening the app and advances only through explicit steps. This changes
no production timer or budget and does not stand in for the separate real-time soak.

The full PostgreSQL suite runs in four CI shards on PR #382. A redundant local full
run was stopped to preserve resources for the running demo and targeted proofs;
its partial results are not full-suite evidence. Local live-browser attempts timed
out at the unchanged 90-second database-migration bound, while the identical
current-main Control Tower journey passes in CI. No timeout threshold was weakened.
Final head-specific CI and targeted results are recorded after completion.

The paused-clock session passes all eight controlled hours: the four observation
endpoints issue 5,747–5,753 reads, preserve bounded charts and exact review state,
retain investigation-day context across midnight, reset company context and report
zero browser errors. This is deterministic proof, not the real-time pilot soak.

The combined targeted PostgreSQL group passed 84 tests and skipped the existing
credential-dependent case, while exposing two test-fixture assumptions. One
ordering fixture compared repeatedly sampled wall times instead of a fixed
attributable ordering instant; the other expected no retained planning actions
before default coordination. Both repaired regressions pass (2 tests, 13.44 s),
including the unchanged 55-read budget and scalar/batched parity. The deviation
proof now verifies exact proposed/executed planning actions, explicit absence of
causal-response/provider-outcome claims and no invented next check. No production
response rule or action ordering was weakened. Final full-suite CI remains the PR
review gate and its head-specific result is recorded in the PR description.


## Instrument console increment — 2026-10-07

Owner-approved FR-047–051 add compact instruments and one selected detailed analysis.
The reviewed implementation tree was identical to current main after PR #382 merged;
the follow-up uses its own branch, retaining the optimized activity-owned flow read.
No shipping/case authority, schema definition, poller or extra SQL query is introduced.

Executed proof: 24 operating-flow tests and 29 cockpit adapter/snapshot tests passed
against a disposable PostgreSQL database, including scalar/snapshot modes, exact mail
lineage, missing scope and inclusive-hour/bucket boundary reconciliation. The 478
frontend contracts passed. Production TypeScript/Vite build, final formatting,
four-language audit (3,015 used strings), full-shell browser checks, specification
policy, Ruff, generated catalog freshness and business annotation audit passed.
The controlled eight-hour browser session passed with zero errors and each live
endpoint below the unchanged 5,800-request budget. This is controlled-time proof,
not the unrun real-time eight-hour pilot soak.

The first mail boundary fixture failed because its observation minute was not aligned
to clock buckets; the corrected test fixes that independent premise and separately
proves a partial rolling-hour start. The first language audit exposed a missing time
label and a protected domain-term mismatch; both were corrected and the final audit
passed. The obsolete original-checkout live-session proof exceeded the endpoint budget;
the final merged shared-reader architecture passed without weakening that budget.

Local activation uses the reviewed API/web build context and the original stack's
configuration. A real-browser check found the older local database at the obsolete
`0145_shipping_plan_inputs` revision without `case_rollout`. Before any schema change,
a complete custom-format local backup was saved. The old and canonical shipping DDL
were proved identical after whitespace normalization (all eight statements). Only
the already-reviewed frozen `0145_default_operational_cases.upgrade` was executed
transactionally, with a five-second lock timeout and a sixty-second statement timeout;
the revision was then reconciled to canonical `0146_shipping_plan_inputs`. Existing
shipping inputs, cases, manual ownership and immutable business records were retained.
No business record was rewritten, no scenario input was invented and no job or
external effect was submitted. Operator, simulator, MCP and worker processes retained
their running state. Full background platform reconciliation remains separately visible.

Real local API `/healthz` and web responded HTTP 200. The actual company showed
separate incoming/first-reply and backlog curves with real counts, current event
activity and one existing human-owned case. The sole confirmed demo shipping plan
is dated 2026-10-06: a pinned view showed 853 due and 35 confirmed handovers. Today's
missing plan remains unavailable; a finished day's future forecast is not reconstructed.
Finance remains explicitly unavailable in this projection. Observed values change live
and are proof observations, not fixed acceptance targets.

Final responsive proof passed in both themes and all four languages at 320/390/1440/1920px,
with existing docked-container coverage retained. The narrow-screen spacing change
initially exposed long-label overflow; explicit metric-cell wrapping and the unchanged
page-width assertion resolved it. The final browser run also proves a sixteen-pixel
metric-row gap, preserving source disclosures, selected analysis and case confirmation.

The final web image was activated and reloaded in the actual local browser. Its
selected analysis computed the asserted 16px metric-row gap. The confirmed demo
shipping plan and handover curves remained present. The actual unanswered count
changed from 1,985 to 1,945 during inspection; automated case totals and recent
business events also advanced. The manually owned case stayed visible as automation
stopped. Both HTTP health and web returned 200; the existing simulator/MCP containers
kept their uptime. Existing platform rollout coverage remains incomplete and is
shown explicitly, rather than represented as complete autonomy verification.


## Preview parity verification — 2026-10-07 (FR-052–056)

The new tests first reproduced absent service partitions (six failures) and the
shipping/log layout mismatch. Final affected PostgreSQL proofs pass: 30 operating-flow
cases in scalar/snapshot modes and 29 cockpit adapter/snapshot cases. Frontend contracts
pass (478); all four language audits pass (3,024 covered phrases each); format, build,
feature policy, business annotations and generated-catalog freshness pass.

The full cockpit browser matrix passes at 320/390/1440/1920 and the docked narrow
container, both themes and all four languages. It checks two-row/stacked geometry,
exact category counts and proportional widths (including small positive categories),
the swatch legend, no artificial analysis-header spacer, no green stale assessment,
shipping inspection beside its originating chart, selected intake/reply plus backlog
plots, named owner-access inventory, and existing reviewed case-control races/retries.

Controlled eight-hour proof passes with no page errors and bounded four-read budgets:
overview 5,746, activity/flows 5,750, Agent inventory 5,752, case register 5,753. Hidden
suspension/recovery, day changes, inspected event/source state, paused following and
exact pending takeover reason/revision survive. This remains controlled browser time,
not the separately required real-time pilot soak.

Execution list: [preview-parity.md](preview-parity.md). No new schema, SQL read,
scheduler, permission or business effect. Existing performance/pilot rollout gates
remain separate; the PR stays a reviewable follow-up rather than an enablement claim.

Final actual-company inspection verifies aligned shipping/log and analysis/responsibility
rows, a named active Agent access, the retained human-owned case, separate message
intake/reply and backlog plots, and aligned metric values beneath wrapping captions.
The current UTC business day (2026-10-07) has no confirmed source-backed shipping
plan/capacity, so its shipping curve remains explicitly unavailable. The delivered
local view is pinned to the existing 2026-10-06 plan (853 due, 35 handovers, 818 at
risk; no historical forecast). Company-wide operational flows continue observing
the current company independently of that pinned shipping day. PR 383 is ready
for review; prior enterprise-load and real-time pilot rollout gates remain open.

The corrected actual-stack hold/takeover/return-register journey passed locally
(1 test, 58.89 seconds) with no browser errors. The committed hold reached the
display within the existing ten-second requirement; confirmation payload and
persisted manual ownership remain asserted. CI is rerunning on the follow-up commit.

## Stable analysis interaction verification (FR-057–058)

The first new browser assertion failed because monitoring summaries still contained
duplicate analysis links. Final full cockpit browser matrix passes: summaries are
non-interactive, one labelled native analysis selector changes the diagram in place,
retains focus/heading position/history length, restores a bookmarked area and resets
a non-default selection after company change. Existing source/disclosure/live refresh,
shipping and manual-control proofs remain green in both themes, four languages and
320/390/1440/1920/docked layouts. No diagrams, measurements or service rules changed.

Frontend contracts: 478 passed; four language audits: 3,023 covered each, no missing or
invalid entries; full formatting and TypeScript/Vite build passed. Controlled eight-hour
lifecycle passed with zero page errors and each existing shared refresh read below
5,800 requests (overview 5,746; activity and Agents 5,749; register 5,748). Exact pending
manual reason/revision, inspected evidence and paused following survived. This is
controlled browser time, not the separate real-time pilot soak. Spec policy and diff
checks pass; earlier enterprise rollout gates remain separate.

Local activation updated only the frontend image. Actual company inspection verified
Messages → Supply → Messages kept analysis-header top at 353.84375px and focus on the
single selector; Messages retained both SVG diagrams. The existing human-owned case
remained visible in Responsibility, and the existing Agent access/activity and pinned
shipping plan stayed available. Final screenshot: stable-selection-live.jpg in the
temporary verification artifacts. API, simulator, operator and database were untouched.


## Prioritized console and quiet observation controls (FR-059–061)

The added pre-implementation geometry regression failed on the previous row placement.
The final cockpit browser matrix passes with shipping/Responsibility in the first row,
analysis/log in the second and Agents below the log. Narrow layouts and document order
prioritize Responsibility before observation. Analysis has a single frame, its only
labelled selector belongs to the header, all main cards share their insets/headings,
and the collapsed case entry retains natural height. Keyboard activation and localized
names/titles/pressed/expanded state are proved for shipping Info, following Pause/Play
and Agent List/Compact icons. Explicit reviewed business controls are unchanged.

Frontend contracts: 478 passed. Four-language audit: 3,023 covered phrases each, no
missing/invalid entries. Full formatting, TypeScript/Vite build, spec policy and diff
checks pass. Controlled eight-hour lifecycle: zero page errors; overview 5,742 reads,
activity 5,745, Agents and register 5,746 each (all below 5,800). Paused events, selected
sources and the exact pending manual reason/revision survive. This is controlled
browser time, not the separately required real-time pilot soak.

Only the local web image was rebuilt/recreated. Actual company inspection confirms
shipping and Responsibility share top 754px, analysis and log top 1,731.703px, and all
five main cards have 20px insets. The case card keeps its natural 603.906px height next
to the 957.703px shipping card. The existing manual case remains visible, the named
Claude access remains available, and Messages retains both SVG diagrams. Info expands
and closes the original source basis; Pause/Play changes only following and was restored
to following. Screenshot: priority-console-live.jpg in temporary verification artifacts.
The existing pinned shipping day retains 853 due/35 confirmed/818 risk, without a
reconstructed forecast. API, database, simulator, worker and operator were untouched. Live observation
advanced from 06:03 to 06:05 UTC without reload; both mail diagrams and the existing
manual case remained available. A brief failed activity refresh retained aged data
with its explicit stale indicator, then recovered automatically.

CI on the preceding head b890740f passed frontend, browser and the actual-stack cockpit
journey, but the enterprise backend load test exceeded its unchanged 3-second p95 limit
(3.251606216 seconds); 1,736 tests passed in that shard and the aggregate backend-quality
check inherits that failure. This UI-only refinement does not resolve or waive that
performance gate. New-head CI and the earlier enterprise/pilot rollout gates remain open.
