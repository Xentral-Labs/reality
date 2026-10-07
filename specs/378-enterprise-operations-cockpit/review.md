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

The corrected controlled session passes all eight simulated hours, 5,747–5,753
observation reads per endpoint and zero browser errors. The final targeted group
isolated two fixture assumptions (wall-time ordering and default-linked planning
history); both regressions pass after fixture-only corrections, retaining the
55-query budget and explicit no-causal-response/provider-outcome guarantee.
The final-head complete CI result is the remaining PR readiness gate; the PR
records that evidence without representing the separate pilot soak as complete.

The complete browser matrix exposed a stale Storyline assertion that expected
Inbox and Chat to be the first two navigation links. FR-039 requires the persistent
Control Tower destination before them. The regression now asserts all three links
in order while preserving the existing Chat navigation and selected-page checks.
This updates the integration fixture to the approved navigation requirement and
changes no product behavior. The repaired full Storyline browser script passes
locally, as do formatting, spec policy and whitespace checks. The final-head
matrix remains the readiness gate.

Full backend shard 3 found a repository-layout wording regression in the coverage
matrix: prose abbreviations used the forbidden legacy path token `backend/`.
The documentation now spells out backend and browser regressions and backend JSON
workload; measured outcomes are unchanged and the path invariant is not weakened.
Spec impact: none; documentation wording only. The existing layout regression
first reproduces the failure, then all nine repository-layout tests pass after
the prose correction. Remaining final-head backend gates must pass before review
readiness.

Full shard 2 isolated two more legacy opt-in integration artifacts. The additive
flow test now asserts default coordination, exact canonical readiness and unchanged
company-scoped event/proposal/adoption/rollout/case counts instead of requiring a
false compatibility flag. The orphaned `case_already_adopted` refusal is removed,
matching current main and the executable refusal inventory. Neither correction
reintroduces activation, writes during observation or a new authority boundary.

Full shard 1 found the same default-coordination assumption in enterprise fixture
setup: canonical plan acceptance already binds cases, then a legacy bulk seed
tried to create a second case for the same order. The fixture now preserves
canonical identities/links and inserts only missing accepted-history fixture
cases, asserting exactly 110,000 cases. Legacy activation is removed. All
10,000 active / 100,000 historical / 500,000 observations, ten readers, query and
latency limits, full totals and sustained committed-change proofs are unchanged.
The complete suite has now finished; its remaining findings are confined to
these repaired default-coordination integration fixtures/vocabulary.

All 15 affected operating-flow/refusal-inventory tests pass locally. Ruff, spec
policy and whitespace checks pass; canonical documentation regeneration introduces
no generated-file change. The corrected full enterprise profile is still running
against isolated PostgreSQL; its unchanged limits and the final-head complete CI
remain required before marking the PR ready.

The corrected local full workload reaches its real observations and exposes a
performance failure (cold 12.988 s, ten-reader p95 19.231 s, committed-change
13.613 s). Source/action totals are correct; no threshold is relaxed. The bounded
register currently joins large shared original action input/output for each case.
SC-004/T036/T071 plan a snapshot-only equivalent projection, exact scalar parity
and a meaningful large shared-action regression before implementation. Constitution
Check PASS; no schema, business rule, mutation authority or persisted cache change.

The shared large-action regression first fails specifically on opaque invocation
input transfer, then passes with the equivalent projection. All 32 affected
case/flow/snapshot tests pass, including original per-case proposed-review
obsolescence, executing totals, privacy/limit boundaries and the unchanged
55-query budget. Stored original invocation input remains lossless and available.
Canonical documentation generation has no output change; lint/spec/whitespace
checks pass. Full enterprise latency and final-head complete CI remain pending.

The late-day local workload reproduces a fixture-time failure before latency
measurement: its fourteen-minute canonical setup consumes more than the spare
capacity in the remaining same-day window (9,932 forecast instead of 10,000).
The shipping reader already accepts an explicit business observation instant.
Pin that instant to fixture capture only in this profile; retain real monotonic
latency, real concurrent PostgreSQL writes, all volumes and all limits. This
restores a reproducible business scenario independently of runner time, without
changing forecast rules or product behavior. Spec impact: none. Constitution
Check PASS; the observed failing scenario supplies the regression evidence.

The measured profile attributes the remaining read cost to historical ORM
materialization in operating flows and exception inputs. Refine only clean
cockpit snapshots: use the canonical delivery SQL expressions for complete
open/supplier-received cohorts, and scope the commitment exception inputs to
the exact open promises that its derivator evaluates. Other exception classes
retain separate original scopes, and ordinary callers retain ORM semantics.
Test scalar/snapshot full DTO parity and absence of historical promise ORM
materialization first; then rerun unchanged enterprise and full CI gates.
Spec impact: none; equivalent read projections only. Constitution Check PASS.
No new rule, schema, retained cache, case family or mutation authority.

Measured shipping/site reads currently repeat independent company-wide flows.
Place those flows in the existing authorized activity snapshot instead, and lift
its existing UI lifecycle to the page to serve status, flow and activity panels.
Retain four read lifecycles, current timestamps, stale/access isolation, filter
separation and stable child investigation state. No timer/endpoint/schema/rule or
cache is added. FR-033/contracts now explicitly define the observation boundary.
Test activity flow authority/absence from shipping first, then fixture/all-day
UI and unchanged four-read enterprise cadence. Constitution PASS; no unresolved
clarification or critical review conflict.

