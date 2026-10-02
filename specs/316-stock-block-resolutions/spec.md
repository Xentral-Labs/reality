# Feature Specification: Stock Blocks Keep What Was Stated

**Feature Branch**: `316-stock-block-resolutions`

**Created**: 2026-10-02

**Status**: Implemented

**Language**: English

**Input**: Owner review of the tables added since 2026-09-29: `stock_block` (spec 304) is the one new table that rewrites a stated value and stores a derived state, against Constitution VIII, AGENTS.md rule 11 and spec 304's own DR-002.

## Context and Intent

### Problem

Spec 304 records a stock block as one row with a mutable lifecycle:

- A partial release or scrap **overwrites the block's stated quantity** with the resolved part and continues the rest as a new row (`previous_block_id`). After "block 20, release 5", no row says 20 any more; what the clerk stated is only recoverable by walking the chain.
- `status` (`active`, `released`, `scrapped`) is stored although it follows from what happened to the block. A block that is partly released and partly scrapped becomes several rows, each with one status, instead of one statement with two outcomes.
- `movement_id` means two different things: the receipt that stated the block, or the adjustment that scrapped it. A correction guard (`movement_correction_scrap_block`) has to combine it with `status` to know which.
- One block id per statement is lost: a release returns a `remainder_block_id`, so links, events and the web card follow a different id after every partial resolution.

This is the split-and-rewrite pattern of a classic ERP stock record, not the Source → Evidence → Reality model where a statement stays as made and what happened afterwards is recorded beside it.

### Scope

- A stock block keeps the quantity, reason and identity as stated, unchanged for its lifetime, under one id.
- Each release or scrap is recorded as its own resolution of that block, with its quantity, reason, who and when; a scrap resolution names its adjustment movement.
- What is still blocked, and whether a block is still open, is derived at read time: stated quantity less the resolved quantities.
- The block names the receipt movement that stated it, separately from any scrap adjustment.
- Existing blocks and their split chains are migrated losslessly into this shape.
- Every reader that subtracts blocked stock keeps one shared rule, now "open quantity" instead of "active rows".

### Non-Goals

- Changing what can be blocked, the reasons, the review/confirmation flow, or the availability rule of spec 304 (physical − reserved − blocked).
- Changing `reservation`, which follows the same split pattern. Measured and declined in [spec 317](../317-reservation-resolutions/spec.md): deriving its open state makes company-wide reads about 1,500× more expensive.
- Releasing or scrapping across several blocks in one action.
- Undoing a resolution. A wrong release is followed by a new block; a wrong scrap by recording the goods again, as spec 304 states.
- Any document status field (Constitution II).

## Clarifications

### Session 2026-10-02

- Q: Where do releases and scraps live? → A: In their own record per resolution, pointing at the block (shortest true link: resolution → block). The block row is never updated after it is created.
- Q: Which list filters remain? → A: `active` (open quantity > 0, the default), `resolved` (open quantity = 0) and `all`. `released` and `scrapped` are dropped as filters, because one block may now have both outcomes; each block shows its resolutions instead. *(Accepted by the owner 2026-10-02.)*
- Q: What happens to existing split chains? → A: Each chain folds into its first block. That block's quantity becomes the sum of the chain, which is what the clerk stated; every closed row of the chain becomes one resolution with its own quantity, reason, who and when, and scrap movement. The continuation rows are removed. Event history keeps its old ids. *(Accepted by the owner 2026-10-02.)*

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The block says what was blocked (Priority: P1)

As a warehouse clerk I block 20 for quality. Quality releases 5 on Tuesday and 3 are scrapped on Friday. When I open the block, it still says 20 blocked for quality, lists both outcomes, and shows 12 still blocked.

**Why this priority**: It is the defect: today the block reads 5, and the 20 the clerk stated exists nowhere.

**Independent Test**: Service and adapter tests through the reviewed tools; the business stories B05, H08, H15, J05 keep passing unchanged in outcome.

**Acceptance Scenarios**:

1. **Given** 20 in stock and 20 blocked, **When** 5 are released, **Then** the block still states 20, has one release of 5 with its reason, shows 15 open, and 5 are available.
2. **Given** that block, **When** 3 are scrapped, **Then** the block still states 20, has a release of 5 and a scrap of 3 naming its adjustment, shows 12 open, and physical stock is 17.
3. **Given** that block, **When** the remaining 12 are released, **Then** it shows 0 open, appears under `resolved` and no longer under `active`, and keeps its id throughout.
4. **Given** a receipt of 20 with 5 blocked for damage, **When** the block is read, **Then** it names that receipt movement, and a later scrap names its own adjustment separately.

### User Story 2 - Nothing else changes for availability (Priority: P1)

