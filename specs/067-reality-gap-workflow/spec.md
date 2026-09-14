# Feature Specification: Reality Gap Workflow

**Feature Branch**: `067-reality-gap-workflow`

**Created**: 2026-09-04

**Status**: Approved — product scope approved by the owner on 2026-09-04

**Input**: User description: "Create the first Spec Kit version of Reality Gap so a user can operate it completely from request through visibility and implementation through Chat, MCP, or the Web UI."

**Language**: English

Specifications, plans, tasks, code, tests, migrations, contracts, documentation, and recorded decisions use English. User-entered business questions and lossless source examples retain their original language.

## Context and Intent

### Problem

Customers first discover missing business meaning while asking a question or inspecting an operational record. Today they can inspect the lossless SourceRecord, but Reality has no durable way to capture the unanswered question, collect supporting source examples, guide a classification decision, or carry the accepted decision through implementation. The learning remains in a conversation or outside the product, so recurring needs do not systematically improve the tenant's Reality model.

### Scope

- Capture one tenant-scoped missing-information request from Chat, MCP, or Web.
- Keep every request in one shared queue independent of the surface that created it.
- Guide the requester through business-language questions about intent, evidence, recurrence, and intended use.
- Attach exact same-tenant SourceRecords, subjects, source paths, and bounded example values as investigation evidence without copying or mutating source payloads.
- Let an authorized human classify the gap as source-only, Fact, typed Evidence, typed Reality, derived Projection/Exception, or rejected.
- Produce and review an implementation proposal that explains the target, extraction rule, affected records, replay behavior, and verification before any operational effect.
- Make the complete lifecycle readable and actionable through Chat, MCP, and Web using the same application operations.
- Preserve the distinction between a modeling gap, an operational exception, a Fact, and a mutation ChangeProposal.

### Non-Goals

- Treating model output, frequency, or a source-field guess as business truth.
- Allowing an agent to create arbitrary schema, predicates, or executable code without an explicit approved contract.
- Copying complete SourceRecord payloads into the gap.
- Replacing feature specifications, code review, migrations, or the Constitution Check for changes to shared product behavior or schema.
- Turning missing-information requests into operational Exceptions.
- Automatically promoting existing Facts into typed Reality.
- General-purpose product feedback, support tickets, or project management.

### Existing Contracts

- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [`docs/features/chat.md`](../../docs/features/chat.md)
- [`specs/043-observe-facts/spec.md`](../043-observe-facts/spec.md)

## Clarifications

### Session 2026-09-04

- Q: Should V1 activate a constrained tenant-specific extraction rule or only produce a developer implementation package? → A: ERP and Operations administrators can activate safe declarative SourceRecord-to-Fact rules; every other model destination produces a developer implementation package.
- Q: Which rule capabilities are required before the self-service workflow is ERP-ready? → A: V1 includes closed conditions, extracted or constant outputs, Commitment and DocumentLine subjects, controlled line iteration, effective-time extraction, conflict visibility, resumable replay, execution observability, and complete cross-surface tests.
- Q: What is the next safe logic extension beyond flat all-of rules? → A: Rules may use bounded nested ALL and ANY groups, with no scripts, formulas, regex, or free-form expressions.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Capture a Missing Business Answer (Priority: P1)

An operator asks a question that Reality cannot answer, or notices missing context while inspecting a record. The operator records the question as a Reality Gap without needing to understand Facts, predicates, JSON paths, or the domain model.

**Why this priority**: Durable capture at the moment of discovery prevents the customer's operational learning from disappearing into chat history or an external backlog.

**Independent Test**: Create equivalent gaps from Chat, MCP, and Web, then verify that each appears once in the same tenant queue with its origin, business question, intended use, and optional record context.

**Acceptance Scenarios**:

