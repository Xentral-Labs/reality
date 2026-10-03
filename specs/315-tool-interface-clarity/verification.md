# Verification and review

## Pre-implementation analysis

Reviewed spec, plan and tasks after task generation. Six functional requirements and one domain requirement have scenario and task coverage (100%). Eleven tasks; zero critical findings, ambiguities, conflicting requirements or unmapped tasks. All Constitution Check rows PASS. Product scope was accepted in the session. No extension hook configuration exists. The built-in requirements checklist passed before implementation.

## Test-first evidence

The three new Python guide tests first failed with missing `interface_guide` and `build_interface_guide`, then passed after implementation. The later Vue rendering tests found English-only guide text in the German edition; using the existing localized text helper resolved it. Tests also verify the real reservation mapping, optional agent quantity and rejection of a broken example mapping.

## Final checks

| Check | Result |
|---|---|
| `make spec-check` | PASS |
| `make lint` | PASS |
| Python documentation reference suite | PASS: 14 tests |
| Documentation `npm test` | PASS: 112 tests, including two actual Vue rendering tests |
| Documentation `npm run format:check` | PASS |
| Documentation `npm run build` | PASS; existing bundle-size advisory only |
| `make docs-generate` | PASS |
| Repeat generation | PASS: all 24 generated files byte-identical after regeneration |
| Existing generated catalog entries compared with Git HEAD | PASS: every entry, parameter/schema representation and link identical |
| `git diff --check` | PASS |

`make docs-catalog-check` regenerates successfully, then returns exit 2 because its `git diff --exit-code` compares the intended uncommitted generated changes with Git HEAD. The equivalent stale-output proof for this working tree is the successful byte-identical second generation. No staging or commit was performed to manufacture a green comparison.

An initial build overlapped generation and failed reading an incomplete JSON file; subsequent completed-file builds passed. No browser is exposed in this session, and the sandbox also prevented starting a local listening server; mobile/light/dark browser inspection was unavailable. Actual Vue rendering proves both language guides and command/tool/action detail sections, but does not replace visual or click testing.

## Final review

Only documentation presentation, generator metadata, generated reference pages and tests changed. Existing kind keys, routes, explicit anchors, schemas, handlers and business state are preserved. General business resource/process Actions terminology is retained. The audit covers reservation, order creation and customer payment, including their Web forms. Their shared service/proposal paths already avoid duplicate business implementation; the demonstrated duplicated category definitions were removed from the Vue and renderer copy tables.

No new persistent model, input generator or runtime schema abstraction was justified. No migration, backend PostgreSQL suite or operational application frontend build is required for this documentation-only execution scope, as recorded in the plan. The existing untracked database dump was untouched.

## Integration branch

The original commit's `make docs-catalog-check` passed after commit. The previous branch's PR was already merged, so the documentation commit was cherry-picked onto `codex/docs-tool-interface-clarity` from current `origin/main` (`590c4d72`). Regeneration also applies the shared Command label to the newer main entries in the German manual. The complete main catalog entries, schema representations and links remain identical. The spec gate, 14 reference tests, 112 Node tests and format check were repeated on this integration branch; production build and committed catalog gate are checked before publishing the draft PR.

## Business-object refinement verification (2026-10-03)

Pre-implementation analysis: FR-007/008/009 each map to T012–T014 and US4 acceptance scenarios. DR-001 remains covered. No ambiguity, unmapped tasks or critical findings. Constitution Check remains PASS; scope was explicitly approved in the conversation. No extension hooks are configured.

The two new Vue render tests failed first (duplicate blocker rows and missing read relationships), then passed. Complete documentation Node suite: 125/125 pass. Production VitePress build: pass. Scoped Prettier and git diff whitespace checks: pass. Spec policy: pass. Generated catalog identities and service interfaces remain unchanged by grouping. Actions retain one Command per offering and existing adapter links.

