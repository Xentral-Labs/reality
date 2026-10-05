# Feature Specification: Operational cases and Shopify intervention boundaries

**Feature**: `371-operational-cases`
**Created**: 2026-10-05
**Status**: Product scope and the concrete five-table schema approved by the owner in chat on 2026-10-05 ("ja gebe ich frei"). First-slice implementation present; complete verification in progress. No production rollout or live connector claim.
**Language**: English
**Input**: Plan an operational layer that groups Shopify fulfillment, returns and refund work, detects obsolete work, and permits human takeover and reconciled handback.

## Context and Intent

### Problem

A customer can repair Shopify while an agent still holds work based on an older state. Existing business objects, proposals and events explain facts and decisions but do not provide a common responsibility boundary for stopping related work. Receiving every event does not by itself invalidate a plan or establish human takeover.

### Scope

- A vendor-neutral operational case layer with fulfillment and announced-return policies enabled in the first slice. Refund execution remains unavailable until an explicit authoritative intent is designed; refund evidence may reconcile supported work.
- Explicit event-to-case rules, replay-safe processing, action applicability and human takeover/handback.
- Existing supported Shopify evidence as the first acceptance slice; adapter capability gaps remain explicit.
- Read-only case explanation and controls through shared application services and Web/CLI/MCP. Built-in Chat remains read/propose only.

### Non-Goals

- Live Shopify authentication, webhooks, API retrieval, fulfillment or payment transport.
- New authority to approve business effects, send refunds or dispatch shipments.
- A generic workflow designer, AI-invented case boundaries or a replacement task queue.
- Persisting fulfillment, stock or financial balances on cases or documents.
- Full-company process coverage, automatic historical takeover, or rollout-wide pause controls.
- Guaranteeing cancellation of an already accepted external action or claiming external atomicity.

### Existing Contracts

- [Architecture](../../docs/ARCHITECTURE.md), [Data model](../../docs/DATA_MODEL.md), [Web](../../docs/WEB_SPEC.md).
- [Events](../../docs/features/operational_fields.md), [scheduled jobs](../../docs/features/scheduled-jobs.md).
- [Reviewed intake](../../docs/features/decision-gated-intake.md), [Shopify integration](../../docs/maintainer-guides/integrations/shopify.md).
- Specs 357, 360 and 361 retain interpretation/decision boundaries and finite agent mandates.

## User Scenarios & Testing

### User Story 1 - Group actual outstanding work (Priority: P1)

An operator sees one responsibility boundary for an accepted order's customer delivery work, and separate related boundaries for independent returns and refunds.

**Independent Test**: Accepted order with two lines produces one fulfillment case; replay does not duplicate it. Historical completed facts produce no newly active work.

**Acceptance Scenarios**:

1. **Given** an accepted order with outstanding customer delivery commitments, **When** its committed events are processed, **Then** one fulfillment case exists, anchored to that order and containing those commitments.
2. **Given** a partial fulfillment or quantity revision, **When** events arrive, **Then** the same case is reevaluated; no new case is created for each event or line.
3. **Given** an accepted return announcement, **When** it is processed, **Then** a separate return case is linked to the fulfillment context without reopening or transferring it.
4. **Given** an already successful external refund, **When** its evidence is accepted, **Then** it settles matching supported work or remains evidence; it does not create a new payout request.
5. **Given** a location/product creation or duplicate event, **When** processed, **Then** it creates no case solely due to arrival.
6. **Given** an explicit authorized refund intent, **When** its supported case policy is invoked, **Then** a refund case groups that intent and execution evidence; absent intent support the capability is unavailable.

### User Story 2 - Take over and repair (Priority: P1)

An active authorized member takes responsibility for a case while repairing Shopify. The agent cannot continue case-bound work and the operator sees outstanding execution uncertainty.

**Independent Test**: Takeover races a queued action and delayed event processing; no new action begins after takeover commits.

**Acceptance Scenarios**:

1. **Given** queued case-bound work, **When** an authorized member takes over, **Then** its ownership revision changes and subsequent agent execution is refused immediately.
2. **Given** an action already claimed or sent, **When** takeover occurs, **Then** that action remains visible with its actual outcome or unresolved state; takeover does not pretend to cancel it.
3. **Given** a manual Shopify repair subsequently accepted into Reality, **When** the human requests handback, **Then** the system reviews current facts, outstanding work and unresolved external actions; handback refuses unresolved uncertainty or known required source-coverage gaps.
4. **Given** a clean handback review, **When** the member confirms its exact current version, **Then** automation resumes only with still-valid or newly prepared work; older action generations remain invalid.
5. **Given** a return/refund case related to a taken-over fulfillment case, **When** takeover occurs, **Then** related cases are shown but not silently transferred; explicitly selected additional cases are separately taken over.

