# Review and analysis: Demo Data pays its orders

**Feature**: [spec.md](spec.md) · [plan.md](plan.md) · [tasks.md](tasks.md)
**Language**: English

## Analysis of 2026-09-10 (spec ↔ plan ↔ tasks)

| # | Finding | Severity | Resolution |
|---|---|---|---|
| A1 | Plan bounds the settlement scan to orders of the last 30 days; spec FR-018 did not state a window, so "never paid" orders would be rescanned forever. | Medium | Spec Assumptions now state the 30-day window and that a late payment is planned within it. |
| A2 | Plan lets connections created before this feature receive a settlement schedule on their next start; spec did not say so. | Low | Added to spec Assumptions. |
| A3 | Tasks T033–T035 confirm candidates through the spec 148 settlement flow in mode `allocate_credit`; this needs an unallocated `customer_payment` to count as an original credit. | Verified | `services/finance/settlement_flows.py` `CREDITS` maps `customer_payment` to the customer side and `credits.py` lists `customer_payment` documents; no new flow is required. |
| A4 | Invoice lines must carry `billed_document_line_id` through `create_manual_document_with_lines`. | Verified | The manual-line normaliser reads `billed_document_line_id` (core.py) and `demo_profile.py` already uses it. |
| A5 | The worktree producer already exposes a function named `plan` (orders per delivery); the spec's "planning function" must not collide. | Low | Plan and tasks name it `settlement_plan`. |
| A6 | Identities `{order external id}:invoice|payment:{n}` begin with the order schedule id, so the existing `_imports` join (`external_id LIKE schedule.id || ':%'` on `demo.generate_orders`) still attributes them to the connection. | Verified | `_imports` only needs the source-type filter generalised (T026). |
| A7 | FR-022 (contract amendment) has review evidence only, no executable test. | Accepted | Documentation requirement; `make spec-check` and PR review are its gate. |
| A8 | Spec 146 contract already lags the code ("at most one SourceRecord per occurrence" versus delivery bursts). | Medium | T042 rewrites the contract to current behaviour plus settlement records, not only adds payments. |

No CRITICAL finding. Coverage: every FR-001–FR-025 and DR-001–DR-007 has at least one test task and one implementation or documentation task (tasks.md Requirement Coverage).

## Branch condition

The branch was created from `165-unified-page-actions-polish` because it needed the spec 148
slices that were not on main at the time. Spec 165 reached main through a squash merge
(PR #189), so on 2026-09-11 the fifteen feature commits were rebased onto `origin/main`
(`12bfc4b`) with `git rebase --onto`, dropping the squashed base. Main had meanwhile taken
the number 167 for another feature, so the specification was renumbered to 168 in its
directory, every reference and the branch name (`168-demo-order-to-cash`); no pull request
existed yet, so nothing was closed by the rename. Never merge main into the branch.

## Approvals

- Product scope: owner decisions of 2026-09-10 recorded in spec Assumptions; spec text approval pending.
- Architecture/domain: Constitution Check PASS in plan.md; no exception.
- Pre-implementation: this analysis; implementation may begin with Phase 2 of tasks.md.

## Implementation review of 2026-09-10

| # | Topic | Decision |
|---|---|---|
| I1 | Candidate confirmation surface | The plan foresaw a new candidates route and MCP tool. The existing guided settlement context already lists matching invoices for an available credit and the Payments register already opens it for an unallocated payment, so the context gained `reasons`/`candidates` instead (FR-014, FR-015 satisfied with one read and one flow; tasks T033–T035 adapted). |
| I2 | Migration number | The plan named 0050; the checkout's head was `0054_target_mappings`, so the migration is `0055_demo_settlement_schedule`. |
| I3 | Payment term creation | `core.create_payment_term` committed unconditionally; it gained a `_commit` flag so connect can create the demo term inside its bound scope. |
| I4 | Interpretation references | `INTERPRETATION_RECORD_TYPES` gained `ledger_entry` and `settlement_allocation`; `_interpretation_references` flattens any interpreter result shape. Only the validation guard consumed the set. |
| I5 | Settlement scan bound | `settlement_work` loads only orders without an invoice, with an invoice but without a first payment, or received in the last 12 hours, all within 30 days, so the per-minute plan recomputation stays bounded at high rates. |
| I6 | Browser script (T038) | Deferred; needs the running local stack. Panel and dialog are covered by contract tests, the TypeScript build and the four-language audit. |
| I8 | Settlement batch bound | The live run at 300 orders per hour showed the ten-record bound saturating (five invoices plus five first payments per minute). Resolved on 2026-09-11: FR-018 and SC-005 now say 25 per occurrence, `SETTLEMENT_BATCH = 25`, tests exercise the bound with a patched batch of ten. |
| I9 | Sleep and stale claims | Overnight machine sleep produced one `stale_claim` failure per schedule and the shared scheduler disabled both; stop/start recovered. Pre-existing spec 147 semantics, recorded for the scheduler owners; not changed here. |
| I7 | Spec 146 contract drift | The contract's "at most one SourceRecord per occurrence" now describes delivery bursts and the settlement batch (T042). |