1. **Given** an authenticated tenant member is in Chat, **When** Reality cannot answer a business question and the member accepts the capture suggestion, **Then** one open Reality Gap is stored and the conversation links to it.
2. **Given** a member is inspecting a same-tenant SourceRecord or operational record, **When** the member chooses "Capture open question," **Then** the new gap carries that record as context without copying its payload.
3. **Given** an authorized MCP caller supplies the same required business context, **When** it creates a gap, **Then** the gap is visible and behaves identically in Chat and Web.
4. **Given** a retried request with the same tenant-scoped idempotency identity and identical content, **When** it is submitted again, **Then** the original gap is returned without duplication.
5. **Given** foreign-tenant context, **When** capture is attempted, **Then** the request fails without disclosing whether the referenced record exists.

---

### User Story 2 - Investigate and Classify the Gap (Priority: P1)

An operator or domain owner works through a short guided review. Reality collects the business purpose first, then suggests relevant source evidence and a model destination while keeping uncertainty explicit.

**Why this priority**: A raw field request is insufficient; the business question and intended use determine whether information belongs only in Source, in a Fact, in typed Evidence or Reality, or in a derivation.

**Independent Test**: Complete the guided questions, attach bounded source examples, request a recommendation, and verify that the recommendation includes evidence, reasoning, uncertainty, and one allowed destination without changing Facts, Evidence, or Reality.

**Acceptance Scenarios**:

1. **Given** an open gap, **When** the guided review is incomplete, **Then** Chat, MCP, and Web expose the same unanswered questions and saved answers.
2. **Given** a source-backed gap, **When** the investigator selects same-tenant examples and source paths, **Then** Reality stores references and bounded extracted examples while the immutable SourceRecords remain unchanged.
3. **Given** sufficient answers and evidence, **When** classification is requested, **Then** Reality recommends exactly one destination with reasons, alternatives considered, confidence limitations, and the next required decision.
4. **Given** only model inference or no supporting source, **When** a Fact destination is considered, **Then** Reality refuses to describe the claim as source-supported and identifies the missing evidence.
5. **Given** similar open gaps, **When** a user reviews the queue, **Then** Reality may show possible duplicates but does not merge them without confirmation.
6. **Given** a first-time or uncertain Web user, **When** capture begins, **Then** Reality explains the outcome, offers concrete question examples, and progressively asks purpose, recurrence, and present information source before submission.

---

### User Story 3 - Review and Implement an Accepted Gap (Priority: P1)

An authorized domain owner accepts or rejects a classification, reviews its exact implementation proposal, and carries the accepted gap to a verified outcome through any supported surface.

**Why this priority**: The feature is useful only if a captured need can become supported behavior through a controlled, traceable boundary.

**Independent Test**: Approve one Fact-classified gap, review its exact extraction and replay scope, execute the implementation path, and verify the resulting supported behavior and gap history without permitting an unapproved mutation.

**Acceptance Scenarios**:

1. **Given** a recommendation, **When** an authorized human accepts or overrides it, **Then** the decision, actor, time, rationale, and selected destination are appended to the gap history.
2. **Given** an accepted classification, **When** Reality prepares implementation, **Then** it presents the exact source match, target subject relationship, value contract, affected data scope, idempotency behavior, rollback or disable path, and verification plan before execution.
3. **Given** an implementation proposal that has not been explicitly approved, **When** any surface attempts execution, **Then** no Fact, Evidence, Reality, derivation rule, predicate contract, or interpreter behavior changes.
4. **Given** an approved Fact implementation whose match, subject relationship, value contract, preview, and replay scope fit the safe declarative rule boundary, **When** an ERP or Operations administrator confirms execution, **Then** Reality activates a versioned tenant-specific SourceRecord-to-Fact rule without executing user-authored code.
5. **Given** an accepted typed Evidence, typed Reality, derived-view, or unsupported Fact implementation, **When** implementation is prepared, **Then** Reality produces a complete developer implementation package and does not change runtime behavior.
6. **Given** an implemented gap, **When** its outcome is inspected, **Then** every surface shows what became supported, the approving decision, implementation identity, verification result, and the trace to supporting examples.
7. **Given** a rejected or source-only gap, **When** it is settled, **Then** no business records are changed and the rationale remains visible in history.

---

### User Story 4 - Operate a Shared Gap Queue (Priority: P2)

An operator can find open, awaiting-decision, implementation-ready, implemented, and rejected gaps without returning to the originating chat or record.

