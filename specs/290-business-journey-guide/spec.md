# Feature Specification: Business Journey Guide

**Feature Branch**: `290-business-journey-guide`

**Created**: 2026-09-27

**Status**: Approved

**Input**: Publish the complete business-scenario catalog as a living guide, let public and internal users ask whether and how Reality handles a situation, and let authenticated users submit and support missing-capability suggestions. The product name “Atlas” is reserved and must not be used.

**Language**: English

## Context and Intent

### Problem

Reality already has a broad, evidence-backed business-scenario inventory, a smaller demo-data guide and executable tool catalogs. They are not presented as one understandable product capability guide. A prospective user cannot ask an ordinary question such as “What happens when a supplier delivers too little?” and receive an honest answer that distinguishes proven support, partial support, recognition-only behavior, a product gap and deliberate non-scope. Product teams also lack one visible route from an unanswered question to a deduplicated, measurable suggestion.

### Scope

Create a public **Business Journey Guide** containing every cataloged business scenario and its current support evidence. Provide the same read-only, capability-focused conversation in three places: as a conventional public AI-chatbot widget across the public marketing website, inside the public Guide in Docs, and inside the normal authenticated Reality Chat. Ground all three only in published guide entries, tools and demo references; the authenticated Chat may additionally show approved internal or tenant-relevant context without changing the public capability conclusion. Let authenticated users propose missing journeys, find similar proposals before submitting and cast one reversible vote per proposal. Generate all consumer views from one governed journey catalog so newly added or changed scenarios appear without parallel manual maintenance.

### Non-Goals

- The public question surface does not inspect company data, execute tools or prepare mutations.
- The guide does not claim that every cataloged journey is supported.
- Votes do not automatically prioritize the roadmap or approve implementation.
- This feature does not implement business capabilities that the guide identifies as missing.
- This feature does not expose private specifications, source paths, tests or tenant data publicly.
- “Atlas” is not used in product names, routes, headings or copy.

## Clarifications

### Session 2026-09-27

- Q: Where must people be able to ask whether Reality supports a business situation? → A: In normal authenticated Reality Chat and as a conventional public AI-chatbot on the marketing website; the Docs Guide also retains the same question surface.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explore the complete capability guide (Priority: P1)

As an evaluator, customer or contributor, I can browse every cataloged journey by business process and support status so I understand what Reality can prove today and where its limits are.

**Why this priority**: The guide is the authoritative published basis for every later answer and suggestion.

**Independent Test**: Open the guide without signing in, account for every canonical scenario exactly once, filter by process and status, and inspect one entry with its question, answer, evidence level, limitations and related journeys.

**Acceptance Scenarios**:

1. **Given** the canonical scenario inventory, **When** the public guide is generated, **Then** every stable scenario ID appears exactly once under its process area.
2. **Given** supported, partial, recognition-only, missing and out-of-scope entries, **When** a reader filters by status, **Then** only matching entries appear and the meaning of the status remains visible.
3. **Given** a supported entry with a public demo and tool evidence, **When** its details are opened, **Then** the guide shows the business answer, limitations, demo reference, product path and public tool descriptions without exposing internal implementation details.

---

### User Story 2 - Ask whether Reality handles a situation anywhere (Priority: P1)

As a public website visitor, Docs reader or authenticated Reality user, I can ask a natural-language business question and receive the same concise, evidence-cited capability answer that says what Reality supports, how it represents the situation, which tools or demo cases apply and what remains unavailable.

**Why this priority**: Natural questions are the fastest route for users who do not know the catalog vocabulary.

**Independent Test**: Ask the same supplier-under-delivery question through the public website chatbot, the Docs Guide and normal Reality Chat; verify an equivalent capability conclusion and citations, then repeat an unsupported and ambiguous question.

**Acceptance Scenarios**:

