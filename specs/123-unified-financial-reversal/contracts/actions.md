# Interfaces
Canonical ledger_reverse accepts posting_group_id and reason, with existing optional expected_revision/preview_fingerprint. Common prepare/review/confirm/reconcile binds current state and explicit confirmation. Result remains {reversal_id, original_posting_group_id, reversing_posting_group_id, replayed}.
GET /finance/reversal-choices exposes tenant-scoped paginated group choices with document/party context. It does not mutate or prepare proposals. Existing direct reversal API remains available.
Historical verification requires this action's attributable event, matching original/inverse relation and exact entry snapshots. Current observations are separate. No bank transfer, source deletion or renewed invoice eligibility is implied.
