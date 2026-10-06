# Approval and pre-implementation review

**Date**: 2026-10-06
**Language**: English

## Owner authorization

After reviewing the product concept, proposed three-table shipping-input model, completion-slot-v1, all-day-live observation and named Agent/access overview, the owner explicitly approved proceeding in chat: "I like all of it, approval." The earlier schema/model approval gate is satisfied. Proceeding with implementation is authorized without requesting the same permission again. No production enablement, default-route replacement, merge or new external execution mandate is inferred.

## Checklist gate

| Checklist | Items | Checked | Unchecked | Meaning |
| --- | --- | --- | --- | --- |
| requirements.md | 23 | 21 | 2 | Historical schema approval and future runtime acceptance markers remain unmodified |
| shipping-control.md | 25 | 0 | 25 | Reviewer-owned quality markers remain unmodified; owner approved the complete prepared proposal |

The owner's current approval authorizes proceeding despite these existing markers. Do not self-complete reviewer-owned checklist markers or future runtime acceptance. This record supplies the current authorization while preserving their ownership.

## Spec Kit analysis report

| ID | Category | Severity | Locations | Finding | Disposition |
| --- | --- | --- | --- | --- | --- |
| U1 | Verification timing | Medium | SC-007, T041, quickstart | Accelerated eight-hour proof is not the separate real-time soak | Keep real-time soak and pilot acceptance pending until measured |
| S1 | Disclosure boundary | Low | FR-024, live contract, interfaces | Agent inventory has narrower visibility than ordinary cockpit reads | Implement the specified independently guarded panel; test non-owner isolation |

29 FR/DR requirements have scenario, proof and implementation-task mappings (100% coverage); seven measurable success criteria have verification paths. All 42 task identities are sequential. No unresolved requirement clarification, missing behavioral task, Constitution exception or CRITICAL conflict remains. Design Constitution Check passes. Governance/review tasks map to authorization and final evidence rather than a behavioral FR.

The analysis was read-only; this record was created afterwards to record the owner's implementation authorization. No unchecked acceptance requirement is represented as passing. Spec policy and local artifact-link/reference checks pass; the archived concept stays byte-exact.

## Execution

Use domain → service → tool → adapter order. Observe meaningful failing proofs before each implementation where practical. Use isolated PostgreSQL and fixture-backed browser infrastructure; keep the optional capability disabled by default and current Home available. Record exact outcomes, limitations, migration allocation and pending long-run/pilot checks.

## Performance design refinement review

The measured SC-004 failure establishes the use case for exact in-flight read sharing in the approved batching work. The plan retains current membership and owner disclosure checks for every caller, exact Engine/company/operation/filter isolation, immutable repeatable-read observation and fresh later reads. No completed result, authority, schema or scheduler is retained or introduced. Caller-owned transactions keep their independent guards. Snapshot/context/copy/failure and committed revocation proofs pass. This refinement is consistent with FR-010/018/021/023 and DR-001/003/005; no Constitution exception or CRITICAL artifact conflict is introduced. Enterprise timing and the complete completion gates remain red/pending.

## Implementation review checkpoints

The implementation preserves the three connected product levels: an optional
Operations cockpit, existing specialist workspaces and the Reality Inspector.
Home and genuine approvals remain reachable. Only the supported fulfillment and
announced-return cases expose the existing reviewed controls. No display read
adopts history, adds autonomous authority, cancels an external action or stores a
derived business observation.

| Requirements | Reviewed implementation and executable proof | Current acceptance boundary |
| --- | --- | --- |
| FR-001, FR-016–017 | Default-off capability; same-company safe origin; Shell/routing tests and full Shell journey; current membership guards | Focused proof passes; complete regressions pending |
| FR-002–009, DR-002 | Pure completion-slot-v1; source-backed quantities/plans/capacity; physical contents and effective event time; independent two-site, partial, revision, DST and unknown-input tests | Focused domain/service/browser proof passes |
| FR-010, FR-018, DR-001 | Full fingerprint and bounded disclosed evidence preview; essential planning Sources retained; supporting-order paging; read-only RR and caller-owned drift guards | Focused parity/source/snapshot proof passes |
| FR-011–012 | Exact canonical blockers and case-linked recorded actions; explicit reaction absence, pending external outcome and unsupported/deferred measures | Focused reaction and preservation review passes |
| FR-013–015, DR-004 | Canonical complete register, attributed reviewed takeover/handback, related independent cases and unsettled-action visibility | Focused races/replay/register and real takeover proof passes |
| FR-019 | Shared display locale/timezone formatting; explicit business/site date and offset; all four languages, themes, keyboard and bounded mobile layout | Final component and 478 frontend tests pass |
| FR-020 | Byte-exact reference and per-item C01–C25 preservation audit in migration-map; generated executable vocabulary | Documentation review present; final aggregate acceptance pending |
| FR-021–023 | Shared recorded-business activity; cancellable bounded five-second lifecycle; stable investigation/review and company-day rollover | Controlled eight-hour and real committed-change proof pass; enterprise timing and separate real-time soak pending |
| FR-024 | Opaque credential-kind-qualified manual/OAuth identities, complete totals and paging, current owner disclosure, exact supported attribution and redaction | Focused access proof passes; no persistent runtime identity/state is inferred |
| DR-003 | Tenant predicates/FKs, current active membership, owner-only inventory and same application services in Web/CLI/MCP | Focused foreign-reference/refusal/adapter proof passes |
| DR-005 | Complete SQL case counts, full shipping input cohort, complete counts before paging and no observation writes/scheduler | Functional proof passes; SC-004 workload remains pending |