The full forecast currently transports one point per completion slot (10,000 in
the declared profile). FR-023 now makes the bounded daily curve explicit: keep
small exact-event series; aggregate dense series into exact cumulative counts
at five-minute boundaries, including endpoints, and disclose resolution. Count
every source-backed order before projection; retain full fingerprint and exact
supporting-order/evidence readers. This is chart aggregation, not cohort sampling
or invented handover times. Test independent dense-series counts, duplicate
times/opening/end/out-of-window behavior before implementation. Constitution
PASS; no business rule/schema/authority/cache change or unresolved clarification.

The full targeted quantity/exception/case/flow selection passes 305 tests. Its
source-inspection assertion ran while source offsets changed and failed on stale
loaded code; the unchanged test passes in a fresh process. The final 24
activity/flow/snapshot tests pass. All 44 shipping/curve tests pass, including
independent dense cumulative counts. The complete cockpit browser proof and
production web build pass, including explicit independent stale states and
localized curve-resolution disclosure. Lint/spec/annotations and generated
references pass. No performance limit was raised. Held-fixture diagnostics
reduce response size from 373,336 to 109,565 bytes and ten-reader p95 from
4.442 to 3.742 s on the concurrently loaded local stack; these are diagnostics,
not a fresh accepted enterprise run. Final-head full CI, controlled session and
unchanged enterprise timing remain required before readiness. Final exact-head
results will be recorded in the PR body; real-time soak/UI aggregate pilot gates
remain separate.

Exact-head CI confirms every other gate, but SC-004 remains red at 3.235 s p95
(3.075 s cold; 3.087 s committed-change visibility). Preserve the unchanged
three-second limit. The source basis currently transfers original/current
metadata twice and joins the entire source table before selecting latest stream
versions. Replace these with one tenant-correlated LATERAL latest-version read
using the existing stream/version index. Preserve complete original/current
metadata, missing-reference and intake/current-required refusals. Existing
source/version/snapshot proofs precede the equivalent query refinement; inspect
its full-profile query plan and rerun complete CI. Spec impact: none, no new
rule/schema/cache/authority. Constitution Check PASS.


The final exact-head profile passes opening/site p95 (2.976 s) and committed
visibility (2.928 s), but its four-read live cadence fails at 9.847 s in cycle 2.
A newly accepted unreserved order activates commitment exception trace loading:
that snapshot still materializes every historical Document/Source/Line before
returning one current risk. Profiled activity rises from 1.960 to 7.211 s after
one real canonical order commit. Restrict only the existing open-commitment input
scope to its exact referenced documents, lines and original source metadata;
leave all other class scopes and ordinary readers unchanged. Add independent
scalar/snapshot risk/source-trace parity and historical payload/materialization
proof first, then rerun unchanged live cadence and complete CI. Spec impact:
none; equivalent read projection under DR-005/SC-004. Constitution Check PASS;
no rule, source mutation, retained cache, schema or authority change.


The actual UI never reads the shipping snapshot's duplicate `supported_cases`:
its always-mounted responsibility panel already owns the independently authorized
case-register lifecycle. Remove that redundant shipping calculation/field, retain
the exact full register and case-linked deviation explanations, and explicitly
define the independent authority in FR-033/contracts. Complete case counts remain
asserted in every register request of the unchanged ten-observer four-read live
profile; add the same full-count proof outside the shipping-only opening samples.
No request, reader, live cycle, volume, limit, business claim or UI state is removed.
Test that shipping does not invoke the register, and that the independent register
retains complete evidence/counts, before implementation. Constitution Check PASS;
no new authority, schema, timer or retained cache.


Refine the reviewed trace cohort further to exactly the current finding IDs,
collected before the existing three shared evidence reads. Ordinary derivation
retains immediate traces; clean snapshot derivation fills the same immutable
finding DTOs after its complete calculation. This avoids loading all 9,000 open
orders to explain one unreserved arrival while retaining bounded queries when
all promises are risky. Use existing full scalar/snapshot trace equality and a
many-current-risk bounded-query regression; no findings or source links change.
Case-linked shipping deviations also reuse the existing bounded original-action
projection for their at-most-50 exact cases, and then preserve their existing
six-action presentation limit. Constitution PASS; equivalent reads only.

The historical-trace regression first fails on eighteen retained historical
evidence/source objects. Final one/61-current-risk variants pass with exact
scalar/snapshot trace equality, no historical evidence/payload materialization
and the unchanged bounded query assertion (four passes). All 52 affected
flow/cockpit/control/snapshot regressions pass. The broader exception selection
passes 289 tests before the final exact-finding allocation; full final CI remains
the definitive regression gate. Independent responsibility authority and no
duplicate shipping register pass. First cold read, all four live request types,
480 requests/twelve real canonical writes, volumes and every latency/query limit
remain unchanged. Lint/spec/annotations and generated references pass. No UI
code changed, no target was raised and no real-time/pilot gate is closed.

SC-004 requires reported hardware and cold/warm measurements. Retain the
existing exact printed JSON measurements as JUnit properties for successful and
failing CI runs, including every live epoch and final visibility; normal pytest
capture otherwise omits passing measurements. This changes only verification
artifact reporting, not product behavior, scenario data, time or acceptance.
Spec impact: none; no additional business authority or Constitution exception.

The ce5a2be6 exact-head CI retains all functional/browser gates but fails the unchanged opening/site p95 at 4.134 s (cold 3.142 s); live cadence is not reached. Local complete-cohort profiling attributes substantial allocation to 10,000 duplicated readable readiness dictionaries and their JSON. Review FR-046 before implementation: hash every canonical readiness field with a declared v2 representation, and materialize the unchanged public readable shape only for disclosed preview/selected details. No cohort/fingerprint input, threshold, reader, write or cadence is removed. Add failing allocation and complete-field proofs first, preserve existing normal/snapshot parity, then rerun full acceptance. Constitution Check PASS.