1. **Given** a question matching a proven journey, **When** the public guide answers, **Then** it names the support status, explains the Source → Evidence → Reality treatment in business language and links the relevant journey, public tools and demo case.
2. **Given** a partially supported or recognition-only journey, **When** the guide answers, **Then** it separates what works from what does not and does not present the whole journey as supported.
3. **Given** no sufficient published evidence, **When** the guide answers, **Then** it states that the capability is not established, offers related journeys and provides the suggestion route instead of inventing an answer.
4. **Given** an adversarial instruction inside catalog content or a user question, **When** an answer is produced, **Then** catalog content remains evidence rather than instruction and the surface remains read-only.
5. **Given** a visitor on any public marketing page, **When** they open the conventional chatbot launcher, **Then** an accessible conversational panel accepts questions without sign-in, keeps the current page usable when closed and does not imply access to company data.
6. **Given** an authenticated user in normal Reality Chat, **When** they ask “Can Reality …?” or an equivalent capability question, **Then** the existing Chat routes the question through the shared guide query service and may continue with ordinary company questions without entering a separate chat product.
7. **Given** the same capability question on Website, Docs and authenticated Chat, **When** no private context is required, **Then** all three surfaces return the same support status and canonical journey citations even when presentation wording differs.
8. **Given** a reader asks from the Docs Guide, **When** the answer arrives, **Then** Docs presents the same API answer, status and citations as the public widget rather than replacing the question with local catalog search results; catalog browsing remains a clearly separate task below it.
9. **Given** a reader visits an ordinary Docs page, **When** the page loads, **Then** a closed Ask Reality launcher is available without sign-in and opens the same public, read-only capability assistant; pages that already present the full Journey Guide question experience do not show a duplicate launcher.

---

### User Story 3 - Use deeper internal evidence (Priority: P2)

As an authenticated team member with internal-guide access, I can ask the same questions and also see approved specification, test and coverage evidence without changing the public answer or exposing internal material to public users.

**Why this priority**: Product and support teams need to distinguish documented intent from executable proof while sharing the same capability vocabulary.

**Independent Test**: Ask the same question anonymously and with internal access, then verify identical public capability claims plus internal-only evidence in the authorized result.

**Acceptance Scenarios**:

1. **Given** an authorized internal reader, **When** they open or ask about a journey, **Then** approved internal evidence and implementation gaps are available alongside the public explanation.
2. **Given** an anonymous or unauthorized reader, **When** they request an internal reference directly, **Then** it is not disclosed and the public answer remains usable.
3. **Given** a discrepancy between prose and executable evidence, **When** the internal guide evaluates the journey, **Then** it lowers or flags the support claim rather than treating prose as proof.

---

### User Story 4 - Propose and support a missing journey (Priority: P2)

As an authenticated user, I can propose a missing business journey, see likely duplicates before submitting, vote once for a proposal and withdraw my vote so product demand is visible without creating a duplicate backlog.

**Why this priority**: Questions that expose real gaps should feed a reviewable demand signal.

**Independent Test**: Submit a new proposal, encounter a similar existing proposal, vote, withdraw the vote and verify the public count and lifecycle status.

**Acceptance Scenarios**:

1. **Given** a question without sufficient support, **When** an authenticated user chooses to propose it, **Then** the proposal starts with the question, related journey and known limitation already attached for review.
2. **Given** similar open proposals, **When** a user begins submission, **Then** those proposals appear before final submission and can be voted for instead.
3. **Given** an eligible user and proposal, **When** the user votes repeatedly, **Then** at most one active vote is counted; withdrawing removes that vote without deleting the proposal.
4. **Given** a reviewed proposal, **When** its lifecycle changes, **Then** users can distinguish proposed, under review, planned, in progress, available, declined and out of scope.
5. **Given** a proposal becomes an implemented catalog journey, **When** it is marked available, **Then** it links to the published journey and keeps its prior demand history.

---

### User Story 5 - Keep the guide alive as Reality changes (Priority: P1)

As a maintainer, I can add or change a journey once and have the public guide, question evidence, internal coverage and generated documentation remain consistent.

**Why this priority**: A stale capability assistant is worse than no assistant because it produces confident but false product claims.

**Independent Test**: Add a fixture journey and change a tool or evidence reference; verify generated outputs update and inconsistent or unsupported claims fail validation.

**Acceptance Scenarios**:

1. **Given** a new valid catalog entry, **When** documentation artifacts are generated, **Then** it appears in guide navigation, search and question evidence without a second hand-maintained entry.
2. **Given** an entry marked supported without the required evidence, **When** validation runs, **Then** publication fails with the exact scenario and missing evidence.
3. **Given** a referenced public tool, demo reference or related journey that no longer exists, **When** validation runs, **Then** the stale reference is reported before publication.
4. **Given** public and internal fields in one entry, **When** public artifacts are built, **Then** no internal-only value is present in the published payload or rendered page.

### Edge Cases

