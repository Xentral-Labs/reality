# Verification: Live Business Logic and Test Blueprints

**Date**: 2026-10-03
**State**: Automated checks green. ERP-professional and natural-language cross-surface review remain pending. No deployment, merge or commit performed.

## Authorization and design

The user explicitly directed implementation through green checks. Constitution Check PASS and pre-implementation cross-artifact analysis found zero CRITICAL issues. The built-in requirements checklist remains checked; the reviewer-owned live-evidence checklist remains unchanged. The five-minute ERP-professional exercise (T047) has not taken place and cannot be certified by automated tests.

No business schema, scheduling infrastructure or stored explanation was added. Generic explanations inspect approved loaded callables and matching source bytes. Actual raw tests/helpers are parsed without execution. Web, docs, application tools and MCP delegate to one shared explanation service; authorized case comparison uses existing tenant-scoped reads.

## Executed feature proofs

| Check | Observed result |
|---|---|
| All seven blueprint test files, including credit business story | **36 passed**, 24.23 seconds, including final default-binding provenance and mismatch classification |
| Reference-boundary business journey | Included above; all **53 obligations** resolve to actual returned source symbols across nine canonical roots |
| Catalog guidance/provenance regression subset | **23 passed**, 64.18 seconds |
| Application catalog, scope and command parity | **50 passed**; expected isolation counts updated and the corrected denominator proof passed fresh (**1 passed**, 3.50 seconds) |
| Previously failing playground security/API subset, repeated serially | **617 passed, 1 skipped**, 165.37 seconds |
| Complete PostgreSQL `make test` | **5414 passed, 10 skipped**, 2504.22 seconds; one existing transaction-cleanup warning |
| Frontend contract suite | **456 passed**, zero failures |
| Frontend localization audit | All four languages PASS; **2535/2535** keys each |
| Frontend formatting and production build | PASS; production build 14.16 seconds |
| Docs reference Python tests | **14 passed** |
| Docs Node tests | **116 passed** |
| Docs production build | PASS, 59.51 seconds |
| Blueprint Web and live-docs browser cases | PASS; changed live responses without an explanation-generation step; unavailable docs response clears old content |
| API and MCP release image builds | PASS, `REALITY_COMMIT=blueprint-verification` |
| API and MCP image evidence smoke | PASS: identical source digest, **34 sources, 28 scenarios, 11 raw files**; configured database endpoint deliberately unreachable |
| `make lint`, `make spec-check` | PASS |
| `make docs-generate`, `make docs-catalog-check` | PASS reproducibility against a temporary index snapshot; real Git index untouched |

Initial proofs failed with absent modules. Integrated tests then found missing MCP capability topics, canonical projection roots, reference helper traversal and a catalog-guidance classification error; corrections were verified before final feature proofs. Final review also found a local dynamic-dispatch disclosure gap: its new regression failed first (1 failed), then passed with all 31 feature proofs after unresolved callables were named explicitly. Test counts represent executed checks, not branch coverage.

## Evidence meaning and limitations

The planning boundary contains 53 business outcome obligations, 62 source symbols and 323 baseline predicate sites. It is a denominator for validation, never a generated explanation authority. The runtime captures current exact expressions and operators; durable markers carry identity only. Text and diagrams share graph nodes/edges. Expression-level predicate gaps are included. Unsupported syntax, unvisited helpers, traversal budgets and unresolved fixtures are disclosed rather than hidden.

Source-versus-loaded-code mismatch, expanded literal globals/default mutation, source changes during reads, missing/mismatched raw manifests, unsafe paths/symlinks and secret runtime bindings have executable proofs. A changed loaded source or test assertion changes the next response. Disk changes alone cannot masquerade as running behavior.

Test setup/action/assertions retain exact snippets and helper evidence. Candidate relationships do not claim asserted rule coverage; discovery does not claim execution. Unknown runs remain unknown. Optional run evidence must match release, timestamp and source/test digests. Packaged smoke output is deliberately **partial**, because supported extraction is not formal proof of all business semantics.

Comparison preserves Decimal, units/currency and missing values, distinguishes supplied/current facts from recorded hold decisions, rejects other-tenant records and adds no writes. Historical rule versions are unknown where events do not record them. Similar conditions are never an outcome guarantee.

Generic public routes accept registry/evidence IDs only, reject tenant/fact inputs, omit credentials and use no-store responses. Private comparison retains authentication and tenant scope. Raw source/test strings are escaped by both UIs. English explanation fallback is visible; localized controls do not imply a translated business explanation.

## Complete-suite progress and shared-worktree baseline

All **83 registered browser scripts passed**: 79 in the initial complete run, four after targeted repetition with unchanged assertions. The original run took 3085 seconds. Initial timeouts affected company setup, finance, operations and workspaces. Successful repeats cover all 16 setup combinations, finance (48 localized screenshots), operations (64 localized screenshots) and workspaces (64 localized screenshots). An intermediate retry lost its server when the complete runner shut down; final retries used a persistent server. Blueprint-specific checks passed both focused and registered runs.

