# Feature Specification: Explainable Business Logic and Test Blueprints

**Feature Branch**: `codex/live-business-logic-blueprints`
**Created**: 2026-10-03
**Status**: Scope accepted for planning — user continuation on 2026-10-03
**Language**: English
**Input**: Make the ERP's business logic readable and inspectable by ERP professionals, with source-backed flow diagrams or business pseudocode, shared across Web, documentation, Chat and MCP. Show existing tests as understandable business cases and compare a user's case with their actual tested conditions.

## Context and Intent

### Problem

The executable catalogs expose available operations and reads, but a professional cannot consistently inspect their actual decision rules, calculation inputs, refusal conditions or tested business scenarios. Source code alone is difficult for non-developers to evaluate. Independently written or pre-generated explanations risk drifting from implementation. The user explicitly requires explanations derived dynamically from the actual live source, rather than maintained or generated ahead of time. Users need to assess both how the system behaves and whether their own situation matches a proven test case.

### Scope

- A shared business blueprint derived on demand from the live source of the running application version for public commands, agent tools, Web actions, views and projections, including the underlying shared rules they invoke.
- Readable purpose, prerequisites, inputs, calculations, decisions, effects and refusal paths, presented as business steps and a flow diagram.
- Inspectable implementation and requirement references, plus existing executable tests described as business scenarios.
- Equivalent dynamically derived explanations and evidence through the Web technical catalog, public Tool Usage documentation, Chat and MCP.
- Read-only comparison of a described or authorized company case with existing test scenarios, and explanation of current decisions where evidence is available.
- Credit-limit checking and delivery release as the mandatory end-to-end reference journey, using actual existing behavior rather than the illustrative examples in the discussion.
- No pre-generated explanation, diagram or test-case catalog may serve as the current business blueprint; current content is derived at read time from actual source and executable registrations.
- An inventory of all public entries with explicit complete, partial, missing or outdated explanation status; shared logic is explained once and referenced by its consumers.

### Non-Goals

- Changing credit policy, fulfillment rules, financial calculations or any other existing business behavior.
- Executing a mutation or running arbitrary tests from an explanation request.
- Claiming arbitrary source code can be translated automatically into a verified business explanation.
- Building a second rule engine, storing derived observations as business authority, or introducing universal execution logging.
- Retroactively claiming complete test coverage or historical execution evidence where none exists.
- Exposing secrets, production fixtures, private infrastructure code or unauthorized tenant data.

### Existing Contracts

- [Architecture](../../docs/ARCHITECTURE.md): shared application boundaries and executable vocabulary.
- [Web specification](../../docs/WEB_SPEC.md): simple surface and explainable operational results.
- [Test strategy](../../docs/TEST_STRATEGY.md): unit, service, business-story and adapter evidence.
- [Constitution](../../.specify/memory/constitution.md): traceability, tenant scope, shared services and received-value authority.
- [Spec workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md): review and verification gates.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspect a business operation (Priority: P1)

An ERP professional opens a catalog entry and reads its real business procedure, including decisions and failure paths, then follows a step to its source and governing requirement.

**Why this priority**: Makes actual behavior reviewable without requiring programming knowledge.
**Independent Test**: Inspect the credit-limit/delivery-release reference journey and establish its inputs, boundary behavior, refusals and effects from the blueprint and linked implementation.

**Acceptance Scenarios**:

1. **Given** a supported operation, **When** its blueprint is opened, **Then** purpose, trigger, prerequisites, inputs, ordered steps, calculations, branches, effects and refusals are readable in business language and as a diagram.
2. **Given** several adapters invoking the same rule, **When** each is inspected, **Then** each links to the same rule identity and version, while adapter-specific prerequisites are distinguished.
3. **Given** changed or missing source evidence, **When** the entry is read, **Then** the explanation is derived from the exact running version or explicitly reports unavailable evidence; a previous explanation cannot stand in for current source.
4. **Given** the complete public inventory, **When** a professional searches by business topic or technical entry name, **Then** matching entries and their explanation status are discoverable, including entries without a completed blueprint.
5. **Given** an application release changes a decision and its tests, **When** the blueprint is next requested without any explanation-generation step, **Then** it reflects the new running source and tests and identifies the new version.

### User Story 2 - Inspect tested business cases (Priority: P1)

A professional reads the tests associated with a rule as concrete business examples and checks whether their assumptions match the user's situation.