Normal service callers retain their ORM identity-map and pending-value behavior.
Narrow original-column reads are limited to the clean, read-only cockpit snapshot;
their scalar/batch stored-value parity is tested. Large opaque-ID membership uses
one safely bound PostgreSQL array, with actual unusual/null/empty/70,000-ID proof.
Exact in-flight joining publishes independent JSON values and removes the entry
before completion; authorization remains individual and is rechecked afterwards.

SC-001/002/003 have independent populated shipping, responsive and real three-action
control evidence. SC-005 has the per-item preservation audit. SC-006 additionally
requires the final complete regressions. SC-004 and the enterprise-load portion of
SC-007 remain red/pending; the pre-pilot real-time soak has not run. Task completion
and final acceptance must follow the actual final results in quickstart, not these
review checkpoints alone.


### Final read-only refinement review

The original current-statement selector retains its version/withdrawal and company
joins while clean cockpit snapshots project original header/source metadata and
exact reviewed basis only. Full payloads remain lossless and linked. Scoped
original order/commitment inputs are reused within the same observation by the
canonical terms, readiness and delivery-policy readers; normal callers keep ORM
behavior. Incomplete/foreign policy input falls back to its canonical scoped read
and never supplies a permissive default in place of a recorded customer rule.
Complete observation/fingerprint parity, unchanged original payloads, one cohort
read and direct standard/prepayment parity have passing proof; all 147 affected
regressions pass. No schema, cache, authority or Constitution exception is added.
The selected-day caption restores FR-003 in the existing browser; four-language
and complete frontend gates pass. This refinement introduces no unresolved
requirement or CRITICAL consistency finding. Enterprise timing and the separate
real-time soak remain required; no pilot or final aggregate acceptance is inferred.

The bounded case-input refinement above implements the existing approved
FR-010/FR-013/FR-018 and DR-001/DR-005 read contracts. Design review finds no
Constitution exception or unresolved requirement: exact canonical results and
company/control/source boundaries are required; performance remains a separate
red acceptance gate. Implementation may follow the failing parity proof.

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

The overview-only detail projection is a read allocation refinement under the
existing FR-010/FR-018/DR-001/DR-005 contracts. Review requires unchanged complete
calculation/fingerprint and complete deviation counts, while public supporting
reads remain fully paged. No additional business rule, schema or Constitution
exception is proposed; proceed after the failing exact-parity proof.

Final overview projection review: all full source/physical/readiness inputs and
curves remain canonical before detail allocation. Healthy, held and source-gap
parity plus the 63-order/61-deviation full-count/supporting-list proof pass.
All 183 affected regressions are green; known-empty optional case SQL removal
then retains all 53 affected controls/source/scope proofs. Actual browser
committed-change display, three-action review and retained control/reason pass
with final code. No rule, schema, mandate, cache or Constitution exception is
added. Opening/site-filter timing has passed in the last standard run, but
continuous three-second p95 remained red; the new unchanged measurement is
pending. No enterprise-DOM, real-time-soak or aggregate rollout claim is inferred.

Source-metadata-cohort design review retains the same per-statement canonical
version/interpretation checks, exact-confirmation and company/session scope.
It proposes no new authority or Constitution exception; implementation follows
the failing result/error parity proof. Three-second enterprise acceptance remains
red and all previous measurements stay recorded.

