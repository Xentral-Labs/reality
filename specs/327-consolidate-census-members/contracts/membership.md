# Contract: Census Membership and Protected History

No new public API, MCP tool, command, scheduled job or confirmation surface is added.
Existing internal service and original SQL/ORM logical contracts remain authoritative.

## Existing services

`retain_company_cost_census` retains a consistent REPEATABLE READ observation in a
clean session and caller-owned transaction, with savepoint rollback, request replay
and original limits. `company_cost_census` returns retained metadata;
`company_cost_census_members` uses the original family field allowlists, limit up to
500 and capture-bound paging cursor. `verify_company_cost_census` retains original
counts/hashes/bounds and refuses corruption. Captured-basis/company generation still
resolve retained subjects, not current replacements, and census is never publishable.

## Original logical interfaces

Four original names and exact 6/6/7/7 column sets remain. Fixed-family routing performs
INSERT with original fields and returns stored original values. Bulk chunk inserts,
rowcount, RETURNING and ORM tenant/id identity must be proven. No alias/discriminator
appears in service hashes, observed rows, record inspection or downstream inputs.
Native logical UPDATE/DELETE reaches physical immutable-member refusal; a no-match
statement retains its original zero-row behavior.

## Physical integrity

Wrong tenant, missing subject/outcome, unknown/mixed shape, duplicate family selection,
wrong-family incoming identity and different-census document member fail at the database.
Equal old IDs across families/tenants remain valid. Document membership enforces the
captured link only; do not add a stronger live document-line semantic constraint.
Building admission locks the same parent row as sealing. Test both race orders with
two READ COMMITTED sessions: insert waits behind a seal then fails, or sealing waits
behind admitted insertion then proceeds. Retain locks through transaction completion;
use bounded events/DB lock observation rather than sleeps as race proof.

## Storage administration

Count physical members once. Preserve existing purge authority and outcome: removable
records are removed once, protected census history still refuses deletion and caller
rollback restores any prior attempted deletions. Assert another tenant is unaffected.
No privileged trigger bypass or new history cleanup is authorized by this feature.

## Transition

Upgrade and rollback are transactional, populate document family before line family,
validate exact rows in both directions, preserve downstream local tuples, and restore
original FK/index/trigger/function contracts on rollback. Deliberate parity failure
must roll back all schema/data changes. This contract is a planned proof, not acceptance.