**Why this priority**: Distinguishes an understandable rule from demonstrated behavior.
**Independent Test**: Read linked acceptance, refusal and boundary cases and verify each description against its executable assertions and fixtures.

**Acceptance Scenarios**:

1. **Given** a linked test, **When** its business case is opened, **Then** setup, relevant values, action, expected result, asserted effects, tested rules and executable source are visible.
2. **Given** parameterized tests or shared fixtures, **When** their cases are inspected, **Then** distinct relevant conditions and fixture assumptions are preserved rather than collapsed into an inaccurate example.
3. **Given** a branch without a linked test, **When** its blueprint is inspected, **Then** the missing evidence is explicit; a nearby test does not imply branch coverage.
4. **Given** a recorded test run, **When** its result is shown, **Then** outcome, run time, tested code version and evidence location are shown; absent, skipped, failed or older-version results cannot be presented as current success.

### User Story 3 - Ask through Chat or MCP (Priority: P2)

A user asks how a business process works or which tests cover it and receives the same grounded explanation available in the documentation.

**Why this priority**: Makes the evidence usable through every application entry point.
**Independent Test**: Ask equivalent credit-limit questions through Chat and MCP and compare their rules, versions, conditions and citations with Web and documentation.

**Acceptance Scenarios**:

1. **Given** a supported topic, **When** Chat explains it, **Then** the answer uses business language, cites the applicable blueprint and evidence, and preserves conditional rules and uncertainty.
2. **Given** the same topic, **When** an MCP consumer requests it, **Then** it receives identifiable steps, branches, rule references, tests and evidence status sufficient to inspect the same explanation.
3. **Given** an unsupported or outdated topic, **When** either channel is asked, **Then** it reports the evidence limitation instead of inventing a rule or test.
4. **Given** equivalent deployed and published versions, **When** all channels are compared, **Then** their substantive rules and test references agree; different versions are visibly identified.

### User Story 4 - Compare my case and explain a decision (Priority: P2)

A user supplies a situation or selects an authorized business record and sees which tested conditions match, which differ and which are unknown.

**Why this priority**: Helps determine whether a refusal is expected and whether a reported defect has existing evidence.
**Independent Test**: Compare a matching case, a materially different case and an incomplete case with the reference journey's real tests, without business mutations.

**Acceptance Scenarios**:

1. **Given** a fully described case, **When** it is compared with a test, **Then** each relevant prerequisite and value is classified as matching, different or unknown, with the relevant rule references.
2. **Given** insufficient information or no applicable test, **When** comparison is requested, **Then** missing inputs and untested aspects are stated and the case is not declared proven.
3. **Given** an authorized record with available decision evidence, **When** its result is explained, **Then** the applicable rules, available decisive values and shortest evidence links are shown; current-state reevaluation is distinguished from a recorded historical decision.
4. **Given** a record belonging to another tenant, **When** explanation or comparison is requested, **Then** it behaves as not found and discloses no record or values.

### Edge Cases