The source-cohort implementation retains per-statement selected-ID and exact
current-confirmation checks, session/company/cohort guards and ordinary read
freshness. Result/error/scope parity, 184 affected regressions and the final real
browser pass. No additional source interpretation, rule, schema, authority or
Constitution exception was introduced. Enterprise timing is rerun separately;
real-time soak and aggregate rollout review are still open.

Final declared service/JSON workload review: unchanged 10,000 active /
100,000 historical / 500,000 shipment observations / ten readers passes.
Opening/site p95 2.792587 s, 480-read live p95 2.823270 s, maximum cycle
3.511253 s, twelve concurrent canonical commits and final visibility 4.056409 s
all meet the original gates with complete semantic counts. Prior red runs remain
recorded; no target, cohort, deadlines or write duration was relaxed. Full
functional/backend/browser/frontend/source-control proofs are green. This
establishes the measured backend/JSON boundary only; large enterprise DOM
timing, the unrun real-time soak and aggregate pilot/rollout review remain open.
Reviewer-owned checklists and rollout authority are not inferred from test passes.

Final integration checks and generated-reference freshness pass. The prepared
source/UI first increment is reviewable and its verified functional tasks are
marked individually. Aggregate enterprise-display, real-time-soak and rollout
review remain open; no production enablement or reviewer-owned checklist
approval is inferred. Reference bytes/sandbox/CSP remain unchanged.

## Follow-up pre-implementation review (2026-10-06)

The owner requested live operation and an intuitive review of the entire cockpit, explicitly asking for a Head of UX. Read-only UX review found unbounded default deviation evidence, technical case language and an unseen bottom-of-page shipping drilldown. FR-025–027 and T043–045 trace the bounded refinements to fixture browser, frontend and mobile checks; implementation changes presentation only. Existing event-title vocabulary is reused rather than inferring document purpose. Constitution Check PASS; no CRITICAL analysis finding, unresolved clarification, new schema or execution mandate. Earlier enterprise-workload/soak/full-feature rollout gates remain open.

## Usability follow-up verification (2026-10-06)

T043–045 are verified: test-first browser evidence, **478/478 frontend contracts**, complete frontend formatting, **2,976/2,976 localization entries in each of four languages**, frontend production build and actual fixture browser proof pass. Browser coverage includes dense cutoff/deviation previews, full disclosure, focused adjacent shipping drilldown and return focus, paging, takeover/handback, stale/revoked states, live refresh, themes, desktop and mobile. The final reviewed web image was rebuilt and activated on the existing local port 8080.

The real retained company cockpit independently showed four default deviation previews, business-readable activity names, registered operator use, six compact cases with complete totals, and the filters Still open / Taken over manually / All cases. Shipping handover counts advanced automatically from 29 to 34; the service read at 18:03:39 UTC confirmed 853 due, 34 handed over, 406 forecast and 819 at risk. Screenshots: `/private/tmp/reality-cockpit-live-final.png` and `/private/tmp/reality-cockpit-ux-final.png`. Existing exact action guards, source links and live observation semantics remain intact. No frontend business formula, source reinterpretation, historical handover backfill or new execution mandate was added. Aggregate enterprise-display timing, eight-hour real-time soak and rollout review remain open.

## Operating flow scope/design review

The owner's direct request authorizes FR-028–033 implementation. Message acknowledgement, reply, business completion, receipt, handover and return disposition remain distinct; missing provider completeness remains unknown. Open quantities and exceptions reuse canonical shared services. All five cards use complete-company counts, exact evidence and bounded displays, with explicit timing/units. No new schema, mandate or timer. Constitution Check PASS; no unresolved product clarification or CRITICAL requirement/plan/task finding. Existing rollout, enterprise and soak gates are not closed by this increment.

## Operating flows verification (2026-10-06)

FR-028–033 now have independent PostgreSQL and UI evidence. The final affected backend group passes **55 tests in 120.45 s**, covering local reply/ack lineage, duplicate and foreign replies, complete cohorts, partial/corrected receipts, physical return disposition, canonical stock risk, access/snapshot adapters and no implicit adoption. Log: `/private/tmp/reality-flows-backend-reviewed.log`. Frontend contracts pass **478/478**; final cockpit browser proof passes across desktop/mobile, four languages, themes, evidence links, unknown/stale states and retained shipping/deviation/case controls. Logs: `/private/tmp/reality-flows-contracts.log`, `/private/tmp/reality-flows-browser-reviewed.log`. Formatting, **2,994/2,994** localization keys in each language and production build pass. Local pending queues are labelled pending work rather than active execution; backlog curves disclose their displayed range and missing history stays unknown.