Browser visual verification is unavailable because the computer-use provider exposes no browsers. `make docs-generate` succeeds. `make docs-catalog-check` exits red because it compares generated files to HEAD and the workspace already contains uncommitted catalog changes; this is not a clean-checkout freshness verdict. T014 remains open for the clean-checkout catalog gate and browser review. No completion claim for these outstanding checks.

## User revision: separate Views and Projections

The user withdrew grouping before push/PR creation. Individual rows, badges, counts and search are restored; relationship explanations remain. Updated full documentation suite in the original workspace: 125/125 pass. Previous grouping evidence is historical and does not describe the final behavior. No push or PR was performed.

## Canonical vocabulary and complete object navigation verification

User-approved scope: FR-010–FR-013; existing separate View/Projection rows remain. Pre-implementation analysis reviewed requirements, plan and T015–T020: full coverage, no unresolved clarification or critical finding, Constitution PASS. Category and membership tests were observed failing before implementation. Optional event placement retains existing technical details because no answer was supplied.

Results: complete frontend contract suite 459/459 pass; complete documentation Node suite 127/127 pass; Python reference suite 14/14 pass. Effective-language category tests 15/15 pass after final wording changes. Web and documentation production builds pass. Four-language localization audit, scoped formatting, generator Ruff and spec policy pass. Catalog regeneration succeeds and a second run produces identical catalog/manual content. Scoped review confirms ordinary Actions/controls stay translated, no service/schema/tool identities change, and command-mapped tools use registered resource membership. Global and object search include Agent Tools and Web Actions.

No visual browser run was available; no push or PR created. The historical HEAD-based freshness failure from the dirty workspace remains distinct from repeatable generation; clean-checkout review is still recorded under T014. Generator lint cleanup only formats imports and binds the immediate resource-members lambda to its current collection.

## Shared five-category guide verification

FR-014 specification/design/task review found complete coverage and no ambiguity or Constitution conflict. The initially-open guide assertion failed before implementation. Shared definitions now include all five categories; registered View/Projection/Agent Tool links validate the fulfillment-blocker example, and existing reservation links retain Command/proposal confirmation. Both manuals reuse the guide and both Docs languages render the same metadata. Object navigation links to the existing Technology tab. No new page or business behavior.

Complete Docs Node suite: 129/129 PASS. Python reference suite: 15/15 PASS, including actual read-example relationships and both manual renderers. Docs production build, scoped Ruff, spec policy and whitespace review PASS. Visual browser review remains unavailable. No push or PR created.

## Extending Reality navigation verification

FR-015 scope was approved; pre-implementation review found no clarification, coverage gap or Constitution conflict. Updated navigation/title assertions failed first. Both Docs editions now organize development around Commands, Views/Projections, exceptions and Agent Tool/Web Action/API/CLI entrypoints. Connector example and contract are nested, existing URLs retained, and the old exception sections link to dedicated guides. Existing substantive code examples and service/tenant/confirmation rules remain.

Complete Docs suite: 130/130 PASS, including nested navigation, bilingual guide existence, shared vocabulary and legacy onward links. Production Docs build, spec policy, formatting and whitespace checks PASS. No business commands/tool schemas changed; catalog regeneration is not required for this documentation-only navigation refinement. Visual browser review is unavailable. No push or PR created.

## Self-service extension tutorial verification

FR-016 scope/design and T023 reviewed before changes: documentation-only, no clarification/Constitution/coverage conflict. Both-language pages audited against actual implementation; findings and retained ERP example/contract scope are recorded in research.md. Commands support reads; provenance follows shortest true links; inventory example references _inventory_rows. Dedicated Agent Tool/Web Action pages provide actual registration templates, implementation steps, schema/confirmation boundaries, workspace/form integration and verification stories. They are nested beneath entrypoints and linked from customization/Command guides.

Complete Docs suite: 131/131 PASS, including source-exact MCP excerpt and bilingual tutorial identities/links. Spec and whitespace checks PASS; scoped documentation formatting applied. Visual browser review unavailable. These are implementation-grounded guides, not newly executed business capabilities. No push or PR created.

