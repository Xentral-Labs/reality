# Research: Agent Capability Guidance

## Decision: Extend the canonical command catalog

**Rationale**: Commands, agent eligibility, events, and projections already compose in
one validated catalog. Colocated guidance prevents prompt copies and enables reference
validation.

**Alternatives considered**: A database table adds unproven tenant state. Prompt-only
guidance cannot be validated. A second agent registry would drift.

## Decision: Describe public agent tool identities

**Rationale**: Agents know proposal-tool names. Resolving them through existing agent
coverage avoids advertising blocked or administrative operations.

**Alternatives considered**: Arbitrary service names expose internal vocabulary.

## Decision: Validate references during catalog composition

**Rationale**: Existing loading already rejects command, event, tool, table, and
projection drift, so the same gate should reject unsafe guidance before advertising it.

**Alternatives considered**: Runtime-only validation discovers defects too late.

## Decision: Re-read existing projections

**Rationale**: This slice describes verification rather than persisting orchestration.
Existing projections expose the selected outcomes without schema expansion.

**Alternatives considered**: A verification table belongs to a later closed-loop slice.

## Decision: Adopt guidance incrementally

**Rationale**: Four commands prove observation, evidence/promise, allocation, and
physical-event distinctions. Inventing semantics for all commands would reduce accuracy.

**Alternatives considered**: Mandatory guidance for every command creates an unproven
review surface.