`make lint`, `make spec-check`, business annotations (668 described functions / 115 approved tests / zero missing), `git diff --check`, generated reference freshness and Docker API/MCP/web builds pass. Documentation freshness uses an isolated temporary index and object directory against prepared generated files; the real index/history/objects stay untouched. The plain working-tree check compares against the committed version and therefore reports the intentionally uncommitted generated changes; the isolated-index run proves regeneration introduces no further changes. Logs: `/private/tmp/reality-flows-quality-final.log`, `/private/tmp/reality-flows-docs-final.log`, `/private/tmp/reality-flows-compose-reviewed.log`.

The first per-message correlated reply query was rejected by local timings near 190 s and replaced with grouped same-company/system first-reply and acknowledgement joins. Canonical commitment terms are batch-read. The final independent complete cockpit observation at 18:30:09 UTC took **1.908 s** on the retained local demo; this is local verification, not a repeated enterprise workload or production capacity claim. It observed 501 open orders, 75 first-recorded orders and 48 physical dispatch records in the hour; 1,942 messages without recorded replies, 1,864 unacknowledged, 54 first replies and a **+21** reply-backlog change; two supplier promise lines still expected (both dates unknown), 21 fully received supplier lines; two canonical oversold-item risks; zero recorded physical return positions or announcements. Return counts do not infer return processing from customer messages. The fixed shipping cohort remains 853 due and 34 handed over; newer orders outside that reviewed plan remain separately inspectable rather than silently enlarging the authority.

The existing simulator and Claude supervisor remain running, without a new operator, credential, mandate, recurring queue, migration or history adoption. API/MCP/web activation on local port 8080 preserves the background workers. Expanded enterprise DOM/query load, separate eight-hour real-time soak and rollout review remain open. Final real-browser refresh and screenshot evidence follows below.

### Final live UI and layout receipt

All five cards are visible in the real retained company. Without navigation/reload, the observed time advanced from 20:31 to 20:32 Europe/Berlin, open orders changed from 504 to 503, dispatch records from 48 to 50 and unanswered messages from 1,945 to 1,946. Named access showed the retained Claude operator's recent approved tool use; four default shipping-deviation previews and all three shipping series remained present. The final layout uses three/two equal groups at 1440 px, all five cards side by side on wide displays, and a single column at 390 px. Both real desktop and mobile reads confirm five cards and no horizontal page overflow. The final fixture browser proof also asserts the grouped layout and passes (`/private/tmp/reality-flows-browser-layout-final.log`). Final web image build/activation pass (`/private/tmp/reality-flows-web-image-final.log`, `/private/tmp/reality-flows-web-final-activation.log`). Screenshots: `/private/tmp/reality-cockpit-flows-desktop-final.png`, `/private/tmp/reality-cockpit-flows-mobile-final.png`. Temporary viewport overrides were reset; the test-only port 5177 server was stopped. User-facing port 8080, simulator port 8768 and the existing Claude supervisor remain running. T046–049 are verified within this local increment; earlier enterprise/soak/rollout gates remain open.

The actual 1920 × 1080 responsive check also confirms all five flow cards on the same row and zero page overflow. Wide live screenshot: `/private/tmp/reality-cockpit-flows-wide-final.png`; retained artifact: `/Users/benediktsauter/.codex/visualizations/2026/10/06/01a10ffd-6b60-7800-bb0e-c8f98d6a29f1/operations-cockpit-live-wide.png`. The temporary viewport override was reset after capture.

## Visual consistency pre-implementation review

The owner explicitly requested the refinement and Head-of-UX review. The independent read-only reviewer identified duplicate 24px margin plus 20px parent gap, a standalone h2 missing the card heading rule, 3/5/4 metric rows causing offset charts, cramped live-panel headings and inconsistent general-action styling for view filters. FR-034–036/T050–052 specify the smallest presentation correction with explicit geometry, accessibility and regression acceptance. Constitution PASS, no schema/business/service/control/mandate change, no unresolved clarification. Existing enterprise/soak/rollout scope remains separate.


## Visual consistency verification (2026-10-06)

FR-034–036 and T050–052 are verified within this local presentation increment. The test-first browser run failed on offset order/message charts; a second independent narrow-content assertion failed because viewport-only breakpoints did not accommodate a docked panel. Shared content-sized grid tracks, common chart/note/evidence/footer slots, container-aware layout and unified selection/navigation styling resolve both failures. No fixed whole-card height, placeholder business metric, fabricated stock history or alternate business rule was added. An independent read-only UX review of the implementation and desktop/mobile screenshots found no blocking issue.

