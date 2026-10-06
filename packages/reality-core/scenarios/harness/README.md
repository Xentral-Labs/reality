# Local rehearsal harness

For the owner's broader interactive goal, see the
[Reality Company Simulator direction](../../../../docs/scenarios/company-simulator.md).
The implemented harness below is the fixed-action replay; reactive world responses
and operator scoring require the separate planned company-simulator contract.

The controller reads one authored fixture, creates a new company through its adapter,
submits one event at a time, reads complete authoritative state, and stops at the first
failed oracle or invariant. This is synchronous compressed execution: a week takes
minutes rather than seven real days. Scenario dates and actual booking times are logged
separately. No application clock is changed and no automatic retries occur.

- `runner.py`: fixture validation, ordered clock/barriers, local command invocation.
- `observer.py`: complete tenant-scoped reads and deterministic Decimal comparison.
- `reporting.py`: immutable-per-run manifest, JSONL journal and readable report.
- Adapter `reference_week/simulator.py`: fixture-specific input resolution and effects.

A later Shopify-company profile can reuse control/reporting while submitting simulated
Shopify payloads to the existing integration boundary. A real shop and an AI operator
are independent future choices. Neither is implemented or enabled here. Keep Shopify
business interpretation in `src/reality/integrations/shopify/`, not the harness.

This developer module is not an API authentication boundary or packaged product CLI.
Use only a local migrated PostgreSQL test database. An existing eligible owner and
explicit fixed-fixture confirmation are required. The observer is read-only; no
materialized projection refresh is performed or claimed.