Final production Docs build: PASS, including internal-link resolution for all added bilingual pages.


## Systematic extension handbook verification (2026-10-03)

FR-017–FR-021 design/requirements/task review passed before implementation; Constitution PASS and no critical analysis finding. A new bilingual table/outline test was observed failing against the old overview. Final coverage checks learning-navigation order, separate View/Projection pages, ordered chapter headings, preserved legacy headings/links and the source-exact Projection builder. The existing exact MCP reservation template and workspace-action relationships remain tested.

Results:
- Complete Docs Node suite: 132/132 PASS.
- Complete Python documentation-reference suite: 16/16 PASS. The new training proof compiles both localized test snippets, constructs the alias using real MCP helpers, compares its full inventory schema, proves tenant/arguments pass through the shared read handler and confirms it is absent from the production registry.
- Executed the tutorial's two tests against the repository-created temporary PostgreSQL database: 2/2 PASS. The alias was injected only into the test process with monkeypatch; the temporary test module was removed afterwards. The fixture seeds 10 units through record_movement and verifies the same nonempty inventory result through both canonical dispatcher names. No production registry/schema/database was changed. Initial sandbox TCP denial was resolved by authorized local-test execution.
- Production VitePress build: PASS, including all bilingual internal links and static pages.
- Scoped Prettier, Python Ruff lint/format, spec policy and whitespace review: PASS.
- Existing local development server on port 5179 responds with its Vite shell. This is availability verification, not visual browser verification.

No catalogs or business-runtime contracts changed for this handbook phase; make docs-generate is therefore not required here. The exercise instructs readers to regenerate after their local registry modification and again after cleanup. Historical unrelated clean-checkout catalog/visual gates remain open under T014.

Review: all planned handbook placements and actual legacy headings were retained or moved deliberately; both locales have the same teaching structure. Browser desktop/mobile inspection and an independent first-time-reader trial were unavailable and are not claimed. No push or PR created.


## Vendor integration guide verification (2026-10-03)

FR-022/023 scope approved by the user; specify/review/plan/tasks/analysis completed before implementation. Constitution PASS; requirements fully map to T029–T032; no unresolved clarification or critical finding. The new vendor test failed first because Xentral navigation was absent. Both locales now have dedicated Xentral/Shopify/Odoo guides, source coverage/gap matrices, ordered implementation steps, a labelled end-to-end acceptance story, operating criteria and official references. The Connector Contract provides shared scoped-completeness, authority/cutover rules and acceptance checklist. Connector/pilot pages and nested data-source navigation link the guides. Stale Shopify update/refund descriptions were corrected against actual services.

Final checks: complete Docs Node suite 133/133 PASS; Python reference suite 16/16 PASS after regeneration; production VitePress build PASS including bilingual internal links; scoped Prettier, spec policy and whitespace checks PASS. make docs-generate PASS. The Python generated-output test initially failed after the allowlisted Connector Contract changed, then passed after refreshing the derived Product Advisor knowledge/capability map. This is a document-derived metadata refresh, not a new vendor capability. The full Node suite/build were rerun after generation and passed. Historical HEAD-based dirty-workspace freshness limitations remain recorded under T014; no clean-checkout freshness claim.

Source-status proof checks actual registry pairs and absence of Xentral/Odoo pairs. Existing tests retain executable inventory/MCP/workspace templates. New end-to-end vendor scenarios are proposed acceptance examples, not real-vendor calls or completed live integration tests. No credentials, vendor effects or business runtime/schema changes; no push/PR. Browser visual review and an independent reader trial remain unavailable and are not claimed.


## Readable Docs layout verification (2026-10-03)

FR-024 scope/design/task review completed before edits; approved scope, Constitution PASS, no critical finding. The added layout test failed first on the old 1500px shell. Article max-width is 960px; shell is capped with min(1680px, 100vw) to avoid negative VitePress sidebar offsets at intermediate widths. The native outline dropdown replaces the aside below 1920px. Up-to-five-column tables fit on desktop; mobile cells retain readable minimum widths with local overflow. Dedicated demo/journey layouts and code-block whitespace are excluded from the prose overrides.