The new allocation proof first fails because all 63 healthy orders materialize readable readiness instead of the disclosed fifty. The canonical-field proof first fails because no v2 fingerprint exists. After implementation all 82 shipping/plan/cockpit regressions pass, including complete normal/snapshot evidence equality, all 61 deviations and full supporting pagination, fifty-only healthy overview materialization, every declared readiness field in the hash and field-change sensitivity. Canonical lint/spec/annotations/generated-reference checks pass. A concurrent local full-cohort diagnostic is not acceptance evidence; unchanged exact-head CI remains required.

32ddbe91 complete CI passes every functional/browser/installer gate and all twelve live cycles (<4.420 s), opening/site p95 2.240 s and final visibility 4.735 s. Only live-read p95 fails at 4.047 s. A retained-cohort forty-reader diagnostic attributes 3.591 s to shipping, 2.455 s to flow observation and 1.777 s to responsibility; serial profiles expose 9,001 open Commitment ORM instances and full physical shipment/package objects. Review equivalent clean metadata projections and scoped canonical grouped net fulfillment before implementation; tests first, no volume/reader/cadence/limit change. Aggregate acceptance remains open.

The four-reader profile also exposes repeated company/member/user reads for all forty callers. Authorize only a query-shape refinement owned by canonical `_member`, never a separate cockpit policy: fresh exact joined predicates plus refreshed membership identity; preserve before/after checks for every caller, including waiters and owner-only access. Query-budget and committed stale-identity revocation tests precede implementation; existing ordinary/mutating readers remain unchanged. Constitution PASS; no authorization sharing, retained cache or business mandate.

The fresh access proof first fails on five SELECTs and retained private user/company ORM state; one fresh canonical joined read passes all 44 authority/cockpit/control regressions, including committed stale user/company/role revocation and independent waiting callers. Final review adds exact ordinary refusal parity: unknown company first fails on changed error code, then preserves canonical tenant lookup only on a denied read. No successful access is cached or shared. The allocation suite passes 131 scenarios; its invalid extra-shipment test setup is repaired to a canonically admitted linked/unlinked full shipment, whose two full-evidence parity variants pass. All final 56 shipping/domain/story tests pass, including an independent seven-microsecond/three-slot rounding oracle. Lint/spec/annotations/generated references pass; local diagnostics run alongside the original busy simulator/operator and remain non-acceptance evidence. Complete CI still must pass unchanged limits.

After the exact refusal repair, all 28 final snapshot/adapter regressions pass, including unchanged error code/values for missing company/user/principal. The positive access check remains one query and retains no private user/company ORM state. All 56 final shipping/domain/story regressions pass after exact integer-ceiling/singleton allocation refinement; completion-slot-v1 and every original threshold/cadence remain unchanged. Full exact-head CI is the final gate.

The 7f70603a exact-head run passes all functional/browser/installer gates, all twelve cycles (maximum 4.117 s), opening/site p95 2.573 s and final visibility 4.542 s. Live-read p95 alone remains red at 3.953 s; preserve the three-second limit. Complete-cohort profiling shows repeated SQL row attribute resolution and per-promise correlated revision lookups in the live fulfillment cohort. Review equivalent immutable tuple metadata allocation and canonical latest-stated-value relations before implementation. Preserve every field/type, same-company revision order/null fallback, complete cohorts, all four readers, real writes and all original limits. Spec impact: none; restore SC-004 using existing DR-005 semantics. Add metadata-boundary and independent revision/correction parity proofs first. Constitution Check PASS; no authority, cache, domain policy, schema or cadence change.

Retain per-reader p95 alongside the unchanged aggregate enterprise measurements in JUnit, so any remaining cost is attributable to overview/register/activity/access rather than inferred from a diagnostic host. Reporting only; no workload, timing clock, assertion or policy changes.

All 131 affected allocation/revision/shipping/stock/responsibility regressions pass after repairing the iterator's explicit full-cohort materialization. The same immutable metadata allocation also applies to the already-reviewed clean finding/stock projections; original Item objects and ordinary readers are unchanged. Repeat their full scalar/snapshot parity selection on the final code, then unchanged enterprise CI.

The final immutable finding/stock projection passes all 44 scalar/snapshot flow and stock regressions. Together with the prior 131 affected regressions, exact typed metadata, revision ties/null fallback, movement corrections, quantities, evidence, access and responsibility remain covered. Canonical lint, Spec Kit policy, business annotations and generated-reference freshness pass. Full exact-head CI and unchanged enterprise limits remain required; aggregate real-time/browser pilot gates remain open.

The f98f7479 exact-head run passes every functional/browser/installer gate, opening/site p95 2.011 s, all twelve live cycles (maximum 3.383 s) and final visibility 4.796 s. Aggregate live p95 remains red at 3.258 s. Per-reader p95 isolates overview 3.335 s; register 1.765 s, activity 2.401 s and access 0.214 s already pass. Review equivalent shipping allocation only: query a source stream's newer versions rather than retransmitting the same original's current metadata; preserve exact latest metadata and all current-intake refusals. Hash the same acyclic typed v2 basis with byte-identical standard JSON, and select deviation detail IDs after full calculation without sorting/materializing healthy detail pairs. Every canonical readiness/input, full cohort, hash field, supporting record and original limit remains unchanged. Existing full source/version/allocation/scalar parity and an independent standard-v2 byte oracle precede implementation. Constitution PASS; Spec impact: none under DR-005/FR-046/SC-004; no schema, policy, retained cache or authority change.

