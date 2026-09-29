# Feature Specification: Reality Product Advisor

**Feature Branch**: `291-reality-product-advisor`
**Created**: 2026-09-28
**Status**: Draft for product review
**Language**: English
**Input**: "Turn the public and authenticated Reality capability chat into a strong product advisor that researches the relevant journeys, documentation, tools, product contracts and verified implementation evidence before answering, like an expert examining the repository, while remaining public-safe, current, cited and honest about limitations."

## Context and Intent

### Problem

The Business Journey Guide can answer natural-language capability questions, but it treats the journey catalog as nearly its entire knowledge base and asks one language-model response to select evidence and explain the product at the same time. This works for narrow catalog questions such as supplier under-delivery, yet it produces weak or unsafe conclusions for the broader questions asked by serious ERP evaluators: complete B2B or procure-to-pay flows, migration, integrations, controls, multi-entity operation and reasons to adopt Reality.

The current answer can cite adjacent scenarios whose individual behavior exists without proving the broader claim. It may turn partial evidence into words such as “automatic” or “end to end”, infer migration support from item-history behavior, or answer a technical question as unknown even though an approved public product contract contains the answer. Fluent prose therefore appears more certain than Reality's evidence.

An effective advisor must work the way a knowledgeable product expert works: understand the question, break broad questions into relevant concerns, inspect the right authoritative sources, distinguish proof from gaps, resolve contradictions conservatively, ask for missing context when needed, and only then produce a clear answer.

### Scope

- Upgrade the shared capability-question service used by the public website, Docs and authenticated Reality Chat into a research-backed Reality Product Advisor.
- Let the advisor answer narrow capability checks, broad solution-design questions and product/technical questions from the appropriate approved evidence sources.
- Combine published business journeys with approved public documentation, executable tool and command descriptions, public API and integration contracts, durable product contracts and verified implementation evidence.
- Produce claim-level evidence before prose and validate every material capability statement before returning it.
- Explain what works, how Reality represents or performs it, which relevant tools exist, what remains limited and which follow-up information would change the recommendation.
- Keep public and authenticated answers on one shared advisory service while applying different authorized evidence scopes and preserving tenant boundaries.
- Keep the knowledge base current through governed generation and validation when its authoritative sources change.
- Establish a repeatable multilingual ERP-buyer evaluation set that prevents regressions in factuality, completeness and readability.

### Non-Goals

- This feature does not implement capabilities that the advisor identifies as absent or partial.
- The public advisor does not receive unrestricted repository, filesystem, database or tenant access at question time.
- Source code, tests, private specifications, internal paths, secrets and unpublished roadmap material are not exposed to public users.
- Plans, tasks, ideas and unimplemented specifications are not treated as available product behavior.
- A language model's general ERP knowledge is not evidence of Reality capability.
- The first release does not provide autonomous consulting engagements, procurement guarantees, contractual commitments or compliance certification.
- The public advisor remains read-only and does not execute business actions, create proposals or mutate company data.
- This feature does not create a separate website-only answer engine or a second product truth.

### Existing Contracts

