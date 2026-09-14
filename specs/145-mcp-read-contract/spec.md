# Feature Specification: Seven MCP Read Improvements

**Feature Branch**: `145-mcp-read-contract`
**Created**: 2026-09-08
**Status**: Implemented and verified locally after seven owner-approved decisions; see [verification.md](verification.md).
**Language**: English

## Context and Intent

### Problem
Agents can mix currencies, fail to discover postings, lose closed-order context, mistake tenant-wide stock for local availability, or treat truncated results and unspecified units/freshness as complete evidence.

### Scope
Implement precisely the seven owner decisions: currency-separated balances; ledger discovery repair; explicit units without conversion; item/location inventory and optional filter; retained open/fulfilled/cancelled order explanation; complete paginated traversal; explicit scope/freshness/persistence. Reuse existing business services on main `2183b88`.

### Non-Goals
No demo seeding, new financial metrics, period analytics, historical point-in-time reconstruction, source completeness guarantee, currency/unit conversion, new business tables, automatic transfers, mutation changes, deployment or merge. Existing authentication telemetry remains allowed.

### Existing Contracts
[Constitution](../../.specify/memory/constitution.md), [workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md), [inventory](../../docs/features/inventory.md), [explain](../../docs/features/explain.md), [ledger](../../docs/features/ledger.md), [chat](../../docs/features/chat.md).

## User Scenarios & Testing

### User Story 1 - Read money and reference evidence correctly (Priority: P1)
An agent reads all represented balance currencies separately and discovers retained ledger entries without losing debit/credit direction.

**Independent Test**: Balanced EUR and USD postings and a foreign tenant produce separate correct amounts; discovery returns posting directions; an empty tenant has no invented EUR balance.

**Acceptance Scenarios**:
1. Given EUR and USD receivable/payable postings, reading balances yields one row per represented currency, with no conversion or combined amount.
2. Given non-empty ledger records, discovery returns their opaque IDs and debit/credit direction, including through more than one page; no foreign records appear.

### User Story 2 - Explain location and retained orders (Priority: P1)
An agent sees the real unit and local availability and follows an order after fulfilment or cancellation.

**Independent Test**: Stock at B does not supply A; a partially reserved then fulfilled/cancelled order retains source, lines, commitments and effects.

**Acceptance Scenarios**:
1. Given the same item at two locations, inventory exposes physical/reserved/available per location and an optional exact location filter; aggregate mode is labelled across locations.
2. Given units absent or different between a line and item, reads expose actual units and unknown/mismatch status without conversion. Supply, commitments and fulfilment quantities identify their item quantity basis.
3. Given open, fulfilled, cancelled or mixed-status order commitments, explanation by opaque order ID exposes retained records and source; closed quantities are not presented as executable demand. Duplicate human numbers are refused as ambiguous, never chosen as identity.

### User Story 3 - Read complete, attributable pages (Priority: P1)
An agent follows pages to an explicit end and understands their scope and freshness without causing projection writes.

**Independent Test**: Traverse over 100 records with filters and no duplicates in unchanged data; reject invalid/foreign/filter-mismatched cursors; intercept SQL writes during diagnostics.

**Acceptance Scenarios**:
1. Given more matching records than the limit, each response contains records, continuation token and has_more; final and empty pages explicitly terminate. Exact totals are optional.
2. Given a cursor reused for a different tenant, tool or filter, reject it without disclosure. Live keyset traversal documents insert/update/delete behavior and does not claim snapshot isolation.
3. Given a stale projection cache, new page-mode reads return directly derived current retained values without cache writes or commits, with tenant/filter/observation metadata and honest unknown upstream freshness.
4. Given an existing internal application list consumer or explicit legacy-format client, its list contract remains usable; default public MCP responses use the documented page envelope. Finance never recreates the defective false-EUR response.

## Requirements

