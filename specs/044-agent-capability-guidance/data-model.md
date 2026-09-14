# Data Model: Agent Capability Guidance

No persisted business entity or migration is added. These values are immutable
application metadata composed from versioned configuration.

## Capability Description

- canonical command and service identity;
- public proposal-tool identity;
- purpose, use conditions, and prohibited-use conditions;
- required context and preconditions;
- confirmation and retry/idempotency guidance;
- expected Refusals and Business Events;
- Verification Reads;
- at least one positive and negative Example.

One public proposal tool resolves to one command. Different tools mapped to the same
service may carry different guidance because their business intent can differ, such as
reservation creation and release.

## Verification Read

- stable public read name;
- kind: materialized projection or registered read-only application tool;
- business-readable proof statement.

The read must exist and must not mutate state.

## Refusal

- stable lower-case machine code;
- business-readable description.

Refusals document expected outcomes but do not replace service validation.

## Example

- scenario;
- expected use or non-use;
- reason;
- optional placeholder inputs.

Examples contain no tenant data and never treat display numbers as identity.

## Validation invariants

- Guidance resolves to an eligible canonical command and registered public tool.
- Mandatory text and arrays are non-empty.
- Events and verification reads resolve to their canonical registries.
- Confirmation metadata matches the executable application tool.
- The four initial services have complete guidance.
- Guidance grants neither tenant authority nor executable domain logic.
