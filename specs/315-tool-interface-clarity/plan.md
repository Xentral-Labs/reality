# Implementation Plan: Tool interface clarity

**Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)
**Language**: English

## Summary

Publish one localized interface guide from the catalog generator to both Vue and Markdown. Label workspace actions Web actions, add an actual reservation example, and explicitly group operation relationships. Record the three-operation audit; consolidate the proven category-copy duplication only.

## Technical Context

Python 3.12+ catalog generator, Vue/TypeScript VitePress documentation, existing JSON metadata. No storage, dependencies, MCP runtime or business service changes. Node documentation contract tests and Python reference tests plus documentation build provide the required checks.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Catalog presentation only; no record writes | PASS |
| Reality owns operational state | No state/schema changes | PASS |
| Proven schema only | No database changes | PASS |
| Tenant + shared service boundaries | Existing handlers/services untouched | PASS |
| Spec/test traceability | FR/DR mapped below; regression proof precedes implementation | PASS |
| Explainable web behavior | Real command relationships and proposal confirmation explained | PASS |
| Received values not recomputed | No business values processed | PASS |
| Smallest coherent design | Reuse generator/model; reject universal schema/form generation | PASS |

## Repository Structure and Layer Changes

- `apps/docs/scripts/generate-catalog-reference.py`: canonical guide metadata and manual rendering.
- `apps/docs/.vitepress/theme/components/ToolUsage.vue`: consume guide and existing links.
- `apps/docs/scripts/docs-contract.test.mjs`: generated-data and UI integration assertions.
- `apps/docs/scripts/test_interface_guide_reference.py`: renderer/catalog relationship proof.
- `apps/docs/scripts/tool-interface-render.test.mjs`: actual Vue rendering for both languages and mapped/unmapped entries.
- Generated `apps/docs/content/{,de/}tool-usage/` and `.vitepress/data/tool-usage.json`.
- Feature artifacts document audit and verification.

## Design

### Reality and service flow

No domain/service/tool behavior changes. Audit shows Web/action and agent proposal paths reuse application services. The reservation explanation includes preparation, explicit approval and execution rather than suggesting immediate mutation.

### Presentation flow

Generator guide → generated JSON → Vue labels/overview; the same guide → manual tables and example links. Resolve reservation action, command and proposal tool through existing catalogs, fail on inconsistent example references. Derive operation relationship groups from existing entry links, avoiding a new hand-maintained mapping. Keep general business-resource Actions wording.

### Data, migration, failure and security

No migrations or mutations. Preserve technical keys/anchors and public MCP schema. Existing loading/error behavior remains; render the guide only after model load. Category counts retain their current computation. Existing unmapped tools remain discoverable and described.

## Test Strategy and Traceability

| Requirement | Proof | Initial failure |
|---|---|---|
| FR-001, FR-002 | Node contract and Python renderer guide tests | Missing guide and Web label |
| FR-003 | Python/Node catalog-resolved example tests | Missing example metadata |
| FR-004 | Node relationship/UI integration checks | No explicit relationship section |
| FR-005 | Python shared-definition and Node consumer checks | Independent copy remains |
| FR-006 | `research.md` audit and final review | Documentation review, no speculative runtime tests |
| DR-001 | Existing MCP reference/schema tests, identifier comparison and diff review | Compatibility proof; no intended failure |

## Rollout and Rollback

Deploy documentation normally. Revert documentation changes and regenerate to roll back. No client migration. Run all documentation tests/build/format, spec gate and core lint; broader PostgreSQL/backend and operational frontend suites are not required because no executable business path changes.

## Review Risks

Do not equate optional schemas with required service fields, imply proposals execute immediately, count all Web buttons, or rename general resource actions. Keep the guide compact and keyboard-accessible using existing buttons and native disclosure.

## Complexity Tracking

No Constitution exceptions. Post-design check: all rows PASS. Product scope is the already-approved session plan.

## Business-object overview revision (2026-10-03)

Restore individual catalog list entries, counts, searches and typed badges after the user withdrew grouping. Retain the localized View/Projection relationship explanation and navigable links in details. No generator, schema, service or runtime changes. All Constitution rows remain PASS. Validate separate offerings with Vue rendering tests and complete documentation tests; retain the no-push/no-PR instruction.

## Canonical technical category vocabulary

Presentation-only refinement: update shared generator interface-kind labels and localized category headings, Vue View/Projection labels, and existing application catalog category entries. Register ten exact singular/plural terms in the localization invariant registry. Ordinary Actions and control verbs remain localized; no runtime rewriting, new dependencies, schemas or business rules. Add tests first for both rendered docs editions and de/nl/es effective catalogs. Regenerate docs; run documentation tests/build, frontend tests/build/localization audit and spec gate. All Constitution rows remain PASS. Scope approval is the user's explicit instruction.