Complete Docs Node suite 134/134 PASS; Python reference suite 16/16 PASS; scoped Prettier, spec policy and whitespace checks PASS. Native Chrome inspection was available despite no browser connector: wide desktop screenshot confirms widened content and retained aside; responsive 1705px screenshot confirms all four Xentral columns fit, aside is hidden and the localized outline dropdown opens and navigates to the matrix heading without covering it. Responsive 390px inspection exposed squeezed mobile columns; added minimum column widths and rechecked readable cells with overflow confined to the table. Normal browser mode was restored. Native horizontal gesture did not provide a conclusive changed screenshot, so programmatic scroll geometry/keyboard table interaction is not claimed. An unrelated pre-existing widget.js HTML/syntax error was visible in DevTools; this CSS change neither adds nor repairs that integration.

No business logic, catalog, schema or generated advisor content changes for this layout phase. No push or PR.

Final layout production VitePress build: PASS. Visual evidence is the German Xentral page; shared CSS/contracts cover both editions, but an English screenshot or automated DOM geometry check was not performed.

## Integration acquisition guidance verification (2026-10-03)

FR-025 requirements/design/tasks reviewed before prose: user-approved scope, Constitution PASS, no unresolved clarification or critical finding. New bilingual acquisition check failed first on missing sections. Shopify/Xentral chapters now include initial capture, named verified triggers, suggested fallback intervals and official references. Startup buffering, replay/checkpoints, source version deduplication, resource-specific filters and daily reconciliation are explained. Shopify Bulk completion is distinguished from business events; Payments uses separate reads. Xentral dispatch/document communication is distinguished from physical warehouse execution. Intervals are recommendations, not implemented connectors or vendor guarantees.

Complete Docs Node suite: 135/135 PASS. Python documentation-reference suite: 16/16 PASS. Production VitePress build, scoped Prettier, spec policy and whitespace checks: PASS. Reviewed both localized sections and official sources. No runtime/schema/catalog or advisor-input changes; generation unnecessary. No live vendor calls, new visual verification, push or PR claimed.

Final rerun correction: after a small prose heading/checkpoint wording cleanup, acquisition checks still PASS, but the workspace-wide Node rerun is 130/135: five ToolUsage rendering/live-contract checks fail amid additional independent component changes (ToolUsage.vue, LiveBusinessBlueprint.vue, SourceEvidence.vue). These are outside this documentation scope and were not overwritten. T038 remains open; the earlier 135/135 result describes the earlier workspace state, not the latest tree.

## Operating modes verification (2026-10-03)

FR-026 reviewed; observation check failed first. Master direction clarified explicitly by the user: Reality decides, Xentral executes. Both locales now explain A Shopify observation, B Xentral observation and C Reality-owned scoped decisions with outbound requests. User further clarified concrete invoice-creation/shipping-release Commands; prose explicitly distinguishes these business examples from implemented command names/API calls. Original payloads and local interpretation remain, no outbound runtime is introduced. Confirmation, idempotency, independent execution evidence and competing automation boundaries are explained.

Targeted observation/master/acquisition checks PASS. Python reference suite 16/16 PASS. Full Node suite 132/137; same five independent ToolUsage render/live-contract failures persist. Build PASS, formatting/spec/whitespace PASS. T039/T040 complete; T041 remains open because the required full suite is red. No unrelated components changed, no push/PR, no live vendor effect or visual check claimed.

## Mode-scoped coverage verification (2026-10-03)