The complete PostgreSQL `make test` target passed with four workers and stable file grouping: **5414 passed, 10 skipped**, 2504.22 seconds. It emitted one SQLAlchemy transaction-cleanup warning in an existing storyline HTTP test. Final source-default hardening was made while that run was finishing; all **36 related feature tests were then rerun fresh and passed**. The complete-run count is 5424; five newly added feature regressions were covered by the final focused run. This records the two executed test sets honestly rather than claiming the whole suite ran on one final source snapshot.

Earlier runs are not passes. Root-directory invocation initially caused Alembic configuration errors; the corrected Makefile invocation identified missing registration for four new tools. Two evidence-backed isolation families now classify generic metadata and private comparison separately (35 families / 618 operations). Fresh MCP foreign-record refusal and denominator proofs passed. Initial frontend/browser timeouts were resolved by unchanged targeted retries on a persistent server.

The final provenance review added failing tests for imported default mutation and unsupported factories (2 failed before correction), and for misclassified default-layout drift (1 failed before correction). Capture now checks raw Python positional/keyword default slots, verifies safe imported scalar bindings without executing factories, reports unsupported defaults as explicit source limitations and marks mismatches outdated. The service propagates these limitations; existing comparison rejects outdated evidence. Cross-function duplicate IDs were already rejected; an additional regression secures that behavior without changing product logic.

The worktree also contains pre-existing storage/migration work and concurrent company-settings changes. They are preserved. Generated-file reproducibility uses `GIT_INDEX_FILE=/tmp/blueprint-catalog-verification.index`: snapshot current generated files, rerun the exact make target, verify zero generated diff. This does not certify a clean HEAD or stage/commit unrelated changes.

## Pending review

T047 remains pending: an ERP professional must identify inputs, refusal condition and closest existing test in five minutes. T034 retains the real natural-language Chat / all-surface review exercise; canonical read-tool delegation, schemas, source rules and browser presentations are tested, but no live AI-provider conversation is invented. T033 has regenerated vocabulary ready in the worktree; its commit step remains pending because unrelated shared changes must not be included. Reviewer-owned checklist markers stay untouched. Automated T048 and agent diff review T049 are complete. Final API/MCP smoke checks passed with identical source digest `4822e0efa9d23bd0a817b7a0697b00a1222d1b8de2e1b96460434cdc70528f71`, 34 sources, 28 scenarios and 11 raw files. The temporary isolated PostgreSQL container was removed after verification.

## Local Docs CORS regression

The live API returned HTTP 200 but the Docs browser preview on port 5178 could not read it because Compose did not forward DOCS_URL to the API. The deployment regression test now requires that forwarding. The local API preview uses an explicit DOCS_URL override matching port 5178; no migration or database changes are required. This restores the specified configured-origin live Docs access.

## ERP readability correction: generic live LLM presentation

The user rejected the literal source-statement view and explicitly authorized a generic,
request-time LLM interpretation, without saved or pre-generated narratives. FR-020–FR-022
reopen the original readability requirement. Specification/plan/task correction analysis
found no unresolved clarifications or CRITICAL conflicts; Constitution recheck PASS.
The original no-provider presentation constraint is explicitly superseded by that approval.

Implementation adds a shared deployment-provider interpreter for every registered entry.
No per-operation narrative, vocabulary rule table, saved response, model cache or generation
step is added. Request-local evidence aliases are validated against verified original rule,
source and test identities. The server derives diagram connections from original source
edges; the model cannot supply paths. Bounded diagram contraction discloses omissions.
Then statements retain validated indices of actual assertions; remaining assertions are
counted from actual test code. Model text is visibly interpretation, not semantic proof.
Source/test bytes are checked again after inference; drift discards the answer. Source-only
reads and case comparisons do not invoke the model. Missing configuration or failed model
calls retain technical evidence and show unavailable interpretation.

Web/docs put the business overview, selected rules and Given/When/Then first; technical
analysis, full versions, raw setup and code stay expandable. Existing case comparison and
read-only tenant boundaries are retained. Unsupported language falls back to English.

Executed checks for this correction:

- Generic presentation regressions: 14 passed, including unfamiliar function operands,
  changed live source, invalid citations, invalid assertion indices, provider/schema bounds,
  missing/failing provider, concurrency/input limits, contracted branches, post-inference
  source drift and source-only reads without model calls.
- Initial full affected backend set: 45 passed; after overview/provenance changes: 49 passed.
  The final expanded set is recorded below after completion.
