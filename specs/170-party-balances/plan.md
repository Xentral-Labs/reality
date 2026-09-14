# Implementation Plan: Party balances

**Branch**: `170-party-balances` | **Date**: 2026-09-11 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Add one read-time aggregation, `party_balances`, that groups what the open items derivation and
the credit derivation already produce by party and currency, and expose it three ways: a Finance
register "Balances" in the unified App with drill-down into the party's open items and credits,
a public agent read `finance_party_balances`, and two playbook steps that name it. No schema, no
new rule: overdue is the open items' original due date against the read's instant, exactly as the
`overdue_*` classes judge it.

## Technical Context

**Language/Version**: Python 3.12+, TypeScript (React, VitePress) · **Primary Dependencies**:
unchanged · **Storage**: no schema change · **Testing**: pytest service and tool tests, node
routing tests, the Finance Playwright suite, docs build · **Scale/Scope**: one service module, one
API flow plus a party filter, one App register, one MCP read, two playbooks.

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | The view derives from ledger entries, allocations and documents; it records nothing and emits no event. | PASS |
| Reality owns operational state | No stored balance; every read recomputes from the same derivations the registers use. | PASS |
| Proven schema only | No schema change; a `party_id` query filter reuses existing columns. | PASS |
| Tenant + shared service boundaries | The service takes `tenant_id` and calls tenant-scoped derivations; the tool runs the same service; the isolation catalog lists the operation. | PASS |
| Spec/test traceability | Each FR maps to a service, catalog, routing or browser test below. | PASS |
| Explainable web behavior | Every row drills down into the exact documents that were summed. | PASS |
| Received values not recomputed | Amounts are summed, never divided or re-priced; the AST guard against division stays untouched. | PASS |
| Smallest coherent design | One aggregation over two existing derivations; no new projection table, no cache. | PASS |

## Design

### Service

- New module `services/finance/balances.py` with
  `party_balances(session, tenant_id, *, side, credit_only=False, query="", page=1, size=50, sort="balance", sort_direction="desc", as_of=None) -> {items, totals, page}`.
- Open side: `core.aging_register(session, tenant_id, as_of=as_of)` (the open items rows
  enriched with the one due-date rule) filtered to the side's control account and
  `status in {open, partial}`; per row add `open` to the party and currency bucket, add to
  `overdue` when `due_date` is before `as_of.date()` (the condition of `_open_item_exceptions`),
  count the document, track the minimum due date.
- Credit side: refactor `available_credit_items` into an unpaged core `available_credit_rows(session,
  tenant_id, *, side, status)` plus the existing paging wrapper, so the aggregation reuses the
  identical row set (FR-002) instead of a second query. Per row add `available` to the bucket and
  count it.
- Row: `party_id`, `party`, `currency`, `open`, `overdue`, `credit`, `balance = open - credit`,
  `open_count`, `credit_count`, `oldest_due_date`. Drop rows with `open == 0 and credit == 0`.
  `credit_only` keeps rows with `credit > 0`. `query` matches the party name.
- Sorting keys: `party`, `open`, `overdue`, `credit`, `balance`, `oldest_due`; paging with the
  same helper `available_credit_items` uses today; totals per currency over all rows before
  paging.
- Decimal arithmetic only; amounts are returned as strings like the other registers.

### API and App

- `web/api.py::tenant_open_items`: new `flow` values `customer-balances` and `supplier-balances`
  routed to the service; new optional `party_id` query parameter applied to the open items rows
  and to `available_credit_items` (the drill-down filter, FR-007). `as_of` is the request instant.
- `unified/routing.ts`: `financeView` gains `"balances"`; a `party_id` selection field travels in
  the URL so the open items and credit flows can be opened pre-filtered.
- `unified/FinancePage.tsx`: tab "Balances" with a side selector (Customers, Suppliers), the
  register search, a "Credit only" checkbox, and a `RegisterTable` profile `balances` with
  right-aligned numeric columns and sortable headers. Each row offers "Open items" and "Credits"
  actions that navigate to the existing flows with `party_id` set.