The final complete cockpit browser regression passes at 1440/1920/390 px, narrow 720/440 px content, all four languages and themes, keyboard selection, expanded evidence, stale/unknown states, source inspection, shipping series and existing takeover/handback guards. Log: `/private/tmp/reality-cockpit-polish-browser-final.log`. Frontend contracts pass **478/478**, formatting passes, localization covers **2,995/2,995** keys in each language, and production build passes (`/private/tmp/reality-cockpit-polish-web-gates.log`). Lint/spec/annotations pass with 668 described functions, 115 described tests and zero missing (`/private/tmp/reality-cockpit-polish-quality.log`). Generated documentation was regenerated and freshness passed using the isolated temporary index/objects baseline; the actual index/history/objects remain untouched (`/private/tmp/reality-cockpit-polish-docs.log`).

The final local web image build passes (`/private/tmp/reality-cockpit-polish-web-image.log`); only web was recreated with `--no-deps`, and port 8080 returned HTTP 200. API/MCP, scheduler/workers, the simulator and sole Claude supervisor were not restarted. The retained real-company browser confirms identical primary-metric starts and chart slots across all five wide-display cards (0 px difference); the three desktop SVG chart starts also match exactly. Both selection groups are 44 px high. At 390 px all five cards use natural-height single-column layout, with no card or page horizontal overflow. Actual lower-page inspection confirms grouped filters, bounded deviations and six-case paging.

Automatic observation remained active: without another reload the local observation advanced from 20:44 to 20:45 Europe/Berlin, open orders changed from 506 to 507, recorded first replies from 43 to 44 and recent business-object activity from 53 to 54. Shipping still exposes its reviewed plan, 34 confirmed handovers and live forecast. Saved actual UI evidence: `/Users/benediktsauter/.codex/visualizations/2026/10/06/01a10ffd-6b60-7800-bb0e-c8f98d6a29f1/operations-cockpit-polished.png`, `/private/tmp/reality-cockpit-polish-wide.png` and `/private/tmp/reality-cockpit-polish-mobile.png`. Temporary viewport overrides were reset and the fixture-only port 5177 server stopped. Business scope, data semantics, action permissions and live lifecycle are unchanged. Earlier enterprise-display/soak/rollout gates remain open.


## Central status overview scope/design review

The owner asks to make existing condition signals centrally visible. FR-037–038 preserve FR-032's canonical meaning, including neutral ordinary work and explicit unknown coverage. No summary score or new business threshold is inferred. The display reuses identical service observations and area definitions. Direct owner authorization covers this small local UI refinement; Constitution PASS, no unresolved clarification or critical scope conflict. T053–055 map both requirements to test-first implementation and complete UI/live verification.


## Central status overview verification (2026-10-06)

FR-037–038/T053–055 are verified for this local presentation increment. Test-first browser proof failed on the absent central overview (`/private/tmp/reality-status-red.log`). The final complete cockpit browser proof passes placement before shipping, all five canonical states, exact primary-metric parity, keyboard anchors, stale/missing unknown status and absent metrics/no dead links, four-locale/theme desktop/mobile/narrow layout, existing shipping/case/evidence behavior and exactly the original two reviewed test mutations. Log: `/private/tmp/reality-status-browser-final.log`. The fixture restores its explicit harness URL for isolated state resets rather than reloading an application URL generated by existing navigation.

Frontend formatting, **478/478** contracts, **2,999/2,999** audited localization entries per language and production build pass (`/private/tmp/reality-status-web-gates.log`). Lint, spec and business annotations pass (668 described functions, 115 described tests, zero missing; `/private/tmp/reality-status-quality.log`). Generated references are fresh against the prepared changes using temporary index/objects, without touching the actual Git index/history/objects (`/private/tmp/reality-status-docs.log`). The final web image build and web-only activation pass (`/private/tmp/reality-status-web-image.log`, `/private/tmp/reality-status-web-activation.log`); port 8080 returns HTTP 200.

Actual retained-company inspection confirms five prominent status tiles immediately under the live observation and above shipping: orders critical with 509 open orders, messages ordinary pending work with 1,956 without recorded reply, supply unknown with two expected lines, stock critical with two uncovered-demand items, and returns no finding in the evaluated scope with zero pending physical positions. Status is accompanied by text and uses the exact existing service signal, not a new company-health or agent-quality score. The native keyboard message link focuses `cockpit-flow-messages` at the 80px header offset and retains the cockpit context. The 390px real page and all five tiles have no horizontal overflow. The reviewed plan/confirmed-handover/forecast shipping panel remains present (853 due, 34 handed over, 346 forecast at this observation).

