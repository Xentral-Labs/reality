# Research: Compact Chat Answer Basis

## Decision: Persist the basis on the assistant message

**Rationale**: The answer and its support share tenant, lifetime, identity, and read authorization. One nullable bounded snapshot is the shortest durable relationship and needs no independent cleanup or join.

**Alternatives considered**: Reusing `StorylineTraceEntry` would incorrectly require a Playground run and contradict its bounded Storyline lifecycle. A new support table adds identity, retention, and join complexity without a multi-row query use case. Encoding metadata in message content would mix presentation with authority and damage lossless chat text.

## Decision: Capture canonical tool results, not model citations

**Rationale**: The dispatcher already knows exactly which read ran and what it returned. Capturing there is deterministic, provider-independent, and cannot cite a record the model never read.

**Alternatives considered**: Prompting the model to emit citations is probabilistic and provider-specific. Parsing IDs from assistant prose loses opaque identities and fails for translated or reformatted answers.

## Decision: Present recognized business shapes in the service

**Rationale**: The browser must not create alternative business semantics. The service can map known returned fields into labels, values, explicit observation text, and allowlisted record routes while retaining the full bounded snapshot for future presenters.

**Alternatives considered**: A generic JSON tree repeats the current technical problem. A browser-only mapper violates the shared-service boundary. A universal catalog-driven presenter is larger than the proven open-order use case.

## Decision: Preserve Storyline tracing as a secondary channel

**Rationale**: Existing proposal and later-decision trace behavior is already specified and useful in eligible Sandboxes. Separating `basis` from `items` avoids pretending that later changes supported the original answer.

**Alternatives considered**: Replacing Storyline traces would regress proposal explanation. Mixing both into one row list would obscure their different meaning.