FR-027 user-approved scope and Odoo extension reviewed before prose; Constitution PASS, no unresolved clarification/critical finding. Both new checks failed first. Shopify, Xentral and Odoo matrices in both locales now have five columns including mode/necessity. Narrow observation entry requires orders/lines, relevant changes and identity/context; stock, delivery, finance, purchasing, returns and optional modules are goal-dependent. No full master-data import is universally required. Xentral C and Odoo execution require reviewed outbound requests and returned evidence only for transferred decisions. Completeness/acquisition/acceptance framing is scoped rather than mandatory full-system integration. Odoo has separate read-only and Reality-directed execution sections with order/shipping/invoice examples, confirmation and implementation limits. No live adapters or business runtime changed.

Targeted acquisition/modes/coverage/Odoo checks PASS. Full Node suite 134/139; same five unrelated ToolUsage render/live-contract failures remain. Python reference suite 16/16 PASS. Production VitePress build PASS; scoped Prettier, spec policy and whitespace PASS. T042/T043 complete, T044 remains open while the required complete suite is red. Official Odoo API search corroborates version-specific access/security; direct page retrieval timed out and no new executable method recipe is claimed. Existing official reference remains linked. No catalog/allowlisted advisor-input changes; generation unnecessary. No unrelated UI components changed, visual review, live vendor effects, push or PR claimed.

## Progressive example ERP chapter verification (2026-10-03)

FR-028 user-approved requirements/design/tasks reviewed before implementation; Constitution PASS, no unresolved clarification or critical finding. New chapter/navigation test failed first. Both locales now have integrations/example-erp.md as the first child of ERP/data sources, with links from connector introduction, technical order example and vendor guides. Seven stages explain required upstream data, illustrative business output, unknowns and acceptance checks. Narrow observation distinguishes stated promises from reliably open delivery quantities; historical execution/cutover completeness is explicit. Shipment 4 against promise 10 leaves 6; later opening stock 3 plus receipt 3 gives physical 6 without subtracting historical shipment twice; supplier promise 5 and linked receipt 3 leaves expected 2; other-customer reservation 2 leaves calculated available 4. Invoice 80 and allocated successful payment 30 leave 50 under its stated finance contract. Examples do not introduce a connector, API recipe or executable product capability.

Chapter regression PASS. Full Node suite 135/140 with the same five independent ToolUsage render/live-contract failures; no unrelated components overwritten. Python reference suite 16/16 PASS. Production build, scoped formatting, spec policy and whitespace PASS. T045/T046 complete; T047 remains open while the required full suite is red. No catalogs or allowlisted advisor inputs changed, so generation is unnecessary. No actual vendor calls, new browser visual verification, push or PR claimed.

## Agent-centered chapter verification (2026-10-03)

FR-029 user-approved prose refinement reviewed before edits; Constitution PASS, no unresolved clarification or critical finding. Stage agent-capability check failed first. Both example ERP chapters now lead with building an autonomous system; the table asks what the agent can answer and each stage explicitly explains its read/proposal/execution capability. Setup responsibilities remain assigned to the owner/developer. The agent uses shared tools/services; automatic execution requires reviewed authority, mutating agent/chat calls retain human confirmation. The final stage explains observing, assessing, acting and checking evidence without claiming a newly implemented autonomous runtime.

Targeted chapter tests PASS. Full Node suite 136/141, same five unrelated ToolUsage failures. Python reference suite 16/16 PASS. Production build, scoped Prettier, spec policy and whitespace PASS. T048/T049 complete; T050 open while the full required suite remains red. No runtime/catalog/schema/allowlisted advisor changes, live vendor effects, browser visual checks, push or PR.

## Source concept chapter verification (2026-10-03)

FR-030 user-approved concept/navigation refinement reviewed before implementation; Constitution PASS, no unresolved clarification/critical finding. Navigation and source-concept checks failed first. Both stable connector-contract URLs now lead with From source data to Reality / Von Quelldaten zu Reality, explaining Source, Evidence and Reality with a new order of 10 and actual shipment of 4, yielding read-time remainder 6 under complete history. Connector/interpreter/shared-service responsibilities precede retained identity/version/error/acceptance rules and existing anchors. Concept page is a child of shared development reference; data-source menu contains example ERP and vendors only. Technical order example is renamed and remains contextually linked. Public link labels updated; scope-dependent coverage/checklist retained. Added the missing exampleErp label type for the existing new sidebar entry.