- `api.ts`: `partyBalances(tenant, side, q, creditOnly, page, table)`; `openItems` gains an
  optional `partyId`.
- `localization.tsx`: labels "Balances", "Customers", "Suppliers", "Credit only", "Balance",
  "Of which overdue", "Oldest due", "Open documents", "Credits" in de, nl, es; the i18n audit
  must pass.

### Agent read

- `tools/application.py`: `TOOLS["finance.party_balances.list"]` calling the service with
  `side`, `credit_only`, `query`, `limit`.
- `mcp/catalog.py`: `MCPToolDefinition("finance_party_balances", "Party balances", …, "read",
  "finance", schema `{side (enum customer|supplier, required), credit_only, query, limit}`)`.
- `config/command_catalog.yaml`: `capability_guidance.finance_party_balances` with `use_when`
  (who owes the most, who holds credit, a party's position before a call), `do_not_use_when`
  (deciding that a credit may be netted, judging creditworthiness, converting currencies),
  `verification` (the drill-down documents are the proof), examples with reasons.
- `config/tenant_isolation_catalog.yaml`: `tool:finance.party_balances.list` in the
  `agent_credit_reads` family (description widened to balances); count assertions in
  `tests/test_application_catalog.py` follow.
- Docs catalogs: one row added by hand to `content/catalogs/mcp-tools.md` (en, de) as in #192,
  because regenerating drifts unrelated tables.

### Docs

- Receivables playbook, situation "Overpayment", step "Ask": "Who paid too much?" reads
  `finance_party_balances` with `credit_only`; situation "Watch the money" names it. Purchasing
  playbook "Watch the supply side" names the supplier side. English and German, with the agreed
  German vocabulary (Saldenliste, Geschäftspartner, Minderzahlung).
- `docs/features/finance.md` (or the existing finance feature doc) gains a short section on the
  derivation and its limits.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001, FR-002, FR-004, FR-005 | service | `tests/finance/test_party_balances.py::test_party_rows_sum_open_items_and_credits` (three invoices, one overpayment, one credit note; a second customer with nothing open) | module missing |
| FR-003 | service | `::test_overdue_follows_original_due_date_and_as_of` | overdue 0 |
| FR-002 (credit refactor) | service | existing `tests/finance/test_available_credits.py` and `test_credit_reads.py` stay green | none |
| FR-006 | web routing | `apps/web/scripts/finance-settings-routing.test.mjs` sibling: `balances` view and `party_id` round-trip through the URL | view rejected |
| FR-006, FR-007, DR-004 | browser | `apps/web/scripts/unified-finance-browser.mjs` section: open Balances, sort by balance and overdue, open a row's open items and assert only that party's rows | tab missing |
| FR-008 | tool + catalog | `::test_tool_matches_view_and_is_tenant_scoped`; `tests/test_application_catalog.py` counts; `tests/test_capability_guidance.py` | tool unknown |
| FR-009, SC-004 | docs | `npm test`, `npm run build` in `apps/docs` | none |
| DR-001–DR-003 | review | no migration in the diff; AST division guard unchanged | none |

## Rollout and Rollback

Code and docs only; deploy the API and web images. Rollback: revert the commit; no data to
migrate back.

## Review Risks

- Refactoring `available_credit_items` into rows plus paging must keep its output byte-identical;
  the existing credit tests are the guard.
- Performance: both derivations are full scans per tenant, as the registers already are; the
  aggregation adds one pass. Acceptable at current tenant sizes; if a large-tenant benchmark shows
  otherwise, the fix is a shared cached derivation, not a stored balance.
- "Overdue" follows the aging register's due date (payment term, or the stated date of an
  opening item); a due date revised elsewhere is not known to the register, matching the
  exception classes. Stated in the spec.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
