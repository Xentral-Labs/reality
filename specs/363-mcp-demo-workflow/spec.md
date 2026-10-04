# Feature Specification: Browser-free MCP Demo Workflow

**Feature Branch**: `codex/363-mcp-demo-workflow`
**Created**: 2026-10-04
**Status**: Draft for scope review; no behavior implemented
**Language**: English
**Input**: Prepare a PR from the complete demo walkthrough and the owner's corrected
16-item follow-up list. The operational agent has no browser. MCP review and explicit
human confirmation are primary; a browser review link is optional.

## Context and Intent

### Problem

The October 4 demo walkthrough proved external MCP reads, a reservation proposal,
post-execution verification and a scheduled external-agent run. It also exposed
incorrect internal Chat routing, oversized pending-decision answers, incomplete
financial navigation and a shipping report that mistook absent Shipment objects for
absent shipment Movements. A successful local test with manual help is not proof of
a complete browser-free agent workflow.

### Scope

Make an authorized agent able to identify its company, read operational evidence,
inspect one exact decision and its criteria, hand it to a human confirmation client,
and verify the resulting state without browser access. Preserve existing authority
and services. Complete the associated demo documentation and user-facing corrections.
Every item in the owner's list is accounted for in FR-001–FR-016 and the triage file.

The current `proposal_approve_and_execute` tool is reused, not reinvented. The test
credential deliberately excluded confirmation rights; that does not establish a
missing execution tool. Review links are optional conveniences for humans.

### Non-Goals

- No autonomous approval, widened credentials, bypassed review token or broad
  delegation inferred from an agent's claim that a human said yes.
- No new domain tables, document fulfillment state or alternative business rules.
- No scheduling engine inside Reality, Claude configuration changes, mailbox
  transport, actual payment, shipment or purchase during this development effort.
- No automatic acceptance of live sources to make the demo appear active.
- No duplicate implementation of open PR #367 / spec 362.
- This preparation PR does not claim production fixes or green runtime acceptance.

### Existing Contracts

- Constitution and `docs/SPEC_DRIVEN_WORKFLOW.md`.
- Specs 059, 249, 263, 270, 273, 276, 323 and 325: exact proposal review,
  decision attribution, stale reviews, authorization and safe presentation.
- Spec 145: authoritative, bounded tenant-scoped MCP reads and retained-order evidence.
- Specs 146, 168, 200 and 356: canonical demo and reviewed external intake.
- Specs 291 and 353: product advice versus operational questions and starting prompts.
- Spec 362 / PR #367: purpose in capability discovery, explicitly excluding identity.
- `docs/WEB_SPEC.md`, `docs/features/company-setup-demo.md` and generated tool docs.

## User Scenarios & Testing

### User Story 1 - Review and settle an exact decision without an agent browser (Priority: P1)

A connected agent identifies its company and available rights, prepares a reservation,
reads its exact current review and exposes the decision criteria. An authorized human
confirmation client approves or rejects it using the existing boundary. The agent
verifies the actual effect and remaining work.

**Why this priority**: This is the owner's required operating model, including the
critical distinction between proposing an action and approving it.

**Independent Test**: Two tenant-scoped test credentials (read/propose and explicit
confirmation) exercise the same proposal through MCP with browser access unavailable.

**Acceptance Scenarios**:

1. **Given** a read/propose credential, **When** it reads its context and review,
   **Then** company identity, actual rights, exact input, current effect, prerequisites,
   blockers and duplicate candidates are available without execution rights or writes.
2. **Given** an exact current review and explicit human decision, **When** an authorized
   confirmation client executes it, **Then** one receipt and correct attribution are
   retained; the proposing agent independently verifies quantities and remaining work.
3. **Given** missing rights, a foreign company, changed state or stale review,
   **When** confirmation is attempted, **Then** it fails safely with no business effect
   and a truthful recovery step, not a duplicate replacement or guessed approval.
4. **Given** a growing decision queue, **When** an agent checks duplicates or counts,
   **Then** bounded summaries and detail reads suffice without shell or file searching.
5. **Given** no configured web base URL, **When** the flow runs entirely through MCP,
   **Then** review/confirmation still works; absence of an optional link is not a blocker.

### User Story 2 - Obtain an evidence-correct operational answer (Priority: P1)

A user asks the internal Chat or an external agent to explain current orders, shipping
and a partially settled invoice. The answer reflects held business evidence, not a
product Journey Guide or unsupported inference.

**Why this priority**: A scheduled but factually wrong report does not help operations.

