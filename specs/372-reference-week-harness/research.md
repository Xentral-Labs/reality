# Research Decisions

- Use independent practice Sandbox application proposals, not quick lesson
  `prepare_step` and not `prepare_delivery_action` (which refuses playground).
  Research checked `require_proposal_creation`, `_PRACTICE_APP_OPERATIONS` and
  existing `test_sandbox_read_parity`. Ordinary multiline orders and cancellation
  are admitted through `create_change_proposal` / `approve_and_execute_proposal`.
- Use synchronous authoritative reads; materialized projection timing and external
  raw intake are explicitly separate future adapters. No new timer or queue.
- Reuse PyYAML and PostgreSQL/pytest. No external provider or dependency needed.
- Use a retained executed proposal for replay; a manual order's repeated source
  cannot be accepted as a new order. Do not invent general mutation idempotency.