Actual desktop screenshot: `/Users/benediktsauter/.codex/visualizations/2026/10/06/01a10ffd-6b60-7800-bb0e-c8f98d6a29f1/operations-cockpit-status.png`; mobile: `/private/tmp/reality-status-mobile.png`. Temporary viewport override was reset. Only web was recreated; the existing simulator, sole Claude supervisor, API/MCP and background roles remain running. No additional timer, request, business computation, mutation, schema or mandate was introduced. Final review against FR-032/037/038 and the Constitution finds no scope or authority conflict. Earlier enterprise/soak/rollout gates remain open.


## Permanent navigation scope/design review

The owner explicitly requests discovery of the destination regardless of prior URL use. Actual fresh-root inspection resolves to Acme Bikes GmbH while the retained cockpit uses Live Company Simulator. Capability relies on the canonical business-company/active-member guard; the default company does not provide operational availability to the current viewer. The narrow fix separates navigation discovery from operational availability: retain the always-visible destination and explain unavailable context, while preserving all backend gates. FR-039–040 intentionally supersede prior hidden-entry behavior only; Home remains default, permissions are unchanged and no remembered-company preference is introduced. Constitution PASS and no unresolved clarification.


## Permanent Control Tower navigation verification (2026-10-06)

FR-039–040/T056–058 are verified in the local frontend increment. A complete root-entry fixture first restores the existing playground-entry read; the meaningful pre-implementation proof then fails with zero permanent Control Tower links (`/private/tmp/reality-tower-red.log`). The revised full-shell browser proof passes root/Home discovery, same-company capability gating, enabled-company operational navigation, unchanged Home, on-demand chat and cleared company context, disabled/failed availability without operational reads, a permitted Inbox return and unchanged order/case/source/return context (`/private/tmp/reality-tower-shell.log`). The complete cockpit browser regression also passes, including its four-locale/themes/responsive/traffic-light/alignment/control/source/stale/unknown scenarios (`/private/tmp/reality-tower-cockpit.log`).

All **478 frontend contracts** pass in `/private/tmp/reality-tower-web-gates.log`. The initially unregistered invariant English workspace name was correctly rejected by the audit. Control Tower is now explicitly registered with its FR-040 product-name reason in the existing invariant catalog; no generic translation rule was relaxed. The final affected audit tests pass **5/5**, all four languages cover **3,002/3,002** audited entries, complete formatting and production build pass. Final repair command exit 0; build log `/private/tmp/reality-tower-build-final.log`. Lint, spec and business annotations pass (668 described functions, 115 described tests, zero missing; `/private/tmp/reality-tower-quality.log`), and generated references are fresh against prepared changes using isolated index/objects (`/private/tmp/reality-tower-docs.log`). The actual Git index/history/objects remain untouched.

Docker web build and web-only activation pass (`/private/tmp/reality-tower-web-image.log`, `/private/tmp/reality-tower-web-activation.log`), and fresh port 8080 returns HTTP 200. Actual root entry still selects Acme Bikes GmbH (`ten_fb7f9595f3`) and now immediately displays the permanent Control Tower destination. Opening it displays the truthful unavailable-current-company explanation with the existing company menu and Inbox return. Choosing the exact retained Live Company Simulator (`ten_29a7b31670`) through that menu opens its operational view, with Control Tower in both shell/page titles, all five flow areas, the status overview and protected shipping/case/agent panels. No default company, company purpose, membership, mandate or persisted preference was changed.

Actual desktop screenshot: `/Users/benediktsauter/.codex/visualizations/2026/10/06/01a10ffd-6b60-7800-bb0e-c8f98d6a29f1/control-tower-navigation.png`; unavailable-company screenshot: `/private/tmp/reality-tower-fresh-unavailable.png`; actual 390px mobile screenshot: `/private/tmp/reality-tower-mobile.png`. Mobile retains the new title and destination with zero page overflow; temporary viewport override was reset and the extra root-review tab closed. The retained live observation advances automatically (19:02 to 19:03 UTC); simulator/Claude/API/MCP/background roles were not restarted. Only the fixture-only port 5177 server was stopped after verification. Final review finds the permanent discovery change within owner-authorized scope, with canonical availability and tenant boundaries intact. Earlier enterprise/soak/rollout gates remain open.


## Workspace surface scope/design review

The owner's Light-mode screenshot shows a grey canvas inset absent from ordinary company workspaces. `.operations-cockpit` explicitly uses `--bg`, whereas the company shell/header/workspaces use `--surface`. FR-041 changes this single semantic role in both themes while preserving purposeful shared neutral detail/selection surfaces and the enterprise card grouping. Direct owner authorization covers this correction; no unresolved clarification, schema, business rule, global appearance preference or mandate change. T059 precedes T060 and T061.


