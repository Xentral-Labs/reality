# Data Model: Internal Anthropic Copilot

No schema change is required.

- Existing `ChatSession` and `ChatMessage` records remain tenant-scoped.
- Existing `ChangeProposal` records retain the proposed → confirmed/rejected lifecycle.
- Existing `AISettings` stores the tenant's provider, model, optional compatible endpoint,
  and an opaque reference to its tenant-scoped provider credential.
- Reality-managed mode does not require a tenant credential and uses the deployment's
  `ANTHROPIC_API_KEY` and managed model identifier.
- Existing encrypted provider secrets remain in the generic tenant-scoped secret vault;
  clear API keys are never persisted in `AISettings` or returned by the API.