- Empty test mappings, renamed or deleted functions/tests, unavailable source links and unavailable test-run evidence.
- Exact numeric boundaries, Decimal precision, currency, units, dates and configuration-dependent branches.
- Adapter-specific authorization or confirmation requirements despite a shared business operation.
- Tests that prove only a calculation or transport contract, rather than an end-to-end business result.
- Corrected records, partial fulfillment and changes after the original decision; no historical reconstruction presented as observed fact.
- Caller-provided facts that contradict held evidence; preserve the distinction and identify disagreement.
- Diagrams unavailable to a reader: the text must communicate the same decisions and outcomes.
- A newer public documentation release than the deployed application, or only an older passing test run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every public command, agent tool, Web action, view and projection MUST have a discoverable inventory entry, linked blueprint or explicit missing status, searchable by business topic and technical identifier.
- **FR-002**: Each completed blueprint MUST explain purpose, trigger, prerequisites, relevant inputs and their authority, calculations including units and boundary comparisons, ordered decisions, success paths, refusal conditions, effects and outputs. Inapplicable sections MUST be identified as such rather than invented.
- **FR-003**: Each completed blueprint MUST provide equivalent readable business steps and a flow diagram whose decisions and outcomes have identifiable links to the explained rules.
- **FR-004**: Shared rules MUST have stable identities, and their adapter consumers MUST reference the same explanation; adapter differences MUST be separately identifiable.
- **FR-005**: Explained rules MUST expose source references, applicable requirements and the code version they describe. Professionals MUST be able to inspect the relevant safe source text and navigate to its version-specific location.
- **FR-006**: Explanation status MUST distinguish complete, partial, missing and outdated evidence. Broken references and source changes MUST never allow a previous explanation to be presented as current. Dynamic derivation MUST identify unsupported analysis or unresolved semantics instead of substituting an earlier description. Status MUST NOT imply proof of full semantic equivalence.
- **FR-007**: Each linked executable test MUST have a business-readable case stating actual setup, relevant fixture assumptions, inputs, action, expected result, asserted effects, test type and covered rule identities. Descriptions MUST NOT claim assertions the test does not make.
- **FR-008**: Relevant parameterized cases MUST remain distinguishable. Each decision branch MUST expose linked test cases or explicitly missing test evidence, without claiming aggregate completeness from test existence.
- **FR-009**: Test definitions and test-run results MUST be separate. A reported run MUST identify outcome, time, code version and evidence location; no run, skipped, failed, unavailable and older-version evidence MUST be visibly distinguished from current passing evidence.
- **FR-010**: Web technical entries and public Tool Usage documentation MUST retrieve current blueprints, diagrams, test cases and source evidence dynamically, with consistent identities and visible running-source versions. A static documentation deployment MUST identify its live explanation target; unavailable live retrieval MUST be explicit rather than replaced with a pre-generated explanation.
- **FR-011**: Chat and MCP MUST offer read-only discovery and retrieval of the same explanations and test evidence. Chat answers MUST cite evidence and disclose missing or outdated information; MCP consumers MUST receive identifiable rules, branches, scenarios and evidence status.
- **FR-012**: Case comparison MUST show matching, differing and unknown relevant conditions, identify untested aspects and cite the actual test cases. Similarity MUST NOT be represented as proof of the user's outcome.
- **FR-013**: Concrete decision explanations MUST use available shared-service evidence and identify decisive values and rule references. Recorded historical facts, current-state evaluation and caller assumptions MUST be distinguished; absent historical evidence MUST be stated.
- **FR-014**: Explanation, source inspection, test retrieval and comparison MUST NOT mutate business records, execute proposals or run arbitrary code. Existing authorization and confirmation boundaries MUST remain unchanged.
- **FR-015**: The initial release MUST fully explain the existing credit-limit/delivery-release reference journey across all four surfaces, including every decision branch in its declared boundary and actual linked tests or explicit gaps. Other public entries MUST remain inventoried with honest coverage status.
- **FR-016**: Explanations MUST follow existing presentation-language conventions, with business-readable localized presentation where supported and explicit English fallback. Stable identifiers and source text MUST remain exact; published examples MUST use synthetic data.

- **FR-017**: Every explanation request MUST derive its business steps, diagram and test-case descriptions on demand from the actual source and test definitions matching the running application. Pre-authored or pre-generated descriptions MUST NOT be the authority for current behavior. Requirements and labels may provide context but MUST NOT override executable evidence.
- **FR-018**: Each response MUST identify the exact running release/source revision and resolved evidence version. Mutable working-copy files, repository default branches and a different documentation release MUST NOT be described as the executed implementation. If deployed source or tests cannot be inspected, the affected content MUST report unavailable evidence.
- **FR-019**: A source-version change MUST be reflected on the next explanation request without a manual documentation build or blueprint refresh. Any reuse of analysis MUST be demonstrably bound to unchanged source evidence; pre-generated final explanations MUST NOT replace on-demand derivation. Test discovery MUST reflect actual test definitions and distinguish discovered tests from executed results.

### Domain and Traceability Requirements

- **DR-001**: Concrete explanations MUST preserve Source → Evidence → Reality where applicable and follow shortest true links. Generic blueprints and tests describe logic; they are not new business evidence or authority.
- **DR-002**: Explanations MUST preserve the distinction between source-stated amounts and derived observations and MUST NOT recompute source-owned values or add operational status to documents.
- **DR-003**: All channels MUST use shared application explanation and business services. Company-case reads MUST enforce tenant scope and current access; static public explanations MUST contain no tenant data or secrets.
- **DR-004**: Blueprint, rule, scenario and version identities MUST be stable references distinct from human business numbers. This feature MUST NOT introduce business schema solely to duplicate derived state or evidence links.