- One question matches journeys with different statuses or opposite sales/purchasing perspectives.
- A user asks in German while the canonical catalog remains English.
- A question combines several journeys, such as under-delivery, supplier credit and late payment.
- The answer provider is unavailable, times out or returns uncited content.
- The public marketing site cannot reach the question API or cannot load the embedded chatbot asset.
- A public visitor opens, closes and reopens the chatbot on narrow/mobile and keyboard-only layouts.
- A Docs reader moves between English and German routes or into a page with the full embedded Journey Guide question experience.
- A catalog entry has no demo case because support is proven elsewhere.
- A demo reference exists in an older profile version but not the current one.
- A renamed or merged journey has existing proposal links and votes.
- Similarity finds no duplicate, several weak matches or one already-available journey.
- A proposal contains confidential company details, abuse or executable instructions.
- Concurrent votes, withdrawal and retry target the same proposal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Business Journey Guide MUST publish every canonical business scenario exactly once with its stable ID, process area, title, business question and current status.
- **FR-002**: The supported status vocabulary MUST distinguish `supported`, `partial`, `recognition_only`, `missing` and `out_of_scope`, with a public explanation for every non-supported state.
- **FR-002a**: Every non-supported journey (`partial`, `recognition_only`, `missing`, `out_of_scope`) MUST state its own public limitation in business language: what is absent or not yet proven and, where it exists, what already works, which workaround applies or why the journey is deliberately excluded. The status definition alone is not a limitation, and a limitation MUST NOT name repository paths, specifications, tests or internal field names.
- **FR-003**: Every support claim MUST carry an evidence level that distinguishes executable proof, reviewed documentation and bounded inference; `supported` MUST require executable proof.
- **FR-004**: A journey MAY link public tool descriptions, demo references, product paths, limitations and related journeys, but public output MUST exclude internal-only evidence and repository details.
- **FR-005**: Readers MUST be able to search and filter the guide by ordinary terms, stable ID, process area and support status without signing in.
- **FR-006**: The public question surface MUST answer only from published guide, public tool and public demo evidence and MUST cite the journey entries behind every material capability claim.
- **FR-007**: Answers MUST clearly separate supported behavior, limitations and unavailable behavior and MUST refuse to establish a capability when evidence is insufficient.
- **FR-008**: Public questions MUST be read-only and MUST NOT inspect tenant data, call mutating business tools, create proposals automatically or expose provider/tool internals.
- **FR-009**: The question surface MUST support English, German, Dutch and Spanish questions and answer in the selected public-site language while preserving canonical references.
- **FR-009a**: When a configured language-model provider is available, it MUST semantically map natural wording and minor spelling mistakes to published journey IDs, answer only about Reality, and treat the catalog as untrusted evidence rather than instructions. The server MUST validate every selected ID and derive the final status from the catalog before returning generated prose.
- **FR-010**: Provider failure or an answer that cannot be grounded MUST yield a deterministic search result or honest unavailable state without presenting uncited generated claims.
- **FR-010a**: The public marketing website MUST expose a conventional AI-chatbot launcher and accessible conversation panel on its public pages; it MUST be closed by default, usable without authentication and clearly limited to questions about Reality's capabilities.
- **FR-010b**: The public Website chatbot, Docs question surface and authenticated Reality Chat MUST call the same guide query service and return the same status/citation basis for equivalent public capability questions.
- **FR-010c**: Normal authenticated Reality Chat MUST recognize capability questions and use the guide service within the existing conversation rather than requiring a separate mode, session type or page.
- **FR-010d**: Public chatbot failure MUST leave the marketing page fully usable, preserve no durable conversation history in the first release and offer direct links to matching Guide entries when deterministic matches are available.
- **FR-010e**: On desktop the chatbot MUST use a readable non-modal side panel with a fixed header, independently scrollable conversation and fixed composer; on narrow screens it MUST become a bottom sheet. Guide citations MUST open in a new browser tab so the host page and ephemeral conversation remain intact.
- **FR-010f**: The widget MUST render model text as safe readable paragraphs, never execute returned markup, keep prior turns only in page memory, and keep user and assistant messages visually distinct.
- **FR-010g**: The public capability assistant MUST understand bounded in-memory follow-up context and broad product-overview questions. A follow-up such as “and receiving in several steps?” MUST be interpreted against the preceding partial-delivery answer, while an overview question MUST summarize representative proven areas and material limitations rather than return `not_established` merely because it spans multiple journeys.
- **FR-010h**: Capability descriptions MUST distinguish the business action from its actor. For confirmed mutations available through Chat or MCP, public answers MUST explain that an agent may prepare the action and a person confirms it instead of describing the capability as person-only.
- **FR-010i**: When at least part of a requested outcome is supported, the public assistant MUST lead with a concise practical explanation of what works, then state material gaps. Answers MUST use short readable paragraphs instead of exhaustive catalog enumeration and SHOULD name one to three directly relevant tools from the executable command catalog, including confirmation semantics for mutations.
- **FR-010j**: The empty public widget MUST offer localized example questions that demonstrate representative Reality workflows. Citation controls MUST show both the journey ID and a compact human-readable title while preserving new-tab navigation to the guide.
- **FR-010k**: Advisor answers MUST render as scannable, safe structured content with separated headings, short paragraphs and bullet lists for workflows and tools rather than one continuous prose block.
- **FR-010l**: Selecting an example question MUST immediately submit it, remove the empty state and show an accessible modern assistant loading indicator until the answer or bounded failure appears. Motion MUST respect reduced-motion preferences.
- **FR-010n**: The public widget loading state MUST use only a compact three-dot visual indicator. Its accessible status text MUST remain available to assistive technology without adding visible icon or explanatory copy.
- **FR-010o**: When a public widget answer arrives, the conversation MUST position the beginning of the new answer in the readable viewport instead of forcing the reader to the answer's end. The composer MUST remain fixed and available below the conversation.
- **FR-010p**: On desktop the open public widget MUST use the full available browser height, preserving the established outer offsets so the panel never extends beyond the viewport. The header and composer MUST remain visible while only the conversation scrolls.
- **FR-010q**: Ordinary public Docs pages MUST expose the shared public capability widget as a closed-by-default launcher, configured for the active Docs language and Guide route. Docs pages that already contain the full Journey Guide question experience MUST suppress the launcher so only one Ask Reality surface is presented.
- **FR-010m**: Answer citations MUST use a compact tabular source list with journey ID, truncated human-readable title and an accessible new-tab control instead of space-heavy badge controls.
- **FR-011**: Authorized internal readers MUST be able to view approved specification, test and coverage references while the public capability assessment remains derived from the same journey entry.
- **FR-012**: Internal evidence MUST be access-controlled and MUST never enter public generated assets, public search indexes or anonymous answers.
- **FR-013**: Authenticated users MUST be able to prepare and explicitly submit a journey proposal containing a business question, expected outcome, process area and optional business context.
- **FR-014**: Before proposal submission, the system MUST show materially similar open proposals and already-published journeys so the user can reuse or vote instead.
- **FR-015**: A user MUST be able to hold at most one active vote per proposal and MUST be able to withdraw it; displayed counts MUST be derived from active votes.
- **FR-016**: Proposals MUST expose the lifecycle `proposed`, `under_review`, `planned`, `in_progress`, `available`, `declined` or `out_of_scope`, a public rationale for terminal states and a journey link when available.
- **FR-017**: Proposal submission and voting MUST use existing authenticated application-service, tenant/account and confirmation boundaries; no adapter or agent may write persistence directly.
- **FR-018**: Public proposal text MUST pass bounded validation and moderation, avoid publishing personal/confidential details by default and provide a review path for rejected content.
- **FR-019**: One governed journey catalog MUST generate the guide data, navigation/search input and question evidence; consumers MUST NOT maintain independent capability claims.
- **FR-020**: Catalog validation MUST reject duplicate IDs, invalid status/evidence combinations, broken related-journey references, stale declared tool/demo references and leakage of internal-only fields.
- **FR-021**: New catalog entries and status changes MUST be included in generated documentation through the existing documentation generation and freshness gate.
- **FR-022**: The product and documentation MUST use “Business Journey Guide” and MUST NOT introduce “Atlas” as a name, heading or route.
- **FR-023**: The guide MUST distinguish the complete capability catalog from the smaller set of journeys available in the current demo profile.
- **FR-024**: Proposal votes are advisory demand signals; the interface MUST NOT describe ranking as an automatic roadmap commitment.