## Complete business-object navigation

Add two resourceSections from registered entry membership: all related tools and registered Web actions. Render kind badges unconditionally on resource rows; existing Commands remain under business Actions and reads under lookups. No services, generation schema or business behavior changes. FR-012/013 have rendered tests before implementation; events retain existing details unless selected. All Constitution rows PASS; scope explicitly approved.

FR-014: Extend shared generator interface_guide with View/Projection definitions and a catalog-validated reading example. Consume in Vue and existing manual renderer; render guide initially expanded in Technology and link there from objects. Existing reservation example remains. No service/model/schema changes, Constitution PASS. Add rendered tests before implementation; run docs suite/build, generator reference tests, spec and generation repeatability.

FR-015 documentation design: revise both Docs locales and sidebar labels; keep existing routes, nest connector children, add exceptions.md in both locales, retain old exception heading with onward link. Reuse existing code-grounded guides; clarify registered View and Web Action catalog placement without adding business rules. Constitution PASS. Tests precede changes; validate docs suite/build/spec and internal links.

FR-016: Inspect implementation/catalog registrations before documenting templates. Reuse reserve/reservation_propose/reserve_stock, inventory and commitment-at-risk; add dedicated bilingual agent-tools and web-actions pages under entrypoints. Correct existing guide claims, use exact catalog/MCP excerpts with omissions disclosed, include workflow/tenant/confirmation/source and test steps. Validate existing docs tests plus source-backed tutorial assertions/build/spec. Constitution PASS; no executable business changes.

## Proposed systematic extension handbook redesign (planning only)

Status: proposed for review; no content implementation authorized in this planning turn.

### Review findings

The current section grew by appending paragraphs rather than composing a learning sequence. Its introduction combines an orientation table, repository map, implementation workflow and service example before readers have a stable model. The opening table hides the named building block behind long need descriptions and groups distinct interfaces in one row. The View/Projection chapter mixes both instructions, a legacy exception link and examples placed after that link. Guides differ in order and depth. Examples explain registrations but do not consistently identify prerequisites, required changes, resulting behavior and a verification read. API/CLI guidance and full reference material should remain available without interrupting the first learning path.

### Intended reading sequence

1. Overview: audience, prerequisite knowledge, expected outcome and a small relationship diagram. A concise table starts with Building block, followed by Purpose, Example and Guide; one row per View, Projection, Command, Exception, Agent Tool, Web Action and Connector/Interpreter. API/CLI are additional entrypoints linked from their chapter.
2. Configuration or development: keep the existing customization page focused on choosing the smallest extension.
3. First extension walkthrough: one bounded example using an existing service/read model, with prerequisites, actual code locations, required registration/UI wiring and result verification. No new business schema, executable feature or duplicated business rules introduced by the documentation project.
4. Views: a dedicated page covering direct-register and Projection-backed surfaces. Preserve routes and distinguish catalog metadata from actual page/reader integration.
5. Projections: a dedicated page covering derived observations, authoritative inputs, builders, freshness, rebuild and explanation. Keep legacy derived-views URL/anchors as a concise onward reference.
6. Commands: reads and mutations, shared service/application boundary, exact inputs/results, confirmation and replay.
7. Exceptions: condition, affected Reality record, derivation and clearing, with resolution through a Command.
8. Entrypoints: short orientation with dedicated Agent Tool and Web Action tutorials and focused API/CLI guidance. Teach existing operation reuse before schema/form wiring.
9. ERP and data sources: transport versus interpretation, immutable versions, shortest provenance and scheduling. Keep the ERP example and connector contract as subordinate worked example/reference.

Final sidebar labels and ordering should mirror this sequence in both Docs languages. Detailed repository maps and common engineering contracts belong in a shared reference section near the end, linked where needed rather than repeated in every opening.

### Chapter template

Each implementation chapter follows: learning outcome; plain definition and explicit boundaries; when needed; prerequisites; one worked existing example; numbered changes with exact paths and purpose; verify expected result; a small adaptation exercise with expected outcome; common mistakes; next chapter/reference links. Explain the business goal before showing code. Label excerpts and supply the complete source reference; never imply that omitted guards/events are optional. Keep variable/operation names and the same reservation/fulfillment storyline consistent across chapters. Distinguish mandatory steps from optional adapters and configuration-only changes.

### Implementation phases

