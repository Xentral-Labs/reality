# Research: Complete Demo Business Journeys

## Decisions

- **Decision**: Reuse existing return, credit, allocation and cancellation services.
  **Rationale**: They already enforce quantity, party, tenant and posting invariants.
  **Alternatives considered**: Fixture-only ORM writes were rejected as untraceable.
- **Decision**: Keep continuous intake unchanged.
  **Rationale**: Its contract is incoming demand and settlement, not automatic physical
  or exception execution.
- **Decision**: Document unresolved examples explicitly.
  **Rationale**: An exception is useful demo evidence and must not be made artificially
  complete merely to produce a green status.

