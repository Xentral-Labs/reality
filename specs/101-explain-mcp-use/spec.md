# Feature Specification: Explain MCP Use

**Feature Branch**: `101-explain-mcp-use`
**Created**: 2026-09-07
**Status**: Approved
**Input**: Make the landing page and documentation explain what customers can do with Reality MCP and how they connect an external agent.
**Language**: English

## Context and Intent

### Problem

Reality explains why agents need traceable business context, but a prospective customer cannot quickly identify concrete MCP jobs or the current connection method. The documentation describes individual capabilities without one customer-facing setup journey.

### Scope

Add a compact landing-page bridge from product value to MCP setup, with the governed read/propose/approve boundary and a direct documentation link. Keep concrete jobs and connection detail in one bilingual public guide that explains endpoint discovery, bearer-token creation, tool permissions, client configuration, verification, and revocation.

### Non-Goals

- Adding OAuth, PKCE, dynamic client registration, or refresh tokens.
- Claiming certified or one-click integration with named agent products.
- Changing MCP tools, permissions, transport, authentication, or business behavior.

## User Scenarios & Testing

### User Story 1 - Understand MCP Value (Priority: P1)

A prospective customer sees concrete business jobs an external agent can perform through Reality and understands that changes remain governed.

**Why this priority**: A protocol name alone does not communicate customer value or the safety boundary.

**Independent Test**: Review the landing page and identify MCP as the external-agent connection path, the immediate-read versus approved-change distinction, the current access method, and the documentation path without interrupting the surrounding product narrative with a capability catalog.

**Acceptance Scenarios**:

1. **Given** a visitor reaches the end of the agent section, **When** they scan the MCP content, **Then** they see one compact connection bridge rather than a second capability showcase.
2. **Given** the current token-based implementation, **When** the connection method is described, **Then** it says HTTPS endpoint and restricted access token without promising OAuth or one-click connection.
3. **Given** a visitor wants setup detail, **When** they follow the MCP guide action, **Then** they reach the canonical public connection guide.

### User Story 2 - Connect an MCP Client (Priority: P1)

A company administrator can use the public documentation to connect a compatible external MCP client safely and verify the first read.

**Why this priority**: Discovering capability without a setup path does not let a pilot customer use it.

**Independent Test**: Follow the English or German guide from endpoint discovery through token revocation without requiring undocumented knowledge.

**Acceptance Scenarios**:

1. **Given** an administrator has a Reality company, **When** they follow the guide, **Then** they can find the endpoint, create a named token, choose tools, configure a generic MCP client, and perform a safe read.
2. **Given** a proposed mutation, **When** the guide explains execution, **Then** it distinguishes proposal, human approval, execution, and verification.
3. **Given** a leaked or obsolete credential, **When** the administrator follows the security section, **Then** they can revoke it and understand that Reality does not currently issue OAuth refresh tokens.

### Edge Cases

- Client configuration formats differ, so the guide uses a generic HTTP/bearer contract and labels product-specific configuration as client-owned.
- A client supports MCP but does not accept manually configured bearer headers.
- A token lacks permission for a requested tool.
- A valid read returns no records; the guide does not treat that as proof that no business issue exists.

## Requirements

### Functional Requirements

- **FR-001**: The landing page MUST present MCP as one compact connection bridge after the agent-context example and MUST leave the concrete business-job catalog to the linked guide.
- **FR-002**: The landing page MUST explain that reads can run immediately while changes are proposals requiring human approval.
- **FR-003**: The landing page MUST describe the current connection as an authenticated HTTPS MCP endpoint with a tenant-scoped restricted access token.
- **FR-004**: The landing page MUST link directly to the public MCP connection guide.
- **FR-005**: The public documentation MUST provide matching English and German MCP connection guides.
- **FR-006**: Each guide MUST cover prerequisites, endpoint discovery, named token creation, least-privilege tool selection, generic client configuration, a first read, governed changes, troubleshooting, and token revocation.
- **FR-007**: Public claims MUST NOT imply OAuth, PKCE, dynamic registration, refresh-token rotation, certification, or one-click support while those capabilities are absent.
- **FR-008**: The guide MUST link to the canonical MCP tool catalog and agent-capability guidance instead of duplicating their full contracts.
- **FR-009**: Automated content contracts MUST fail if the compact landing bridge, safety boundary, setup route, bilingual guide, or token-auth limitation disappears, or if the five-column capability panel returns.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A first-time reader can identify how an external agent connects and state the approval boundary after reviewing the bridge for under 30 seconds.
- **SC-002**: An administrator can locate every step required to connect and revoke a client credential from one guide in under five minutes.
- **SC-003**: Every advertised setup statement matches the currently implemented authentication and permission model.
- **SC-004**: English and German readers receive the same setup steps and safety boundaries.

## Assumptions and Dependencies

- The existing authenticated Streamable HTTP MCP runtime, company settings, token allowlists, and generated tool catalog remain authoritative.
- Compatible clients may expose different user interfaces; their current product-specific screens are outside Reality's contract.
- Public documentation is available through the configured Docs origin.

## Requirement Traceability

| Requirement | Acceptance evidence |
| --- | --- |
| FR-001–FR-004 | User Story 1 scenarios 1–3 and landing content contract |
| FR-005–FR-008 | User Story 2 scenarios 1–3 and bilingual Docs content contract |
| FR-009 | Site and Docs automated content-contract suites |