## Workspace surface verification (2026-10-06)

FR-041/T059–061 are verified for this presentation-only follow-up. The test-first computed-style proof failed with the Light canvas `rgb(248, 250, 252)` against the common workspace surface `rgb(255, 255, 255)` (`/private/tmp/reality-surface-red.log`). Changing only `.operations-cockpit` from `--bg` to `--surface` resolves the mismatch. The complete existing cockpit browser proof passes, including four languages, light/dark, responsive geometry, neutral selection/explanation surfaces, expanded calculation basis, all shipping series, source links and reviewed case controls (`/private/tmp/reality-surface-browser.log`). All 478 frontend contracts, complete Prettier validation, production build, lint, spec policy and diff whitespace checks pass; build log `/private/tmp/reality-surface-build.log`. No localization key, business read/tool, schema, scheduling, global theme token or control policy changed, so generated tool reference content is unaffected.

The existing Docker web image was rebuilt and only web was recreated with `--no-deps` (`/private/tmp/reality-surface-web-image.log`, `/private/tmp/reality-surface-web-activation.log`). Real port-8080 Light inspection shows identical white canvas/header/cards; Dark inspection shows identical `rgb(16, 24, 40)` canvas/header. All five operating areas and all three shipping series remain present. The observation advanced from 19:14 to 19:15 UTC, with open orders from 518 to 519 and unanswered messages from 1,959 to 1,960. Light screenshot: `/Users/benediktsauter/.codex/visualizations/2026/10/06/01a10ffd-6b60-7800-bb0e-c8f98d6a29f1/control-tower-light-consistent.png`; Dark screenshot: `/private/tmp/reality-surface-dark-live.png`. The temporary Light choice was restored to the original System preference. The retained cockpit tab remains available; the fixture-only server is stopped. Simulator, Claude, API/MCP and background roles were not restarted. Final review confirms the single surface-role change and preserved neutral detail/selection roles; earlier enterprise/soak/rollout gates remain open.


## Case takeover entry scope/design review

The owner asks to raise and clarify existing whole-case takeover, not to change case policies or stop actual work. The narrow design places a compact bounded responsibility entry before shipping while revealing the same adjacent register on demand. Explicit copy distinguishes automated ownership, confirmed human takeover and actual completion; detailed confirmation retains related-case/started-action disclosures. Counts retain complete-register semantics and human view includes completed work. Direct owner authorization covers this scope. No unresolved clarification, Constitution exception or additional execution mandate. FR-042–044 map to ordered T062–064, with failing proof first.


## Case takeover discoverability verification (2026-10-06)

FR-042–044/T062–064 are verified for the owner-authorized frontend refinement. Test-first placement failed because takeover followed shipping (`/private/tmp/reality-case-entry-red.log`). The existing register now appears once between status and shipping as a bounded, initially collapsed entry. The density proof explicitly restores this new routine collapsed state after exercising the keyboard/count shortcuts. Full cockpit browser proof passes compact placement, keyboard disclosure, human/open-work shortcuts, bookmarked context, preserved draft on close/reopen, original exact takeover/handback, four-locale/theme/mobile/narrow geometry, all shipping/evidence/deviation/flow behavior (`/private/tmp/reality-case-entry-browser.log`). The complete shell regression passes (`/private/tmp/reality-case-entry-shell.log`). Eight controlled hours pass with bounded requests and retained inspection/review through quiet intervals, rollover, hidden/recovery/failure and company changes; zero browser errors (`/private/tmp/reality-case-entry-session.log`). This remains simulated-time proof, not the outstanding real-time rollout soak.

Complete Prettier validation, all 478 frontend contracts, 3,005/3,005 audited entries per language and production build pass. Final affected-file formatting passes (`/private/tmp/reality-case-entry-final-format.log`), as do lint/spec policy and diff whitespace (`/private/tmp/reality-case-entry-lint.log`, `/private/tmp/reality-case-entry-spec.log`). No service, tool/schema, polling, mandate or mutation contract changed; generated tool references are unaffected. The existing web image build and web-only `--no-deps` activation pass (`/private/tmp/reality-case-entry-web-image.log`, `/private/tmp/reality-case-entry-web-activation.log`).