A. Record approved requirements and map every current paragraph to retain/rewrite/move/remove; resolve scope and pass Constitution review before edits.
B. Restructure bilingual navigation/overview and split View/Projection pages, preserving old routes and anchors. Add the short first-extension walkthrough.
C. Rewrite chapters to the common template, consolidate repeated prerequisites/contracts, and verify every cited registry, function and fixture against repository code. Add missing actionable API/CLI guidance without documenting a parallel executor.
D. Add source-backed documentation/link/navigation tests, render both editions, and review desktop/mobile layouts including table column order and wrapping. Run full Docs tests/build/format, spec policy and relevant generator checks where catalogs change.
E. Perform a novice-path review: follow the first walkthrough using only its stated prerequisites, then adapt the template. Record what can be proved through existing tests and what still requires an actual guided reader trial. Do not claim tutorial executability from string-presence tests alone.

### Acceptance criteria

- Overview table starts with the building block, with short scan-friendly cells and individual Agent Tool/Web Action rows.
- Views and Projections have separate discoverable guides; legacy URLs remain usable.
- A reader can identify the needed building block before seeing file lists.
- Every chapter states prerequisites, required edits, one real example, verification and common failure cases.
- All examples preserve tenant scope, shared services, explicit mutation confirmation and shortest true source/evidence/reality links.
- Existing content is retained or intentionally superseded; duplicate workflow prose and unrelated examples are removed from the primary learning sequence.
- Both language editions share structure and canonical English technical terms.
- Documentation tests/build are green; desktop/mobile rendering is visually reviewed where browser capability is available. Pending visual/reader review is reported honestly.

### Scope and risks

Documentation and navigation only. No new application capability, schema or demonstration company lifecycle. Reject a flat list of unrelated code fragments and unnecessary top-level pages. A full guided reader exercise needs a reproducible local environment and must not mutate a production company. The currently unavailable browser provider may limit visual verification; keep that gate pending instead of declaring it passed.

Approved for implementation by the user. FR-017–FR-021 and T024–T028 trace the proposed design. The first walkthrough uses a training-only inventory read alias as a bounded exercise, with no new domain logic or production registration in this documentation change. Analysis: full requirement coverage, no critical conflict, all Constitution rows PASS.


## Vendor integration guide design

Documentation-only continuation approved by the user. Reuse the existing Connector Contract and add integrations/{xentral,shopify,odoo}.md in both locales, nested under data sources. Do not register runtime capabilities. Tables distinguish candidate source semantics, Reality destinations and actual implementation gaps. Use one authority for duplicated shop/ERP facts; an opening snapshot and later movements have an explicit cutover boundary. Preserve source-stated amounts, shortest provenance and tenant scope. Include live-ingestion reliability, current authority handoff and separately approved outbound design without inventing new infrastructure. Vendor API prerequisites use official documentation, dated/version-qualified; illustrative acceptance stories are not executed integration claims.

Verification before implementation: write and observe a failing bilingual navigation/content test, then implement pages/links/status corrections, run full Docs Node/Python suites, build, scoped format/lint/spec/whitespace and review. No catalog/schema/service changes means no generator change. Constitution Check: all rows PASS; coverage FR-022/023 → T029–T032, no unresolved clarification or critical finding. Spec impact: no business behavior; existing documentation/navigation specification is extended for traceability.

Verification refinement: the allowlisted Connector Contract feeds generated Product Advisor knowledge; regenerate its derived payload and shared references with make docs-generate, then verify output-currentness. This preserves registered business capabilities and adds no vendor runtime.


## Readable Docs layout design

FR-024 is a theme-only behavior refinement approved by the user. Use existing VitePress local-nav outline dropdown rather than add another outline implementation/component. Increase the layout shell to 1680px and ordinary article width to 960px. Hide right aside below 1920px while retaining local navigation; remove the inherited minimum flex width. Fit up-to-five-column prose tables with fixed layout and identifier wrapping at desktop widths; larger/narrow tables keep local overflow. Preserve existing explorer/demo-specific styles, sidebar, anchor behavior and code-block whitespace.

Constitution PASS (presentation only; no source/domain/schema/service/catalog changes). Requirements map to T033–T035. No clarification or critical analysis finding. Validate updated theme contracts first, full Docs Node/Python/build/format/spec gates, and actual browser geometry when available. Browser unavailability must be disclosed, not treated as a passing visual check.

## Integration acquisition guidance design

FR-025 is a user-approved documentation refinement. Add a compact acquisition table under Step by step in both Shopify/Xentral chapters. Cite official API references, distinguish Shopify bulk query support from paginated Xentral reads, and avoid hypothetical finance webhooks. Explain buffered startup, supported incremental filters, overlap/deduplication and freshness. Constitution PASS; no schema/runtime/catalog changes. No unresolved clarification or critical analysis finding. Add the documentation regression check before prose; run complete Docs suites/build and spec/format checks.

