# Generation publication guard

This domain contract refines T080 and FR-007/012/014/018. Its first production
integration is the bounded retained-review builder in inventory-publication.md. It does not expose a
new tool, manufacture a company profile from line reviews or publish a database row.

A generation has an opaque identity and immutable basis: tenant, canonical scope key,
retained manifest, policy/profile revisions, actual effective/knowledge UTC cutoffs,
input event sequence and algorithm version. Inventory has no contribution profile;
contribution requires one. Scope key is a trusted service-computed key for compatible
requested contexts, not a caller-supplied authority. Generation identity is distinct
from context identity and content digests.

Completion facts are constant-size: sealed inputs, validated content, expected/completed
work count and expected/actual inventory, contribution and trace row counts. Every
count is a strict nonnegative integer; completed work cannot exceed planned work. Zero
work/rows is legal only with sealed, validated empty input. Monetary coverage is NOT a
publication condition: a fully calculated generation can accurately report unknown costs.

The guard receives the caller tenant, candidate and observed publication, expected
previous generation ID and current committed tenant event cursor. Validate tenant and
canonical scope before any successful decision. Equal scope keys must also have equal
kind, policy/profile revision and effective cutoff; a key cannot hide conflicting facts. Candidate must be complete, sealed,
verified and have equal counts. A backward live cursor refuses. Different publication
than expected refuses; an older candidate cannot replace a newer input sequence. A
retry already pointing to the identical candidate is unchanged, never a second write.
The same generation ID with different basis is invalid. All refusals return stable
codes without embedding foreign identities.

Return a pure decision: candidate generation ID, whether a pointer change is required,
processed/target event cursors and ready/pending freshness. Late events can coexist
with valid historical publication but return pending; current-required readers must
not present its values as current. This decision changes no state and never approves
financial completeness or schedules follow-up itself.

Each integration MUST lock/CAS the same publication key, verify retained input
membership and content, count persisted work/rows and apply the decision atomically
with shared worker claim fencing. Client-supplied counts/booleans are not accepted
evidence. Unit tests prove decision rules, not PostgreSQL atomicity or bounded runtime
of the future builder. Generalized retained context versions, company-wide profile authority and multi-scope
canonical relations remain separate unfinished implementation obligations.
