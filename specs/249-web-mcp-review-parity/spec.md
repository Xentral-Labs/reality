# Feature Specification: Web and MCP Proposal Review Parity

**Feature Branch**: `249-web-mcp-review-parity`
**Created**: 2026-09-22
**Status**: Approved scope (owner: every real MCP mutation must also work through Web; no demo tools)
**Language**: English for all repository artifacts and review evidence.

## Context and Intent

### Problem

Reality exposes 102 proposal-producing MCP tools, but Web can currently resume and review
only a minority of their proposals. Some server-reviewed actions are merely absent from
Web routing, while many valid proposals are listed as impossible to review. This breaks
the promised MCP → human Web review → shared execution workflow and makes realistic
company operation impossible without transport-specific workarounds.

### Scope

Every production MCP proposal must be discoverable, understandable, explicitly decidable
and recoverable in Web. Existing specialized business reviews remain authoritative.
Tools without a specialized review receive one common truthful review of the exact stored
proposal and server-produced preview before the original shared application tool executes.

### Non-Goals

No demo-only tools, demo execution path, new business rules, automatic approval, bulk
approval, external side effects, schema expansion, direct ORM writes, or replacement of
existing specialized reviews. This feature does not claim that every operation deserves a
new dedicated workspace form; it guarantees complete proposal review and execution parity.

## User Scenarios & Testing

### User Story 1 — Complete an MCP-proposed action in Web (Priority: P1)

As an operator, I can open any pending proposal created through MCP, inspect what will
change, and explicitly approve or reject it in Web.

**Independent Test**: Generate one proposal for every proposal-producing MCP definition,
open its Decisions entry, and prove it reaches either its existing specialized review or
the common review without an unsupported state.

**Acceptance Scenarios**:

1. **Given** an MCP proposal with an existing specialized review, **When** it is opened
   from Chat or Decisions, **Then** Web restores that exact specialized review.
2. **Given** any other valid MCP proposal, **When** it is opened, **Then** Web shows the
   exact stored tool, stated inputs, persisted preview, origin and confirmation boundary.
3. **Given** unchanged valid state, **When** the operator confirms, **Then** the original
   application tool executes once and Web shows its stored receipt.
4. **Given** rejection, **When** the operator confirms rejection, **Then** no business
   mutation occurs and the rejected decision remains auditable.

### User Story 2 — Recover safely after navigation or changed state (Priority: P1)

As an operator, I can reload or revisit a proposal without losing its identity, and I am
stopped when its reviewed assumptions are no longer valid.

**Independent Test**: Open, reload, confirm, revisit and stale one representative proposal
from each review class; verify exact recovery, single execution and useful refusal.

**Acceptance Scenarios**:

1. A bookmarked proposal restores the same review after reload and company navigation.
2. A completed proposal restores its immutable receipt rather than running again.
3. A stale, unauthorized or cross-tenant proposal cannot execute and discloses no foreign data.
4. A malformed or empty proposal is not presented as a valid confirmation; Web explains
   the problem and still permits safe rejection where authorized.

### User Story 3 — Prevent future parity regressions (Priority: P1)

As a product owner, I know that publishing a new MCP mutation cannot silently create an
unreviewable Web decision.

**Independent Test**: A registry contract fails when a proposal-producing MCP tool has no
Web review classification, label or server review descriptor.

### Edge Cases

- Conditional review types such as movement, item import and invoice-linked credit.
- Proposals created before this feature, unknown retired tools and changed catalog labels.
- Secret-bearing inputs, lossless payloads and large nested values.
- Multiple tabs, duplicate confirmation, provider retry and uncertain network outcome.
- Proposal lists containing tools whose dedicated workspace is temporarily unavailable.
- Dependencies between proposals: later proposals must use opaque IDs returned by confirmed
  earlier proposals; Web review does not legitimize invented identifiers.

## Requirements

- **FR-001**: Every proposal-producing MCP tool MUST have exactly one server-authoritative
  Web review classification: existing specialized review or common exact-proposal review.
- **FR-002**: Chat and Decisions MUST use the same classification and destination; they
  MUST NOT maintain divergent hard-coded support lists.
- **FR-003**: The common review MUST show human-readable tool purpose, proposal origin,
  creation time, exact non-secret stated inputs, persisted server preview, current status
  and the explicit approve/reject consequences.
- **FR-004**: Secrets and credential-like values MUST be omitted or redacted by the server;
  the browser MUST NOT infer sensitivity from field names as the primary control.
- **FR-005**: Approval MUST execute the unchanged stored proposal through the existing
  application boundary with tenant scope, current authorization, idempotency and any
  required state-bound review token. Web MUST NOT reconstruct tool input.
- **FR-006**: Rejection MUST remain available for all pending proposals that the operator
  may decide and MUST create no business effect.
- **FR-007**: Reload and revisit MUST restore pending review, refusal or completed receipt
  by opaque proposal ID without re-preparing or re-executing the action.
- **FR-008**: Invalid, empty, stale, unauthorized, retired and cross-tenant proposals MUST
  fail safely with a useful explanation and no information disclosure.
- **FR-009**: Existing specialized reviews and their stronger semantic previews MUST remain
  in use; the common review MUST NOT downgrade them.
- **FR-010**: A generated contract test MUST compare the MCP proposal registry with Web
  review classifications and fail for missing, duplicate or unlabeled coverage.
- **FR-011**: The Web review MUST work accessibly on narrow and desktop layouts in all
  supported product languages, including keyboard confirmation and readable nested data.
- **FR-012**: Documentation MUST state that demo companies use the same production tools,
  services, reviews and confirmation rules as ordinary companies.

## Key Entities

- **Change proposal**: existing tenant-scoped stored intent, input, preview, status and receipt.
- **Review descriptor**: read-time server description of how Web reviews one proposal;
  it is not new business authority and is not persisted as a second proposal.
- **Review class**: specialized or common presentation selected by the server from the
  canonical application/MCP tool identity and proposal content.

## Success Criteria

- **SC-001**: 100% of proposal-producing MCP definitions pass the Web review coverage contract.
- **SC-002**: No pending valid MCP proposal displays “cannot be reviewed in this interface”.
- **SC-003**: Representative browser journeys prove propose → reload → approve/reject →
  receipt for every review class without duplicate business effects.
- **SC-004**: Existing specialized-review regression suites remain green.
- **SC-005**: No schema migration or transport-specific business rule is introduced.

## Assumptions and Dependencies

The current MCP registry and ChangeProposal lifecycle remain authoritative. The common
review is appropriate only because it executes the exact stored production proposal after
server authorization; it is not a generic arbitrary-command runner. Existing tools that
require additional server review continue to obtain it before approval. The owner approved
complete production-tool parity and explicitly rejected demo-specific tools.

## Requirement Traceability

| Requirement           | Story    | Planned proof                                                |
| --------------------- | -------- | ------------------------------------------------------------ |
| FR-001–FR-002, FR-010 | US1, US3 | Registry/service and Web routing contract tests              |
| FR-003–FR-009         | US1, US2 | Service/API tests plus browser review/recovery journeys      |
| FR-011                | US1, US2 | Web build, localization audit and responsive keyboard checks |
| FR-012                | US3      | Durable Web/MCP and demo contract review                     |