### Key Entities *(when data is involved)*

- **Business Blueprint**: On-demand, source-version-identified explanation of an operation or read, its decisions and effects, linked to public consumers and implementation evidence.
- **Business Rule**: Identifiable prerequisite, calculation, decision or refusal shared across relevant blueprints.
- **Test Scenario**: Business-readable representation of an actual executable test case and its proven assertions.
- **Verification Evidence**: A separately identified test-run outcome tied to a code version and time.
- **Case Comparison**: Read-only assessment of supplied or authorized conditions against test assumptions, including unknowns and differences; not business authority.

## Success Criteria *(mandatory)*

- **SC-001**: 100% of public entries in the release inventory have a discoverable explanation status; none silently disappear because their blueprint is missing.
- **SC-002**: The reference journey exposes 100% of its declared decision branches with source references and either linked actual test cases or an explicit test gap.
- **SC-003**: An ERP professional can identify the reference journey's required inputs, decisive comparison, refusal reason and closest tested case within five minutes without reading source code, demonstrated in a documented review exercise.
- **SC-004**: Equivalent questions across Web, documentation, Chat and MCP identify the same rules and scenarios for the same release, with zero contradictory boundary or refusal statements in acceptance checks.
- **SC-005**: All missing, stale, failed and skipped evidence fixtures are presented without a false claim of current verification, and all unauthorized company-case checks disclose zero tenant data.
- **SC-007**: In a controlled release-change acceptance exercise, the first explanation request after each rule/test change reflects the running version without a separate explanation-generation step; no previous-version explanation is labeled current.
- **SC-006**: Every FR and DR has an acceptance scenario and planned executable proof; linked scenario descriptions match their actual test assertions.

## Assumptions and Dependencies

- The user accepted continuation into planning; implementation follows tasks and analysis with all repository gates satisfied.
- Full inventory coverage is mandatory; deep explanations beyond the reference journey may be added incrementally, with visible incomplete status.
- Existing catalog, documentation generation, source repository, test suites, Chat tools and MCP boundaries are reused conceptually; their exact design is determined during planning.
- The user requires dynamic derivation from live source and tests, not a maintained explanatory catalog. The exact analysis approach is determined during planning. Version equality establishes freshness, not semantic correctness; grounding and uncertainty checks remain mandatory.
- No new historical decision capture is assumed. Existing evidence is used, and unavailable history is disclosed.
- Public documentation needs live read access to approved generic explanation evidence, without tenant access; deployment and unavailable-target handling are planning concerns.
- Public source inspection is restricted to approved business implementation and synthetic test content; tenant-specific comparison remains authenticated.
- Diagram layout, evidence storage and change-detection mechanism are planning decisions, not new business rules.

## Open Questions

User clarification: explanations, diagrams and test descriptions must be derived dynamically from actual live source, never generated ahead of time as their authority. No unresolved clarification markers. User continuation accepted the specified scope for planning. No implementation is authorized by this planning artifact alone.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1.4 | Full public-inventory discovery and missing-entry proof |
| FR-002, FR-003 | US1.1 | Reference journey text/diagram branch equivalence and professional review |
| FR-004 | US1.2 | Shared-rule identity and adapter-difference proof |
| FR-005, FR-006 | US1.3 | Versioned source navigation, changed/deleted evidence and status proof |
| FR-017–FR-019 | US1.3, US1.5, US2.4, US3.4 | On-demand live-source derivation, release-change freshness, unavailable deployed tests and live-docs target proof |
| FR-007 | US2.1 | Scenario-to-assertion and fixture grounding review |
| FR-008 | US2.2, US2.3 | Parameterized cases and unmapped branch fixtures |
| FR-009 | US2.4 | Passing, failed, skipped, missing and older-version run fixtures |
| FR-010 | US3.4 | Web/docs identity, evidence and release-equivalence proof |
| FR-011 | US3.1–US3.3 | Chat/MCP retrieval, citation and missing-evidence proof |
| FR-012 | US4.1, US4.2 | Matching, differing, incomplete and untested case comparisons |
| FR-013 | US4.3 | Available history versus current evaluation and unknown history proof |
| FR-014 | US3.1, US4.1–US4.4 | Read-only and unchanged confirmation-boundary proof |
| FR-015 | US1.1, US2.1–US2.4, US3.4 | End-to-end reference-journey coverage review |
| FR-016 | US1.1, US2.1, US3.1 | Localized presentation, fallback and synthetic example checks |
| DR-001, DR-002 | US1.1, US4.3 | Provenance, source-authority and no duplicated derived-state proof |
| DR-003 | US3.4, US4.4 | Shared-service parity, public data safety and tenant isolation |
| DR-004 | US1.2, US2.1 | Stable identity and no additional business authority review |

