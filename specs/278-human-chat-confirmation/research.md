# Research: Human Chat Confirmation

## Decision 1 — Narrow the built-in model's granted access

**Decision**: Ordinary built-in Chat receives `read` and `propose`; Playground receives `read`.

**Rationale**: The catalog already derives provider schemas and dispatch permission from a
server-selected access tuple. Removing `confirm` both hides settlement tools and enforces refusal.

**Alternatives considered**: prompt-only prohibition is not authorization; a new Chat token would
duplicate human review; removing all proposal tools would discard the useful safe handoff.

## Decision 2 — Keep external MCP confirmation unchanged

**Decision**: Do not alter public MCP schemas, permissions or token attribution.

**Rationale**: External clients have an explicit access-token trust boundary. Reality can truthfully
attribute that token without inferring a person behind it.

## Decision 3 — Use the pending proposal as the resumable boundary

**Decision**: Stop built-in Chat at a durable `proposed` record and route to canonical review.

**Rationale**: It already holds exact intent, review data and lifecycle state, survives reloads and
is the shortest true agent-to-human handoff. A new workflow table is unnecessary.
