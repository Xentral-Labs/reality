# Feature Specification: Agent Email Handoffs and Send Decisions

**Feature Branch**: `351-agent-email-handoffs`

**Created**: 2026-10-03
**Status**: Implemented and verified (PR #332, 2026-10-03)
**Language**: English
**Input**: Store email content and attachments handed over by external agents; review outgoing email through Decisions; retain the actual send outcome and make this workflow explicit for every agent using Reality.

## Context and Intent

### Problem

External agents handle everyday correspondence, but a summary in chat does not preserve
the message, attachments, decision basis or actual outgoing communication. Each agent
also needs the same discoverable contract for submitting evidence, proposing a message,
obtaining approval and reporting execution.

The conversation called the product “Relative”; this specification uses the repository's
canonical name, Reality.

### Scope

- Lossless inbound and outbound email handoff, including attachment contents.
- Version-specific outgoing proposals in the existing Decisions workflow.
- External execution authorization and source-backed outcome reporting.
- Shared agent guidance, tool contracts and readable evidence/decision navigation.

### Non-Goals

- Hosting mailboxes, polling inboxes, receiving mail directly or sending through SMTP/providers.
- Autonomous approval, new confirmation rights or a separate email approval queue.
- Automatically treating statements in an email as verified business truth.
- Email campaigns, mailbox synchronization, provider-specific connector implementation,
  attachment OCR or document generation.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md)
- [Data model](../../docs/DATA_MODEL.md)
- [Source ingestion](../../docs/features/source_ingestion.md)
- [Proposal decision policy](../../docs/features/proposal-decision-policy.md)
- [Spec 323: proposal decision policy](../323-proposal-decision-policy/spec.md)
- [Spec 328: chat-scoped proposals](../328-chat-scoped-proposals/spec.md)
- [Spec 350: executing-system boundary](../350-documents-by-executing-system/spec.md)

## User Scenarios & Testing

### User Story 1 - Retain incoming correspondence (Priority: P1)

An agent receives an email and hands its complete content and attachments to Reality.
The user can open the original evidence and understand its origin independently of
the agent's summary or continued access to the mailbox.

**Independent Test**: Submit a multipart message with two attachments; retrieve the
message and files, compare their contents, and replay the handoff.

**Acceptance Scenarios**:

1. **Given** a received message, **When** the agent submits it, **Then** Reality
   returns stable source IDs and preserves supplied plain text, HTML, headers,
   envelope metadata and original message bytes where available.
2. **Given** attachments, including an inline image, **When** handoff completes,
   **Then** each file is independently retrievable as evidence linked to its message,
   preserving filename, media type, bytes, checksum and inline/content-ID metadata.
3. **Given** the same origin identity and contents, **When** submission is retried,
   **Then** existing identities are returned without duplicate evidence; changed
   contents create an immutable version rather than overwrite the original.
4. **Given** missing original bytes or an unavailable attachment, **When** the
   message is submitted, **Then** the exact supplied evidence is preserved and its
   missing components are explicit; handoff is not described as complete.

### User Story 2 - Approve an exact outgoing message (Priority: P1)

An agent proposes a reply. The user reviews exactly what will leave the company and
the sources supporting it in Decisions before authorizing external execution.

**Independent Test**: Propose, review and approve one message; mutate its recipients,
body or attachment bytes and verify the changed version has no send authorization.

**Acceptance Scenarios**:

1. **Given** an outgoing draft, **When** submitted, **Then** a normal Change Proposal
   exposes sender/account, To/CC/BCC, subject, complete body, attachment snapshots,
   reply references, rationale and supporting sources before confirmation.
2. **Given** a pending or rejected proposal, **When** execution authorization is
   requested, **Then** it is refused. Read/propose access alone cannot approve.
3. **Given** approval for one version, **When** recipients, sender, subject, body,
   attachments or reply metadata change, **Then** a new proposal and approval are
   required; the previous decision remains attributable and unchanged.
4. **Given** approval, **When** the executing agent obtains the send instruction,
   **Then** it receives the approved immutable payload and its fingerprint, not a
   reconstructed draft. Proposal execution authorizes dispatch; it does not assert
   that an email was sent.
5. **Given** built-in Chat or an external client, **When** a decision is requested,
   **Then** existing channel/authority restrictions and truthful attribution apply;
   a permissioned API call is not represented as independently proven human approval.

### User Story 3 - Retain what actually happened (Priority: P1)

After external execution, the agent reports its result. The user can trace the actual
message back through the approval to the evidence that informed it.

**Independent Test**: Report success, definitive failure, timeout and an actual-message
mismatch; replay each report and inspect the evidence and send status.

**Acceptance Scenarios**:

1. **Given** an authorized send, **When** the provider accepts it and the agent
   reports evidence, **Then** Reality retains the actual outgoing message, provider
   receipt/identity and reported time as sources and a cataloged source-backed
   observation of provider acceptance. It does not claim recipient delivery.
2. **Given** definitive failure or uncertain execution, **When** reported, **Then**
   the outcome is visible and no successful-send observation is created. Uncertainty
   requires reconciliation before any further dispatch of the same instruction.
3. **Given** a result replay or competing execution claims, **When** processed,
   **Then** one instruction cannot produce duplicate authorization or duplicate
   outcome records; concurrent claim and retry behavior is explicit.
4. **Given** an actual message differing from the approval, **When** reported,
   **Then** Reality preserves the actual evidence, flags the deviation and never
   labels it an approved matching send. An unapproved externally sent message may
   also be archived as historical evidence without retroactive approval.
5. **Given** any retained outgoing message, **When** the user follows its links,
   **Then** the execution outcome, proposal, decision and supporting source versions
   are reachable; unavailable or unresolved links are stated rather than inferred.

### User Story 4 - Every agent discovers the same contract (Priority: P1)

An agent connecting to Reality can discover how to hand over mail and which operation
is permitted next without depending on instructions from a particular chat.

**Independent Test**: Use the documented examples through two external client adapters
and verify identical service outcomes and authorization requirements.

**Acceptance Scenarios**:

1. **Given** a connected agent, **When** it reads capability guidance, **Then** it
   finds schemas, required fields, attachment transfer instructions, size limits,
   stable IDs, decision requirements, retry rules and complete examples.
2. **Given** any workflow response, **When** the agent reads it, **Then** it can
   distinguish evidence stored, decision pending/rejected, dispatch authorized,
   execution uncertain/failed and provider accepted, and identify the next allowed
   operation without guessing from prose.
3. **Given** Web, CLI, MCP or Chat, **When** the same operation is used, **Then**
   shared application services enforce the same tenant, version and decision rules.

### Edge Cases

- Missing Message-ID; duplicate Message-IDs across accounts; forwarded messages;
  separate provider thread identities; thread references arriving out of order.
- Empty bodies, multipart alternatives, Unicode filenames, large files, inline parts,
  interrupted uploads and expiring external download links.
- Cross-tenant message, file, proposal or execution references; removed membership;
  revoked executor access; changed proposal state during dispatch claim.
- Provider acceptance followed by crash before result handoff; conflicting receipts;
  later delivery/bounce evidence; provider-added headers versus changed approved content.
- Untrusted message text and HTML: reading evidence must not execute HTML or treat
  instructions inside a message or attachment as agent authorization.

## Requirements

### Functional Requirements

- **FR-001**: Email handoff MUST preserve the complete supplied external payload,
  direction, origin/account identity, external message/thread identifiers, sender,
  recipients and supplied business timestamps; capture time MUST remain distinct.
- **FR-002**: Attachment handoff MUST retain durable bytes and provenance, support
  interrupted transfer, verify integrity and report completeness. Remote URLs alone
  MUST NOT count as archived attachment contents. Limits MUST be discoverable.
- **FR-003**: Capture MUST be tenant/origin scoped and idempotent; changed payloads
  MUST create immutable versions. Missing external IDs MUST use stable caller retry
  identities without inventing provider identity or merging by subject alone.
- **FR-004**: Outgoing proposals MUST bind the complete dispatch payload and exact
  attachment contents to an immutable version/fingerprint and supporting source IDs.
- **FR-005**: Review MUST expose the full outgoing payload, including BCC and sender,
  attachments and rationale through existing Decisions; a summary alone is insufficient.
- **FR-006**: Approval MUST use existing proposal policy, current authority checks and
  exact-version confirmation. Changed dispatch payloads MUST require new approval.
- **FR-007**: External dispatch instructions MUST be obtainable only for approved
  proposals by permitted executors, with atomic claim/replay protection and a stable
  execution identity. A compliant executor MUST send only the approved snapshot.
- **FR-008**: Result handoff MUST preserve actual message/receipt evidence, distinguish
  provider acceptance, definitive failure and uncertainty, and detect deviations from
  the authorized payload. Provider-added transport metadata alone is not a deviation.
- **FR-009**: Unknown outcomes MUST require reconciliation before redispatch. Receipt
  replays MUST be idempotent; conflicting results MUST remain visible as evidence.
- **FR-010**: Retained messages, files, supporting sources, decisions and execution
  outcomes MUST be navigable in both read tools and the existing user surfaces.
- **FR-011**: Every agent MUST receive a canonical discoverable workflow contract and
  machine-readable states, IDs, permitted next steps and stable error codes.