- [Business Journey Guide](../../docs/features/business-journey-guide.md)
- [Spec 290: Business Journey Guide](../290-business-journey-guide/spec.md)
- [Architecture](../../docs/ARCHITECTURE.md)
- [Web Product](../../docs/WEB_SPEC.md)
- [Test Strategy](../../docs/TEST_STRATEGY.md)
- [Tool Usage generation](../../apps/docs/content/tool-usage/index.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receive a researched capability answer (Priority: P1)

As an ERP evaluator, I can ask whether Reality handles a specific business situation and receive a direct, understandable answer whose important statements are supported by the most relevant approved evidence.

**Why this priority**: A fluent but overstated answer damages trust at the exact moment a prospect is evaluating the product.

**Independent Test**: Ask about supplier under-delivery, automatic three-way matching, blanket purchase orders and customer credit limits; verify that every material statement agrees with the governing journeys and limitations, including the distinction between automatic, manual, partial and unsupported behavior.

**Acceptance Scenarios**:

1. **Given** directly supported evidence, **When** an evaluator asks a narrow capability question, **Then** the answer starts with a plain-language conclusion, explains the practical flow, names relevant available tools where useful and links the supporting public sources.
2. **Given** a journey is partial, **When** the answer is produced, **Then** it states the proven part and the material gap without describing the complete capability as supported, automatic or end to end.
3. **Given** related entries exist but none proves the requested capability, **When** the answer is produced, **Then** it distinguishes adjacent available behavior from the unproven request instead of combining the entries into a stronger claim.
4. **Given** authoritative sources disagree, **When** the advisor resolves the answer, **Then** it uses the more restrictive current conclusion and makes the discrepancy reviewable to an authorized maintainer.

---

### User Story 2 - Explore a broad Reality solution (Priority: P1)

As a prospective buyer, I can ask broad questions such as “How would we run B2B with Reality?” or “Can Reality cover procure to pay?” and receive a coherent solution explanation rather than a list of loosely related scenarios.

**Why this priority**: Buyers evaluate complete operating models, not isolated catalog entries.

**Independent Test**: Ask how Reality handles B2B sales with customer-specific terms, credit limits, partial delivery, collective invoicing and returns; verify that the response covers the requested chain, labels each material limitation accurately and does not introduce unrelated processes.

**Acceptance Scenarios**:

1. **Given** a broad process question, **When** the advisor can identify a coherent interpretation, **Then** it decomposes the question into the material process concerns and returns a concise workflow with proven strengths and important gaps.
2. **Given** a broad question has several materially different interpretations, **When** answering all of them would risk a misleading conclusion, **Then** the advisor asks one focused clarification or explicitly states the interpretation it is using.
3. **Given** only part of a requested process is proven, **When** the advisor proposes how to model the process, **Then** it separates native supported behavior, confirmed manual or agent-assisted work, possible workaround and true product gap.
4. **Given** a relevant mutating tool prepares a proposal, **When** it is mentioned, **Then** the answer explains its role and confirmation requirement without implying that the public advisor can execute it.

---

### User Story 3 - Ask product and technical evaluation questions (Priority: P1)

As a technical or procurement evaluator, I can ask about APIs, integrations, deployment, migration, security boundaries and operating concepts and receive answers from the applicable approved product evidence rather than an unrelated business-journey lookup.

**Why this priority**: These questions determine whether Reality can enter a serious ERP evaluation even when they are not business journeys themselves.

**Independent Test**: Ask which integration interfaces Reality exposes, whether open transactions can be migrated from another ERP, how public and authenticated chat differ, and how tenant isolation works; ask in languages different from the canonical English sources and verify that the advisor responds in the question's language, uses the applicable approved sources and refuses unsupported migration or compliance claims.

**Acceptance Scenarios**:

1. **Given** an approved public technical or product contract answers the question, **When** the evaluator asks, **Then** the advisor answers from that contract and links an appropriate public reference.
2. **Given** implemented code exists without an approved public capability claim, **When** the evaluator asks about that behavior, **Then** the advisor does not promote the implementation detail into a public product promise.
3. **Given** a plan or unimplemented specification describes future behavior, **When** the evaluator asks whether it is available, **Then** the advisor excludes it from current capability and does not expose private roadmap detail.
4. **Given** no approved source establishes SAP or other ERP migration coverage, **When** migration is asked about, **Then** the advisor says which import or continuity primitives are actually proven and states that complete migration support is not established.
5. **Given** a supported natural-language question in a language different from the canonical English evidence, **When** the advisor answers, **Then** it answers in the language of the question while preserving canonical identifiers, tool names and the same product conclusion.

---

### User Story 4 - Receive the same truth in every chat surface (Priority: P1)

As a website visitor, Docs reader or authenticated Reality user, I receive the same public capability conclusion for the same question, while an authorized internal or tenant context may add evidence without silently changing the product truth.

**Why this priority**: Different answers across public and product chat would create competing product commitments.

**Independent Test**: Ask the same question through the public widget, Docs and authenticated Chat; compare claim conclusions and public citations, then verify that authenticated context is additive, scoped and clearly distinguished.

**Acceptance Scenarios**:

1. **Given** equivalent questions and the same public evidence version, **When** they are asked through all three surfaces, **Then** material public claims and their support levels agree even when presentation differs.
2. **Given** an authenticated user asks a tenant-specific follow-up, **When** authorized company reads are required, **Then** the existing tenant-scoped tools provide that context and the answer distinguishes company observations from general Reality capability.
3. **Given** an anonymous request attempts to obtain internal, repository or tenant information, **When** the advisor processes it, **Then** no restricted source, identifier or inferred private detail is disclosed.

---

### User Story 5 - Keep advisory knowledge accurate as Reality evolves (Priority: P1)

As a maintainer, I can change an authoritative journey, tool, contract or public document and have the advisor's searchable knowledge and evaluation evidence update without manually maintaining a second narrative database.

**Why this priority**: A research-backed advisor is only trustworthy if freshness and source authority are enforced continuously.

**Independent Test**: Add or change a fixture source, remove a referenced tool and introduce a deliberately overstated answer; verify that knowledge generation updates the first two cases and validation rejects the stale reference and unsupported claim.

**Acceptance Scenarios**:

1. **Given** an approved source changes, **When** advisory knowledge is generated, **Then** the corresponding public evidence unit changes through one governed process and retains source identity and verification metadata.
2. **Given** an entry references a removed, private or ineligible source, **When** validation runs, **Then** publication fails with the affected claim and reference.
3. **Given** a curated buyer question set, **When** advisor behavior changes, **Then** evaluation detects unsupported claims, missed material limitations, incorrect source scope and prohibited confidence upgrades before release.
4. **Given** a generated answer contains “automatic”, “fully supported”, “end to end”, “compliant”, “migration” or an equivalent high-risk claim, **When** it lacks exact qualifying evidence, **Then** validation rejects or safely weakens the claim before it reaches the user.
5. **Given** the governed Journey, resource or executable catalogs change, **When** advisory knowledge is generated, **Then** a compact Capability Map is regenerated from those sources without maintaining a second hand-written routing catalog.
6. **Given** a public question is semantically phrased without catalog keywords, **When** the provider plans retrieval, **Then** it selects bounded Capability Map identities and the server resolves and validates their evidence; the provider neither receives the complete evidence index nor invokes a business tool.

### Edge Cases

- A question contains several claims with different support levels.
- A business term appears in both sales and purchasing with different meanings.
- A misspelled or multilingual question has no exact vocabulary match.
- Conversation history changes the referent of a short follow-up such as “and in several steps?”.
- Relevant evidence is too broad, stale, duplicated or contradictory.
- A supported low-level primitive is necessary but insufficient for the requested end-to-end process.
- A code path exists but is experimental, unreachable, feature-gated or not publicly contracted.
- A source describes an agent proposal while the question asks whether Reality acts automatically.
- A source states that a person confirms an action while an agent may prepare but not confirm it.
- The research provider times out, exceeds its bounded work budget or returns malformed evidence selections.
- A public reference disappears between research and link selection.
- No approved evidence answers the question, but adjacent capabilities and a useful clarification exist.
- A prompt-injection instruction is present in a document, catalog entry, source excerpt or user question.
- The same question is asked in different natural languages while canonical evidence remains English.
- A short follow-up contains too little text to identify a language reliably.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Website, Docs and authenticated Reality Chat MUST use one shared Product Advisor service for general Reality capability and product questions.
- **FR-002**: The advisor MUST classify each question as a narrow capability check, broad solution question, product/technical question, tenant-specific question or out-of-scope request before selecting evidence.
- **FR-003**: For a broad or compound question, the advisor MUST identify the material subquestions needed for a useful conclusion and MUST NOT infer complete-process support from unrelated or merely adjacent primitives.
- **FR-004**: The advisor MUST retrieve only relevant bounded evidence from approved source classes rather than treating the complete repository or complete knowledge corpus as the answer context. Provider-assisted semantic retrieval MAY inspect a compact generated Capability Map organized by business resource and process topic, but MUST NOT receive the complete evidence-unit index or claim text. It may select no more than six capability identities; the server MUST validate those identities, resolve their governed evidence relationships and send no more than eighteen full evidence units to answer generation.
- **FR-005**: Approved public source classes MUST include published Business Journeys, public product documentation, public executable tool and command descriptions, public interface and integration contracts, and public durable product contracts.
- **FR-006**: Verified tests and implementation metadata MAY strengthen or restrict an internal evidence assessment, but MUST become public answer evidence only through an explicitly public-safe product claim or reference.
- **FR-007**: Plans, tasks, ideas, draft specifications, disabled code, comments and general model knowledge MUST NOT establish current product capability.
- **FR-008**: Every material capability statement MUST be represented as an evidence-backed claim before prose is returned, with a support level, qualifying limitations and one or more eligible sources or an explicit absence of evidence.
- **FR-008a**: A material capability statement is any user-visible assertion that Reality supports, lacks, recognizes, automates, requires, executes, proposes, integrates, secures or represents a business or technical behavior; headings, workflow steps, tool explanations, comparisons and limitation statements carrying such meaning MUST follow the same claim rule, while conversational transitions with no product meaning need no claim.
- **FR-009**: Claim support levels MUST distinguish at least proven, limited, unavailable and not established; generated wording MUST NOT upgrade the source's most restrictive applicable conclusion.
- **FR-010**: Every answer MUST pass a claim validation step that checks source eligibility, semantic agreement, support level, material limitations and high-risk wording before delivery.
- **FR-011**: The validator MUST reject or safely revise claims that turn manual behavior into automatic behavior, a proposal into execution, a primitive into an end-to-end capability, partial support into full support or adjacent behavior into the requested capability.
- **FR-012**: Answers MUST lead with a direct plain-language conclusion and, when relevant, separately present the practical workflow, important tools, material limitations and public references in a readable structure.
- **FR-013**: When a question remains materially ambiguous after bounded research, the advisor MUST use the same provider-assisted semantic assessment for every business term and MUST ask one focused clarification before giving an answer if the plausible interpretations would materially change the workflow or conclusion. It MUST answer directly when missing detail would not materially change the result. Conversation history MAY resolve an explicit referent but MUST NOT silently choose between materially different ERP flows. A clarification response MUST contain no product claims or citations; partial delivery between customer shipment and supplier receipt is one acceptance example, not a hard-coded exception.
- **FR-014**: The advisor MUST distinguish native supported behavior, agent-prepared and confirmation-required behavior, documented manual handling, workaround and product gap.
- **FR-015**: Tool names and modes MUST be derived from governed executable catalogs and MAY appear in the generated Capability Map for discovery. The public advisor MUST treat them only as vocabulary and evidence relationships, MUST NOT invoke them or accept tool arguments, and MUST describe whether a referenced tool reads, previews, proposes or executes without inventing a tool or implying public execution.
- **FR-016**: Public answers MUST be read-only, ephemeral and limited to public-safe evidence; they MUST NOT inspect tenant data, disclose internal source content or reveal provider and repository internals.
- **FR-017**: Authenticated tenant-specific follow-ups MUST use existing tenant-scoped services and tools, distinguish company observations from general product capability and preserve confirmation for mutations.
- **FR-018**: Equivalent public questions MUST return materially consistent claim conclusions and public source references across Website, Docs and authenticated Chat for the same knowledge version.
- **FR-019**: The advisor MUST detect the natural language used in the latest substantive user question and answer in that language while preserving canonical tool names, identifiers, references and equivalent capability conclusions.
- **FR-019a**: When the latest question is too short or linguistically ambiguous, the advisor MUST use the language established by the bounded conversation history and then the active surface language as fallback; language detection MUST NOT change evidence selection or capability status.
- **FR-020**: If research, generation or validation fails or exceeds its bounded stage or request budget, the service MUST return a deterministic evidence result, a focused clarification or an explicit not-established answer without unsupported generated claims and before the public widget's 40-second request timeout.
- **FR-021**: Authoritative source changes MUST update both advisory evidence and its compact Capability Map through one governed generation process without a parallel hand-maintained answer or routing corpus.
- **FR-022**: Each generated evidence unit MUST retain its authoritative source identity, public/internal eligibility, current support meaning and freshness information sufficient to detect stale or ineligible references.
- **FR-023**: Publication validation MUST reject duplicate evidence identity, broken references, public leakage, unsupported status upgrades and current-capability claims derived only from non-authoritative material.
- **FR-024**: A governed ERP-buyer evaluation set MUST cover narrow business cases, broad operating models, technical/product questions, unsupported capabilities, ambiguity and adversarial prompts. Its initial language matrix MUST include English, German, Dutch, Spanish, French, Polish, Turkish, Arabic and Japanese without limiting production answers to those languages.
- **FR-025**: Evaluation MUST assess factual claims and prohibited claims rather than requiring one fixed answer wording.
- **FR-026**: Authorized maintainers MUST be able to inspect which sources and claim decisions produced an answer without exposing that internal trace on the public surface.
- **FR-027**: The existing Business Journey Guide browsing, suggestion and voting behavior MUST remain available and MUST continue to use the same canonical journey identities.

### Domain and Traceability Requirements

- **DR-001**: Business-process explanations MUST preserve Source → Evidence → Reality and MUST NOT describe a Document as owning operational fulfillment, inventory or payment state.
- **DR-002**: Received values, derived observations and product-capability claims MUST remain distinguishable; the advisor MUST NOT present a derived observation as received authority or store it as new business authority.
- **DR-003**: Public evidence is tenant-independent; every tenant-related read MUST enforce tenant scope through existing application services and behave as not found across tenant boundaries.
- **DR-004**: Chat, API, Web and Docs adapters MUST share the same advisory application service and MUST NOT implement alternate retrieval, ranking, validation or capability rules.
- **DR-005**: Evidence and claim relationships MUST use stable opaque internal identity; human-facing journey IDs, document paths and tool names are references, not persistence identity.
- **DR-006**: Any mutating action reached from authenticated Chat MUST continue to use the canonical proposal/confirmation path; advisory research itself remains read-only.
- **DR-007**: No new business-domain status field or alternate operational authority is introduced by storing or presenting advisory evidence.

### Key Entities *(when data is involved)*

- **Advisory Question**: The latest user question, supported language, bounded conversational context, classified intent and authorized evidence scope.
- **Evidence Source**: An authoritative source with identity, source class, visibility, currentness and rules governing which claims it may establish.
- **Evidence Unit**: A bounded public-safe or internal excerpt derived through the governed source process, retaining its source identity and relevant qualification.
- **Capability Map**: A deterministic compact routing artifact derived from governed Journeys, business resources and executable catalogs. Each capability has stable identity, discovery language, validated evidence relationships and optional catalog tool vocabulary, but contains no executable authority or tenant data.
- **Advisory Claim**: One material statement about Reality with requested subject, support level, evidence references, limitations and validation result.
- **Advisory Answer**: A readable composition of validated claims, workflow guidance, tools, limitations, clarification and public references.
- **Buyer Evaluation Case**: A representative question with required facts, required limitations, forbidden claims, permitted source classes and supported languages, without fixing exact prose.
- **Knowledge Version**: The identifiable set of governed evidence used to produce and reproduce advisory conclusions.

## Success Criteria *(mandatory)*

- **SC-001**: In a reviewed acceptance set of at least 75 ERP-buyer questions, 100% of material capability statements have an eligible source or are explicitly labeled not established.
- **SC-002**: The acceptance set contains zero cases where limited evidence is described as full, manual behavior as automatic, a proposal as executed or adjacent primitives as an end-to-end capability.
- **SC-003**: At least 90% of reviewed narrow and broad in-scope questions receive a useful direct answer or one focused clarification rather than a generic catalog-unavailable response.
- **SC-004**: For equivalent public questions across Website, Docs and authenticated Chat, 100% of tested material claim conclusions and support levels agree for the same knowledge version.
- **SC-005**: Public artifact and adversarial tests disclose zero private specification text, repository paths, source code, secrets, unpublished roadmap content or tenant data.
- **SC-006**: A change to a governed source appears in advisory evidence after one documented generation step, and every curated stale-reference case fails publication.
- **SC-007**: Reviewed answers to broad buyer questions can be understood without opening a citation and present the direct conclusion, workflow and material limitation within 180 words unless the user asks for detail.
- **SC-008**: For every multilingual evaluation case, questions in English, German, Dutch, Spanish, French, Polish, Turkish, Arabic and Japanese preserve the same material product conclusion and limitations, and 100% of answers use the detected question language or the documented fallback.
- **SC-009**: Provider timeout, malformed output and failed validation cases return a safe deterministic result or clarification with zero unsupported generated claims.
- **SC-010**: Every FR and DR maps to at least one acceptance scenario and executable proof before implementation is marked complete.
- **SC-011**: In production-like timeout tests, 100% of public advisor requests return an answer, clarification or safe fallback before the 40-second widget timeout; provider planning never receives the complete evidence-unit index.

## Assumptions and Dependencies

- Spec 290's canonical Business Journey catalog, shared question service, public widget, Docs surface and authenticated Chat routing remain the baseline and are extended rather than replaced.
- Existing generated tool, command, resource, event and interface catalogs remain authoritative for their published vocabulary. Canonical knowledge remains English; answer translation does not create a second localized evidence authority.
- Durable public product contracts identify what may be stated externally; implementation and tests can constrain those statements but do not independently create marketing commitments.
- The initial release uses bounded deterministic and lexical search where adequate; a particular semantic indexing technology is not required by this specification.
- Public answers remain ephemeral. Internal answer research traces may follow existing bounded diagnostic and retention policies but are not business records.
- A configured language-model provider may plan research and compose prose, but deterministic authorization, source eligibility, claim status and validation remain server-controlled.
- The public marketing site continues to consume the shared service through the existing widget contract owned by this repository.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-004, FR-012–FR-014, FR-018, DR-004 | US1, US2, US4 | Shared-service stories for narrow, broad, ambiguous and cross-surface questions |
| FR-005–FR-011, FR-015, FR-020, DR-001–DR-002 | US1–US3 | Source-authority, material-claim coverage, claim validation, high-risk wording and provider-failure tests |
| FR-016–FR-017, FR-026, DR-003, DR-006–DR-007 | US3, US4 | Public non-disclosure, tenant isolation, read-only research and confirmation-boundary tests |
| FR-019–FR-019a | US1–US4 | Language-detection, fallback and multilingual conclusion-parity evaluation |
| FR-021–FR-025 | US5 | Evidence and Capability Map generation freshness, stale-reference and ERP-buyer evaluation gates |
| FR-027 | US4, US5 | Business Journey Guide browsing, proposal and voting regressions |
| SC-001–SC-011 | All | Reviewed acceptance corpus, bounded-time provider tests and required repository quality gates |