**Why this priority**: Chat is an entry point, not durable workflow ownership.

**Independent Test**: Create gaps through all three surfaces, advance them through different states, archive the originating conversation, and verify tenant-scoped filters, counts, detail, and available next actions remain correct.

**Acceptance Scenarios**:

1. **Given** gaps from multiple origins, **When** the shared queue is opened, **Then** each gap appears once with question, status, origin, age, evidence summary, and next action.
2. **Given** an archived originating conversation, **When** its gap is opened from the queue, **Then** the complete gap remains usable and unchanged.
3. **Given** two tenants, **When** either lists, searches, reads, or mutates gaps, **Then** it sees and affects only its own records.
4. **Given** concurrent decisions or executions, **When** a stale action is submitted, **Then** it is rejected without overwriting the current decision.

---

### User Story 5 - Configure an ERP-Ready Conditional Fact Rule (Priority: P1)

An ERP or Operations administrator configures a safe business condition, previews which source records and lines satisfy it, chooses whether the Fact value comes from the source or is a reviewed constant, and activates the immutable rule only after understanding conflicts and failures.

**Why this priority**: Real ERP rules distinguish applicable records from explicit negative values, commonly operate on order lines, and must remain supportable after activation and during large historical replays.

**Independent Test**: Configure a rule that emits the constant Boolean Fact `order.requires_manual_review = true` only when all reviewed conditions match, then configure a line-level rule that extracts a value for matching DocumentLines. Simulate, activate, import new immutable source versions, replay multiple pages, and verify skips, failures, conflicts, timestamps, provenance, and operational totals.

**Acceptance Scenarios**:

1. **Given** a rule with one or more conditions, **When** every condition is satisfied, **Then** Reality resolves the subject and creates the configured Fact; when a condition is not satisfied, it records a normal `not_applicable` outcome and creates no Fact.
2. **Given** a rule with an extracted output, **When** it applies, **Then** the output value is read and validated from its configured path; **given** a constant output, **Then** the reviewed constant is validated and emitted without reading an output path.
3. **Given** an order containing multiple lines, **When** a controlled line rule is evaluated, **Then** each matching source line resolves to exactly one corresponding DocumentLine and receives an independently traceable Fact.
4. **Given** an effective timestamp path, **When** the source value is a valid timezone-aware timestamp, **Then** the Fact uses its UTC instant; missing, naive, or invalid timestamps create a failure outcome and no Fact.
5. **Given** two active rule families would produce conflicting current values for the same tenant, subject, and predicate, **When** evaluation or activation is attempted, **Then** the conflict is visible and Reality does not silently select a winner.
6. **Given** more historical sources than one replay page, **When** replay is run and resumed, **Then** each page returns a deterministic continuation cursor, aggregate progress remains visible, and no source-subject-rule evaluation is duplicated.
7. **Given** a rule has executed, **When** an operator inspects it, **Then** the active version, last execution, counts by outcome, representative failures, replay progress, and exact generated Facts are visible through the shared service and every supported surface.
8. **Given** a rule such as `B2B AND (amount over 1,000 OR payment overdue)`, **When** an administrator builds and simulates it, **Then** the grouping is visually explicit and the Fact is predicted or created only according to that exact grouping.

### Edge Cases

