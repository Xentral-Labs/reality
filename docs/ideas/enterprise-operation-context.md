# Idea: End-to-end operation context for an enterprise agent

**Status:** Brainstorming — not approved, not an implementation specification

## Problem

Reality may become one component inside a larger enterprise agent. One user intent can
then cross several systems: the enterprise agent, Reality commands, external services,
business events, projections, and possibly asynchronous workers. Each system can have
useful logs while the complete execution remains difficult to reconstruct.

The caller therefore needs to supply an opaque operation identifier that Reality
preserves across every relevant boundary and returns in its result. An operator should
be able to start with that identifier in any participating system and discover which
systems, commands, events, and outcomes contributed to the final answer or action.

This is technical execution provenance. It is not business identity and does not
replace Source → Evidence → Reality traceability.

## Proposed concept

Introduce a small, immutable **OperationContext** envelope on application calls:

```text
enterprise-agent operation
        |
        | OperationContext
        v
Reality command/tool call
        |
        +---- structured application log
        +---- business event(s)
        +---- asynchronous work
        +---- projection refresh
        |
        v
result + same operation reference
```

Reality accepts the context at its application boundary and passes it through shared
services. Web, CLI, chat, MCP, and API must call the same application services and
must not invent separate propagation rules.

The smallest useful context is:

- `operation_id`: opaque identifier assigned by the initiating system;
- `operation_source`: stable namespace for the issuer, such as
  `enterprise-agent-prod`;
- `correlation_id`: identifier connecting related work inside one wider business or
  conversational process, when different from the operation;
- `causation_id`: identifier of the immediate call or event that caused this step;
- `invocation_id`: Reality-issued identity of one concrete execution step inside the
  operation;
- `parent_invocation_id`: invocation that directly requested this child step;
- `attempt_id`: identity of one execution attempt, changed on retry;
- optional standards-based distributed tracing metadata, such as W3C `traceparent`,
  for infrastructure observability.

The durable reference is the tenant-scoped pair `(operation_source, operation_id)`.
An ID supplied without a trusted issuer namespace is ambiguous across systems.

## Where callers may provide it

Operation context is an optional technical envelope on **every shared application
entry point**, not another business parameter copied into every command definition.
Adapters translate their transport into the same typed envelope:

| Entry point | How context may arrive | Behavior when absent |
|---|---|---|
| HTTP API or webhook | Explicit headers or a versioned request envelope | Generate a Reality context |
| MCP or enterprise-agent tool call | Tool-call metadata or a reserved context envelope | Generate a Reality context |
| Chat action | Inherit the current agent turn or confirmed action context | Generate a Reality context |
| Web application | Inherit the server request context | Generate a Reality context |
| CLI command | Optional global CLI options or environment supplied by an orchestrator | Generate a Reality context |
| Connector/import entry | Connector delivery metadata, separate from the lossless source payload | Generate a Reality context |
| Scheduled/internal operation | Context issued by a reserved Reality scheduler or worker namespace | Always generate a context |
| Retry or replay | Reuse the logical operation as defined below and add a new attempt | Never silently invent unrelated ancestry |

Both read-only and mutating commands accept the envelope. Read-only calls may need an
end-to-end trace even though they emit no Business Event. Mutations still follow the
normal confirmation, authorization, transaction, and idempotency rules.

The context should be passed beside the command payload, not embedded inside
`source_payload`, arbitrary command `context`, or domain fields. This prevents an
adapter concern from polluting lossless evidence and avoids adding `operation_id` to
every catalogued business parameter list.

After the boundary has accepted or generated it, a valid OperationContext is
**mandatory internally** for the lifetime of that application invocation. Internal
services should not repeatedly accept `None` and make different fallback decisions.

## Identity boundaries

Keep these concepts deliberately separate:

| Concept | Answers | Must not be used as |
|---|---|---|
| Internal opaque record ID | Which Reality record is this? | Human number or external identity |
| Source `external_id` | Which object did a named source system send? | Cross-system execution trace |
| Operation ID | Which end-to-end invocation participated in this result? | Domain identity or authorization |
| Correlation ID | Which wider process groups several operations? | Immediate causal parent |
| Causation ID | Which call or event directly caused this step? | Whole-process grouping |
| Idempotency key | May this requested mutation execute more than once? | General logging or correlation ID |
| Trace/span ID | Where did infrastructure time and calls flow? | Durable business audit identity |

An operation ID may sometimes equal a trace ID or idempotency key at an integration
boundary, but Reality must not assume that equivalence. The caller must state each
semantic explicitly.

## Propagation rules