### Domain and Traceability Requirements

- **DR-001**: Journey explanations MUST preserve Source → Evidence → Reality semantics and MUST NOT describe document-owned operational status.
- **DR-002**: Journey and proposal identity MUST use opaque identifiers internally; stable scenario IDs and human references are lookup labels, not persistence identity.
- **DR-003**: Any tenant-related internal read or write MUST enforce tenant scope; public catalog reads are tenant-independent and contain no tenant data.
- **DR-004**: The guide MUST describe received values as stated evidence and derived observations as derivations, never as recomputed source authority.
- **DR-005**: Public Website, Docs and authenticated Reality Chat surfaces MUST call the same guide query service; only the authorized evidence scope may differ.
- **DR-006**: Mutating proposal and vote actions MUST require the same preview/confirmation semantics as other Chat-originated mutations when invoked through Chat.

### Key Entities

- **Journey Entry**: A stable business scenario with public explanation, status, evidence level, limitations and relationships to tools, demos and other journeys.
- **Journey Evidence**: A scoped reference proving or documenting a journey; visibility determines whether it may be published.
- **Guide Question**: A read-only question and its language, matched journeys, grounded answer and citations; public use need not create durable conversation history.
- **Journey Proposal**: A moderated request for a missing or expanded business journey with lifecycle, rationale and optional link to an implemented journey.
- **Proposal Vote**: One user's reversible support signal for one proposal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Automated reconciliation accounts for 100% of canonical journey IDs exactly once in the generated guide.
- **SC-002**: In an acceptance set of representative supported, partial, missing and out-of-scope questions, 100% of material capability statements cite a matching published journey and no answer upgrades the cataloged status.
- **SC-003**: A new journey added through the governed catalog appears in guide search, filters and question evidence after one documented generation step with no parallel content edit.
- **SC-004**: Anonymous users can locate the status, limitations and available demo evidence for a named journey within two minutes.
- **SC-005**: Public artifact inspection finds zero internal paths, private evidence, tenant identifiers or unpublished proposal details.
- **SC-006**: Proposal similarity shows an existing relevant journey or proposal before submission for every curated duplicate case in the acceptance set.
- **SC-007**: Concurrent vote and retry tests always produce zero or one active vote per user and proposal and an exact displayed aggregate.
- **SC-008**: English and German acceptance questions return the same canonical journey references and equivalent support conclusions.
- **SC-009**: Provider failure and ungrounded-output tests return cited deterministic matches or an explicit unavailable response, with zero unsupported capability claims.
- **SC-010**: Documentation freshness, specification, localization, accessibility and applicable full regression gates pass before completion.
- **SC-011**: A production Docs build exposes exactly one localized Ask Reality entry on ordinary English and German pages, exposes no duplicate launcher on either Journey Guide question route, and keeps the content usable when the widget asset or question service is unavailable.