- The original question contains sensitive customer data that should not be copied into summaries or examples.
- A referenced SourceRecord is superseded after investigation; the exact reviewed version remains identifiable.
- A source path exists in some examples but is absent, null, differently typed, or semantically inconsistent in others.
- A proposed target subject cannot be resolved deterministically for every matching source.
- A gap initially appears to be a Fact but repeated operational use proves a typed concept is required.
- Two gaps ask different questions about the same source path, or the same question is supported by different source paths.
- An implementation succeeds for new sources but replay of historical sources partially fails.
- The source interpreter or predicate contract changes between implementation preview and approval.
- An agent recommendation changes after additional answers; prior recommendations remain auditable.
- A user lacks authority to classify, approve, execute, or inspect raw examples.
- A condition path is absent, null, an array where a scalar is required, or has a type incompatible with its operator.
- A source line cannot be mapped to exactly one immutable DocumentLine.
- Two active rule families emit different values for the same subject, predicate, and observation instant.
- Replay stops between pages and is resumed with an expired, foreign-tenant, or rule-mismatched cursor.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST let authenticated tenant members capture a Reality Gap through Chat, MCP, and Web using one shared application operation.
- **FR-002**: A gap MUST record a business question, intended use, origin, requester context, lifecycle status, creation time, and tenant-scoped idempotency identity.
- **FR-003**: A gap MAY reference same-tenant SourceRecords, Documents, DocumentLines, Facts, Commitments, Reservations, Movements, LedgerEntries, or other supported subjects by opaque identity, and MUST NOT use human numbers as identity.
- **FR-004**: Source evidence MUST remain lossless and immutable; the gap MUST store references, selected paths, and bounded reviewed examples rather than duplicate full payloads.
- **FR-005**: The system MUST expose the same gap list, detail, guided questions, answers, recommendations, decisions, implementation preparation, and permitted execution actions through Chat, MCP, and Web.
- **FR-006**: The guided review MUST establish the question, intended decision or action, current workaround, asserted source, recurrence, desired use, scope, and whether the information is an explicit source statement, operational occurrence, or derivation.
- **FR-007**: Saved investigation answers and evidence additions MUST be append-audited and protected from stale concurrent updates.
- **FR-008**: Classification MUST select one of `source_only`, `fact`, `typed_evidence`, `typed_reality`, `derived_view`, or `rejected` and MUST include rationale and considered alternatives.
- **FR-009**: Agent recommendations MUST remain proposals, state evidence and limitations, and MUST NOT settle classification or mutate Source, Evidence, or Reality.
- **FR-010**: Only an authorized human MUST be able to accept, override, or reject a classification, with actor and time recorded.
- **FR-011**: Implementation preparation MUST describe exact input matching, output meaning, target relationship, value validation, affected historical and future scope, idempotency, failure behavior, disable or rollback path, and verification.
- **FR-012**: Every mutating action initiated through Chat or MCP MUST use a preview and explicit human confirmation; Web mutations MUST use the same application operation and authorization rules.
- **FR-013**: Unapproved, stale, rejected, ambiguous, unsupported, or cross-tenant implementation attempts MUST change no Source, Evidence, Reality, predicate contract, interpreter rule, or derived behavior.
- **FR-014**: The complete gap lifecycle and history MUST remain available independently of the originating conversation and surface.
- **FR-015**: The shared queue MUST support deterministic ordering and filtering by lifecycle state, destination, origin, and age, with bounded results and totals.
- **FR-016**: The system MUST identify possible duplicates without automatically merging or discarding independently captured business intent.
- **FR-017**: Successfully implemented gaps MUST identify the supported outcome and its verification evidence; partial or failed implementation MUST remain visible and retry-safe.
- **FR-018**: Settling a gap as source-only or rejected MUST never fabricate a Fact, Evidence record, Reality record, or operational Exception.
- **FR-019**: Raw source examples MUST follow existing tenant access and sensitive-data presentation rules across all surfaces.
- **FR-020**: User-facing language MUST call the item "Open question" (plural: "Open questions") while durable technical contracts MAY use `RealityGap`. The label MUST describe a business question that Reality cannot yet answer reliably, not imply that a single required source field is absent. In primary navigation, Open questions MUST appear immediately after Exceptions.
- **FR-021**: An owner-authorized ERP or Operations administrator MUST be able to create and activate a declarative tenant-specific SourceRecord-to-Fact rule when the reviewed mapping uses only supported source matching, source paths, subject relationships, value contracts, and normalization operations.
- **FR-022**: A declarative interpretation rule MUST NOT contain or execute user-authored code, SQL, templates, network calls, arbitrary expressions, or unrestricted data access.
- **FR-023**: Before activation or historical replay, the system MUST provide a bounded simulation with total sources considered, matches, uniquely resolved subjects, invalid values, ambiguous subjects, expected Facts, and representative failures.
- **FR-024**: Each activated rule MUST be immutable and versioned; editing creates a new inactive version, activation selects one current version for future matching, and disabling stops future interpretation without deleting prior Facts.
- **FR-025**: Facts produced by a rule MUST identify the exact rule version, SourceRecord, opaque subject, predicate, canonical value, observation time, and deterministic idempotency identity.
- **FR-026**: Historical replay MUST be a separate confirmed operation, process only the reviewed source scope, be restartable without duplicate Facts, and retain per-source outcomes.
- **FR-027**: Accepted destinations outside the safe declarative SourceRecord-to-Fact boundary MUST produce an English developer package containing the business question, evidence references, approved classification, behavioral requirements, edge cases, proposed mapping, replay considerations, and acceptance examples.
- **FR-028**: The Open questions Web page MUST act as the durable work register rather than a competing capture form. Its empty state and page introduction MUST explain that questions start in Ask Reality and provide one direct action that opens Chat with a prefilled business-language request to capture an open question.
- **FR-029**: Chat MUST present Reality Gap confirmation inputs as business fields rather than serialized payloads and, after successful creation, MUST state what was created and provide a direct next action to open the Open questions register.
- **FR-030**: Gap detail MUST expose one primary next step at a time: collect a concrete example, request a recommendation, review that recommendation, then prepare implementation. Its progress indicator MUST use checkmarks, numbered steps, connecting lines, and explicit completed/current/upcoming labels so sequence and state never depend on color alone; it MUST become a vertical worklist on narrow screens. Technical destination and rule fields MUST remain secondary to the business explanation.
- **FR-031**: During example collection, a user MUST be able to search the active tenant's immutable source records by business reference without leaving the gap. Results MUST be bounded, show safe scalar field candidates from the exact payload, and allow the user to attach one candidate as evidence containing the source-record ID, field path, and displayed value. Manual observation MUST remain an explicit fallback. Search itself is read-only; attaching evidence uses the existing revision-checked mutation.
- **FR-032**: Selecting a source field as evidence MUST carry its source system, source type, field path, scalar type, and displayed value into the investigation. The technical implementation draft MUST prefill those values and suggest a stable predicate without overwriting later operator edits.
- **FR-033**: Rule simulation results MUST render inside the gap detail in business language, summarize checked sources, prospective Facts, and records needing attention, and retain bounded per-source details. The UI MUST NOT expose the result through a native alert or raw serialized response.
- **FR-034**: The workflow MUST distinguish business adoption from technical activation with a fifth progress step. A draft rule MUST be editable through a prefilled form; saving changes MUST create a new immutable version and require a fresh simulation. Activation MUST only be offered after simulation, and simulation problems MUST require explicit acceptance before activation.
- **FR-036**: Rule activation confirmation MUST use the product dialog pattern rather than a browser-native confirmation. It MUST identify the exact rule version, explain the future effect, disclose accepted simulation problems, and keep cancel and activation as distinct actions.
- **FR-037**: Once a rule exists, its current version, status, and lifecycle actions MUST be visible without expanding a technical disclosure. Editing MUST use a dedicated prefilled dialog with explicit cancel and save-as-new-version actions rather than transforming the detail page in place.
- **FR-038**: The Open questions overview MUST separate actionable gaps from terminal gaps. Actionable gaps MUST remain a work queue, while `implemented`, `rejected`, and `source_only` gaps MUST appear in a compact completed-items table. Opening any item MUST replace the overview with its detail and expose an explicit back action that returns to the overview without relying on browser navigation. On desktop, long business questions MUST wrap inside their bounded column without pushing outcome, update time, or row actions outside the visible table width.
- **FR-039**: The Open questions overview MUST use one full-width paged register with `open`, `completed`, and `all` lifecycle tabs, tenant-scoped text search across question and intended use, and a lifecycle-compatible status filter. It MUST reuse the established Open items table, control-bar, state-badge, and row-action patterns rather than introduce a separate register design. Counts and filtered pages MUST be computed by the shared server-side list operation; the browser MUST NOT load the complete register to implement search, filtering, counts, or pagination.
- **FR-035**: Gap detail MUST list every immutable rule version with status and defining fields. Facts created by a rule MUST display that rule's logical name and version through a tenant-scoped read model while retaining direct links to the exact rule and SourceRecord.
- **FR-040**: A rule MAY contain declarative conditions in nested `ALL` and `ANY` groups; each condition MUST use a restricted scalar path and one of `equals`, `not_equals`, `in`, `not_in`, `exists`, `not_exists`, `greater_than`, `greater_or_equal`, `less_than`, or `less_or_equal` with operator-compatible typed operands. Evaluation MUST preserve the reviewed grouping exactly.
- **FR-041**: Rule output MUST explicitly select either `source_path` mode, which extracts a configured value path, or `constant` mode, which emits a reviewed typed scalar. Existing extraction rules MUST retain `source_path` behavior when upgraded.
- **FR-042**: A valid source that fails a condition MUST produce a durable `not_applicable` outcome and no Fact; missing or invalid required input MUST remain distinguishable from a normal condition miss.
- **FR-043**: V1 subject resolution MUST support exactly `source_document_commitments` and `source_document_lines`. The line resolver MUST use controlled iteration over one restricted source array and map each source element to exactly one existing same-tenant DocumentLine without human-number identity.
- **FR-044**: Controlled iteration MUST evaluate each bounded source-array element independently, prohibit recursive descent and wildcards outside that array boundary, and retain the source element index in every outcome and Fact idempotency identity.
- **FR-045**: `source_path` observation time MUST accept only timezone-aware ISO-8601 datetime values and normalize them to UTC. Missing, naive, or invalid values MUST create no Fact. `source_received_at` remains the default.
- **FR-046**: Simulation, activation, ingestion, and replay MUST detect competing active rule families that produce incompatible values for the same tenant, subject, predicate, and observation instant; conflicts MUST be visible and MUST NOT be silently resolved by activation order.
- **FR-047**: Replay MUST use deterministic bounded pages with an opaque tenant-, rule-, and scope-bound continuation cursor, permit safe retry and resume, and report cumulative as well as page outcome counts without duplicate Facts or outcomes.
- **FR-048**: Rule detail MUST expose current version and status, last evaluation time, outcome counts including `fact_created`, `fact_existing`, `not_applicable`, `invalid_value`, `ambiguous_subject`, and `conflict`, representative failures, replay progress, and links to generated Facts and exact SourceRecords.
- **FR-049**: Conditions, iteration, output configuration, and subject resolution MUST be immutable versioned rule fields. Editing any of them creates a new inactive version and requires a fresh simulation and activation confirmation.
- **FR-050**: Chat, MCP, HTTP, and Web MUST expose the same conditional draft, simulation categories, version fields, replay cursor, and execution summary through shared application services; adapters MUST NOT evaluate conditions or resolve subjects.
- **FR-051**: The Web rule editor MUST present conditions, output, subject scope, and time source as business-readable structured controls, prevent unsupported combinations, and explain the difference between `not applicable`, `unknown or invalid`, and an explicit negative Fact.
- **FR-052**: Rule evaluation MUST remain bounded: at most 20 conditions per rule, 500 iterated elements per SourceRecord, 100 simulation sources, 500 replay sources per page, and 10 representative outcomes per category.
- **FR-053**: A failed rule evaluation MUST never reject or mutate the immutable SourceRecord, block unrelated interpreters, or create a partial Fact for the failed source element.
- **FR-054**: Activating, disabling, editing, replaying, or acknowledging conflicts MUST remain owner-authorized confirmed mutations with immutable audit receipts naming the exact rule version and reviewed simulation. Acknowledgement MUST NOT create, alter, delete, or prioritize a conflicting Fact.
- **FR-055**: Rule and outcome queries MUST be tenant-scoped, deterministic, bounded, and indexed for active-rule matching, per-rule operational summaries, continuation replay, and Fact provenance.
- **FR-056**: Boolean grouping MUST remain bounded to at most three group levels and 20 leaf conditions. Empty groups, unsupported modes, and structures exceeding either bound MUST be rejected before a rule version is stored.
- **FR-057**: Existing flat rules MUST retain their original all-of meaning without migration or reinterpretation, and editing group structure MUST create a new inactive immutable rule version.
- **FR-058**: Web, Chat, MCP, and HTTP representations MUST use the same explicit condition-group structure; no adapter may flatten, reorder, or independently evaluate it.
- **FR-059**: New open questions captured through Chat or MCP MUST use `question` as one concise queue label of at most 100 characters and keep explanatory context in `intended_use` or investigation history. The queue MUST visually bound both fields so business context cannot create an oversized row.