The shipping read also transfers every unused field of two large immutable plan-review bases. Review a private clean-read projection containing every original source key and every original commitment's quantity-revision binding. Preserve empty/null binding truth and legacy fallback shapes; current canonical terms/full current source metadata still determine the observation. Original full Action input and all normal/mutating review/execution paths remain unchanged. Test complete scoped metadata against the retained original review first, plus exact normal/snapshot result/fingerprint/supporting parity and existing original-source refusals. No key cohort is sampled; this is allocation under DR-005, not a reduced approval or new authority. Constitution PASS; Spec impact: none.

The standard-v2-byte/current-source oracles pass before implementation (three tests). The private review-header allocation first fails while absent. PostgreSQL CASE/subscript syntax is repaired with explicit JSONB operators; all nine targeted projection/large-binding/legacy/source/snapshot proofs pass. The final full shipping/source/domain/story/cockpit/snapshot selection passes 118 tests. A retained complete 10,000-source comparison preserves every original/current field against the committed query. Canonical lint/spec/business-annotation/generated-reference checks pass. Repeated retained-cohort reads remain diagnostic only alongside the untouched original simulator/operator; they do not close enterprise latency or real-time/browser pilot gates. Full exact-head CI still must pass original limits before readiness.


The cc4d599d exact-head run passes every functional/browser/installer gate,
opening/site p95 1.852 s, all twelve live cycles (maximum 3.168 s), and final
visibility 5.051 s. Aggregate live p95 alone remains red at 3.062 s; overview
p95 is 3.120 s. Preserve the original three-second limit and complete workload.
Profiled complete shipping inputs still allocate unused cohort filters for
preloaded canonical promises/documents, and repeat ORM row-processing for fresh
scalar-only metadata. Review equivalent allocation only: build unused statements
only in their actual read branch, and execute selected scalar metadata through
the same Session-owned transaction Connection only in a clean consistent
snapshot. Ordinary/dirty readers retain Session execution/autoflush; no ORM
entity query changes. Independent exact typed-value/transaction/dirty-state
and preloaded canonical parity regressions precede implementation. Spec impact:
none under DR-005/FR-046/SC-004. Constitution Check PASS; no authority, source,
schema, field, cached observation, query workload, cadence or threshold change.

The private scalar Connection result is fully buffered once within its current read call, preserving every row, label and value while avoiding one driver fetch call per row. The result is consumed only by its original caller; no shared/completed result is retained. Existing typed metadata, same-transaction and ordinary/dirty Session proofs cover this allocation boundary.

The new regressions first fail on unused promise/document cohort construction and the absent private execution boundary; the fixture is corrected to canonical composite tenant identity before accepting that failure. Both then pass with exact scalar terms/readiness and pending-state autoflush. The full affected selection passes 133 shipping/source/domain/story/cockpit/snapshot/readiness/delivery-policy tests. After final call-local buffering, all five targeted typed-transaction, dirty/ordinary Session, preloaded, scalar-readiness and full observation/fingerprint proofs pass again. Canonical lint/format, Spec Kit policy, business annotations and generated-reference freshness pass. Original workload/cadence/query/latency limits are unchanged. Full exact-head CI remains the final readiness gate; the real-time soak and aggregate browser/display pilot gates remain open. The separately requested instrument-dashboard concept is not part of this functional PR.


## Instrument console follow-up review — 2026-10-07

Scope: FR-047–051, T082–T086. All five requirements have implementation and proof
coverage. Identifiers were rebased onto the merged feature's existing FR-046 and
T081 boundaries before final review. No critical unresolved finding remains in this
bounded increment. The custom requirements-quality checklist stays reviewer-owned;
it does not claim execution acceptance or close earlier pilot/enterprise gates.

Review preserves canonical area conditions, exact first-reply authority, nullable
coverage, physical-record units, source drill-through, four shared live reads and
reviewed whole-case controls. Decorative strips never claim risk fractions. Finance
and stock history are explicit limitations. A legacy CSS rule's metric-row spacing
was corrected with stronger component scoping and a responsive regression assertion.
The local obsolete migration-chain repair is deployment compatibility only, recorded
with backup and exact frozen-DDL parity in quickstart; no source migration was added.


## Preview parity refinement review — 2026-10-07

FR-052–056 explicitly supersede the earlier register placement and decorative uniform
meter. Every new requirement maps to T087–090 and executable service/browser proof;
no critical artifact conflict or unresolved clarification remains. The service uses
already loaded tenant-scoped identities/findings before evidence sampling; line-to-order
collapse and severity priority are read-time observations. Due-soon is an existing
canonical class whose supersession previously hid imminent customer work in this read.
No new deadline threshold, authority, stored status or statement is introduced.

The web remains a thin observer. Unknown message urgency, unknown return timeliness,
only-risk-item stock scope, unavailable Finance and external-Agent runtime limitations
are explicit. The existing four reads own all refreshes. The initial manual preview
reuses the register's human scope; reviewed control services, revision checks, exact
reason, request identity and already-started/related-case limits are unchanged.

Verification is recorded in quickstart; original reviewer-owned quality markers and
prior enterprise/performance/real-time-soak gates are not closed by this increment.

## Stable interaction review (FR-057–058)

Owner authorization: explicitly rethink and implement the most intuitive interaction.
Requirements review PASS: one area selector in analysis, read-only monitoring above,
no automatic scroll, retained bookmarks/refresh/company boundaries. Plan Constitution
Check PASS; no schema/business/mandate changes. Pre-implementation analysis PASS:
FR-057 maps T091/T092/T093 (non-interactive summary and single labelled selector);
FR-058 maps the same tasks (focus/viewport/bookmark/reset regression). Earlier FR-048
is explicitly superseded. No unresolved clarification or CRITICAL finding. Existing
reviewer-owned and enterprise rollout checklists remain untouched and outside this
owner-authorized presentation increment.