- **FR-012**: All adapters MUST use shared services, tenant-scoped authorization and
  safe evidence rendering; none may introduce implicit approval or direct database writes.

### Domain and Traceability Requirements

- **DR-001**: Messages, attachments and provider receipts are immutable Sources.
  Agent summaries are attributed interpretations, never replacements for originals.
- **DR-002**: Use existing SourceRecord/SourceStream, Change Proposal and decision
  attribution concepts. An attachment is separately addressable source evidence linked
  to its originating message. Only operationally required identity, version, integrity,
  authorization and retrieval relationships justify typed additions in the plan.
- **DR-003**: Email does not automatically create a business Document or assert the
  truth of its statements. Evidence/Reality interpretation follows existing rules
  where applicable. A cataloged send observation is supported by reported execution
  evidence and describes its actual evidential strength.
- **DR-004**: Approval and external execution are separate events. An executed
  authorization proposal MUST NOT imply provider acceptance or delivery. Dispatch
  lifecycle MUST NOT be stored as operational status on a business Document.
- **DR-005**: Use shortest true tenant-scoped provenance links and opaque internal IDs;
  do not duplicate evidence links or infer historical approvals from timestamps.

### Key Entities and Logical Operation Contract

These are behavioral contracts, not committed table designs or final tool names.
Planning must map them to existing catalogs and services before adding new APIs.

| Operation | Required input | Result |
|---|---|---|
| Capture email evidence | Origin, retry identity, direction, supplied message payload, attachment manifest/content | Source/version IDs, file IDs, completeness and unresolved references |
| Propose email dispatch | Sender/account, recipients, subject/body, exact attachments, reply references, supporting sources, rationale | Proposal ID, payload fingerprint, review link, decision requirements |
| Read email decision | Proposal ID | Current decision, approved fingerprint, allowed next operation |
| Claim authorized dispatch | Proposal ID, approved fingerprint, executor retry identity | Immutable dispatch instruction, execution ID, claim/reconciliation status |
| Report/reconcile dispatch | Execution ID, observed outcome/time, actual message and provider evidence | Evidence IDs, observed outcome, deviations, allowed next operation |
| Read email history | Source, proposal or execution ID | Same-tenant evidence and decision chain |

Logical entities: email SourceRecord; attachment SourceRecord and durable file content;
existing Change Proposal and decision attribution; authorized external dispatch identity;
execution evidence and optional cataloged Fact. Persistent schema remains a planning decision.

## Success Criteria

- **SC-001**: Incoming and outgoing fixture messages and attachments are retrievable
  with zero content loss relative to supplied payloads; incomplete handoffs are explicit.
- **SC-002**: No pending, rejected, changed-version or unauthorized test case obtains
  a dispatch instruction. A review shows every approved dispatch field.
- **SC-003**: Success, failure, uncertainty, deviation, concurrent claims and replay
  proofs produce truthful outcomes without duplicate dispatch authorization.
- **SC-004**: Two external clients can follow the canonical contract without additional
  chat-specific instructions; every FR/DR has planned executable evidence.
- **SC-005**: A user can navigate from actual outgoing evidence to its decision and
  supporting incoming evidence, including original attachment content.

## Assumptions and Dependencies

- External agents/providers own reception and dispatch. Reality enforces its own
  authorization boundary, but cannot prevent an external agent with independent mail
  credentials from bypassing it. Such bypass is outside the compliant executor contract;
  it must never be presented as an approved Reality send.
- Exactly-once external delivery cannot be guaranteed by a database claim alone.
  Executors must use provider idempotency where available and reconcile unknown outcomes.
- Existing confirmation policy remains authoritative; this feature grants no new
  autonomous decision authority. Source intake follows existing mutation/access rules.
- Durable attachment storage and external dispatch claims require architecture review.
  Planning must choose bounded upload/download and retention/deletion behavior consistent
  with company lifecycle, and define claim recovery before implementation.
- Provider acceptance is the default successful execution observation. Recipient
  delivery requires separate evidence; no delivery guarantee is inferred.
- Documentation impact on implementation: source ingestion, proposal decision policy,
  data model, agent capability guidance and generated Tool Usage catalogs. Web additions
  follow existing localization and review conventions.
- This deliverable is a draft specification only; it does not implement mail handling
  or mark the proposed capabilities as available.

## Open Questions

No unresolved product-scope questions. Final schema, catalog names, limits, storage
mechanism and execution-claim recovery are technical planning decisions constrained
by these requirements.

## Requirement Traceability