As anyone reserving, shipping, transferring or reading availability, I see exactly the numbers spec 304 gives today.

**Independent Test**: The existing spec 304 reader tests, plus one test per reader comparing blocked quantity before and after a partial release and a partial scrap.

**Acceptance Scenarios**:

1. **Given** the US1 sequence, **When** each availability reader runs after each step, **Then** it subtracts 20, 15, 12 and 0 in turn, at the location and at the blocked identity.
2. **Given** a scrap of a block that a receipt stated, **When** that receipt is corrected, **Then** the correction is refused as today.

### User Story 3 - Existing blocks survive the change (Priority: P2)

As an owner whose company already uses blocks, I find every block with the quantity it was stated with and every release and scrap that happened to it.

**Independent Test**: A migration test seeded with a chain (block 20, release 5, scrap 3, open 12) and a whole release, asserting the folded result and that downgrade refuses when it cannot restore.

**Acceptance Scenarios**:

1. **Given** a chain of three rows from spec 304, **When** migrated, **Then** one block states 20 with one release of 5 and one scrap of 3 naming the original adjustment, and 12 are open.
2. **Given** migrated data, **When** availability is read, **Then** every number equals the number before the migration.

### Edge Cases

- Tenant isolation: a resolution belongs to the block's company; nothing crosses companies.
- Releasing or scrapping more than the open quantity is refused; two confirmations racing for the same open quantity cannot both succeed.
- A review carries the open quantity it saw; a confirmation after the block changed is refused, as today.
- A resolution of 0 or below, or without a reason, is refused.
- A block whose open quantity reaches 0 stays readable with its full history.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A stock block's stated quantity, reason, note, identity and creator MUST NOT change after it is created, and the block MUST keep one id for its lifetime.
- **FR-002**: Every release and every scrap MUST be recorded as its own resolution of the block with quantity, reason, who and when; a scrap resolution MUST name the adjustment movement it recorded.
- **FR-003**: A block's open quantity MUST be its stated quantity less its resolutions, read at read time; whether it is open MUST be derived from that and never stored.
- **FR-004**: Every reader that subtracts blocked stock MUST use the open quantity through one shared rule, and MUST return the same availability as spec 304 for the same history.
- **FR-005**: The block MUST name the receipt movement that stated it separately from any scrap adjustment.
- **FR-006**: Block reads (web, MCP, CLI) MUST show the stated quantity, the open quantity and the resolutions; list filters MUST be `active`, `resolved` and `all`.
- **FR-007**: Release and scrap results and events MUST refer to the same block id and MUST NOT introduce a remainder block.
- **FR-008**: Existing blocks MUST be migrated losslessly as described in Clarifications, and availability MUST be unchanged by the migration.

### Domain and Architecture Requirements

- **DR-001**: The block row MUST NOT be updated after insert; resolutions MUST be append-only.
- **DR-002**: No column MAY store a lifecycle state that follows from the resolutions (no `status`, `resolved_*`, `previous_block_id`).
- **DR-003**: The change MUST net-shrink the block's typed state: the plan MUST show the column count before and after.
- **DR-004**: Mutations MUST stay on the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After any sequence of partial releases and scraps, the block shows the quantity the clerk stated and one id.
- **SC-002**: Every spec 304 test and business story (B05, H08, H15, J05) passes with unchanged availability numbers.
- **SC-003**: No query anywhere filters stock blocks by a stored status.

## Assumptions and Dependencies

- Builds on spec 304 (merged as #275 on 2026-10-02); its availability rule, reasons and review flow are unchanged.
- Blocks are few per item and location, so deriving the open quantity from resolutions at read time costs no measurable latency; the plan confirms this against the availability readers listed in spec 304's notes.
- Tool output and MCP schema change (`status` enum, `remainder_block_id`), so the Tool Usage docs are regenerated.

## Open Questions

None. Both proposed clarifications were accepted by the owner on 2026-10-02.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, FR-002, FR-003, FR-007, DR-001, DR-002 | US1 1–3 | `tests/test_stock_blocks.py` |
| FR-004, SC-002, SC-003 | US2 1 | `tests/test_stock_block_readers.py`; stories B05, H08, H15, J05 in `tests/scenarios/test_catalog_stock_and_returns.py` |
| FR-005 | US1 4, US2 2 | `tests/test_stock_blocks.py` |
| FR-006, DR-004 | US1 1–3 | `tests/test_stock_block_adapters.py`; web build, format and i18n checks (no browser script covers the block card, as in spec 304) |
| FR-008 | US3 1–2 | `tests/test_stock_blocks.py::test_the_migration_folds_split_blocks_into_what_was_stated` |
| DR-003 | All | plan data model |