Final scope review PASS: top summary affordances are removed consistently, the single
labelled native select controls only existing area state, and fragment replacement
preserves history without scrolling/focus transfer. All evidence/area articles remain
mounted; tenant reset and reviewed case behavior are unchanged. Executed proof and
actual company observation are in quickstart. PR review/merge and earlier enterprise
acceptance gates remain separate.

## Hierarchy refinement review (FR-059–061)

Owner authorization explicitly covers rethinking box priority/order and replacing
observation buttons with icons. Requirements review PASS: first row shipping/control,
second analysis/monitoring, contained analysis, consistent surfaces, read-only icons,
retained explicit business actions. Plan Constitution Check PASS, frontend only.
Pre-implementation analysis PASS: FR-059/060/061 map to T094–096 and geometry/frame/
style/accessibility/state regressions in the existing matrix and lifecycle proof.
FR-052 is explicitly superseded for placement; FR-057–058 selection remains intact.
No unresolved clarification or CRITICAL issue. Reviewer-owned and enterprise rollout
gates remain untouched, outside this explicitly authorized presentation increment.


Final FR-059–061 presentation review: approved hierarchy, reading order, shared card
rhythm and quiet observation controls match the owner request. Browser matrices,
keyboard/state proof and controlled lifecycle pass; no domain, polling, schema or
permission changes. Business control review and evidence remain explicit. The prior
head's enterprise latency failure is recorded separately and is not waived by this
presentation review; rollout and head-specific CI acceptance remain open.


FR-062–064 owner scope/review and pre-implementation analysis: PASS. The latest explicit
request supersedes separate shipping/flow placement in FR-059, not its responsibility
priority or FR-060–061 clarity/accessibility. FR-062 maps to T097–099 selection/default/
bookmark proof; FR-063 to retained source/basis/curve/lifecycle proof; FR-064 to geometry
and real-view proof. No critical consistency/coverage or Constitution findings, no
unresolved clarification, no authority/permission/schema/polling extension. Existing
enterprise performance and reviewer-owned rollout acceptance remain open.


Final FR-062–064 presentation review: PASS. Shipping is first/default in the sole
analysis selector, all original curves/scope/evidence stay available, switches
preserve disclosure/manual/following state, and the adjacent column prioritizes
Responsibility then log/Agents. Required frontend contracts, full browser matrix,
controlled eight-hour lifecycle, audit/format/build/spec checks and actual company
inspection pass. Only the frontend was activated. PR 383 describes the final
implementation and recorded limitations. Head-specific CI, enterprise performance
and reviewer-owned rollout/pilot acceptance remain open; no threshold was waived.


FR-065–067 requirements/plan/pre-implementation analysis: PASS. Owner explicitly
requests the compact switchable grouping and logical shipping placement. T100–102
map defaults/frame/switch/state/disclosure and full matrix/lifecycle/actual-view
proof. Superseded FR-064 right-stack visibility is explicit; original control priority
and service/evidence semantics remain. No unresolved clarification, critical finding
or Constitution exception. Existing performance/pilot and human review gates remain.


Final FR-065–067 presentation review: PASS. Two primary outer frames, one native
workspace selector with Responsibility default, retained hidden state/readers and
counted shipping disclosure match the owner scope. Existing source/action/control
coverage remains tested, including native keyboard and all viewport/theme/language
views. Contracts, matrix, controlled eight-hour lifecycle, audits and build/spec
checks pass. Actual company view confirms all three right views and contextual
blocker restoration. Existing database_error in case reconciliation and enterprise
performance/real pilot gates remain explicit; no business rule or threshold changed.
PR 383 remains the existing review destination; current-head CI acceptance is separate.

## Compact instrument inspection review (2026-10-07)

Scope: explicit owner request for compact member inspection behind primary and
risk counts. FR-068–070 explicitly supersede only FR-057's non-interactive summary;
chart selection stays independent. Pre-implementation analysis: three requirements,
four mapped tasks, 100% new-scope coverage, no clarification/critical finding;
Constitution PASS. Six expected failing ordinary/snapshot service proofs reproduced
missing inspection output before implementation.

Verification: 65 affected flow/HTTP/snapshot tests passed; 8 tightened inspection,
company-isolation and partial/completed-return proofs passed. Frontend contracts
478/478, production build, four-language audit 3038/3038 each, formatting, spec
policy, business annotations, scoped Ruff and generated-reference freshness passed.
Full cockpit matrix passed, including new stock/order/empty-group modal activation,
Escape/focus, URL/viewport preservation, exact record membership, and dialog geometry
at 320/390/1440/1920 in four languages and both themes. Service ordinary/clean
snapshot parity and existing read-only authority proofs remain unchanged.

No schema, new endpoint/tool, business rule, approval change or browser reader.
Existing enterprise final-head CI/real-time pilot qualification remains open;
these focused checks do not establish production performance. Local activation and
actual company preview verification are recorded separately after completion.

Actual activation and stock/order/mail/zero-group proof passed on the retained
company; see quickstart. Final full browser matrix also proves an open aged preview
shows the warning and retains actual rows. T106 remains open for final-head CI and
existing enterprise qualification, not because local inspection is unavailable.


## Daily plan absence recovery review (2026-10-07)

Owner scope: repair the retained local simulator's missing day plan and keep actual
shipping observable independently of planning authority. FR-071–072 map to T107–109;
the shared local fixture is separately specified in spec 376. Pre-implementation
analysis and Constitution Check passed: no unresolved clarification or critical
finding, no new schema, endpoint, agent permission, business timer or alternate
fulfillment rule. Global commitment ownership by current plans is preserved.

