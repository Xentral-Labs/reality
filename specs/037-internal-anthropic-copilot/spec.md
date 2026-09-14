# Feature Specification: Internal Anthropic Copilot

**Feature Branch**: `037-internal-anthropic-copilot`

**Created**: 2026-09-02

**Status**: Approved

**Language**: English

**Input**: User description: "Default to the internal provider, allow own keys, and support all common providers with a finished settings layout."

## Context and Intent

### Problem

Company owners need a working provider by default without losing the option to use their
own account with a common LLM provider. The managed provider is an infrastructure
decision, while selecting an external provider, compatible model, and credential is a
legitimate company choice.

### Scope

- Make the internal Copilot deployment-managed and preselected.
- Use Claude Haiku as the initial economical model.
- Use the server-side credential by default and allow an owner to opt into a company-specific key for a curated common provider.
- Preserve the existing tenant-scoped application-tool and confirmation boundaries.

### Non-Goals

- Supporting provider-specific protocols beyond Anthropic Messages and OpenAI-compatible Chat Completions.
- Removing the deterministic provider used by automated tests.
- Changing MCP access, business tools, or confirmation semantics.
- Adding schema fields or migrating historical tenant provider settings.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Use the Managed Copilot (Priority: P1)

As an authenticated company user, I can ask Reality a question and receive an answer
from the deployment-managed Copilot without configuring a provider.

**Why this priority**: It is the user-facing outcome and proves the internal provider works.

**Independent Test**: Configure the deployment credential, submit a chat question, and
verify the managed model can call a read tool and return its result.

**Acceptance Scenarios**:

1. **Given** a valid deployment credential, **When** a user asks a business question,
   **Then** the economical managed Claude model answers through registered application tools.
2. **Given** a model requests a mutation, **When** it uses a registered proposal tool,
   **Then** the action remains pending until explicit human confirmation.
3. **Given** the provider is unavailable or misconfigured, **When** a user sends a message,
   **Then** the user receives a safe error and no business mutation occurs.

### User Story 2 - Choose Credential Ownership (Priority: P2)

As a company owner, I can keep the preselected Reality-managed Copilot or opt into using
my company's own API key with a supported provider.

**Why this priority**: The settings surface should describe the product boundary, not infrastructure.

**Independent Test**: Open Copilot settings, switch to a company key, save it, and switch back to managed mode.

**Acceptance Scenarios**:

1. **Given** no company key is configured, **When** the page renders, **Then** Reality-managed mode is selected.
2. **Given** an owner selects company-managed mode, **When** they enter and save a valid key,
   **Then** it is encrypted tenant-scoped and used only for that company's Copilot requests.
3. **Given** a company key exists, **When** the owner switches back to Reality-managed mode,
   **Then** the company key is revoked and subsequent requests use the deployment credential.
4. **Given** either mode, **When** settings are read, **Then** no clear key is returned.

### Edge Cases

- The deployment credential is missing, blank, or rejected.
- Claude returns no text, malformed tool input, an unknown tool, or exceeds the tool-step limit.
- Existing tenant rows still contain legacy provider configuration.
- Company-managed mode is requested without entering a key and no stored company key exists.
- The managed model identifier changes after a provider lifecycle update.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Copilot MUST default to managed Anthropic with an economical Claude model and support curated Anthropic, OpenAI, Google Gemini, Mistral, Groq, OpenRouter, and custom OpenAI-compatible configurations.
- **FR-002**: Reality-managed mode MUST read its credential and optional identity-linked workspace ID only from server deployment configuration and MUST be preselected when no company key exists.
- **FR-003**: Company owners MUST be able to select an external provider and store, replace, or revoke a tenant-scoped encrypted provider key without the clear value being returned or logged.
- **FR-004**: The Copilot MUST preserve registered tenant-scoped read/proposal tool dispatch and MUST NOT gain confirmation-tool access.
- **FR-005**: Provider, transport, protocol, and tool failures MUST produce a safe user-visible response and zero unconfirmed business mutations.
- **FR-006**: The deterministic no-network provider MUST remain available for automated tests.
- **FR-007**: Runtime credential selection MUST use an explicitly configured company provider and key when selected and otherwise use the managed deployment credential.
- **FR-008**: MCP configuration and access MUST remain unchanged.
- **FR-009**: Company settings MUST expose provider and compatible model selection, showing a custom endpoint only for the custom OpenAI-compatible option.
- **FR-010**: Provider choices MUST use shared finished form controls and MUST NOT render browser-default oversized radio controls.
- **FR-011**: The Copilot composer MUST remain visible as conversation history grows; scrolling MUST be contained to the message region.
- **FR-012**: Copilot assistant responses MUST render safe Markdown structure without executing embedded HTML.
- **FR-013**: While a submitted message awaits its assistant response, the conversation MUST show an accessible assistant loading indicator.
- **FR-014**: A submitted user message MUST appear immediately before its assistant loading indicator and remain until the canonical conversation reload replaces it.

### Key Entities

- **Deployment Copilot Configuration**: Server-only provider credential and fixed economical model choice; it is operational configuration, not business data.
- **Company Copilot Credential**: Existing tenant-scoped encrypted secret used only when the owner explicitly selects an external provider.
- **Chat Session/Message**: Existing tenant-scoped conversation records.
- **Change Proposal**: Existing auditable mutation request that still requires confirmation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Company owners see Reality-managed preselected and can configure a curated provider through standard provider, model, key, and—only for custom-compatible providers—endpoint controls.
- **SC-002**: In automated tool-use scenarios, 100% of model-requested business operations pass through registered tools.
- **SC-003**: In failure scenarios, 100% of requests create zero unconfirmed business mutations and return a safe response.
- **SC-004**: A deployment can enable Copilot with one server-side credential and no per-company setup.

## Assumptions and Dependencies

- Anthropic's active economical Claude Haiku model is appropriate for the initial validation.
- The deployment operator supplies `ANTHROPIC_API_KEY` to the API runtime.
- Identity-linked Anthropic credentials additionally require `ANTHROPIC_WORKSPACE_ID`; standard workspace API keys do not.
- Model quality will be evaluated with real usage before considering a more capable model.
- Existing valid Anthropic or OpenAI-compatible AI settings continue to select the tenant runtime; unsupported legacy modes fall back safely to Reality-managed configuration.
- A company-specific key uses the existing tenant secret vault and therefore needs no schema expansion.

## Requirement Traceability

| Requirement | Story | Executable proof |
|---|---|---|
| FR-001, FR-002, FR-004–FR-007 | US1 | Anthropic request, credential-selection, tool-loop, failure, and deterministic-provider tests |
| FR-003, FR-009 | US2 | Secret-vault, settings API, and browser contract tests |
| FR-008 | US2 | Existing MCP API and token tests remain green |
| SC-001 | US2 | Browser source contract asserts curated shared form controls and no oversized native radios |
| SC-002–SC-004 | US1 | Provider adapter, dispatch-boundary, failure, and environment-configuration tests |
