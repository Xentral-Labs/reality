# Feature Specification: Stable Codes in MCP Tool Refusals

**Feature Branch**: `214-mcp-error-codes`
**Created**: 2026-09-16
**Status**: Implemented (2026-09-16); scope from issue #49
**Language**: English
**Input**: Issue #49 (Atlas, 2026-09-16): a client that has to decide whether a refusal is
deterministic or an unknown outcome has nothing to classify on except prose, which no client
should match.

## Context and Intent

### Problem

Service refusals (`InvalidOperation`, `NotFound`, `Conflict`, `InterpretationNeedsReview`) are
raised with a business-readable sentence. The MCP layer returns them as an error result whose
text is "Error executing tool <name>: <sentence>". A person reads that well. An agent that must
decide whether to retry, ask a person, or stop has to match the sentence, and every sentence
change becomes a client change. Atlas, as the first governed client, treats every such text as
an unknown outcome today, so a validation refusal at an inert proposal looks the same as a
network failure.

### Scope

- Every tool refusal that stems from a service error reaches the client as an MCP error result
  whose single text content is one JSON object with `code`, `message` and `tool`.
- Codes follow the service error hierarchy: `not_found`, `conflict`, `needs_review`,
  `invalid_operation`, and `reality_error` for any other `RealityError`.
- The message is the unchanged sentence. Nothing a person reads changes.
- Failures that are not business refusals (unknown tool, missing scope, missing tenant
  context, unexpected exceptions) keep the plain text they have today.
- The tool usage documentation explains the shape in English and German.

### Non-Goals

- No change to which refusals a service raises or to their sentences.
- No new codes per sentence; the hierarchy is the vocabulary. Finer codes come with the
  services that need them, as their own specifications.
- No change to successful results or to the read contract (`data_basis`, `freshness`,
  `limitations`).
- No change to the HTTP API or the CLI, which keep their own error shapes.

### Existing Contracts

- [Separate MCP runtime](../018-separate-mcp-runtime/spec.md): the authenticated HTTP boundary
  the error results travel over.
- [Agent interaction](../014-agent-interaction/spec.md): mutations are proposals; a refusal at
  proposal time has no side effect.

## User Scenarios & Testing

### User Story 1 - An agent tells a missing record from a broken line (Priority: P1)

An agent asks `order_explain` for a reference the tenant does not have. The result is an error
result with `code: not_found`. The agent records the sentence for the person and does not retry.
A network failure on the same call has no code, and the agent treats it as unknown.

**Why this priority**: It is the whole feature; without it every refusal is an unknown outcome.

**Independent Test**: Call `order_explain` with an unknown reference through the FastMCP server
in a test and parse the error text as JSON.

**Acceptance Scenarios**:

1. **Given** a tenant without order `SO-NOT-THERE`, **When** `order_explain` is called with it,
   **Then** the error result text parses as JSON with `code` `not_found`, `tool`
   `order_explain` and a non-empty `message`.
2. **Given** `business_records_discover` with `limit` 0, **When** called, **Then** the code is
   `invalid_operation` and the message is the service sentence.

### User Story 2 - Non-business failures stay as they are (Priority: P2)

A client with a token that lacks a tool's scope, or that names an unknown discovery family,
sees the same plain text as before, without a code.

**Why this priority**: Codes classify business refusals; making transport or authorisation
failures look like business outcomes would mislead the client the other way.

**Independent Test**: Call `business_records_discover` with an unsupported family and assert
the error text starts with "Error executing tool".

**Acceptance Scenarios**:

1. **Given** an unsupported family, **When** discover is called, **Then** the error text is the
   FastMCP text and does not parse as the JSON object.

### Edge Cases

- A `Conflict` is an `InvalidOperation` by inheritance; its code is `conflict`, the more
  specific one.
- A message that itself contains JSON is still carried as a string inside `message`; clients
  read `code` only.

## Requirements

### Functional Requirements

- **FR-001**: A tool refusal caused by a `RealityError` MUST reach the client as an MCP error
  result whose text is one JSON object with `code`, `message` and `tool`.
- **FR-002**: The code MUST be `not_found` for `NotFound`, `conflict` for `Conflict`,
  `needs_review` for `InterpretationNeedsReview`, `invalid_operation` for any other
  `InvalidOperation` and `reality_error` for any other `RealityError`.
- **FR-003**: The message MUST be the service sentence unchanged.
- **FR-004**: Errors that are not `RealityError` MUST keep their current text.
- **FR-005**: The tool usage documentation MUST describe the shape and the codes in English and
  German.

## Success Criteria

- **SC-001**: `tests/test_mcp_error_codes.py` passes: codes per class, JSON shape through the
  server for `not_found` and `invalid_operation`, plain text for a non-business failure.
- **SC-002**: The existing MCP test suites pass unchanged.
- **SC-003**: Atlas can classify a refusal at `order_create_propose` without reading the
  sentence (tracked on the Atlas side).

## Assumptions and Dependencies

- FastMCP wraps every tool exception in `ToolError("Error executing tool <name>: ...")` with
  the original exception as `__cause__`; the code relies on that cause to recognise a
  `RealityError`. A FastMCP upgrade that drops the cause would surface in SC-001.
- The low-level MCP server renders a raised exception as an error result with the exception's
  string as its text, so the JSON reaches the client verbatim.

## Requirement Traceability

| Requirement | Evidence |
| --- | --- |
| FR-001 | `packages/reality-core/src/reality/mcp/server.py` `RealityServer.call_tool`, `tool_error_payload`; `tests/test_mcp_error_codes.py` |
| FR-002 | `ERROR_CODES`, `error_code`; `test_error_codes_follow_the_service_error_hierarchy` |
| FR-003 | `tool_error_payload` carries `str(error)`; `test_service_errors_reach_the_client_as_code_and_message` |
| FR-004 | `RealityServer.call_tool` re-raises other `ToolError`s; `test_other_failures_keep_their_text` |
| FR-005 | `apps/docs/content/tool-usage/index.md`, `apps/docs/content/de/tool-usage/index.md` |