## Operating modes design

Add a Shopify observation section and Xentral observation section before prerequisites, with reciprocal links. Reserve the third mode until the user resolves Xentral-master versus Reality-master direction; independent observation prose can proceed. Reviewed scope: Constitution PASS, no schema/runtime changes; master direction is the sole pending clarification. Test observation sections before prose and verify bilingual docs/build; final mode depends on the answer.

Clarification resolved: user selects Reality decides / Xentral executes. Mode C assigns authority per decision, confirmed mutations, no inferred execution, and separately reviewed outbound scheduling. All requirements mapped to T039–T041; Constitution PASS, no critical finding or unresolved clarification before mode C implementation.

## Mode-scoped coverage design

User-approved documentation-only refinement. Add mode/necessity as the second matrix column (five total) and an explicit narrow observation entry scope before each table. Label stock, finance, purchasing and returns by actual observation/decision purpose. Add C-only outbound/feedback row for Xentral. Qualify completeness, acquisition tables and acceptance stories by selected scope; preserve evidence and confirmation. Constitution PASS, requirements mapped to T042–T044, no unresolved clarification or critical finding. Add fail-first docs check before prose; verify suites/build and preserve unrelated UI changes.

Odoo extension review: same five-column matrix and narrow order-observation scope, two clearly named modes without reusing vendor A/B labels. Outbound business examples are not executable API recipes; official version-specific API contract remains linked. Constitution PASS; no unresolved clarification or critical finding. Extend T042–T044 checks to Odoo before prose.

## Progressive example ERP chapter design

User-approved documentation-only chapter at integrations/example-erp.md in both locales; add first sidebar child and links from connector introduction/order example/vendor chapters. Stage-one order view must not claim fulfilled/open quantity without execution coverage: example starts with new orders at cutover and later adds actual shipments. Distinguish stock coverage, future supplier promises, reservations, invoice/payment and optional outbound control. Raw source -> Evidence -> Reality through shared services only; no new catalog/runtime/schema. Constitution PASS; T045–T047 cover FR-028, no unresolved clarification or critical finding. Fail chapter/navigation check before prose; verify docs suites/build/reference/spec/format.

## Agent-centered chapter design

User explicitly requests agent-oriented prose for building an autonomous system. Rewrite chapter introduction, question table and stage outputs; add a short agent-capability statement per stage and describe observe -> assess -> act -> verify loop. Retain setup instructions for owner/developer, existing missing-data boundaries and human confirmation for mutating agent/chat calls; automatic execution requires reviewed contract. Constitution PASS, T048–T050 map requirement, no unresolved clarification/critical finding. Test agent stage framing first; then prose and docs gates. No schema/runtime/catalog changes.

## Source concept chapter design

User-approved information architecture: conceptual chapter before technical rules; stable integrations/connector-contract URL and existing H2 anchors; shared development reference becomes a linked parent with this child. ERP/data-source submenu retains example-erp and vendors only. Technical order-example remains contextually linked and explicitly named implementation. Explain lossless SourceRecord, Document/DocumentLine evidence, Commitment and actual Movement without copied delivery status, SKU identity assumptions or promised live adapter. Constitution PASS, T051–T053 cover FR-030, no unresolved clarification/critical finding. Update fail-first navigation/concept checks; edit both locales and labels, run generation then reference/suites/build/spec/format.

Navigation correction: user chooses concept-first ordering within the ERP/data-source submenu rather than a reference child. Update the two navigation regression assertions first, then shared bilingual config. Constitution PASS, no unresolved clarification or critical finding; no prose/runtime/generator inputs change. Verify targeted contracts/build/full suite and record known independent failures.

## Source revision prose design

Reviewed against store_source_record/enqueue_source/process_import_job and Shopify apply_order_version. Add a concept-first subsection for received payload -> immutable source version -> interpreted linked records -> later revision. Example order reduced from 10 to 8 with 4 shipped yields open 4 only under supported interpreter/complete history. Identity tenant/system/type/external_id, canonical content hash dedup within stream, source timestamp ordering when provided, no universal inference. Full payload refers to received object, not whole ERP; event payloads preserved and authoritative detail fetched under adapter contract. Source provenance follows existing shortest links; Surface is UI. Constitution PASS; T055–T057 mapped, no unresolved clarification/critical finding. Fail docs check before prose, regenerate advisor, verify suites/build.