- Frontend contract suite: 456 passed; all four language audits passed (2535/2535).
- Docs suite: 118 passed. Web and Docs production builds passed, with existing chunk warnings.
- Both registered Blueprint browser scripts passed against explicitly intercepted test
  responses. They prove primary business rendering, collapsed technical evidence, refresh,
  error clearing, test visibility, graph and existing case comparison; they are not live
  model-quality evidence. Screenshots remain test fixtures.
- Repository lint, spec policy and diff whitespace checks passed.
- Pure local interpreter-envelope measurement against the running API source: credit
  exposure 186731 bytes, item creation 64038 bytes before adding assertion-index metadata;
  both fit the 240 KB limit. Short IDs and deduplicated helpers avoid duplicated evidence.

The automatic approval reviewer initially blocked the external live check pending explicit
payload/destination authorization. The user then expressly approved the credit/item code
and test evidence transmission to api.anthropic.com / Claude Haiku. Actual approved calls
were attempted. The deployment key matches .env but Anthropic returned HTTP 401. No valid
live interpretation has therefore been certified. The user was asked to update the local
ANTHROPIC_API_KEY without sending it in chat. No other credentials or provider destinations
were substituted. Generic code/test evidence only is sent; no company records, case data,
access tokens or tenant API settings are sent.

T050–T053 are implemented. T054 remains open for successful real-provider reference reads
and their review. T047 remains a real ERP-professional exercise; no automated result marks
it complete. The earlier 5414-test whole-suite run predates this correction; it is not
claimed as a fresh whole-suite run of these changes. No deployment, merge or commit.

Final correction snapshot: all 50 affected backend tests passed (12.44 seconds),
including all 14 presentation regressions. Final Docs tests 118 passed; final Web
and Docs builds passed; all four final language audits passed. The shared Chat
prompt now requests the user language and preserves interpretation/technical
evidence distinctions. The true provider success and human review remain pending.

Existing Chat adapter regressions after the shared prompt update: 5 passed.
The automatic-review authorization issue is resolved by explicit user approval;
the remaining blocker is Anthropic authentication (HTTP 401), not tool permission.

## Updated deployment key and provider-format regression

The user updated the deployment key. The API was recreated without dependencies,
builds or migrations, retaining the exact Docs preview origin. Authentication no
longer returned 401. Real replies revealed a steps field encoded as a string rather
than an array. A failing regression reproduced the case (1 failed, 14 passed), then
container-only JSON decoding was added before the unchanged strict Pydantic and
reference validation. Uncited prose and invented IDs remain rejected. All 15
presentation regressions passed after the fix. No provider text or secrets were
logged; diagnostics contain field paths, type names and status categories only.
This restores FR-020's existing structured interpretation contract, without new
requirements, persisted prose or altered business rules.

Provider follow-up: container normalization alone did not resolve every real reply.
The interpreter now requests Anthropic strict tool use with the supported schema
subset, while retaining all original Pydantic bounds locally. Known source/rule/test
references are constrained in the provider schema and checked again server-side.
Reference: https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use
and https://platform.claude.com/docs/en/build-with-claude/structured-outputs .
The observed credit failure was Invalid assertion reference. Parallel sentence/index
arrays were replaced in the provider-only contract by one structured object per
sentence containing its assertion index and text; the public response remains the
same. Both fixes had failing regressions before implementation. All 17 presentation
regressions pass. General ERP-language guidance now prioritizes short overviews,
business rules and natural German, without per-operation prose or rule definitions.

Live verification succeeded after the format/association corrections: actual credit
exposure and item creation responses both returned business.mode=llm, validated source
links, German business steps and interpreted real test cases. Credit returned 13
steps/6 cases; item returned 16 steps/2 cases. A real Playwright browser (no route
interception) requested both through the German Docs page, verified mode=llm and
visible server text, and captured /tmp/blueprint-real-credit.png and
/tmp/blueprint-real-item.png. Both passed actual CORS/live-provider rendering. API
responses remain partial source analysis; this is not semantic completeness or a
human ERP-professional approval. Generic vocabulary guidance further distinguishes
Kundenaufträge from supplier Bestellungen and Kreditobligo from generic exposure.

All 53 affected backend tests passed after the provider-only fixes (19.74 seconds),
including 17 presentation regressions. Lint/spec policy passed; no frontend code or
business behavior was changed in this follow-up. Earlier browser/build checks remain
applicable, supplemented by the two actual live browser reads. The prior 401 blocker
is resolved. T054's real-provider/browser gate is now verified; T047 remains pending.


## Loading, responsive flow and brief-read correction (2026-10-03)

User screenshots showed unexplained waiting and clipped 760px business SVGs. Regression first: the new primary-flow SSR test failed because the responsive flow did not exist, then passed. The brief provider regression failed on the absent `brief` argument, then passed.