- **FR-001**: `finance_balances` MUST return all currencies represented in receivable/payable postings separately, preserving signed receivables and credit-normal payables. No conversion, cross-currency total or mandatory currency selection; an empty result is empty.
- **FR-002**: Ledger discovery MUST read mapped `debit_credit`, with an explicitly documented `side` compatibility alias; no field-access failure on retained postings.
- **FR-003**: Affected quantity reads MUST expose actual item/line units, explicitly unknown units and mismatches where both bases appear, without conversion. Promise quantities/dates MUST distinguish original from effective revisions.
- **FR-004**: Inventory MUST support item-by-location rows and exact optional item/location filters, retain a labelled aggregate mode and include zero stock at a specifically requested location. Location stock MUST use shared authoritative stock/reservation calculations; no new warehouse allocation policy.
- **FR-005**: `order_explain` MUST resolve retained open/fulfilled/cancelled orders by opaque document or commitment ID, expose document lines, commitments, reservations, movements and original source when present, and avoid a current-queue dependency. Legacy human references MUST fail when ambiguous. No historical snapshot is asserted.
- **FR-006**: Public MCP discovery, inventory, commitments, fulfilment queue/blockers and supply/demand MUST default to bounded page envelopes with stable ordering, `next_cursor`, `has_more`, limit 1–100 and explicit retained-record completeness. Cursors MUST be validated against tenant/read/filter/order scope. Exact total counts are not required. Concurrent mutation semantics MUST be documented as live keyset, not an atomic snapshot.
- **FR-007**: Affected responses MUST identify tenant, applied filters and UTC observation time; known derivation version/event sequence MUST be distinguished from unknown source freshness and unavailable snapshot guarantees.
- **FR-008**: New diagnostic page reads and retained-order explanation MUST cause no business/cache writes or commits; existing legacy cache refresh and normal token access telemetry MUST be documented. No fully write-free authenticated transport is promised.
- **FR-009**: Existing internal list consumers MUST remain compatible. A documented explicit `response_format=legacy` allows affected MCP list clients to migrate; page is public MCP default. Finance's new currency envelope is a deliberate correction with no false-EUR fallback. Update tool guidance and generated public reference.

### Domain and Traceability Requirements

- **DR-001**: Preserve Source → Evidence → Reality and shortest opaque links; never introduce document fulfilment status fields or business tables.
- **DR-002**: Every query and reference validation MUST remain tenant-scoped and all adapters MUST use shared application services; no direct writes or independent adapter business math.
- **DR-003**: Use Decimal and UTC; received evidence prices/totals remain unchanged. Derived balances, stock and metadata are read-time observations only.

## Success Criteria

- **SC-001**: All seven decisions map to passing service/adapter regressions; cross-tenant reads disclose nothing.
- **SC-002**: More than 100 unchanged matching records traverse exactly once to a clear end, with no guessed units/currency/freshness.
- **SC-003**: Open and closed orders retain explainability and wrong-location stock cannot appear locally available.
- **SC-004**: New diagnostics issue no business/projection writes; backend, migration, spec, frontend and docs required checks pass before completion.

## Assumptions and Dependencies

The user individually accepted all seven choices and explicitly requested implementation. Feature 144 in current main now belongs to integrations; this implementation is isolated as 145, preserving the broader Atlas decision draft in the original checkout. No further product/schema decision is needed. Supported diagnostics cover the seven named reads plus finance/order detail; other MCP reads retain existing contracts. Live keyset pages guarantee complete traversal for unchanged matching records; inserts before the cursor or changes to matching rows require a fresh traversal for reproducible analysis. Source freshness remains unknown even when a local event sequence is known.

## Requirement Traceability

| Requirement | Scenario | Planned evidence |
|---|---|---|
| FR-001 FR-002 | US1 | test_mcp_read_contract.py currency/discovery regressions |
| FR-003 FR-004 | US2-1/2 | test_mcp_read_contract.py units/location/revision cases |
| FR-005 | US2-3 | test_mcp_read_contract.py retained orders, mixed states and ambiguity |
| FR-006 FR-007 | US3-1/2/3 | test_mcp_read_contract.py traversal, cursors and metadata |
| FR-008 FR-009 | US3-3/4 | SQL interception, MCP server defaults, legacy consumer regressions, generated docs |
| DR-001 DR-002 DR-003 | All | Provenance, tenant, Decimal and no-write tests; schema/diff review |