Verification: the affected shipping/cockpit/planning/live/scenario run passed 141
tests with one conditional browser skip; two new fixture assertions initially used
string intake quantities and failed. After correcting those fixtures, all five
scenario tests passed. The final ten-test daily regression passed (55 deselected),
including partial bookings, absent plans, correction/supersession, prior-day first
handover with a current-day retry, tenant/site isolation, balanced bounded evidence,
unknown deviations, replay, active-owner confirmation and both DST transitions.
Frontend contracts passed 478/478, the complete cockpit browser matrix passed
(including actual no-plan curves, native record/source links and existing viewport/
keyboard/theme/language coverage), production build and four-language audits passed
(3044/3044 each). Scoped Ruff/format, business annotations, generated catalog
freshness, specification policy and whitespace checks passed.

The physical-activity reader performs two scoped SQL reads in the existing snapshot.
First-handover history is reconciled only for selected-day candidate packages; the
full evidence remains in the calculation fingerprint while the member preview is
bounded and includes both independently measured units. No package count is used
as fulfilled plan-order evidence. A missing/incomplete cohort reports unknown
deviations, not a safe zero. Final review found no new authority or source loss.

Local evidence: day 2026-10-07 was accepted via normal owner-confirmed tooling,
statement sps_a0b21f39e4, proposal act_66243ee8ff, synthetic capacity source
src_2cf014a65f: 46 otherwise unassigned open run commitments, 500 explicitly
synthetic completion slots and collection hour 22 in the company's UTC calendar.
Earlier current statements are unchanged. Independent actual activity read 700
orders with shipment bookings and 56 source-backed package handovers, including
work outside today's cohort; these are different units from completed plan orders.
Only API/web were rebuilt for this change. The existing sole operator resumed
round 137 and successfully checked the existing daily fixture before its next round;
workers, agent credentials and the business routine were preserved.

Limits: this focused verification does not qualify enterprise performance, a
multi-day real operator/capacity soak or current-head CI. The prior measured p95
3.252 seconds remains above the unchanged 3-second gate; no threshold is waived.
Production carrier capacity and planning approval are separate from this explicitly
authorized local synthetic fixture. Prior-plan backlog is not silently rescheduled.

Final local activation: API startup initially exceeded its healthcheck during host
resource pressure; it subsequently became healthy without changing thresholds.
The rebuilt web started and the actual member UI showed Live observation on
2026-10-07, plan 46/0/0/46 and independent bookings/package handovers 700/56.
The mail backlog decreased from 1,924 to 1,923 during inspection. Native movement,
package and Source links are present in the basis disclosure. Screenshot evidence:
/private/tmp/reality-instrument-panel/daily-plan-current-live.png. The temporary
frontend test server was stopped; the sole operator and existing simulator remain.


FR-073 pre-implementation review: explicit owner requests removal of duplicated
category/topic headers and inconsistent typography. One requirement maps to
T110–112 and executable browser selection/heading/geometry proof. Constitution
PASS; no unresolved clarification or critical consistency/coverage finding.
Existing enterprise and reviewer-owned rollout checklists remain open and are
outside this explicitly authorized presentation repair.


FR-073 verification: the new product browser assertion first failed on the two
visible shipping headings (Flow analysis and Shipping by end of day), establishing
the reported duplication. After implementation the full cockpit browser matrix
passed, including one selected-topic h2 across six analysis/three workspace views,
category labels, matched shared typography, retained source/manual/log/Agent state,
native keyboard/focus and 320/390/1440/1920 viewport checks in four languages and
both themes. All 478 frontend contracts passed; localization audits remain
3044/3044 for all four languages. Native production build, frontend image build,
scoped formatting, spec policy and whitespace checks passed. No new translation,
business reader, data change or polling change. Only the web was recreated locally;
the API, operator and simulator were preserved. Existing current-head CI, enterprise
performance and real pilot acceptance remain open.

Actual local member inspection after web activation passed: the return view shows
Flow analysis / Returns & disposition beside Operations workspace / Cases & takeover,
with one primary heading per card. Log and Agent selections show the single current
topic (Recorded business activity / Agents & connections); normal contextual
descriptions/actions remain available. Screenshot:
/private/tmp/reality-instrument-panel/control-tower-unified-headings.png.
The retained current-day observations and operator remain live. Final diff review
passed; no dangling embedded heading references, duplicate topic headings or
changes to control/state semantics.


FR-074 pre-implementation analysis: explicit owner requests whole-tile inspection.
One requirement maps to T113–115 and product hit-area/keyboard/filter/focus proof.
Constitution PASS, no unresolved clarification or critical inconsistency; existing
FR-068–070 exact read-only inspection semantics are preserved. Reviewer-owned
rollout/performance checklists remain outside the authorized presentation repair.


FR-074 product proof: before implementation, clicking the tile title timed out
waiting for Quick inspection, reproducing the reported missing hit area. After
implementation, the full cockpit browser matrix passed, including title, meter,
status and padding pointer hits across all five available areas, all-work selection,
Enter/Space and Escape focus restoration. Existing direct risk filtering, exact
member previews, stale/empty evidence, viewport/history/source/manual/live state,
phone/desktop geometry and theme/language proofs remain green. The hit layer is
owned by the existing native button, with sibling risk buttons above it; there are
no nested buttons or delegated business handlers. Finance and unavailable primary
counts retain their previous behavior. Native frontend build, scoped formatting
and spec policy passed. Existing enterprise/CI/rollout qualification remains open.

All 478 frontend contracts passed, four-language localization audits remain
3044/3044 with the tile instruction translated, production/frontend image builds
and formatting passed. The temporary fixture server was stopped after the browser
proof. No backend schema, service, catalog, authority or polling change.

