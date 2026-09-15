# Research: Delete Empty Chat Sessions

## Decision: Derive emptiness from durable messages

**Rationale**: Message existence is the only durable proof of conversational history. Titles and
creation time are presentation data and can be misleading.

**Alternatives considered**: A stored `is_empty` flag or message count was rejected as duplicated,
drift-prone state. Title-based inference was rejected as browser-owned business logic.

## Decision: Reuse the existing removal route

**Rationale**: Callers already express intent to remove a session. The service can choose the only
safe disposition while preserving the existing HTTP boundary.

**Alternatives considered**: A second permanent-delete endpoint was rejected because it would let
callers request an unsafe consequence and duplicate authorization/tenant behavior.

## Decision: Safely fall back to archive under concurrency

**Rationale**: The service rechecks message existence at mutation time. If a message appears after
the UI projection, retaining history is safer than honoring a stale delete label.

**Alternatives considered**: Optimistic revision tokens were rejected as disproportionate for an
empty presentation container; silent permanent deletion after a stale read was rejected.