Implemented accessible spinner/elapsed time with request-lifetime cleanup and reduced-motion support in Web/Docs. Full-text 16px wrapping HTML cards replace primary SVG; technical SVG remains. Group supplied edges by existing target and preserve every original outcome in collapsed code-path evidence. Shared-helper regression proves grouping and absence of invented links between independent steps. Mobile and desktop screenshots were actually viewed; a discovered explosion of credit graph path links was corrected before completion.

Interactive initial reads request a source-cited brief interpretation with six structurally bounded nullable slots, no overview and no generated test summaries. Full interpretation/tests remain an explicit separate read; raw current tests remain in both responses. Default full MCP behavior is unchanged. Actual code/test source freshness is still checked after inference, with no saved answer. Explicit response-language instruction addresses a observed German-request/English-answer mismatch.

Verification: focused Python presentation + adapters **22 passed**; Docs **119 passed** before adding the final shared-helper case, focused five Docs blueprint tests subsequently passed; Web contract **456 passed** before final grouping, final rerun recorded separately. Both production builds passed (existing chunk warnings). English/German/Dutch/Spanish locale audit remains all four configured languages 2535/2535. `make lint`, `make spec-check`, `git diff --check` passed. Docs and Web fixture-browser journeys passed. Actual unmocked German Docs reads for credit and item passed, with six rules and no inferred test executions, at desktop 1280px and mobile 390px; cards show no horizontal overflow. Screenshots: `/tmp/blueprint-loading-item.png`, `/tmp/blueprint-flow-real-item-1280.png`, `/tmp/blueprint-flow-real-credit-390.png`. Browser log `/tmp/blueprint-responsive-live-check-final.log`.

Latency is NOT reliably within the requested 3–5 seconds: original full item 18.4s; valid brief repeated item 4.8s and credit 5.1s; another first brief call after schema change 45.1s; latest final-language browser calls item 22.5s and credit 10.5s. Local evidence analysis 1–2s; actual provider latency varies significantly. No passing latency SLA, human ERP approval, full semantic correctness or fresh complete repository suite is claimed. T047 remains pending. Known unrestricted full-overview arithmetic fidelity issue remains unresolved; the initial brief view omits overview instead of presenting that unsupported summary.

Final adapter gate reruns after grouping: Docs **120 passed**, Web contract **456 passed**, both fixture browser journeys passed. Actual final unmocked German browser latency remained 22.5s item / 10.5s credit, with full mobile/desktop cards visually inspected. No latency SLA is claimed.

Final complete affected backend gate: `tests/test_business_blueprint_*.py` plus `tests/scenarios/test_credit_blueprint_journey.py`: **55 passed in 16.89s**. Lint/spec consistency/diff whitespace checks remain green. No fresh complete repository-suite run is implied.


## Actual Chat/MCP retrieval regression (2026-10-03)

User asked to test the Chat question personally after a screenshot falsely claimed no tests for `credit_exposure`. Browser automation inventory was unavailable (native pipe startup failed, no browsers). Therefore the actual production `reply_via_anthropic_tools` loop was invoked directly with the same configured Anthropic service, no stub model responses. An ephemeral trace wrapper allowed only generic catalog/blueprint reads, refused company-data reads/mutations, recorded call names/arguments, and rolled back the database session. No company records or credentials were included in external tool results. This is actual Chat-service evidence, not a visible browser-chat test.

Before fix: model first called `business_logic_discover(query="credit_exposure",kind="view")`, got empty results, retried broadly, then explained the command. The subsequent provider call failed HTTP400: **311155 tokens > 200000 maximum** because expanded technical graph evidence flooded Chat context. This also explains the screenshot's generic provider failure; the prior screenshot's no-test prose remains an unsupported inference, not system truth.

Regression first: wrong-kind recovery failed on missing `alternative_entries`, and bounded Chat projection failed on missing helper. Shared discovery now exposes bounded genuine alternatives outside requested kind, preserves filtered counts/pagination, and explicitly denies absence inference. Generic unseen-entry proof included. Both provider loops now serialize bounded canonical blueprint evidence (120000 UTF-8 bytes), retaining actual source/rule/test identities, assertions and unknown run outcomes, with total/shown counts; expanded graph/raw bodies remain on-demand technical evidence rather than initial context. Existing full MCP tools are unchanged.

After fix: actual model called discover(kind="tool",query="credit_exposure") then explain(kind="tool",key="credit_exposure",language="de"). Result discovered **32** scenarios, bounded Chat envelope **119361 bytes**; the final German answer described six selected business test examples, including the real **520 EUR** assertion, orders counted once, downpayments, over-limit, other currencies and credit-hold evidence. It stated unknown test-run outcomes and the correct formula and strict threshold. Source testcase numeric example checked against `tests/test_credit_exposure.py`. No success-run, complete coverage or human semantic approval is inferred. Actual answer still did not include the requested source citations and did not clearly distinguish the full 32 discovered scenarios from its six examples; those remain presentation fidelity limits, not a basis to claim no tests. Logs `/tmp/blueprint-chat-live-before.log`, `/tmp/blueprint-chat-live-after.log`.