**Independent Test**: Seed an order with a shipment Movement but no Shipment object,
an open remainder and a partially settled invoice; read each through shared tools.

**Acceptance Scenarios**:

1. **Given** a current-company request mentioning Reality and routine times,
   **When** Chat routes it, **Then** operational tools are selected; a genuine question
   about product capability still routes to public product advice.
2. **Given** a shipment Movement and an empty Shipment list, **When** the agent checks
   shipping, **Then** it reports the Movement and separately states absent tracking;
   it does not conclude that nothing was shipped from an empty object list.
3. **Given** a partially settled supplier invoice, **When** the agent explains it,
   **Then** the received original amount, open amount, lines, relevant allocations and
   original evidence are reachable by opaque IDs with completeness clearly stated.
4. **Given** a stored promise and no remaining shipment evidence,
   **When** a support reply is drafted, **Then** it describes recorded facts, unknown
   cause and recorded promise without a new guarantee or notification commitment.

### User Story 3 - Follow a truthful demo and agent setup guide (Priority: P2)

A German-speaking user creates a demo, connects an external agent, distinguishes
pending source interpretation from accepted orders and understands which system owns
the schedule, permissions and human decision.

**Why this priority**: Setup instructions must explain the working system and its
boundaries rather than make expected controls look like broken automation.

**Independent Test**: Follow the documented startup and inspect a freshly initialized
canonical profile, source queue and one scheduled external-agent run.

**Acceptance Scenarios**:

1. **Given** a German entry, **When** signup opens, **Then** German is preserved and
   translated navigation names match the actual UI.
2. **Given** live synthetic intake requiring approval, **When** the user inspects its
   status, **Then** raw input, pending interpretation and accepted operational work
   are distinguished without auto-approval or additional demo timers.
3. **Given** a proposal reserving two units, **When** reviewed before execution,
   **Then** current zero reserved and proposed two reserved are distinct, with named
   company/order/item/location and the existing authoritative review.
4. **Given** an external agent with scheduling support, **When** setup is followed,
   **Then** the documented mode, tool access, saved assignment, timezone, workdays,
   actual next run, device requirements, pause and technical permission limits are clear.
5. **Given** a fresh demo profile, **When** the guide names a purchase example,
   **Then** its stated received/billed quantities match the canonical profile proof.

### Edge Cases

- Mixed currencies, unknown timezone, partial page coverage and concurrent queue changes.
- Identical human document numbers across distinct immutable source inputs.
- Fulfilled/cancelled orders with retained movements outside current queues.
- Private proposal preview carriers and credentials must remain redacted.
- An executed or in-progress proposal must be reconciled, never blindly redispatched.
- Optional browser links, mailbox access or external scheduling may be unavailable.
- Prompt restrictions are not technical tool isolation; the guide must not imply otherwise.
- Existing MCP clients using an unpaged list require an explicit compatibility decision.

## Requirements

### Functional Requirements

- **FR-001**: The exact proposal review and existing explicit human confirmation path
  MUST be usable through MCP without an agent browser; review URLs MUST remain optional.
- **FR-002**: Review MUST expose company and opaque record references, current versus
  proposed quantities/effects, prerequisites, blockers, duplicate candidates and actual
  decision policy from the same services as Web, with no automatic approval recommendation.
- **FR-003**: An authorized read MUST expose its selected company ID, name, stored
  purpose and actual credential rights without revealing other companies or secrets.
  Reuse spec 362 purpose disclosure; do not change its narrow accepted scope silently.
- **FR-004**: Shipping reads/guidance MUST distinguish shipment Movements, Shipment
  objects and carrier evidence, including retained records and incomplete coverage.
- **FR-005**: Pending-decision discovery MUST offer bounded stable traversal, filters
  and summaries plus exact detail, allowing duplicate inspection without full plans.
- **FR-006**: Demo status and instructions MUST distinguish received source, proposed
  interpretation and accepted business effect without relaxing the intake decision gate.
- **FR-007**: An invoice explanation MUST make held lines, received amounts, settlements,
  allocations and source references reachable with truthful missing-evidence handling.
- **FR-008**: Authored purchase examples in both documentation locales MUST match the
  canonical profile's received and billed evidence; fixture changes need explicit proof.
- **FR-009**: Current-company operational Chat requests MUST not be classified as
  public product advice merely because they mention Reality, tools or scheduling.
- **FR-010**: Support guidance MUST separate recorded facts/promises from new guarantees
  and future actions; no unsupported shipping cause or tracking is invented.