### User Story 3 - Never execute obsolete work (Priority: P1)

Before an agent executes case-bound work, the system checks current ownership and its actual business prerequisites.

**Independent Test**: A revision committed before event-worker catch-up invalidates a previously prepared action at execution.

**Acceptance Scenarios**:

1. **Given** a proposed action and subsequently changed order/reservation/fulfillment facts, **When** execution is attempted, **Then** current checks refuse changed meaning even if the case event consumer has not caught up.
2. **Given** another actor already completed the goal, **When** work is reevaluated, **Then** the pending action is explained as no longer needed without fabricating an execution receipt.
3. **Given** an action with effects in several cases, **When** one case is human-owned, **Then** automated combined execution refuses; independent work is split only through a new exact proposal.
4. **Given** previously completed work and a factual correction restoring outstanding work, **When** processed, **Then** the same anchored case is reactivated without changing history or reusing old action validity.

### User Story 4 - Find and control cases from existing interfaces (Priority: P1)

An operator or external agent discovers the same case from an existing order, return or supported refund-intent view without needing to guess its identity.

**Independent Test**: Existing order read and proposal review expose matching case IDs; Web takeover and MCP reads report the same actual responsibility.

**Acceptance Scenarios**:

1. **Given** an adopted order, **When** it is read through existing Web/API/MCP paths, **Then** associated case IDs and discoverable detail links are returned additively; a multi-case action returns every direct case.
2. **Given** historical or unadopted data, **When** read, **Then** case associations are empty and reads create no case.
3. **Given** an operator selecting manual takeover from the object screen, **When** confirmed, **Then** the real shared control transition stops new automated starts; merely adding a display label has no control effect.
4. **Given** new user documentation, **When** following its examples, **Then** the reader can distinguish new-goal creation from updates and understand that taking back responsibility cannot undo external execution.

### Edge Cases

Mixed supported and unsupported source versions; orders without shipping work; late stock/fulfillment corrections; partial returns; multiple independent refunds; retries; concurrent takeover/claim; actor revocation; missing adapter evidence; manual operations on a taken-over case; events generated by this layer; tenant isolation; consumer upgrade/rebuild.

## Requirements

### Functional Requirements

- **FR-001**: Create or match cases only through a versioned closed policy for outstanding goals; classify inputs as create, update, settle or no case. Replay MUST preserve case identity.
- **FR-002**: Fulfillment MUST group accepted customer-delivery commitments by their order. Return MUST use its accepted return announcement. Refund MUST use an explicit authorized intent, never a successful-refund notification as intent.
- **FR-003**: Membership MUST distinguish owned work from related/dependent work. Takeover MUST NOT traverse the whole business graph.
- **FR-004**: Authorized member takeover MUST immediately revoke further automated starts for selected cases through a revision check, with actor/reason attribution and replay-safe control requests.
- **FR-005**: Claimed/sent/uncertain actions MUST retain their real execution state and remain visible until reconciled; human takeover MUST NOT assert external cancellation.
- **FR-006**: Handback MUST require an exact current review, adequate evidence for the goal and no unresolved execution uncertainty; it MUST recheck authority and facts transactionally.
- **FR-007**: Governed agent proposals MUST declare all directly affected cases server-side and bind their control revisions and relevant business-state prerequisites. Execution/claim MUST recheck current authority, ownership and prerequisites independently of consumer lag.
- **FR-008**: Current facts MUST determine outstanding, blocked, completed or abandoned goal observations. Corrections MAY reactivate the same case, but MUST NOT revive stale action approvals.
- **FR-009**: Event processing MUST commit case changes and its checkpoint atomically, recover from restart without duplication, and expose lag/failure. It MUST NOT accept business evidence or perform external effects.
- **FR-010**: Case explanation MUST show goal, ownership, current work, obsolescence reasons, related cases, original sources and unsettled executions. Reads MUST NOT create cases or execute work.
- **FR-011**: Adoption MUST be opt-in with a retained capture boundary and explicit selection of existing outstanding objects. Completed history MUST NOT become active work; unbound automation in enabled scope MUST refuse until classified.
- **FR-012**: Unsupported refund intent/execution and missing Shopify fulfillment transport MUST be reported as unavailable. Accepted evidence updates cases; newer unresolved relevant sources MUST block dependent automation and handback rather than imply full synchronization.

