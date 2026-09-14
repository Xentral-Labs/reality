# Research: Command Action Guidance

## Decision 1: Reuse the canonical Command effect

- **Decision**: Derive `WorkspaceAction.description` from the referenced Command's non-empty `effect`.
- **Rationale**: The effect already explains the governed shared-service mutation and keeps Web, CLI, API, MCP, Chat, and documentation aligned.
- **Alternatives considered**: Duplicate prose in the workspace catalog; hard-code descriptions in React. Both create competing classifications and drift.

## Decision 2: Separate effect from prerequisites

- **Decision**: Present the effect as primary supporting copy and prerequisites in an optional labelled row.
- **Rationale**: Users need to distinguish the outcome from the records needed to perform it.
- **Alternatives considered**: Replace prerequisites entirely; append them without a label. Both lose useful context or remain ambiguous.

## Decision 3: Keep confirmation unchanged

- **Decision**: Display guidance during entry and review without changing the two-step mutation flow.
- **Rationale**: Explanation improves informed confirmation but does not substitute for it.
- **Alternatives considered**: Show guidance only in the launcher; add another confirmation step. The first leaves direct actions unexplained and the second adds friction without new safety.