## ERP readability correction (2026-10-03)

The user rejected the initial source-statement presentation as unreadable. The existing FR-002/FR-003 and SC-003 remain unsatisfied by literal Python-to-prose rendering. This correction is approved by the user's continuation; there are no unresolved clarifications.

- **FR-020**: On English and German detail reads, all four surfaces MUST expose the same request-time business presentation: source-cited calculations, input validation, decisions, refusals and effects using business vocabulary. Technical assignment scaffolding, internal identifiers and release digests MUST NOT dominate the primary reading view. Unsupported semantics MUST be described as not yet explained, never guessed or hidden as complete.
- **FR-021**: The primary view MUST show the business rules before expandable technical analysis. Each business step MUST retain its original rule/source links. Its flow diagram MUST preserve real source branch outcomes across omitted technical nodes; it MUST NOT invent execution order between independent functions.
- **FR-022**: Discovered tests MUST expose source-derived Given/When/Then summaries in English and German; supplied test facts, assertions and unknown setup remain distinguishable. An untranslatable assertion MUST remain available in technical evidence and be counted as not yet explained. Test existence MUST NOT imply a passing execution.

Acceptance: credit exposure shows the source-derived exposure formula and the exact positive-limit/strict-excess condition, without initialization loops. Item creation shows required fields, allowed item/tracking values, nonnegative lead time and item/event effects. Changing a source expression or allowed value changes the next explanation without editing prose. Unknown business meanings stay explicit. Web/docs show those same server-derived sentences and keep source access. A real ERP-professional review remains required for SC-003; automated wording checks cannot substitute for it.

### Live LLM clarification (user-approved)

The explanation must work generically for existing and future registered operations. The user explicitly permits LLM interpretation at read time, but prohibits pre-generation beside source code. Vocabulary-only translation is insufficient. The shared live service may use the configured deployment model with verified code/test evidence only, without company records or executing tools. Model text is identified as interpretation; validated citations prove reference identity, not semantic correctness. Source unavailable/outdated or provider failure must yield an explicit unavailable interpretation with technical evidence retained. No per-operation text files, saved model answers or keyed financial rules are permitted.

### Loading and diagram usability correction

- **FR-023**: Docs and Web live reads MUST show an accessible animated waiting indicator, elapsed time and an honest explanation that current source and tests are interpreted on demand. No fabricated completion percentage or provider phase. Entry changes and completion stop the timer.
- **FR-024**: The primary business flow MUST display full step text at normal reading size with wrapping and no horizontal clipping on desktop or narrow screens. Numbered cards expose only actual supplied outgoing edges and their original outcomes; disconnected steps are explicitly distinguished from an inferred continuous process.

Acceptance: delay a response, observe waiting feedback and disabled read control, then verify cleanup on completion and navigation. At desktop and 390px viewport width, read a long business sentence completely and follow a supplied branch to its numbered target; no horizontal overflow, truncation or invented edge.

- **FR-025**: Interactive reads initially request a brief live interpretation with at most six decisive source-cited rules and no interpreted test cases. A separate explicit detailed-read control obtains the full rules/tests from current code. Raw tests and source remain available in both responses; brief output is explicitly partial. No persisted or pre-generated answers. Target first useful explanation within 3–5 seconds, measured rather than guaranteed; report actual observed latency and unresolved provider limits.

### Chat discovery recovery regression

FR-011 restoration: a filtered empty discovery is not evidence that an operation or its tests do not exist. If the same query matches other entry kinds, discovery must return bounded alternative identities explicitly outside the selected scope, without changing filtered entries/total/pagination. Chat must use those alternatives or retry unrestricted discovery, retrieve explain before claims about rules/tests, and never infer absence from a failed search. A read-only agent tool is not automatically a view. Acceptance: an exact registered tool queried as a view yields the genuine tool/command alternative; a genuine missing name has no fabricated alternatives. Same generic behavior applies to unseen catalog entries.

### Evidence focus and reading hierarchy