### Domain and Traceability Requirements

- **DR-001**: RealityGap is a tenant-scoped modeling-work item, not Source, Evidence, Reality, Fact, BusinessEvent, ChangeProposal, or OperationalException.
- **DR-002**: RealityGap references its reviewed evidence and subjects but MUST NOT duplicate their authoritative business fields or become operational authority.
- **DR-003**: Lifecycle transitions MUST be append-auditable and every repository query and relationship validation MUST enforce tenant scope.
- **DR-004**: Chat, MCP, and Web MUST call the same application services/tools; adapters MUST NOT write gaps or implementation outcomes directly.
- **DR-005**: A gap classified as Fact MUST still satisfy the existing source, subject, predicate, value, immutability, event, and idempotency rules when implemented.
- **DR-006**: Typed Evidence, typed Reality, and derived-view outcomes MUST follow the normal specification, Constitution Check, schema proof, test-first implementation, and deployment controls; a Reality Gap approval cannot waive them.
- **DR-007**: Implementation execution MUST retain the shortest true Source → Evidence → Reality links and MUST NOT add operational state to Documents.
- **DR-008**: External payloads remain lossless and immutable; a new source version cannot silently replace the exact version reviewed for a gap.
- **DR-009**: Tenant-specific interpretation rules extend the allowed Fact vocabulary only inside their owning tenant and cannot change global predicate contracts or another tenant's behavior.
- **DR-010**: Rule activation and replay are confirmed mutations implemented through the shared application-tool boundary; source ingestion invokes the same rule evaluator after immutable source storage.
- **DR-011**: Conditions and iteration are data, never executable expressions. Their evaluator uses a closed operator and resolver registry owned by the domain service.
- **DR-012**: Line-level Facts link directly to the resolved DocumentLine and exact SourceRecord/rule version; interpretation outcomes may retain source element coordinates but MUST NOT duplicate line business fields.
- **DR-013**: Conflicting Facts remain immutable observations. Conflict handling adds an outcome and operator-visible explanation rather than rewriting, deleting, or assigning hidden precedence to Facts.

