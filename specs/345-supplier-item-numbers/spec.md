# Feature Specification: Supplier Item Numbers

**Feature Branch**: `345-supplier-item-numbers`

**Created**: 2026-10-03

**Status**: Approved

**Language**: English

**Input**: The owner chose five small, valuable gaps to close ("ja mach die fünf plus M07 bis grün"). This one closes journey O06: a supplier's own item number differs from ours, and several suppliers use different numbers for the same item.

## Context and Intent

### Problem

Suppliers confirm, deliver and invoice by their own article numbers. Reality records customer item numbers (spec 308) but not supplier item numbers, so a purchase line or a supplier invoice line that quotes the supplier's number cannot be resolved to our item, and the number the supplier uses is not kept.

| Journey | Title | Status today |
|---|---|---|
| O06 | Supplier item number ≠ own number, several suppliers | gap |

### Scope

- A supplier item number, with the supplier's name for it, per supplier and item. One number names exactly one item at that supplier; an item may have several numbers there, and each supplier has its own.
- Purchase order and supplier invoice/credit note entry (Web, MCP/chat, CLI) accepts the supplier's number instead of our item, and the line keeps it as stated.
- The purchase order and supplier invoice previews and the three-way purchase match show the number.
- The supplier's numbers are listed and maintained on the supplier.

### Non-Goals

- Interpreting documents from a supplier's own system (EDI, order confirmations by file); see spec 311.
- Supplier prices from the number mapping (supplier terms are spec 310).
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-03

The owner delegated these decisions to the recommended options.

- Q: How is the mapping kept? → A: Like customer item numbers (spec 308): its own table per supplier, one number names one item at a supplier, with the supplier's name; stated and changed through the review; every statement kept as a version of one source stream (spec 320 pattern).
- Q: Which lines resolve by the supplier's number? → A: Lines of purchase orders, supplier invoices and supplier credit notes entered by hand, chat/MCP or CLI. A sales line never reads a supplier number.
- Q: What happens to an unknown or conflicting number at entry? → A: It is refused with its own code, as spec 308 refuses an unknown customer number at manual entry. There is no supplier file import to keep unknown lines from yet.
- Q: Where does the number appear? → A: On the line as stated, never recomputed; in the purchase order and supplier invoice preview with the supplier's current name for it, and in the three-way purchase match.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Order and invoice by the supplier's number (Priority: P1)

As a buyer, I enter a purchase order by the supplier's own article number, and the supplier's invoice quoting the same number matches.

**Why this priority**: B2B purchasing works with supplier numbers every day; without them every line needs a manual lookup.

**Independent Test**: Business story O06 through reviewed tools, with a positive control.

**Acceptance Scenarios**:

1. **Given** "LF900-12 → our wheel" at Lindner and "VI-77 → our wheel" at Velo Import, **When** each is ordered from by its own number, **Then** both lines resolve to our wheel and keep the number as stated.
2. **Given** Lindner's delivery and its invoice quoting LF900-12 against the order line, **When** the three-way match is read, **Then** the line is matched and shows the number.
3. **Given** VI-77, **When** it is quoted on an order to Lindner, **Then** it is refused as unknown at that supplier.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII): the number stays on the line even after the mapping changes or is removed.
- Numbers match case- and space-insensitively within one supplier; one number cannot name two items at the same supplier.
- A line that states both our item and a supplier number keeps our item, and the number is checked against the mapping.
- A correction that does not restate the number keeps it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A supplier MAY have supplier item numbers, each naming one item at that supplier with the supplier's name for it, stated and changed through the review.
- **FR-002**: Purchase order, supplier invoice and supplier credit note entry MUST resolve a line by its supplier item number; an unknown or conflicting number MUST be refused with its own code.
- **FR-003**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-004**: When O06 is proven by a business story, the Business Journey Guide MUST promote it with executable evidence.
- **FR-005**: The stated number MUST stay on the line and be shown on the purchase order and supplier invoice previews and in the three-way purchase match.

### Domain and Architecture Requirements

- **DR-001**: The new table is justified in the plan (Constitution III): lines are filtered and resolved by the number repeatedly.
- **DR-002**: Derived states are read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O06 has a passing business story.
- **SC-002**: O06 is `supported` in the Business Journey Guide.

## Assumptions and Dependencies

- Mirrors [spec 308](../308-customer-item-numbers/spec.md) (customer item numbers) and shares its match key.
- Builds on the purchase match of [spec 310](../310-purchasing-depth/spec.md).

## Open Questions

None; see Clarifications.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001 | US1.1 | `tests/test_supplier_item_numbers.py` |
| FR-002, FR-005 | US1.1–US1.3 | `tests/test_supplier_item_orders.py`, story O06 |
| FR-003 | All | `tests/test_supplier_item_adapters.py` |
| FR-004, SC-001, SC-002 | US1 | `tests/scenarios/test_catalog_purchasing.py::test_two_suppliers_name_one_item_by_their_own_numbers` |