- **FR-026**: Docs and Inspector source disclosures MUST initially show cited code lines with original line numbers, visible highlight and nearby context. Derive line ranges from verified rule IDs matched to the same source; unrelated helpers are never highlighted by copying a line from another file/function. Full original function stays accessible with focus on the first cited line. Unknown/unmatched spans are explicitly unmarked. Source disclosure performs no extra inference or network call.
- **FR-027**: Both surfaces MUST separate Business rules, Test cases and Technical evidence into clearly labelled accessible local navigation. Rules are numbered cards with secondary source actions; tests have a distinct selectable list and selected-case panel. Technical limitations, original analysis and coverage gaps remain in the technical area. Navigation/keyboard actions do not reread evidence. Preserve source links, graph fidelity, test-run uncertainty, read freshness and existing authorized case comparison.

Acceptance: a statement far below the start of a long function opens with its correct highlighted line/context, full function retains exact bytes and focuses the cited line; a second helper without matching span is not marked. Three reading areas are keyboard accessible, carry proper selected state, and never leak selected test/facts across tenant/entry changes; refresh clears comparison facts and may retain a selected test only if its identity still exists in the new response. Desktop/mobile screenshots must be visually reviewed. User explicitly requested a UX expert review; reviewed design is three tabs and focused local source excerpt.

- **FR-028**: The primary reading view MUST use numbered business steps and preserve multiline condition descriptions (IF/THEN/ELSE in the requested language). Conditional alternatives MUST be explained only when supported by the cited rule; absent alternatives MUST NOT be invented. A separate business flow diagram is superseded by this reading view. Source evidence remains available at each step; the technical graph may remain in technical evidence.

- **FR-029**: The Docs explorer MUST retain left-hand selection and right-hand details, use localized business-object labels consistently in object cards/headings/breadcrumbs, prioritize order/invoice/item/partner/payment/stock-location navigation, and offer source-catalog-backed read-only entry shortcuts in the unselected right panel. Unknown future objects remain discoverable; missing shortcut entries are omitted. The German objects tab is named Geschäftsobjekte. The page introduction is concise. Technical identifiers and technical/data-model labels remain exact.

- **FR-030**: The Docs live explanation entry MUST state the user's benefit before a read: a question about how the function works and a prominent Explain steps and rules action. A loaded explanation MUST instead show a compact current-code provenance note and a secondary Refresh explanation action. Existing on-demand fresh-source reading, loading/error states and test/detail controls remain unchanged.

- **FR-031**: Function details MUST introduce the function with its business-facing localized title and a single catalog description before the optional live explanation entry. The initial explanation entry MUST be an inline secondary action, not a separate introductory box. Technical identifiers, synopsis and adapter/mode details follow the business introduction. Catalog-localized descriptions may provide concise operation purpose; they MUST NOT replace or precompute live source-derived business rules. Missing translations retain the original catalog text rather than inventing meaning.

- **FR-032**: Docs MUST offer a Code action that opens actual current source without invoking the language-model interpreter, separately from Explain steps and rules. The entry applies to commands/tools/actions/views/projections and registered exception classes. Exception source using a shared evaluator MUST explicitly disclose that scope rather than claiming class-isolated logic. Source-only reads retain original source validation, no-store responses and public-input restrictions.

- **FR-035**: Code inspection MUST retain the actual entry reader as primary source, include registered projection maintenance builders and disclose shared projection branches. The source view MUST display original line numbers, distinguish helper evidence from the entry function, and report HTTP admission/unavailability separately from network failure. Inspection MUST offer local navigation into verified directly called functions, preserve original source bytes and line numbers with visual wrapping on narrow screens, and MUST NOT invent call relationships. All registered views and projections MUST return verified source within the public response boundary, without invoking the interpreter. Registered MCP decision handlers MUST remain inspectable within the existing source approval boundary.

**FR-033**: The Docs source-code tab does not show a Refresh code button. Keep the Function selector, source provenance and current-source opening through the existing Code action. The user explicitly approved removing this redundant control. Acceptance: source tab has no Refresh code/Code aktualisieren button; opening already-loaded code performs no new read.

**FR-034**: The Docs source tab opens with the first verified entry source as the main function, without a function selector. Additional verified source functions are available in an initially collapsed Called functions disclosure with individually expandable original code and provenance. Do not infer call relationships beyond the returned verified source set. User approved this refinement.