1. Accept operation context only at authenticated application boundaries.
2. Validate and normalize it once, then pass the typed context through service calls.
3. Generate a Reality operation ID when the caller supplies none, and return it.
4. Preserve a supplied operation ID exactly as an opaque value; never parse business
   meaning from it.
5. Create a new causation reference for each child command or emitted event while
   retaining the original operation and correlation references.
6. Copy the context into asynchronous job messages so execution can continue after
   the initiating request ends.
7. Include the context in structured logs and error responses that are safe to expose.
8. Persist references at durable audit boundaries, not redundantly on every business
   table.
9. Projections may expose operation references for search and explanation, but they
   derive them from authoritative records and never become their source of truth.
10. Forward context to an external system only through an explicit integration
    contract; do not assume every system accepts the same header or field names.

### Required propagation and recording matrix

| Boundary or artifact | Required handling | Authoritative storage? |
|---|---|---|
| Adapter request | Read optional context, authenticate issuer, or generate it | No |
| Application command/query | Carry a non-optional typed context beside business input | Command audit only if one exists |
| Nested application action | Retain operation/correlation; create a child invocation and causation link | At its durable boundary |
| Database transaction | Make business change and its durable event/participation reference atomic | Yes, where recorded |
| Business Event/outbox | Persist operation source and ID plus correct correlation/causation references | Yes |
| ImportJob or other async job | Persist context when enqueued and restore it before worker execution | Yes |
| Retry attempt | Retain logical ancestry; add a distinct `attempt_id` and attempt number | Job/execution record or logs |
| Fan-out child work | Retain operation; assign distinct child invocation/causation references | Child events/jobs |
| Fan-in/final result | Reference every contributing child that is known, not only the last finisher | Participation graph |
| Projection builder | Read context from source events; never manufacture or overwrite it | No |
| Projection row | Expose operation lookup only when semantically unambiguous | Derived only |
| Structured log/span | Include tenant-safe operation, invocation, correlation, causation, and attempt references | No; retention is operational |
| External service call | Map context through that integration's explicit contract | External system owns its record |
| Success response | Return the effective operation reference | No |
| Safe error response | Return the effective operation reference once one exists | No |
| Operation trace query | Resolve tenant-scoped participation and authoritative record links | Read model over authoritative records |

For a transaction that changes business state and emits a Business Event, the
operation reference must be committed atomically with the event. A business mutation
must not succeed while leaving only a best-effort log line as its trace.

Projection rows often combine many events and therefore many operations. They must
not carry a misleading single `operation_id`. Prefer resolving their
`source_event_sequence` or explicit contributing event references back to the
authoritative Business Events. A projection may denormalize operation references only
when its contract defines whether the value means creator, latest modifier, or full
set of contributors.

### Invocation, retry, and batch semantics

The operation identifies the end-to-end intent, while an **invocation ID** identifies
one concrete execution step inside it. An **attempt ID** distinguishes retries of that
step. This prevents duplicate retries from looking like unrelated operations or like
one uninterrupted execution.

- A transport retry of the same logical request retains operation and invocation
  identity and receives a new attempt identity.
- A user intentionally starting the action again normally creates a new operation,
  even if the business inputs happen to match.
- A parent operation that invokes several Reality commands gives every child its own
  invocation and causation reference.
- A batch has a parent operation plus child invocations per independently observable
  item. Failed and successful items must remain distinguishable.
- A replay used to rebuild a projection retains the original events' operation
  references but the rebuild execution itself has a separate operational context.
- Idempotency remains an explicit command contract. Reusing an operation ID alone
  must never suppress a mutation.

## Durable operation participation

A log-only solution is insufficient because logs expire and asynchronous work may be
separated in time. Investigate a small append-only **OperationParticipation** record
for durable boundaries. One operation can have zero to many participation records.

A participation could record:

- tenant, operation source, and operation ID;
- Reality component and action name;
- command execution, business event, job, or other durable record reference;
- parent/causation reference;
- start and completion timestamps plus outcome category;
- safe error classification, without copying secrets or full payloads.

Participation outcome should distinguish at least `running`, `succeeded`, `failed`,
`partially_succeeded`, `cancelled`, `timed_out`, and `unknown`. A missing completion
record must not be rendered as success. Start and completion updates need a defined
crash-recovery rule so abandoned work can eventually become `unknown` or `timed_out`.

This produces an explainable participation graph:

```text
operation
  +-- enterprise agent plan step
  +-- Reality command
  |     +-- business event
  |     +-- projection refresh
  +-- external system call
  +-- final enterprise-agent response
```

Reality owns only its own participation records. The enterprise agent or observability
platform assembles the cross-system view from the shared operation reference. Reality
must not pretend to know that an external step succeeded unless it received reliable
evidence of that step.