### Key Entities

- **RealityGap**: The durable tenant-scoped missing-information question, current lifecycle state, origin, intended use, optimistic revision, and latest next action.
- **Gap Context Reference**: An opaque link from a gap to a same-tenant source, evidence, Fact, or Reality subject that framed the missing answer.
- **Gap Investigation Entry**: An append-only answer, selected source path, bounded example, or agent recommendation with actor, time, evidence references, and limitations.
- **Gap Classification Decision**: The authorized accepted, overridden, or rejected model destination and rationale.
- **Gap Implementation Proposal**: The reviewed extraction or product-change contract, scope, safety behavior, and verification plan awaiting approval.
- **Gap Implementation Result**: The immutable receipt for activation or external deployment, including status, supported outcome, verification, and failure details.
- **Interpretation Rule Version**: An immutable tenant-specific declarative SourceRecord-to-Fact contract with source match, path, subject resolver, value contract, normalization, observation-time selection, lifecycle state, and originating gap.
- **Interpretation Outcome**: A per-source evaluation receipt recording match, skip, ambiguity, validation failure, or produced Fact without replacing the immutable source or Fact.
- **Rule Condition**: A versioned declarative comparison over a restricted scalar path, represented as validated data.
- **Condition Group**: An immutable bounded node that combines conditions or child groups using explicit `ALL` or `ANY` semantics.
- **Replay Cursor**: An opaque continuation token validated against tenant, exact rule version, source scope, and deterministic last position; it conveys no authority and cannot broaden the authenticated query scope.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A user can capture a missing business answer from Chat or a contextual Web action in under two minutes without supplying a technical model term or source path.
- **SC-002**: The same captured gap, history, status, and next action are visible through Chat, MCP, and Web with no surface-specific lifecycle behavior.
- **SC-003**: Every classification recommendation names exactly one destination, cites its reviewed evidence, and states at least one limitation or missing prerequisite.
- **SC-004**: In acceptance testing, 100% of unapproved, rejected, stale, ambiguous, and cross-tenant implementation attempts produce no business-model effect.
- **SC-005**: An authorized reviewer can move a supported Fact candidate from captured question to implementation-ready proposal in under ten minutes when source examples and subject relationships are already available.
- **SC-006**: Every settled gap can be reconstructed from its history with requester, evidence, recommendation, human decision, implementation scope, outcome, and verification.
- **SC-007**: Lists remain deterministic and return the first bounded page within two seconds for a tenant with 10,000 gaps and 100,000 investigation entries under the documented benchmark environment.
- **SC-008**: In usability review, a first-time business operator can explain what the capture will do and submit a well-formed gap without external instruction or technical terminology.
- **SC-009**: The conditional evaluator produces the same classification and canonical output in simulation, ingestion, and replay for 100% of shared contract fixtures.
- **SC-010**: An interrupted replay of 10,000 sources can resume from its returned cursor without duplicate Facts or outcomes and with cumulative totals equal to an uninterrupted replay.
- **SC-011**: In acceptance testing, every unsupported operator, path, operand type, resolver, iteration shape, and naive timestamp is rejected before activation or results in a bounded failure outcome without business-model mutation.

