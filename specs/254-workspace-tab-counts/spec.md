# Feature Specification: Work counts on workspace tabs

**Feature Branch**: `254-workspace-tab-counts`
**Language**: English
**Created**: 2026-09-23
**Status**: Approved
**Input**: On every main page, a person should see at a glance which tabs hold open work, without clicking each tab and without a performance cost.

## Context and Intent
### Problem
A tab shows a number only while it is open: the active register portals its own list total into its tab (spec 225 FR-013, `PageRecordCount`). From Commitments nobody sees that Exceptions or Decisions hold work, and from Customer orders nobody sees open Commitments. Spec 253 lifted this for the pending-decision queue only.
### Principle
Two kinds of numbers answer two questions:
- A **work count** answers "do I need to go there?" It names a queue that should trend to zero in normal operation (open commitments, open findings, pending decisions, outstanding open items). It is always visible, on inactive tabs too.
- A **stock count** answers "how many exist?" (customers, locations, movements, all orders). It stays on the active tab only, as today.
A tab earns an always-visible count only if that count should trend to zero. Showing every total would make 312 customers look as urgent as 14 exceptions.
### Scope
Classify every tab of every main page; give work tabs an always-visible count read with the same query their register pages, one row wide.
### Non-Goals
No counts on stock tabs, Inspector, Analytics, Integrations or Settings. No new status fields on documents (Hard rule 2): "open orders" is not introduced as a document status. No push channel. No change to what a register lists.

## Inventory (measured 2026-09-23, local docker stack, two largest tenants, warm, one row wide)

| Page | Tab | Kind | Count it would show | Read it reuses | Cost |
|---|---|---|---|---|---|
| Inbox | Welcome | — | none | — | — |
| Inbox | Commitments | work | open customer-side commitments (the tab's default view) | `delivery_work(status=open, customer_delivery, size=1)` | 60–73 ms |
| Inbox | Exceptions | work | open findings | `attention_register(size=1)` (stored exceptions, spec 180) | 59–75 ms |
| Inbox | Decisions | work | pending decisions | `change_proposal_count(pending)` | ~1 ms (done in spec 253) |
| Sales / Purchasing | Customer / Supplier orders | stock | none (no document status by Hard rule 2) | `documents` | — |
| Sales / Purchasing | Commitments | work | open commitments of that direction | `delivery_work(status=open, type, size=1)` | ≤ 73 ms |
| Sales / Purchasing | Shipments | stock | none (recorded shipments have no open state) | `shipments` | — |
| Warehouse | Stock | work signal (warning) | overallocated items (`state=shortage`); badge only when > 0 | `warehouse_register(stock, state=shortage)` | 6–8 ms |
| Warehouse | Reservations | stock | none (an active reservation is not a task) | — | 3 ms |
| Warehouse | Movements | stock | none | — | — |
| Finance | Open items | work | outstanding receivables (the tab's default view) | `OPEN_FINANCIAL_ITEMS` projection page | 7–13 ms |
| Finance | Payments, Journal, Balances, Settings | stock | none | — | — |
| Master data | Customers, Suppliers, Items, Locations | stock | none | — | — |
| Analytics, Integrations, Reality Inspector, Settings | all | stock | none | — | — |

Overdue open items (the sharper signal) cost 400–450 ms and are not proposed for a tab count.
The Inbox Welcome dashboard derives exceptions live (`exception_page`, 1.1–1.5 s) and reported 1,458 where the register's stored rows reported 1,469 on the same tenant; that mismatch is a separate finding, not solved here.

## User Scenarios & Testing
### User Story 1 — See where work waits (P1)
On any main page, a person sees the open work behind every work tab, and no numbers on stock tabs.
Acceptance: on Inbox · Commitments, the Exceptions and Decisions tabs show their counts; on Sales · Customer orders, the Commitments tab shows open sales commitments; on Warehouse · Movements, Stock warns about overallocated items; on Finance · Payments, Open items shows outstanding receivables; clicking a tab lists exactly the number its badge showed (same filter, same query); a zero shows no badge; above 99 reads 99+; Master data tabs show no counts on inactive tabs.

## Requirements
- **FR-001**: Each work tab listed in the inventory shows its count while inactive, in the existing header count style; stock tabs keep the active-register-only count. The open tab shows only its own register count.
- **FR-002**: A work tab's count uses the same endpoint and filters as its register's default view, so the number after the click equals the number before it (up to intervening changes). The one exception is Warehouse · Stock, whose tab opens every item: its count is a warning signal (overallocated items), shown in a warning tone and described as such.
- **FR-003**: Counts are read from the existing register endpoints with a page size of one; no new endpoint, service or counting rule is added. A count is not read while its own tab is open.
- **FR-004**: Counts refresh like spec 253: on company change, when the tab is shown again, at most once a minute while visible, and after writes in this browser. Hidden tabs do not read.
- **FR-005**: A failing or slow count never blocks the page; the badge stays at its last value or is absent.
- **FR-006**: Zero shows nothing; above 99 reads 99+. The tab's accessible description states the count.
- **FR-007**: The sidebar keeps a single badge (Inbox, spec 253); workspaces carry no sidebar badge.
- **FR-008**: The Inbox orders its queues by who must act: Welcome, Decisions, Exceptions, Commitments; the Welcome tiles follow the same order. While decisions wait, the Decisions count carries the sidebar badge's accent on the tab (inactive and open) and the Welcome tile shows its number in the accent with "waiting for you"; at zero it looks like the other tiles. Exceptions and Commitments stay neutral.
- **FR-009**: Welcome leads with the queue tiles, followed by the activity graph. The graph's header carries its title, a "Live" indicator and its resolution on the left and the period control on the right. Readiness is not shown while everything is ready and appears as a caution notice above the tiles when it is not. The page heading "Your company, in motion", its subtitle and the "View all activity" button are removed; full history remains in Reality Inspector · Activities.

## Decisions (owner, 2026-09-23)
1. Warehouse · Stock shows the overallocation warning count.
2. Finance · Open items counts outstanding items (not overdue).
3. No sidebar badges for Sales, Purchasing, Warehouse or Finance.
4. The dashboard's live exception total is fixed separately (moved to the stored rows in its own pull request).
5. Decisions are the most important Inbox queue: they come right after Welcome and carry the accent (owner, 2026-09-23).
6. Welcome is decluttered as in FR-009 (owner, 2026-09-23).

## Assumptions and Dependencies
Builds on spec 253 (Inbox decision badge, refresh rhythm, `reality:records-changed`; its hook is generalized to `useWorkCount`) and spec 180 (stored exceptions, ~2 min staleness accepted by the owner). Measurements are local; a large production tenant may differ, so FR-005 is mandatory.

## Success Criteria
A person can tell from any main page which neighbouring tabs hold open work. A page adds at most one one-row read per work tab per minute while visible: about 135 ms of server time per minute on the Inbox, under 75 ms elsewhere.

## Requirement Traceability
FR-001–009 → US1 → T002–T004. Verified by `apps/web/scripts/workspace-tab-counts-browser.mjs`, `apps/web/scripts/inbox-decision-badge-browser.mjs`, `apps/web/scripts/pending-decisions.test.mjs`, frontend build and i18n audit.
