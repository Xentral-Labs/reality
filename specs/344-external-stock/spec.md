# Feature Specification: External Stock Statements

**Feature Branch**: `344-external-stock`

**Created**: 2026-10-03

**Status**: Accepted

**Language**: English

**Input**: Journey J07 "3PL stock differs from own records — reconciliation difference visible?".
The owner asked for it after finding that the existing `inventory_snapshot` file import posts the
difference as an adjustment, so a difference never becomes visible. A 3PL report or a shop's stock
level must be compared, not taken over. It is also the building block a shop or ERP that is only
observed needs for stock.

## Clarifications

### Session 2026-10-03

The owner delegated these decisions to the recommended options.

- Q: Where is a statement kept? → A: In an append-only typed table, one row per item, location and
  stated time, with its source record and, where known, the business partner that reported it.
- Q: What is it compared with? → A: The stock Reality's movements hold at that location at the
  stated time (as of the statement, corrections left out as in spec 307), never stock now.
- Q: Which statement counts? → A: The latest stated per item and location; earlier ones stay as
  history.
- Q: How does a difference clear? → A: By a newer statement that matches, or by a reviewed stock
  count (spec 307) dated at the statement's time, or by the missing movement being recorded. Nothing
  is adjusted automatically.
- Q: Lots? → A: A statement is per item and location, compared with all lots together.
- Q: A row without a stated time? → A: It is stated as of the moment the file or statement arrived.
- Q: Web? → A: The finding appears in the existing exception surfaces with its values and trace;
  statements are read through the API, MCP and CLI. No new screen in this increment.
- Q: The existing `inventory_snapshot` import? → A: Unchanged; it takes over opening stock by
  posting adjustments. Its documentation now says so, next to the new statement that only compares.

## Context and Intent

### Problem

Stock reported from outside — a 3PL's stock report, a shop's stock level, an ERP that is only being
observed — can only be taken over today, which hides every difference. Reality cannot show that a
3PL reports 95 where its own movements hold 100.

### Scope

- Record an external stock statement per item and location, as stated, without moving stock.
- Two intake paths: a CSV file target `external_stock`, and a reviewed statement through MCP, CLI
  and the web API.
- A finding `external_stock_differs` with both quantities, the difference, the reporter and the time.
- A read of the latest statements with Reality's quantity at the same time and the difference.

### Non-Goals

- Taking over stock from a statement; adjustments stay a person's reviewed decision (spec 307).
- Live connectors to 3PLs or shops.
- Per-lot comparison.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A 3PL's report differs from Reality (Priority: P1)

As a warehouse lead using a 3PL, I see where the 3PL's stock report differs from what Reality's
movements hold, and I decide how to resolve it.

**Independent Test**: The J07 business story.

**Acceptance Scenarios**:

1. **Given** Reality holds 100 at the 3PL location, **When** the 3PL states 95, **Then** a finding
   names 95 stated, 100 held and a difference of −5; **When** the 3PL states 100, **Then** there is
   no finding.
2. **Given** the finding, **When** a person confirms a stock count dated at the statement's time,
   **Then** the finding clears and the count's adjustment is the only change to stock.
3. **Given** a statement that matches, **Then** no finding; **Given** a later statement that
   differs, **Then** the finding names the later one.

### Edge Cases

- A statement in the future, a negative quantity, an unknown item or location, or a location that
  holds no stock is refused.
- A statement for another company's item is not visible.
- A movement recorded later but dated before the statement changes Reality's side of the
  comparison; a movement after it does not.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: An external stock statement MUST be recorded as stated per item, location and stated
  time, with its source record, and MUST NOT move stock.
- **FR-002**: Statements MUST be accepted from a CSV file target `external_stock` and from a reviewed
  statement shared by Web API, MCP and CLI.
- **FR-003**: The latest statement per item and location MUST be compared at read time with the
  stock Reality's movements hold at the stated time; a difference MUST be reported as
  `external_stock_differs` with both quantities, the difference, the reporter and the time.
- **FR-004**: The difference MUST clear only through a newer matching statement or recorded
  movements (including a reviewed stock count) that make the stock at the stated time match.
- **FR-005**: J07 MUST be proven by a business story and promoted in the Business Journey Guide.

### Domain and Architecture Requirements

- **DR-001**: A new table `external_stock_statement` is justified in the plan (Constitution III).
- **DR-002**: The difference is derived at read time and never stored.

## Success Criteria *(mandatory)*

- **SC-001**: J07 is `supported`, and no statement path creates a movement.
- **SC-002**: Deriving the finding reads all latest statements with a bounded number of queries.

## Assumptions and Dependencies

- Builds on the stock count of spec 307 (`stock_counts.book_as_of` semantics and the reviewed count
  as the way to take a difference over) and on the file interpreters of source ingestion.
- Live connectors that deliver statements (3PL, Shopify, Xentral) are separate work; they use the
  same statement once they exist.

## Requirement Traceability

| Requirement | Evidence |
|---|---|
| FR-001, FR-003, DR-002, SC-001, SC-002 | `tests/test_external_stock.py` |
| FR-002 | `tests/test_external_stock.py`, `tests/test_external_stock_adapters.py` |
| FR-004 | `tests/test_external_stock.py`, J07 story |
| FR-005 | `tests/scenarios/test_catalog_external_stock.py` |