Local activation proof: only the web container was recreated. In the actual
company on port 8080, a pointer click on the Stock tile title opened Quick
inspection with All open work selected and both underlying item rows. Escape
closed the dialog. Screenshot: /private/tmp/reality-instrument-panel/
control-tower-tile-inspection.png. Final scoped diff review passed; no business
reader, automatic agent action or runtime fixture was changed. Existing ready
PR 383 receives this verified presentation change; enterprise qualification
and current-head CI remain independent gates.

FR-075 pre-implementation analysis: explicit owner visual-grouping request maps
to T116–118 with exact-value/group/plot-boundary and responsive proof. Constitution
PASS, no unresolved clarification, conflict with FR-073/074 or critical finding.
Before implementation the product proof failed because message current/recent
groups were absent. Existing enterprise/release gates remain independent.

FR-075 verification: the full cockpit browser matrix passed with explicit metric
period/count groups for all five flow areas in four languages, both themes and
320/390/1440/1920 layouts. Exact message counts remain 8/5/3 (current) and 2/34
(recent), with -36 change owned by the backlog plot. Each plot visibly bounds its
title/series/legend/range/context. Initial Dutch 320px header height proof failed;
compact phone typography/gap restored the unchanged height gate and the complete
matrix passed on rerun. Existing full-tile/risk previews, chart selection, live
refresh, source links, manual review and stale/missing evidence proofs remain green.
All 478 frontend contracts, four-language 3045/3045 audits, formatting, native build,
final production web image, spec policy and diff whitespace checks passed. Manual
visual review of the generated light desktop product screenshot confirms distinct
metric periods and separately bounded flow/backlog plots with retained data.

Final FR-075 alignment pass: responsibility count buttons share label/value
subgrid rows with left-aligned text. The complete cockpit browser matrix passes
again including the new wrapped-label ownership-value alignment proof; final
production web build passes. Only web was recreated on port 8080. Actual current
company inspection confirms messages retain current counts and separate incoming/
first-reply and declining backlog plots, each with owned metadata. Shipping retains
46 due plan orders, 700 physically booked orders and 56 confirmed packages as
separate units; no fixture or operator was changed. Actual responsibility value
tops both equal 1124.75px. Screenshot:
/private/tmp/reality-instrument-panel/control-tower-content-grouping.png.
Final semantic/diff review PASS: explicit period metadata only classifies existing
metrics for presentation; source values, read/action handlers, live lifecycle and
case authority remain unchanged. Temporary fixture server stopped; primary dirty
checkout untouched. Existing PR receives the repair; CI/enterprise/soak gates are
not certified or weakened.

FR-019 timezone regression review: T119–121 map UTC/Tokyo/actual Berlin display
proof to existing formatting authority. Constitution PASS; no unresolved issue or
critical finding. Before repair the initial UTC header proof fails: 14:30 company
clock instead of 12:30 viewer observation. Case/general supporting timestamps use
the same wrong override; explicit shipping clocks are intentionally retained.

FR-019 initial verification: full cockpit browser proof passes UTC header/case/
control timestamps and Tokyo header/case/supporting-read timestamps while retaining
Berlin shipping/reference clocks and Amsterdam cutoff date/offset. The existing
478 frontend contracts pass; four-language audits remain 3045/3045. No preference
is mutated and no recorded UTC instant, business-day evaluation or agent action
is changed. The explicit business calendar date is retained in shipping context
using the existing formatCalendarDate helper (FR-003). Final head browser/image
verification and actual Berlin inspection follow this additional calendar proof.

FR-019 final verification/review PASS: final-head full cockpit browser matrix
passes including the explicit business calendar date and independent UTC/Tokyo
observation clocks. All 478 frontend contracts, four-language 3045/3045 audits,
formatting, production web image, spec policy and whitespace checks pass. Only
web was recreated locally; the simulator and operator were not restarted or
changed. Actual Berlin inspection on port 8080 reads the original UTC instant
2026-10-07T08:50:45.191254+00:00 as 07. Okt. 2026, 10:50 GMT+2, exactly matching
the personal Europe/Berlin formatter. Case read observation also shows 10:50
GMT+2. Screenshot: /private/tmp/reality-instrument-panel/control-tower-viewer-timezone.png.
The final semantic review confirms display-only changes: business calendars,
shipping/site deadlines, retained stale instants, tenant scope and control
authority remain intact. Existing PR receives this repair; earlier CI, enterprise
performance and sustained-live gates remain open. Temporary fixture server stopped.

FR-076/077 pre-implementation analysis: both scoped requirements have test-first
coverage in T122, implementation in T123/T124 and verification/review in T125.
No duplicated authority, schema expansion, unresolved clarification or critical
finding; 2/2 scoped requirements covered, 0 unmapped tasks, Constitution PASS.
Existing incomplete enterprise/shipping release checklists retain their gates;
the owner explicitly authorized these presentation repairs. The standalone
case harness currently does not load production CSS and the component uses an
undefined br-card class. Its first bounded-card regression fails (0px versus
1px). Shipping's initial named-plan-group regression fails (0 versus 1).
Existing domain/services and control contracts are unchanged.

FR-076/077 implementation review: AnalysisSections wraps presentation only;
existing SVG path generation, provider values, UTC clocks and inspect handlers
remain unchanged. Original shipping plan/actual units and no-plan actual curve
are retained. Native site disclosure preserves all exact cutoffs, with product
proof updated to open it explicitly. Object-case warnings remain outside the
technical disclosure and control services are untouched. The standalone case
browser passes all four languages/both themes at 320/390/1440/1920px and the
original confirmation, retry, provenance and exact-handback proofs. All 478
frontend contracts and four-language 3048/3048 audits pass. A removed grouped
figure rule was detected by the existing bounded-metadata proof during CSS
consolidation and restored; final full cockpit matrix and local proof pending.


