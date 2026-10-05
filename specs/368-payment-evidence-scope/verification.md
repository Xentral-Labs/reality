# Verification: Payment evidence and selection scope
**Language**: English
## Test-first evidence
New PostgreSQL standard/orphan/unstated proofs failed with missing payment_interpretation before implementation. Discovery and existing prepayment/release proofs were extended first. Final focused shared service, shipment review, MCP HTTP and demo suites: 104 passed before the final completed-constraint assertion; final count recorded below after rerun.
## Compatibility and review
Shared helper decorates existing canonical direct/exact readiness and existing prepayment queue readiness. Standard queue retains null readiness and consumers use fulfillment_readiness; no extra per-line query or mixed cached/live settlement evidence. Raw cached payloads and reviewed dispatch token remain unchanged. No schema or business rule change. Independent research review found the standard queue shape and it was explicitly preserved/documented.
## Live runtime
Local stack rebuilt/restarted from merged PR373 (0e8b0e8774ff347e77942bae96cd5c045209b672), preserving named volumes. API/MCP/database/object storage healthy, all operational roles running. New source acceptance uses isolated loopback API/MCP against the existing synthetic tenant ten_f5328569e6; no business mutation or scheduler change.
## External acceptance
Actual Claude MCP read-only round and cleanup in progress. Results will be recorded before completion. Existing paused routine observed belongs to older tenant ten_62d117ec24; its custom weekday slots are visible, but no separate timezone or checkpoint field or next active run was established. Do not infer external absence from Reality capability discovery.
## Required gates
Full final-head Quality CI and final review pending. Tasks remain open until required checks pass.