- **FR-013**: Existing supported object reads, proposal reviews and execution receipts MUST expose associated case IDs additively, including multiple cases where applicable. Historical/unadopted objects MUST return explicit empty associations without fabricated cases. External tools MUST support discovering cases from an existing business object and reading by case ID. Caller-supplied case IDs MUST be validated against server-resolved membership and never grant authority.
- **FR-014**: Web MUST provide a case list/detail and object-context entry points with copyable case ID, responsibility, related work and unsettled effects; controls MUST include manual takeover (which stops new automated starts), reconciliation review and exact handback. A label alone MUST NOT stop automation. UI MUST distinguish automation stopped from external cancellation confirmed.
- **FR-015**: Maintainer and user documentation MUST explain create/update/no-case rules, owned versus related work, external correlation versus case identity, manual takeover and handback, and capability limits. Generated tool references MUST describe actual input/output contracts; existing API/tool consumers retain backward compatibility.

- **FR-016**: Before enabling adopted scope, every reachable goal-creation, proposal-preparation, business-execution and claim entrypoint for the selected case families MUST have an explicit reviewed disposition and executable boundary proof. Canonical accepted goal creation MUST ensure/match its case atomically; enabled automated execution MUST NOT bypass server-side case guards through a lower-level path or omitted case ID. Source staging MUST NOT create accepted goals and authorized human repairs retain existing authority.

### Domain and Traceability Requirements

- **DR-001**: Preserve Source → Evidence → Reality. Case controls are coordination authority only; quantities, money and physical completion remain derived from authoritative Reality records.
- **DR-002**: Use tenant-scoped opaque identities and shortest existing links. Preserve caller-supplied external correlation IDs unchanged as foreign-system tracing references; never replace them with case or action IDs or use them as case identity. Do not persist derived business balances/status on cases.
- **DR-003**: Every read, link and mutation MUST preserve tenant isolation and existing action-specific decision authority. Controls MUST use shared services; a case or agent mandate never grants new business authority.

### Key Entities

- **OperationalCase**: Stable goal identity, explicit responsibility, control revision and policy version.
- **Case membership**: Typed same-company link to an authoritative goal/work object; not a copy of its business facts.
- **Case action binding**: Exact case control generations against which an existing proposal was prepared.
- **Case consumer checkpoint**: Durable incorporated-event position, distinct from business truth.

## Success Criteria

- **SC-001**: Replay and worker restart produce exactly one case per declared goal anchor and no duplicate business effect.
- **SC-002**: After committed takeover, every new governed automated start is refused, including when the event consumer is delayed.
- **SC-003**: Every FR/DR has a test task and an implementation task; all three initial policy families have supported or explicitly unavailable outcomes.
- **SC-004**: The operator can explain what remains open, what was superseded and what is externally unresolved from case reads alone.

## Assumptions and Dependencies

- The user authorized the recommended first implementation slice on 2026-10-05. Concrete schema/domain decisions in contracts/first-slice.md were subsequently approved by the owner ("ja gebe ich frei"); this is implementation authorization, not release approval.
- Normal intake reviews and existing mandate scope remain mandatory. Raw source arrival can invalidate freshness without accepting its meaning.
- Fulfillment ends at authoritative fulfillment of delivery commitments, not assumed carrier delivery or payment settlement. Carrier claims, receivables and invoicing remain related independent work.
- Partial shipments share the fulfillment case. Each accepted return announcement is its own case; return fragments are not heuristically grouped.
- Multiple refund intents are separate cases. Return/refund relationships do not imply joint ownership.
- Live Shopify adapter completion is a separate prerequisite for live end-to-end assertions.
- Static inventory confirms customer delivery commitments without an order (including exchange replacements) and return receipts without announcements. These remain supported human/evidence paths but are unavailable for initial adopted automatic case execution until a separate reviewed root policy exists. No fabricated order/announcement may be used to hide coverage gaps.
- Owner clarification: correlation_id is an optional reference supplied by an external system to trace the originating processing context. It is not a verified source identity or business authority. A case may span multiple external correlation IDs; one external correlation may touch multiple cases. Internal case/action/causation links remain separate.
- Initial related links express association; concrete dependency impact is evaluated by explicit case policies. A generic directed dependency graph and recursive propagation are out of scope.

## Open Questions

No unresolved product ambiguity in this draft. The initial choices above are explicit proposed defaults, subject to owner review before implementation.

## Requirement Traceability

See [tasks.md](tasks.md) for complete requirement-to-test-to-implementation mapping and [quickstart.md](quickstart.md) for acceptance stories.
