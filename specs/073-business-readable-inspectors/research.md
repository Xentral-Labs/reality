# Research: Business-readable Inspectors

## Use one shared hierarchy

**Decision**: Improve the existing shared inspector contract and drawer instead of
creating Fact-, Exception-, or register-specific detail components.

**Rationale**: Every important register already opens the same inspector. A common
hierarchy makes investigations predictable and prevents visual and semantic drift.

**Alternatives considered**: Redesign only Facts; add dedicated pages per record. Both
leave the same problem elsewhere and increase UI surface area.

## Put business interpretation on the server

**Decision**: Return explicit business meaning, best available reference, and guidance
from tenant-scoped server reads.

**Rationale**: The server owns relationship traversal and exception guidance. The
browser must not infer that a predicate or cause means a particular business action.

**Alternatives considered**: Assemble sentences from `kind`, trail labels, and metrics
in React. Rejected because it duplicates business interpretation in an adapter.

## Collapse support detail, never remove it

**Decision**: Move opaque identity, exact fields, raw event types, and payload beneath
one explicit Technical details disclosure after the business explanation.

**Rationale**: ERP users get a clear first answer while support retains the exact audit
path needed to verify it.

**Alternatives considered**: Keep IDs next to status; remove duplicate technical rows.
The first preserves current confusion and the second weakens traceability.

## No presentation persistence

**Decision**: Derive all new copy and references per read from existing records.

**Rationale**: The business need is presentation hierarchy, not a new authoritative
concept. Stored summaries would become stale and violate the shortest-link principle.

**Alternatives considered**: Add display labels or summaries to Fact and Exception
storage. Rejected because no repeated core calculation requires them.