Verification: focused discovery/Chat suites **24 passed**; complete affected Blueprint + MCP Chat + Anthropic + Chat streaming gates **87 passed in 11.18s**. Lint/spec/diff checks green. Catalog freshness initially detected stale derived capability fingerprints after source changes; regenerate and rerun recorded below. No fresh entire repository suite, deployment, commit or human ERP approval is claimed.

Final Chat citation correction: regression failed on absent `_with_blueprint_evidence`, then passed. Both provider loops append live discovered-test counts and canonical source links after successful explanation reads; unrelated answers remain unchanged. Final affected suite **88 passed in 11.29s**. Catalog regeneration is byte-for-byte idempotent across **24 generated files**. `make docs-catalog-check` still exits nonzero because its gate compares generated content to Git HEAD, and this authorized worktree has intentionally uncommitted generated changes; it does not indicate a stale second generation. No commit was requested or made. Original T033 commit/release gate remains open.

Final actual Anthropic Chat loop passed with citation-footer assertion: discover resolved command identity, explain returned **28** linked scenarios and **118030-byte** Chat context, the German response named six real tests and included the deterministic discovered-count footer plus current source URLs. Log `/tmp/blueprint-chat-live-final.log`. Counts differ for command/tool wrappers because their captured boundaries differ; do not present either as a global test total. Model prose still used imperfect wording ("verified status" alongside unknown-run caveats); the footer makes presence/run distinction explicit, but human semantic review remains necessary. This proves working retrieval and provenance, not universal prose correctness.

## Focused source and UX review correction (2026-10-03)

User-requested UX expert reviewed and implemented the Docs hierarchy; root implemented the shared source helpers and Inspector adapter. Both adapters now separate steps, selectable test cases and technical evidence with keyboard-accessible tabs. Matching source/function/rule spans are marked with original line numbers and context; unrelated helper code is not highlighted. Full-function navigation scrolls within the code pane and reuses the existing response.

The user subsequently preferred Chat-like steps over the duplicate business diagram. FR-028 supersedes that primary diagram; the secondary technical graph remains. Generic live instructions request translated multiline IF/THEN/ELSE only for supported conditional rules. Existing bounded response schema is unchanged; no additional inference or authored operation prose is introduced.

Source-span regressions failed before helpers were added and passed afterward. The new conditional presentation regression failed on the missing generic instruction first (1 failed, 19 passed), then passed with the complete presentation subset (20 passed). Docs tests: 121 passed. Docs and Inspector browser journeys passed exact line marking, whole-function focus, no extra read for local navigation, keyboard tabs, test comparison, freshness/retry and mobile bounds. Both production builds passed.

Actual unmocked German credit-exposure Docs read used the previously authorized source-only Anthropic integration: six interpreted steps and 32 discovered tests. Source/tab/full-function navigation produced exactly one API read total. Root and UX reviewer inspected actual desktop rules, source, tests and mobile screenshots; cited lines were visibly highlighted and hierarchy was distinct. Final updated step layout was inspected again after diagram removal. Evidence: `/tmp/blueprint-ux-live-check.log`, `/tmp/blueprint-ux-live-rules-desktop.png`, `/tmp/blueprint-ux-live-source-desktop.png`, `/tmp/blueprint-ux-live-tests-desktop.png`, `/tmp/blueprint-ux-live-rules-mobile.png`. These checks do not certify natural-language correctness or T047 ERP acceptance.

Final frontend contract suite: **456 passed** (123.56 seconds). Localization audit: **2535/2535** keys for all four languages. `make lint`, `make spec-check` and `git diff --check` passed. T060–T063 complete; human semantic acceptance T047 remains open.

Documentation reading-help relocation: Spec impact: none; existing explanatory text is moved unchanged to English/German standalone reading-guide pages, with a small link from the tool index. No catalog, runtime behavior, business rule or evidence contract changes. Docs production build and diff whitespace checks passed.

Full documentation separation: Spec impact: none; the unchanged agent-selection/confirmation guidance and list assertion-limit explanations now live on bilingual agent-guide/list-guide pages. The overview retains the explorer plus compact guide/manual links. Handbook/MCP/reading-guide links now point to the relocated sections; sidebars expose the guides. Existing content-contract tests follow the new locations: 121 passed. Docs production build passed; diff whitespace checks passed. No executable catalog or business behavior changed.

Documentation navigation refinement: Spec impact: none; navigation and explanatory content only, no executable behavior changed. User approved separating understanding from reference. The bilingual Functions & business logic sidebar now groups principles, inventory/open-work explanations, agent guidance and playbooks under Understand, with the interactive explorer, function reference and analytics model under Reference. Existing reading-guide URLs remain available for compatibility; the standalone view-help item is removed from navigation and concise operating instructions appear in the explorer. English/German browser navigation and page-render checks passed.