Targeted concept/navigation checks PASS. make docs-generate PASS, including derived Product Advisor knowledge. Python reference suite 16/16 PASS after generation. Full Node suite 137/142 with the same five unrelated ToolUsage failures. Production build, scoped formatting, spec policy and whitespace PASS. T051/T052 complete; T053 remains open because complete required Node suite is red. Historical HEAD-based dirty-tree catalog freshness caveat unchanged. No runtime/schema/new vendor capability or unrelated UI-component change, live vendor effects, new visual review, push or PR.

## Concept-first navigation correction (2026-10-03)

User corrected FR-030 placement: concept page is now first directly under ERP/data sources, before the progressive example and vendors. Shared development reference returns to a simple sibling link. Both updated navigation checks failed first, then passed; existing example chapter check also passes. Shared locale config covers both editions. Production build, formatting, spec policy and whitespace PASS. Full Node suite remains 137/142 with five independent ToolUsage failures. T054 implementation is present but remains open because the required full suite is red. No prose/generator input/runtime change; no new generation or visual review claimed.

## Source stream/revision explanation verification (2026-10-03)

FR-031 user-approved explanatory refinement reviewed against actual store_source_record, enqueue_source, process_import_job and shop_order_changes contracts before prose; Constitution PASS, no unresolved clarification/critical finding. New source-stream semantics check failed first. Both chapters now explain original received object capture, tenant/system/type/external_id SourceStream identity, canonical payload-content dedup, immutable versions, optional source timestamp stale/conflict classification and interpreter-specific update semantics. Source versus Surface, change events/detail reads, own linked business records and shortest provenance are distinguished. Supported order reduction example 10 -> 8 with shipped 4 leaves 4 only under complete coverage; not generic arbitrary field-diff interpretation. No source/runtime semantics changed.

Targeted source concept/revision checks PASS. make docs-generate PASS, derived advisor refreshed. Python reference suite 16/16 PASS. Full Node suite 138/143 with the same five independent ToolUsage failures. Production build, scoped Prettier, spec policy and whitespace PASS. T055/T056 complete, T057 remains open while complete required suite is red. No live vendor calls, new visual checks, unrelated UI edits, push or PR.

## Isolated PR verification (2026-10-03)

PR branch codex/docs-extension-handbook starts from current origin/main d86d45c6 in a separate worktree. Copied the scoped bilingual handbook, integration guides, layout and type vocabulary changes; regenerated catalogs against this branch's executable registry. ToolUsage changes include type/read relationships and badges only; unrelated incomplete LiveBusinessBlueprint wrappers, backend work and other main-worktree edits are excluded. Current-main navigation entries outside this scope are preserved. The original workspace's five render failures do not occur here. Historical red-state notes above describe that workspace, not this reviewed branch.

Full Docs Node suite 142/142 PASS. Full Python Docs suite 16/16 PASS using PYTHONPATH=packages/reality-core/src (required to select this checkout over the shared editable installation). Production build, complete Docs Prettier check, Python Ruff lint, spec policy and whitespace PASS. Generation PASS. Reference tests exercise the first-extension schema/handler against this branch's actual registry. No new live integration or automated execution is claimed. A supplementary generator Ruff-format probe fails on both unchanged origin/main and this file; repository CI requires Ruff lint and Docs Prettier, both pass. No unrelated mass Python formatting was introduced.

Relevant verification tasks are closed for the isolated branch after the required green suites; final generated freshness is checked against the committed branch. Earlier desktop/mobile visual evidence remains recorded above; no new screenshot or first-time-reader trial claimed.

Committed-branch make docs-catalog-check: PASS, with no generated-file diff after complete regeneration. This resolves the earlier dirty-workspace freshness limitation for the isolated PR branch. Final diff contains no apps/web, reality-core/src, migration or unrelated Blueprint changes.