FR-076/077 final verification and semantic review PASS: final-head full cockpit
browser matrix passes, including shipping group geometry, shared metric/figure
typography, missing-plan actual activity, live updates, exact site disclosures,
retained order links and all locale/theme/viewport variants. The independently
styled object-case matrix also passes, including confirmation, takeover retry,
provenance, exact handback and visible stable IDs in the company-wide case list.
All 478 frontend contracts, four-language 3048/3048 audits, formatting, production
web image, spec policy and whitespace checks pass. No service, recorded value,
clock, business reader or authority changed; warnings remain visible outside the
technical disclosure. Only web was recreated on port 8080. Actual inspection
retains 46 due plan orders, 700 physically booked orders and 56 confirmed packages
in separate groups, both message plots and decreasing backlog, and the styled
previously manual order without changing responsibility. Screenshots:
/private/tmp/reality-instrument-panel/control-tower-unified-analysis.png,
/private/tmp/reality-instrument-panel/control-tower-unified-messages.png and
/private/tmp/reality-instrument-panel/control-tower-object-case-layout.png.
The existing PR receives these presentation changes; primary checkout is untouched
and simulator/operator runtimes are unchanged. Existing CI, enterprise performance
and sustained-live gates remain open.


FR-078 pre-implementation analysis: the single scoped requirement maps to T126
(test first), T127 (presentation) and T128 (verification/review). 1/1 coverage,
zero unmapped tasks, unresolved clarifications or critical findings. Constitution
I–VIII PASS. Risk values and categories retain shared service authority; the
empty-zero meter changes rendering only. Owner authorized this refinement;
existing incomplete CI/enterprise/soak checklists retain their release gates.

FR-078 test-first proof fails on the old unbounded overview (0px versus 1px).
Implementation review: only presentation wrappers/classes and the explicit
known-zero meter branch change. Counts, shared service partitions, percentages,
button handlers/labels, Finance destination and polling stay intact. The retained
prominent-status proof caught an initial smaller indicator; 16px is preserved.
The meter keeps explicit flex rendering and a new proof checks actual segment
geometry, in addition to existing exact percentages. No catalog/tool/schema change.

FR-078 browser verification PASS: the complete retained cockpit matrix passes
with the new bounded overview, same-row tile-slot geometry, compact rendered
proportions, label/count alignment, centered four-key footer and known-zero versus
unknown meter assertions. All four languages, both themes and 320/390/1440/1920px
pass the existing no-overflow, whole-tile/category inspection, dialog focus, live
state, shipping and manual-control proofs. An initial Dutch 320px text overflow
was corrected with a single-column narrow layout and contained translated labels;
no assertion was weakened. 478 frontend contracts, four 3048/3048 audits, scoped
formatting, spec policy and whitespace checks pass. Final local image/inspection
and PR update remain the completion step; earlier release gates stay open.

FR-078 final local verification/review PASS: the final production web image
builds and only web was recreated on port 8080. Actual company inspection shows
494 open orders, 1,326 locally unanswered messages and 6 expected supply lines;
all six meter tops equal 493.640625px and all six condition tops equal 602.640625px.
The legend footer is centered and contains all four keys, exact scope and retained
classification caveat. Zero stock/return work has no unclassified segment;
unavailable Finance stays explicitly unknown. The manual case remains owned by
the same human. Screenshot:
/private/tmp/reality-instrument-panel/control-tower-instruments-refined.png.
No business mutation was performed; the temporary fixture server was stopped,
primary checkout and simulator/operator runtimes remain unchanged. The existing
PR receives the refinement; CI/enterprise/soak release gates remain open.

FR-079/080 pre-implementation analysis: 2/2 scoped requirements map to T129 tests,
T130 service observation, T131 adapter/presentation and T132 verification/review.
Zero unmapped tasks, unresolved clarification or critical finding. Constitution
PASS; no new case family, schema or claimed Agent execution state. Existing
checklist/CI/enterprise gates remain open; owner authorized this bounded follow-up.


FR-079/080 implementation verification PASS: the test-first backend proofs first
failed on missing kind_counts; complete tenant-scoped grouped counts now pass 55
affected PostgreSQL service/adapter/snapshot tests, including supported returns,
completed human work, zero cohorts and independence from page filters. The browser
first failed on missing overview, then the final complete cockpit matrix passed
exact preview filters, no business writes, native Escape/focus, live disclosure
retention and contained tables/briefing cards across four languages, both themes
and 320/390/1440/1920 widths. Intermediate fixture assertions were corrected to
match the held three-row briefing and avoid an ambiguous repeated dialog label;
content-group assertions await the mounted area without weakening their checks.
478 frontend contracts, four 3057-key audits, production build/images, scoped Ruff,
business annotations, spec policy, formatting, catalog freshness and whitespace
checks pass. Grouping reuses the existing aggregate and same register poll, and
briefing never attributes actors/causal resolution/external outcomes. Earlier CI,
enterprise performance and sustained-live release gates remain open.


FR-079/080 final local inspection: API/web production images were recreated on
port 8080 without migrations or restarting simulator/operator/scheduler/worker/MCP.
Actual company observation shows 1,153 registered order cases, 48 outstanding,
1,152 automation-owned and one human-owned; the exact human preview names the
previously stopped LIVE-f1ad500666008054 and its original order link. The selected
day still has 46 affected planned orders, separate from 700 shipment-booked orders
and 56 confirmed packages. Messages decrease live (1,144 to 1,138 during inspection).
Canonical rollout remains incomplete, so the upper table now repeats the existing
readiness warning; the final complete browser matrix covers this condition and
passes again. No business responsibility or external operation was changed.
Unsupported families remain explicit. Primary checkout is untouched. The existing
PR is updated; earlier release gates remain open.