## Requirement Traceability

| Requirement group                                   | Acceptance story                                  | Planned proof                                                                                   |
| --------------------------------------------------- | ------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| FR-001–FR-007, FR-014–FR-016; DR-001–DR-004         | US1 capture and US4 shared queue                  | Service, tenant, proposal, HTTP, MCP, Chat, Web, and migration stories                          |
| FR-008–FR-011, FR-017–FR-020, FR-027; DR-006–DR-008 | US2 investigation and US3 governed implementation | Recommendation, authorization, developer-package, trace, and no-mutation stories                |
| FR-021–FR-026; DR-005, DR-009–DR-010                | US3 self-service Fact implementation              | Evaluator, simulation, activation, ingestion, provenance, replay, disable, and recovery stories |
| SC-001–SC-006                                       | US1–US4 end-to-end journeys                       | Cross-surface quickstart and focused acceptance tests                                           |
| SC-007                                              | US4 bounded queue                                 | PostgreSQL benchmark                                                                            |
| FR-040–FR-058; DR-011–DR-013; SC-009–SC-011         | US5 ERP-ready conditional rules                  | Evaluator matrix, grouped logic, line resolution, conflict, replay-resume, cross-surface, migration, and operational-summary tests |

## Assumptions and Dependencies

- Existing authentication, tenant membership, Chat sessions, SourceRecord inspection, ChangeProposal confirmation, and application-tool boundaries are reused.
- All active tenant members may capture and investigate gaps; classification and implementation approval require an existing owner-level authority unless a narrower permission model is explicitly proven during planning.
- Chat may suggest gap capture when an answer is unsupported, but the user explicitly chooses whether to persist it.
- Agent source analysis is limited to tenant-visible records and bounded examples and does not send raw payloads to an unapproved provider.
- V1 starts with source-backed ecommerce questions. Safe declarative SourceRecord-to-Fact mappings include closed, bounded ALL/ANY condition groups, extracted or constant typed output, Commitment or DocumentLine resolution, and one bounded source-array iteration. They can be activated by an owner-authorized ERP or Operations administrator; every other destination follows the normal product-development workflow through a generated developer package.
- Gap history is retained with the tenant's business records; deletion and cross-tenant sharing are outside V1.
- All repository artifacts, generated implementation material, contracts, and recorded decisions are English; user-entered questions and lossless examples retain their original language.
