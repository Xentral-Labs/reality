# Validation

Run focused tests in test_read_evidence_boundaries.py with the existing PostgreSQL pytest environment, then related read/discovery/HTTP regressions. Run make docs-generate, make docs-catalog-check and make spec-check; full CI is required.

For the authorized paused synthetic company, use temporary read-only MCP access in a fresh external Claude conversation: discover SO-006, discover executed Decisions by returned order ID, read review/status and explain current order. Supply no Decision ID and no expected quantity. Ask for history only through inspected evidence. Inspect tool calls and final answer separately; compare before/after operational state and revoke the test access. Never replay effects.