## Relationship to existing Business Events

Business Events already carry `correlation_id` and `causation_id`. A future
specification should decide whether their current fields can represent the operation
context precisely or require an explicit operation source and operation ID.

Do not rewrite existing semantics merely to reuse a column. In particular:

- business-event correlation remains useful for a domain process;
- an enterprise-agent operation may contain several domain correlations;
- one domain correlation may continue across several agent operations;
- SourceRecord identity remains the identity of imported evidence, not the identity
  of the agent execution that requested or interpreted it.

## Security and tenancy

- Every persisted operation reference is tenant-scoped and every query enforces the
  tenant scope.
- Caller-supplied identifiers are untrusted input: limit length and character set for
  safe transport and indexing, but retain their opaque semantics.
- An operation ID grants no access. Looking up a trace requires normal authorization.
- Do not put prompts, personal data, credentials, access tokens, or business payloads
  into IDs, headers, metric labels, or log context.
- Do not use unconstrained operation IDs as high-cardinality metric labels. Logs and
  traces may carry them; aggregate metrics should use bounded dimensions.
- Trust boundaries must prevent one caller from impersonating a reserved
  `operation_source` belonging to another integration.
- Actor/user identity comes from authentication and confirmation records, not from
  untrusted operation metadata. A trace may link to the authenticated actor but may
  not use operation context to assert one.
- Arbitrary distributed-tracing baggage is not persisted or forwarded by default.
  Each propagated field needs an allowlisted contract.
- Mutating agent actions still require confirmation. Trace context neither represents
  consent nor bypasses application rules.

## Completeness and failure rules

- Context propagation is part of the integration contract. If a boundary that must
  preserve it cannot do so, record the gap explicitly or fail the call according to
  that boundary's criticality; never pretend the trace is complete.
- The trace view differentiates **observed participation** from inferred
  participation. Only durable local records or acknowledged external references may
  be presented as confirmed participants.
- Partial failure, timeout, cancellation, compensation, and retry are first-class
  outcomes. A final answer should be able to explain both successful contributors and
  failed attempted contributors.
- Timestamps help navigation but do not establish causality across systems. Explicit
  parent, causation, and acknowledged-call references do.
- Context contracts require a schema version so fields can evolve across independently
  deployed components.
- Retention of durable participation, Business Events, application audit, technical
  logs, and infrastructure traces may differ. The UI must show when only part of the
  technical history remains available.
- The command catalog should declare OperationContext once as a global application
  envelope and state which exceptional entry points cannot carry it. It should not
  duplicate the same optional parameters on every command.
- A final enterprise-agent response can cite Reality's returned operation reference.
  Reality can list its known contributors; only the orchestrator can make a supported
  claim about the complete cross-system execution.

## Smallest useful slice

1. Define a typed OperationContext accepted by one shared application command path.
2. Accept a caller-supplied `(operation_source, operation_id)` or generate a Reality
   operation reference when absent.
3. Add the reference to structured application logs and emitted Business Events.
4. Preserve it through one asynchronous boundary.
5. Return it from success and safe error responses.
6. Provide a tenant-scoped read service that lists Reality records participating in
   the operation.
7. Prove with a business-story test that one enterprise-agent request can be traced
   through command, event, projection, and final response.
8. Prove that the same operation ID in two tenants or issuer namespaces never joins.

Out of scope for the first slice: building a complete observability platform,
retaining full prompts or responses, cross-company trace sharing, treating logs as a
business ledger, or adding operation columns to every domain entity.

## Open questions

1. Which system is authoritative for the first operation ID: the enterprise agent,
   an API gateway, or Reality when no upstream context exists?
2. Is the enterprise agent expected to use W3C Trace Context already?
3. Which Reality boundaries require durable participation records rather than logs
   alone?
4. How long must operation participation remain searchable compared with technical
   logs and business audit records?
5. Must an operator see only Reality participation, or does the first product slice
   need links into the external observability system?
6. Can one operation contain several confirmed mutations, and if so how are individual
   confirmation and idempotency keys represented?
7. Which issuer namespaces are trusted and how are they bound to integrations?
8. Which propagation failures make an operation fail, and which may complete with an
   explicitly incomplete trace?
9. Does the existing application command audit provide the durable command boundary,
   or is OperationParticipation required from the first slice?

## Promotion trigger

Move this idea into a numbered Spec Kit feature after selecting the authoritative
issuer, the first synchronous and asynchronous propagation paths, and the minimum
durable participation boundary. The specification should describe observable trace
workflows; the plan should decide storage and transport details without making the
operation ID a new universal business identity.