## Assumptions and Dependencies

- The existing 228-entry business scenario catalog and coverage inventory are the baseline to migrate, not evidence that all entries are supported.
- Existing public tool-catalog generation, documentation navigation/localization and authenticated account/session facilities are reused.
- Public Website and Docs questions may use a configured language-model provider, but deterministic retrieval and citation validation remain authoritative and provide the fallback.
- Public questions are ephemeral in the first release; durable public conversation history and personal profiling are not required.
- The existing framework-neutral public widget remains the single Docs launcher implementation; Docs supplies only its public API URL, localized Guide URL and route visibility.
- The `runreality.ai` marketing site is maintained in the private operations repository. This repository owns the shared API, embeddable chatbot artifact and integration contract; final public rollout additionally requires the corresponding operations-repository embed and deployment evidence.
- Proposal submission and voting require an authenticated account. Browsing proposals and aggregate counts may be public after moderation.
- Moderation and lifecycle changes are performed by an existing authorized internal role; they do not create a public self-service roadmap commitment.
- No new business-domain status fields or alternate operational rules are introduced.

## Requirement Traceability

| Requirement | Scenario(s) | Planned evidence |
|---|---|---|
| FR-001–FR-005, FR-019–FR-023, DR-001, DR-004 | US1, US5 | Catalog schema/generator tests, complete-ID reconciliation, public guide browser coverage |
| FR-006–FR-010q, DR-005 | US2 | Grounded-answer service stories, adversarial/uncited/provider-failure tests, Website/Docs/normal-Chat parity, global Docs launcher contracts and English/German browser journeys |
| FR-011–FR-012, DR-003, DR-005 | US3 | Authorization and public-artifact non-disclosure tests |
| FR-013–FR-018, FR-024, DR-002–DR-003, DR-006 | US4 | Proposal/vote service stories, concurrency/idempotency tests, API/Chat confirmation and moderation tests |
| FR-019–FR-021 | US5 | Generation freshness gate and injected stale-reference failures |
| SC-001–SC-010 | All | Acceptance matrix and required repository quality gates |