Reader-first correction after user review: Spec impact: none; documentation organization only. Restored the previous Tool Usage / Overview, Agents and Analytics navigation with no Understand/Reference subgroups. The interactive explorer remains the primary entry, with brief inline operating guidance. Relocated agent-selection/confirmation text to API and agent interfaces; relocated list assertion-limit text to the ERP guide area. Removed newly added standalone reading/principles pages from this workspace. Updated internal handbook/MCP links and preserved full function manual pages without adding them to the primary sidebar. Docs content suite: 121 passed; production build and whitespace checks passed.

ERP explorer entry correction (FR-029): retained left selection/right detail layout, changed business-object labels to catalog-localized labels, prioritized familiar objects while retaining all others, added catalog-backed read-only entry shortcuts and shortened the intro. Technical/data-model vocabulary remains exact. Regression added before implementation and failed on old labels/layout; full Docs suite passed with 122 tests after implementation. Actual German browser verified the first six object labels/order, starter navigation to credit exposure without executing a tool or requesting live inference, localized resource detail heading and mobile overflow bounds. Root visually inspected desktop/mobile screenshots. No catalog or MCP schema changes, no generated explanation and no business rule changes.

Docs server-address presentation restores FR-027 technical-detail segregation: primary live read shows a business-facing hint, with the configured API address retained in technical evidence. Initial-render regression failed first on the prominent address and passed after the change. Docs suite: 122 passed; production build and diff checks passed. No request, provider, source freshness or business behavior change.

Explanation entry correction (FR-030): initial Docs question and primary Explain steps and rules action replace technical Live logic wording. Loaded state has Steps and rules heading, compact current-code provenance and a secondary refresh action. Regression failed on old wording first; rendered initial/loaded checks passed with all 122 Docs tests. Existing browser delayed-read, freshness/retry, source navigation and test comparison journey passed with the new accessible names. Production build, spec policy and diff whitespace checks passed. No new API/provider call, saved explanation or business behavior.

Business-first detail correction (FR-031) supersedes the separate initial card from FR-030: localized function heading and one catalog purpose appear first, followed by an inline explain action; technical identifier/synopsis/reference follow. Catalog optional descriptions.de provides operation-purpose translations without inferred rules; missing translations retain original text. Reorder-point command/tool labels and purpose translated from existing catalog meaning. Existing technical browsing retains canonical English names. No extra model call or precomputed business explanation. Red-first actual Vue SSR regression passed with all **123 Docs tests**; reference generator proofs: **4 passed, 15 subtests passed**. Production build, existing explanation browser freshness/loading/retry and actual German detail navigation/mobile bounds passed. Root inspected full-page desktop screenshot: localized title/purpose precede borderless action and technical reference. Generated pages/JSON regenerated; repeat generation was idempotent. Spec policy and diff checks passed. Human interpretation acceptance remains separate.

## Isolated PR verification

Prepared on current origin/main in an isolated checkout. Excluded concurrent storage migrations and company-settings work. Renumbered the feature to 343 because current main already owns 337 for drop shipping. Preserved main's updated cross-currency credit behavior when resolving source-comment overlap. Fresh isolated checks: 107 backend feature/catalog/parity tests passed (79.43s); 462 frontend contract tests passed; all four localization audits passed (2701 keys each); 123 Docs tests passed; Docs and frontend production builds passed; Ruff and spec policy passed. The earlier full-database run in this document applies to the original workspace baseline, not this rebased branch. T047 remains open; the PR is a draft for human review, without merge or deployment.

## Direct source entry and exception coverage (FR-032)

Docs exposes a separate source-only action alongside the business explanation. Loaded source opens locally; refreshing uses `interpret=false`. The browser regression verifies both behaviors. Views, projections and registered exceptions are covered by public API tests that fail if the deployment interpreter is accessed. Exception evidence explicitly describes its shared evaluator scope. No business evaluator or test case is executed during inspection.

Verification: 62 business-blueprint backend tests passed; 123 Docs tests passed; Docs production build, browser regression, Ruff, spec policy and affected-file formatting passed. Existing PR checks were green before this follow-up; CI must rerun for the new commit. Human semantic acceptance remains open (T047).

## View/projection source audit and readable navigation (FR-033–FR-035)

Reproduced the commitments request in the actual running browser: HTTP 200 with verified `tenant_commitment_control` source. The earlier generic failure could not be reproduced; the UI now distinguishes HTTP admission/unavailability, malformed responses and network failure rather than obscuring their cause.

The catalog-wide regression inspects every registered view and projection without an interpreter, checks source presence, positive original line numbers/digests and the public 2 MiB response limit. The local deployment audit covered 17 views and 13 projections. Root inventory inspection found the missing public `proposal_reject` handler; its existing decision adapter is now explicitly approved and tested. Commercial terms retain payment-term, price-list and pricing-group readers.

