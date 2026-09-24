# Feature Specification: Engine Room

**Feature Branch**: `266-engine-room`
**Language**: English
**Created**: 2026-09-24
**Status**: Draft
**Input**: Owner: I want a live monitor of everything that happens — via MCP, chat, the API and the web — where I can look into the engine room: every access, every proposal, every click that interacts with the data model, and how it could be shown. Placement agreed in conversation: a "Live" tab next to Activities in the Inspector, plus contextual entry points.

## Context and Intent

### Problem

Reality can explain every record it holds, but not what is being done to it right now. An owner who lets an agent work through MCP, or watches a colleague use chat, sees the result only afterwards and only where the result is a change. Measured on `origin/main` (2026-09-24):

1. **Reads leave no trace.** Changes are recorded as change proposals (`action`) and business events (`business_event`, with `action_id`, `causation_id` and `correlation_id`). A read — an agent listing inventory, a chat turn asking for open items, a register page loading — is not recorded anywhere. What an agent looked at before it proposed something cannot be seen.
2. **There is no common entry point to observe.** MCP and Chat reach the application through one dispatcher (`reality.mcp.catalog.dispatch_tool`). The web API does not: of 192 tenant routes in `web/api.py`, 22 call `run_read_tool`; the rest call services directly. CLI commands call the tool layer in-process. Observing only the tool dispatcher would miss most of what the web does.
3. **Activities shows outcomes, not causes.** The Activities tab and drawer list business events. They cannot answer "which channel, which person or token, and which request caused this", and they do not update while one watches.
4. **A connected view was drafted and never wired.** `apps/web/src/unified/FlightRecorder.tsx` (lanes over a zoomable time axis) has existed since the initial public release and is not rendered by any page.

### Principle

The engine room is observation, not authority. It shows who touched which part of the model, through which channel, with what intent and what outcome, and links every outcome to the Reality record that already explains it. It never becomes a second record of business truth: what happened to the business remains in business events; the engine room records only that an interaction took place.

### Scope

- Record, per company, every interaction with the data model: tool reads and proposals through MCP, Chat and CLI; tenant API requests from the web; decisions (approve/reject); background work by scheduler and worker; source intake.
- Group interactions that belong to one cause (one web click, one chat turn, one MCP request, one job run) and connect them to the business events they caused.
- A live "Live" tab beside Activities in the Inspector that streams these interactions in three lanes — access, intent, reality — with filters and pause.
- A model map that shows which stage of Source → Evidence → Reality was read or written as it happens.
- Contextual entry points that open the Live tab pre-filtered.
- Replay of a past window on the time axis.

### Non-Goals

- Recording business truth: the engine room never replaces, duplicates or derives business events, and no business rule reads it.
- Showing raw payloads, full arguments, tokens or secrets; values stay behind the existing Inspector and source-payload links and their permissions.
- Browser navigation that sends no request: pure view changes do not touch the model.
- Cross-company or platform-wide monitoring; one view shows one company.
- Performance profiling, SQL-level tracing or replacing OpenTelemetry; the existing metrics stay as they are.
- Alerting or notifications based on interactions.
- Replaying (re-executing) interactions; replay only re-plays the view.

### Existing Contracts

