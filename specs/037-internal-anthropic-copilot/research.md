# Research: Internal Anthropic Copilot

## R1 — Managed model

**Decision**: Start with `claude-haiku-4-5-20251001`.

**Rationale**: Anthropic lists Claude Haiku 4.5 as the active replacement for retired Haiku generations and positions Haiku as the economical tier. A dated identifier makes runtime behavior explicit and reviewable.

**Alternatives considered**: Retired Claude 3/3.5 Haiku identifiers were rejected; Sonnet and Opus were rejected for the initial cost-validation run.

## R2 — Transport

**Decision**: Call Anthropic's native `/v1/messages` endpoint with `x-api-key` and `anthropic-version` headers through the existing httpx dependency.

**Rationale**: Anthropic is not an OpenAI-compatible endpoint. Native request and tool-use blocks preserve protocol correctness without adding an SDK.

**Alternatives considered**: OpenAI-compatible emulation is invalid; adding an SDK is unnecessary for the bounded API surface.

## R3 — Configuration ownership

**Decision**: Resolve `ANTHROPIC_API_KEY` at request time and report only availability.

**Rationale**: Deployment ownership removes tenant configuration, avoids browser secret handling, and supports key rotation without database writes.

**Alternatives considered**: Copying the environment secret into every tenant vault duplicates one deployment secret and creates unnecessary rotation work.

## R4 — Common provider coverage

**Decision**: Keep native Anthropic Messages support and route OpenAI, Gemini, Mistral,
Groq, OpenRouter, and custom gateways through their documented OpenAI-compatible Chat
Completions endpoints.

**Rationale**: This covers the common provider families with the existing two protocol
adapters and one tenant-scoped secret lifecycle.

**Alternatives considered**: A separate SDK and adapter for every provider would add
dependencies without improving the supported tool-calling contract.