Actual port-8080 observation confirms the collapsed entry before shipping, 827px entry width at the natural 915px viewport, no page overflow, all five operating areas and all three shipping series. It shows 184 automatic cases and one existing manually owned case. The human shortcut returns `LIVE-f1ad500666008054` with manually owned/automation stopped and open work; this verification performs no takeover or handback. The default outstanding-view disclosure was collapsed again, and the retained tab remains available. Screenshot: `/Users/benediktsauter/.codex/visualizations/2026/10/06/01a10ffd-6b60-7800-bb0e-c8f98d6a29f1/control-tower-case-entry.png`. Observation advanced from 19:24 to 19:25 UTC during this read-only check. No appearance preference/viewport changed, and simulator/Claude/API/MCP/background roles were not restarted. The fixture-only server is stopped. Final scope review confirms truthful existing counts, existing supported case scope, full confirmation safeguards and preserved Source/Evidence/Reality links. Earlier enterprise/soak/rollout gates remain open.


## Classic palette pre-implementation review (2026-10-06)

The owner explicitly requested green/red/orange instead of blue/grey in the company status. FR-045 supersedes FR-037's former five-color presentation without changing FR-032's canonical business meaning. Unknown and pending conditions stay distinguishable by text, never claim health or execution, and never render green. Plan/tasks align with existing fixture and real-company verification; no unresolved clarification or CRITICAL consistency finding. All Constitution rows PASS. Tests precede the styling change; completion remains pending evidence.


## Classic palette verification (2026-10-06)

The new computed-style browser assertion first failed against the previous attention color (187/124/36 versus required orange 217/119/6). The complete existing cockpit browser regression then passed with summary dots/borders and detail dots matching red/orange/green for all five canonical signals, stale unknown coverage, both themes, four locales and responsive widths. Distinct labels, metrics, evidence navigation and responsibility controls remain unchanged. All 478 frontend contracts pass; localization covers 3,005/3,005 used strings in each of four locales. Whole-web formatting, TypeScript/Vite build, spec policy and whitespace checks pass. Only web was rebuilt and recreated locally; no simulator, Claude, API/MCP, source data or approvals were changed. No generated catalog work is required for this presentation-only change.

Actual port-8080 company verification retains critical orders/stock in red, pending messages and incomplete supplier evidence in orange and evaluated-clear returns in green, with the new German legend. The original System theme preference was preserved. Screenshot: `.codex/visualizations/2026/10/06/01a10ffd-6b60-7800-bb0e-c8f98d6a29f1/control-tower-classic-traffic-lights.png` under the owner's home directory. Earlier backend/enterprise throughput, soak and rollout gates remain open; this is scoped presentation evidence only.

## Current-main PR integration review (2026-10-06)

The owner requested a review-ready PR. Work is isolated on
`codex/enterprise-control-tower`, based on current main `bb74d120`; the running
local simulator and operator checkout are preserved. Local runtime files, tokens
and database backups are excluded.

Analysis found two blocking integration inconsistencies: the new register still
required historical owner adoption, and the shipping-input revision collided with
current-main migration 0145. The spec, plan, contracts and integration tasks now
retain spec 377 default coordination and place migration 0146 after 0145. All 50
FR/DR requirements have task coverage, with separate paths for seven success
criteria. No unresolved clarification or Constitution exception remains; earlier
real-time-soak and aggregate enterprise-display acceptance remain explicit gates.

The default-coordination regression failed on hidden accepted work before repair.
The register now returns existing cases without CaseAdoption and includes canonical
read-only rollout readiness, preserving scalar/batched evidence and confirmed
member takeover. The UI reuses existing migration/reconciliation explanations.
Combined catalogs retain 214 commands, 103 events and 728 tenant-classified
operations, including current-main operational status and intake completeness.
The legacy arrival regression now verifies handover first and later delivery,
matching the approved source-backed carrier contract rather than conflating them.

Spec policy and Ruff pass. The populated four-locale/theme/responsive cockpit
browser proof and full-shell navigation proof pass on the combined checkout.
Complete backend, frontend, live-browser and documentation results are pending;
this record does not mark aggregate acceptance or production readiness complete.

### PR validation refinement

Frontend formatting, 478 contracts, 3,003 keys per locale and production build pass.
Document generation now uses the actual formatting runtime, removing unrelated
raw-output churn; documentation contracts/build and tooling checks pass. The first
PR documentation job reproduced the raw-versus-formatted output difference.
The controlled-session harness now excludes host wall time while keeping the exact
eight-hour progression and request/memory/state assertions; it changes no runtime
behavior. A local live journey hit its unchanged migration timeout under concurrent
load; the same journey passes in CI, including absence of legacy owner activation.
The complete final-head CI result remains required before review readiness.