- [Home activity and readiness](../../docs/features/home-live-status.md) (spec 149)
- [Decision Trail](../263-decision-trail/spec.md) — decider and token attribution
- [OAuth MCP user access](../265-oauth-mcp-user-access/spec.md) — MCP calls on behalf of a person
- [Scheduled background work](../../docs/features/scheduled-jobs.md)
- [Web UI Specification](../../docs/WEB_SPEC.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Watch interactions live (Priority: P1)

As an owner I open Inspector → Activities → Live and see every interaction with my company's model as it happens: when, channel (MCP, Chat, Web, CLI, Scheduler, Worker, Source intake), actor (person, MCP token/client, job), what was asked (tool or operation), outcome (ok, refused, failed, awaiting decision) and duration.

**Why this priority**: It is the feature. Everything else refines it.

**Independent Test**: With the Live tab open, perform one read through MCP, one through chat and one page load in a second browser; each appears within two seconds with the correct channel and actor.

**Acceptance Scenarios**:

1. **Given** the Live tab is open, **When** an MCP client calls a read tool, **Then** a row appears within 2 seconds naming channel MCP, the token (and person, where spec 265 supplies one), the tool, outcome and duration.
2. **Given** a chat turn calls three tools, **When** it completes, **Then** the three calls appear under that chat turn and link to the chat session.
3. **Given** a person opens a register page in the web, **When** its requests complete, **Then** they appear as channel Web under that person, named by their operation, not by raw URL.
4. **Given** a tool call is refused (missing scope, cross-tenant, validation), **When** it happens, **Then** it appears as refused with the error code, without the refused values.
5. **Given** the connection drops, **When** it resumes, **Then** interactions missed in between are filled in, in order, without duplicates.
6. **Given** the viewer pauses the stream, **When** interactions continue, **Then** the list stays still, a counter shows how many arrived, and resume inserts them.

### User Story 2 - Follow a cause to its effect (Priority: P1)

As an owner I see a proposal travel: requested (by whom, through which channel), awaiting decision, approved or rejected (by whom), and the business events it caused, each opening the existing Inspector.

**Why this priority**: The owner's question is "what did the agent do to my data"; a read log without the link to outcomes cannot answer it.

**Independent Test**: An agent proposes a change through MCP, an owner approves it in the web; the Live tab shows one connected trace from request to events.

**Acceptance Scenarios**:

1. **Given** an MCP client creates a proposal, **When** it is approved in the web, **Then** request, decision and resulting business events appear connected in one trace, and each event opens the event Inspector.
2. **Given** a single web click triggers several requests, **When** they complete, **Then** they are grouped as one interaction that can be expanded.
3. **Given** a job run of the worker records events, **When** it completes, **Then** the run and its events appear under channel Worker with the job kind.
4. **Given** a source record is ingested, **When** it is interpreted, **Then** source record, documents and reality records appear as one trace along the Source → Evidence → Reality chain.

### User Story 3 - See where in the model it happens (Priority: P2)

As an owner I see a map of the model stages (Source, Document/Line, Fact, Commitment, Reservation, Movement, Ledger, plus master data and finance) that marks a stage when it is read and, differently, when it is written.

**Why this priority**: It turns a log into the "engine room" picture, but the log is already useful without it.

**Independent Test**: Trigger a read of inventory and a confirmed reservation; the Movement/Reservation stages mark read and written respectively.

**Acceptance Scenarios**:

1. **Given** a read touches reservations, **When** it completes, **Then** the Reservation stage marks as read.
2. **Given** an interaction's model stages are not known, **When** it appears, **Then** no stage is marked rather than a guessed one.
3. **Given** a viewer prefers reduced motion, **When** stages mark, **Then** the mark is shown without animation.

### User Story 4 - Arrive with the right filter (Priority: P2)

As an owner I reach the Live tab from where I am, already filtered.

**Acceptance Scenarios**:

1. **Given** Settings → MCP access, **When** I choose "Calls of this client" on a token, **Then** the Live tab opens filtered to that token.
2. **Given** a chat answer in the dock, **When** I choose "Show in engine room", **Then** the Live tab opens filtered to that chat turn.
3. **Given** a record in the Inspector, **When** I choose "Who touched this", **Then** the Live tab opens filtered to interactions whose outcome or known read subject is that record.
4. **Given** the shell header, **When** interactions occur, **Then** a small activity indicator pulses, and choosing it opens the Live tab; Home and the command palette offer the same entry.
5. **Given** a filter in the URL, **When** the page is reloaded or the link shared with another owner of the same company, **Then** the same filter applies.

### User Story 5 - Replay a window (Priority: P3)

As an owner I move back on a time axis and play a past window, for example one agent run, step by step.

**Acceptance Scenarios**:

1. **Given** interactions within the retention window, **When** I select a range, **Then** they are shown in recorded order with their lanes, and I can step forward and backward.
2. **Given** a range beyond retention, **When** I select it, **Then** the view states that interactions are no longer kept while business events remain reachable in Activities.

### Edge Cases

- **Self-observation**: the Live tab's own requests and routine background refresh (Home polling, work counts, readiness) must not flood the view; they are either excluded or collapsed and hidden by default.
- **Volume**: a company under continuous demo intake produces many interactions per second; the view must stay responsive and say when it aggregates.
- **Tenant boundary**: an interaction is visible only in its own company; a request refused for a foreign company is not shown to that foreign company.
- **Unauthenticated or pre-tenant requests** (sign-in, OAuth authorization, company list) are not company interactions.
- **Failure of recording** must never fail or slow the interaction being recorded beyond a small bound.
- **Company archive or delete** removes its interactions with the company.
- **Clock**: order is recorded order, not client time.
- **Deleted person or revoked token**: past interactions keep naming them as revoked/removed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST record one interaction for every tool invocation through MCP, Chat and CLI, every tenant-scoped web API request, every proposal decision, every scheduled job run that read or wrote company data and every source intake, per company. Empty scheduler sweeps and idle worker polls are not interactions.
- **FR-002**: Each interaction MUST state recorded time, channel, actor, operation (a bounded name from the tool/command catalog or route template, never a raw URL or query), kind (read, propose, decide, job, intake), outcome with error code where applicable, and duration.
- **FR-003**: Interactions MUST NOT contain argument values, result values, payloads, tokens, secrets or free text; at most a bounded summary (argument names, result count).
- **FR-004**: Interactions that share a cause MUST share a correlation: the web client sends one per user action, each chat turn, MCP request and job run carries one, and business events written in that cause carry the same correlation.
- **FR-005**: The Live tab MUST show new interactions of the company within 2 seconds of completion, in recorded order, and resume without gaps or duplicates after a disconnect.
- **FR-006**: The Live tab MUST offer filters by channel, actor, kind, outcome and correlation, and a subject filter; filters are part of the URL.
- **FR-007**: The Live tab MUST link each interaction to the Reality it produced (business events, proposal, source record, chat session) through the existing Inspector, and state when an interaction produced nothing.
- **FR-008**: The model map MUST mark only stages the interaction is known to have read or written, distinguish read from write, and respect reduced-motion preferences.
- **FR-009**: The system MUST offer the entry points of US4: header indicator, Home, command palette, MCP token, chat turn and Inspector record.
- **FR-010**: The Live tab's own requests and routine background refresh MUST be excluded from the default view.
- **FR-011**: Interactions MUST be kept for 7 days and then removed by a scheduled job through the shared job registry.
- **FR-012**: Recording MUST NOT fail the observed interaction; a recording failure is counted in metrics and the interaction proceeds.
- **FR-013**: The Live tab and its data MUST be available only to active owners of the company; members and other companies receive not found.
- **FR-014**: The Live tab MUST let the viewer pause and resume the stream without losing interactions.
- **FR-015**: Replay MUST show interactions of a selected past window within retention in recorded order with step controls.

### Domain and Traceability Requirements

- **DR-001**: Interactions are operational telemetry, not business records. No service, projection, exception rule or business decision may read them. Source → Evidence → Reality is unchanged; the engine room only links to it.
- **DR-002**: An interaction links to business events through the shared correlation, not by duplicating event, document or source identifiers; the proposal link reuses `business_event.action_id`.
- **DR-003**: Interactions are tenant-scoped; every read enforces the tenant. Recording happens at the shared dispatcher, the tenant API boundary, the decision service, the job runtime and source intake — never inside individual adapters' business logic.
- **DR-004**: Actor attribution reuses the principal the channel already establishes (session user, MCP token and person per specs 263/265, job identity); it never infers a person.

### Key Entities

- **Interaction**: one observed use of the model in one company, by one actor through one channel, with operation, kind, outcome, duration and correlation. Short-lived by design.
- **Correlation**: the shared cause that groups interactions and the business events they produced.

## Success Criteria *(mandatory)*

- **SC-001**: An owner can answer "what did this MCP client read and change in the last hour" from the Live tab without leaving it, in under a minute.
- **SC-002**: A new interaction appears in an open Live tab within 2 seconds at p95.
- **SC-003**: Recording adds at most 5 ms at p95 to an observed interaction.
- **SC-004**: No interaction record contains an argument or result value (verified by test over every catalog tool).
- **SC-005**: Every FR and DR has an acceptance scenario and executable proof.

## Assumptions and Dependencies

- Spec 265 supplies the person behind an MCP call where OAuth is used; token-only MCP calls name the token and issuer as spec 263 does.
- The web client can attach a correlation header to every API request of one user action.
- PostgreSQL remains the only store; live delivery uses PostgreSQL facilities, no new broker.
- `FlightRecorder.tsx` is evaluated for reuse in replay; reuse is not required.
- Model stages per operation come from the existing resource catalog (`resource_catalog.yaml` tables/match) where available.

## Clarifications

### Session 2026-09-24

- Q: How long are interactions kept? → A: 7 days (FR-011). Business events are unaffected.
- Q: Who may see the engine room? → A: Active company owners only (FR-013).
- Q: How does background work appear? → A: Only job runs that read or wrote company data; empty sweeps and idle polls are not recorded (FR-001).

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 1–3, US2 3–4 | service test per channel; business story |
| FR-002 | US1 1, 3 | unit test on interaction shape |
| FR-003 | US1 4 | catalog-wide test (SC-004) |
| FR-004 | US2 1–2 | business story MCP propose → web approve |
| FR-005 | US1 1, 5 | API stream test; browser test |
| FR-006 | US4 5 | routing test; browser test |
| FR-007 | US2 1 | browser test |
| FR-008 | US3 1–3 | unit test on stage mapping; browser test |
| FR-009 | US4 1–4 | browser test |
| FR-010 | Edge: self-observation | API test |
| FR-011 | US5 2 | job test |
| FR-012 | Edge: recording failure | service test with failing recorder |
| FR-013 | — | role test: member and foreign owner get not found |
| FR-014 | US1 6 | browser test |
| FR-015 | US5 1 | browser test |
| DR-001 | — | architecture test: no business import of interactions |
| DR-002 | US2 1 | business story |
| DR-003 | Edge: tenant boundary | isolation catalog |
| DR-004 | US1 1–3 | service tests |