| Requirement | Scenarios | Planned test/evidence |
|---|---|---|
| FR-001–FR-003, DR-001–DR-002 | US1.1–4; edge cases | Lossless multipart/file round trip, partial upload, version and retry service tests |
| FR-004–FR-006 | US2.1–3, US2.5 | Exact-payload review, mutation, rejection and authority matrix |
| FR-007, DR-004 | US2.4; US3.3 | Concurrent claim, replay, executor access and authorization-versus-send tests |
| FR-008–FR-009, DR-003 | US3.1–4 | Acceptance, failure, uncertainty, reconciliation and mismatch story tests |
| FR-010, DR-005 | US3.5 | Read-tool and browser provenance navigation proof |
| FR-011 | US4.1–2 | Discoverability, schema and complete external-client examples |
| FR-012 | US2.5; US4.3; edge cases | Adapter parity, tenant isolation and safe evidence-rendering proofs |

## Mandatory business context extension (owner approved 2026-10-04)

The owner requires every newly captured email and every outgoing proposal to have
explicit business-object context. Business partners include suppliers, customers,
carriers and other partner roles; this is not a customer/order-only feature.

- **FR-013**: Require one or more distinct existing same-company business references
  (`kind`, opaque `id`) for email capture and dispatch proposals. Support parties of
  every role, items, locations, documents/lines, commitments, reservations, movements,
  ledger entries (payments), lots, shipments/packages, facts and business events.
  Resolve and validate references before any evidence write. Never infer identity
  from an email address, a name or a human document number. Agents must include all
  relevant known objects; unresolved context blocks capture/proposal until resolved.
- **FR-014**: Preserve context in immutable source versions and the approved proposal;
  retain indexed source-to-object memberships. Actual outgoing messages inherit the
  approved context from the proposal, never from executor-supplied overrides. Context
  changes require a new proposal; source correction creates a new source version.
- **FR-015**: Extend `email_history` with a mutually exclusive business-reference
  selector and bounded pagination. Return only explicitly linked emails and related
  decisions, with navigable source IDs, original content/file routes and context.
  Return counts/empty state; never silently drop older pages or cross companies.
  Existing source/proposal/execution selectors remain available. Context is not an
  inferred Fact and does not change stock, fulfilment, money or business authority.
- **FR-016**: Show linked correspondence on supported business-object Inspector detail
  views and show named business references on email reviews/evidence. Read after
  returning to an object or completing a decision; preserve original text safely.
  Agents discover required context and object queries through the same running
  workflow/schema. No automatic inclusion in unrelated read responses is promised.
- **DR-006**: One tenant-scoped `email_business_link` membership stores source ID,
  business kind and business ID with a composite source FK, unique membership and
  object-lookup index. The shared service validates polymorphic targets against a
  closed model map under the tenant boundary, as existing Fact subjects do.

### Extension acceptance and traceability

| Requirement | Acceptance / executable proof | Tasks |
|---|---|---|
| FR-013 | Missing/duplicate/unknown/cross-company context is rejected atomically; supplier and non-order objects work | T014, T015, T016 |
| FR-014, DR-006 | Capture replay is stable, context correction versions original; claimed/reported context matches approval; populated-link downgrade refused | T014, T015, T016 |
| FR-015 | Object history includes only explicit memberships and pending/settled proposals; bounded stable pages and tenant isolation | T014, T016, T017 |
| FR-016 | Supplier/object Inspector opens linked originals/files; outgoing review names context and updates after decisions | T014, T017, T018 |

Historical sources without verified context are preserved and readable by ID,
explicitly flagged as missing context; they are not assigned a guessed partner.
Re-capture with verified context creates a linked immutable version. Generic source
imports cannot manufacture authoritative correspondence memberships. Original file
and attachment-only Sources reach business context through the email message.

## Accepted local-test contract feedback (2026-10-04)

The owner authorizes these response improvements in PR #332.

- **FR-017**: Email detail history includes `decision.decider` from the existing
  tenant-scoped decision-attribution service, preserving person, MCP token, Chat
  agent and unknown distinctions and its existing identity disclosure rules. Never
  infer approval identity from the dispatch executor.
- **FR-018**: Each paged object correspondence summary includes `next_read` with
  tool `email_history` and its exact `source_id` argument. Related decision summaries
  provide the same explicit handoff using `proposal_id`. Follow-up reads in the same
  company expose original messages, attachment manifests and applicable decision/
  execution evidence. Listings remain bounded summaries without embedded bodies.
  Workflow guidance and MCP schema descriptions explain this distinction.

Acceptance: pending and unattributed decisions return unknown; attributed human,
MCP and Chat decisions match the shared attribution reader; foreign-tenant detail
reads remain not found. Following returned summary selectors retrieves the stored
original and applicable report chain without guessing an identity.