- **FR-011**: Agent setup instructions MUST state the actual external mode and verified
  tool/scheduling prerequisites without claiming the untested OAuth path was verified.
- **FR-012**: Setup guidance MUST distinguish credential enforcement and technical
  connector restrictions from instruction-only restrictions; no automatic widening.
- **FR-013**: Recurrence guidance MUST distinguish company timezone from schedule
  timezone and show actual next/last run, device dependency, lateness and pause behavior.
- **FR-014**: Decision UI MUST distinguish recorded state from proposed effect and show
  named business context without replacing authoritative review or confirmation rules.
- **FR-015**: Signup MUST retain the selected locale; demo navigation terminology MUST
  match the localized running UI while preserving source payload languages.
- **FR-016**: Affected tool contracts MUST enumerate closed parameter choices, expose
  supported discovery families and name callable follow-up reads; regenerate references.

### Domain and Architecture Requirements

- **DR-001**: Source → Evidence → Reality, received values and shortest true links remain
  authoritative. Reads introduce no business writes or stored derived authority.
- **DR-002**: All reads/reviews/decisions enforce tenant and actor permissions through
  shared services; explicit approval, replay, stale-review and attribution rules remain.
- **DR-003**: No new schema, scheduler, mailbox transport or Claude permission management
  is introduced by this scope. Any later need must be separately justified and reviewed.

### Key Entities

Existing Company, credential, ChangeProposal/review/receipt, SourceRecord,
Document/DocumentLine, Commitment, Reservation, Movement, Shipment and LedgerEntry
are read or acted on through their existing boundaries; no new business entity is required.

## Success Criteria

- **SC-001**: A complete reservation review/decision/verification story succeeds with
  the agent browser unavailable and exact explicit human confirmation retained.
- **SC-002**: Unauthorized, wrong-company, stale and replay cases have executable proof
  of zero unintended effects and one correct receipt for a successful decision.
- **SC-003**: The full demo mission routes to business records, and movement-only shipping
  and partial-settlement examples have evidence-correct, complete explanations.
- **SC-004**: The published guide matches the fresh profile and names missing capabilities,
  rights and approval prerequisites without promising unattended execution.
- **SC-005**: Every requirement has a regression/acceptance proof or a stated manual
  external-agent verification; no failed gate is marked complete.

## Assumptions and Dependencies

- The owner approved the follow-up list and requested PR preparation. This specification
  is the concrete scope-review artifact, not an implementation or merge authorization.
- Code planning follows human scope acceptance as required by the repository workflow.
- Test data is synthetic; original live tenant IDs, credentials, local connection files
  and full source payloads are intentionally excluded from this PR.
- Open PR #367 provides stored company purpose. Additional identity and authorization
  disclosure is a separate requirement to review, not an amendment to its FR-002.
- External-agent model behavior, schedule jitter and connector isolation cannot be
  enforced by Reality. Improve tool contracts and truthful documentation; test the agent.
- Live intake approval is intentional under spec 356; preserve it.

## Requirement Traceability

| Requirements | Stories | Planned acceptance proof |
|---|---|---|
| FR-001, FR-002, DR-002 | US1.1–3, US1.5 | MCP exact review/confirmation, stale, authorization and replay story |
| FR-003 | US1.1, US1.3 | Context disclosure and cross-tenant/secret refusal tests; spec 362 reuse |
| FR-004 | US2.2 | Movement without Shipment, mixed evidence and partial coverage story |
| FR-005 | US1.4 | Filtered/keyset traversal, bounded payload, duplicate and compatibility proof |
| FR-006 | US3.2 | Pending source versus accepted record and no auto-admission proof |
| FR-007 | US2.3 | Part-paid invoice → lines/allocations/source proof, mixed currencies |
| FR-008 | US3.5 | Canonical profile and EN/DE guide evidence contract |
| FR-009 | US2.1 | Exact October 4 mission plus product-question routing regressions |
| FR-010 | US2.4 | Draft source grounding plus manual external-agent review |
| FR-011–FR-013 | US3.4 | Documentation contracts and external manual/timer/pause qualification |
| FR-014 | US3.3 | Review presentation source/browser proof with shared-service assertions |
| FR-015 | US3.1 | Signup locale/navigation source and browser proof |
| FR-016 | US1, US2 | Schema choices/discovery/follow-up tests and generated-catalog check |
| DR-001, DR-003 | All | Read-only service/tenant review, no migrations or scheduler added |
| SC-001–SC-005 | All | Required gates and evidence recorded after implementation, not in this draft |
