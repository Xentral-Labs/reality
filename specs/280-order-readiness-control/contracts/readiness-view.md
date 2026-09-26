# Readiness View Contract

- Source: tenant-scoped `fulfillment_queue` specialized projection page.
- Read-only: opening, searching, paging and expanding issue GET requests only.
- Order navigation: exact `document_id` to Document Inspector.
- Line navigation: exact `commitment_id` to Commitment Inspector.
- Freshness: show completed observation timestamp; pending changes mark retained rows stale.
- Missing completed snapshot: unavailable state, never zero/ready.
- Quantities: line-local and unit-preserving; no browser sum across lines.
- Money: render canonical readiness amounts only when returned.