Projection evidence includes the stored reader, the registered change builder where present, and shared full derivation. Source roles are runtime-derived from the existing executable registry. The Docs primary source prefers the registered builder and distinguishes incremental work from stored reads and full fallback. Verified callable resolution records direct callers; local links open the actual called calculation. This does not claim isolated source or complete branch coverage.

Checks: 66 backend feature tests, 124 Docs tests, production Docs build, Ruff and spec policy passed. Actual local browser verified commitments, fulfillment queue and orders, original line numbers, local navigation to `_narrowed_open_work` and return to entry, with desktop/mobile screenshots. Mocked browser regression verifies freshness, escaping and retry. Red-first tests failed for old generic-reader selection and missing rejection source before implementation. The redundant source refresh and selector remain removed under the user's earlier approved design. Source has visual wrapping and original line numbers; formatting does not rewrite the returned bytes. Human semantic acceptance T047 remains open.

## Chat/MCP fixed projection binding (FR-036)

The first adapter parity regression failed: inspecting the public fulfillment queue tool contained no registered builder, although direct projection inspection did. The shared inspector now follows a verified source AST call to the actual `_projection_read` callable and the fixed literal or loaded constant argument. It appends calculation roots from the executable projection registry, retaining the real wrapper/read path and shared-scope limitations. Name similarity does not create this relationship. Dynamic/subscript/unknown/local-shadow arguments are not guessed.

Tests verify application-tool and direct MCP projection evidence have the same digest, and public projection-tool builder function/digest pairs match them. A renamed future adapter with a different runtime constant resolves the actual bound projection. Bounded Chat context preserves source role and verified caller metadata while omitting raw bodies; `business_logic_source` remains the exact evidence read. This tests deterministic routing, not an unconditional guarantee that an LLM selects the correct entry or explains it correctly.

Final complete feature suite: 70 tests passed. Ruff and spec policy passed. No provider transmission was needed for these deterministic adapter tests. Previous Docs tests/build/browser verification remains applicable because this follow-up changes only shared service routing and Chat metadata.

## Compact syntax-colored source (FR-037–FR-038)

The user's screenshot showed soft-wrapped Python statements that were difficult to follow. Direct code now uses 12px monospace with original line numbers and one visible row per source line; long lines scroll inside the panel instead of wrapping. Syntax colors use the existing Shiki 2.5.0 version with only the Python grammar and GitHub light/dark themes explicitly declared. Dynamic imports start only when code is inspected; only selected functions/opened helpers are tokenized. Plain escaped source appears immediately and remains the fallback if highlighting fails. Token content is rendered using Vue text interpolation, with no HTML insertion, source rewriting, model call or external source transmission.

Verification: 124 Docs tests and production build pass. Live-browser regression verifies computed 12px font, preserved white-space and single-row height, at least three syntax colors, unchanged statement text and dark-theme token styles. Real commitments, fulfillment queue and orders reads plus local calculation navigation pass; the colored calculation screenshot was inspected. Ruff/spec policy passed. The browser also verifies that actual keyword colors change under dark mode, and the SSR regression preserves HTML-looking source as escaped text. Generated catalog checks are run against the committed result. The earlier 70 backend tests remain applicable: this change alters only source presentation and declared Docs dependencies.

### Four-section inspector and typography
125 Docs tests passed; production build and browser regression passed. The browser verifies lazy brief/full/source-only reads, current-entry reuse, refresh invalidation, retries, escaped and syntax-colored original source lines, and technical-reference segregation. Real local view/projection inspection verified commitments, orders and fulfillment queue. Presentation uses subordinate query labels and two-column navigation on narrow screens. Human semantic acceptance remains open (T047).

FR-041: 125 Docs tests and production build passed. Actual localhost browser inspection confirmed section heading border/background, heading weight above execution values, and regular related-link weight; screenshot visually reviewed. No external inference requested.

### Source-authored descriptions without external inference (FR-042–046)

- Red-first proof: the initial annotation tests failed, including a configured-provider sentinel reached by the old shared service.
- Final backend feature/credit gate: **92 passed** (`test_business_blueprint_*.py`, credit journey and `test_credit_exposure.py`). Covers generic future names, real marker binding, invalid/duplicate/unresolved sections, empty/oversized sections, conditional THEN text, variants, current docstring drift, helper-purpose isolation, unknown run state, repository audit, and identical public/application authored output while provider access raises.
- Docs: **126 passed**, production build passed. Web: **462 contract checks passed**, production build and localization audit passed. Ruff, formatting, spec policy, annotation lint and regenerated catalogs passed.
- Actual local browser: credit rules loaded in **1,130 ms**, mode authored, model null, 26 described rules and six authored test descriptions; original assertions/source remain inspectable. API read **0.732 s**. Unprepared commitments view returned HTTP 200 in **0.526 s** with original source and six explicit preparation gaps, no provider fallback. Existing freshness/escaping/source/retry browser regression passed. Desktop/mobile screenshots visually reviewed.
- Credit business function and test executable ASTs match their pre-change versions after stripping docstrings. No business calculation, persistence or tenant scope changed. Root preview synchronization used exact previous-PR guards/backups; differing root credit code received only commentary and markers, with unchanged executable AST.
- Authoring audit: **534 entries**, **495 distinct roots**, **five described functions**, **six described direct tests**; **494 roots and 109 approved tests remain unprepared**. The report is repository evidence, not deployed completeness or measured test coverage. Tool wrappers reuse actual called-service descriptions; audit root gaps need review rather than copied narratives.
- T047 human semantic acceptance remains open. Format/citation checks cannot establish semantic equivalence of commentary and code. No whole-repository backend-suite or universal latency guarantee is claimed. No extension hooks configured.

## Complete current source preparation (FR-047–050)

Parallel, disjoint source owners prepared the current catalog and approved direct tests. A subsequent live review expanded preparation beyond adapter roots to actual commitment, fulfillment, currency and invoice helpers. All commentary is English in the original function/test docstrings; exact stable marker comments bind it to actual source statements. No business handler, test or inference provider is executed by a description read.

- Authoring inventory: **534 catalog entries**, **495 distinct runtime root templates**, **558 described physical functions**, **115 described approved test definitions**. No missing registered root descriptions, approved test descriptions, source bindings or annotation errors. Public entries can share physical templates without invented per-operation rules. The gate also rejects future gaps, missing approved files, malformed or duplicate markers and unresolved references.
- **247 backend tests passed** in a coherent frozen-source run after integration with Main, including all approved test files, source/provider boundaries, public/application/MCP parity, future audit gaps, credit journey and payout-cost regressions. An earlier concurrent run correctly rejected seven sources changed after Python import; all passed in subsequent fresh runs.
- **145 Docs tests passed** after the Main rebase, Docs production build and formatting passed. **462 Web contracts**, Web production build and all four localization audits passed; Web files are unchanged by the rebase. Full package Ruff, spec policy, regenerated catalogs and catalog drift check passed.
- Executable AST proof against current Main **cf94d145** covers **63 business source/approved test files** after removing docstrings. The sole documented exception replaces the finance-account lambda with a named pure delegate; its service call and ignored arguments remain identical and have a regression test. Main's payout batching, private source-record storage, atomic transaction boundary and retained reads are preserved. Description bindings moved to actual current implementation functions where Main extracted wrappers.
- Real browser reads use the actual PR public router/service, with no inference model: commitments **19** described rules, fulfillment queue **156** shared/captured rules, supplier-invoice posting **27**, credit exposure **62** and all **28** discovered credit scenarios described. Original source, exact line citations and assertions remain available. Desktop/mobile screenshots inspected. This is source-description presence, not isolated projection scope or complete branch coverage.
- Measured browser reads under the concurrent backend run ranged from about **3 to 18 seconds** for cold/complex reads. Removing inference does not establish a universal 3–5 second bound; no such guarantee is claimed. Reads preserve analysis, source-byte, scenario and freshness bounds.
- Local preview received only comment/docstring transfers where executable functions matched, with backups and unchanged local executable AST. Divergent/unavailable local functions were preserved; the isolated PR is the complete audited catalog snapshot.
- PR #319 was already merged before this expansion. Remaining inspector/source-description follow-ups are rebased onto current Main for a separate PR. Main's new View/Projection navigation and integration handbook remain intact.
- T047 human ERP semantic acceptance remains open. Actual data-flow/branch evidence and test execution remain independent of reviewed commentary. Generated dataclass methods, unprepared helpers and source-boundary limitations are disclosed; this does not claim every repository helper or test has a narrative.

## Runtime source-span indexing (FR-051)

- Indexed function spans once per content-keyed parsed module with a bounded 32-entry cache. Every read still reads current source bytes and retains compiled-code, global/default binding and final freshness checks; no narrative is cached or generated ahead of source. Decorator starts and breadth-first first-match behavior remain identical.
- Three red-first regressions cover decorator/nested/collision parity, repeated capture and revalidation reuse, and changed source invalidation with stale callable rejection. The final focused backend run passed **96 tests** in 48.74 seconds, including release, annotation, service/adapter parity and credit journey checks. The earlier 247 business regression checks remain applicable because no business implementation changed. Ruff, whitespace and spec policy passed.
- Fresh actual-router browser reads measured commitments **2,468 ms**, fulfillment queue **1,321 ms**, supplier-invoice posting **792 ms** and credit exposure **863 ms**. Rule counts remain 19/156/27/62, all 28 discovered credit scenarios retain descriptions, and the inference model remains null. These are local measurements, not a universal latency guarantee.
- T047 human semantic acceptance remains open.
