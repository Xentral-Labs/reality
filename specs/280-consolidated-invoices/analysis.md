# Analysis: Consolidated invoices across orders

Cross-artifact consistency and coverage review of spec.md, plan.md and tasks.md against the
Constitution and the current code, 2026-09-26. No CRITICAL finding.

## Coverage

| Requirement | Tests | Implementation |
|---|---|---|
| FR-001 | T001, T002 | T004 |
| FR-002 | T001 | T004 (writer unchanged) |
| FR-003 | T003 | none needed: billing reads are already per order line; T003 turns green with T004 |
| FR-004 | T007 | T008 |
| FR-005 | T009 | T010 |
| FR-006 | T011, T016 | T012, T013, T017 |
| FR-007 | T005, T011 | T006, T012, T013 |
| FR-008 | T014 | T015 |
| FR-009 | T005 | T006 |
| FR-010 | T001 | T004 |

Every requirement has a test task before its implementation; every task maps to a requirement.

## Findings

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| A1 | MEDIUM | FR-007 requires CLI parity, but no CLI invoice command exists and the plan adds none. | FR-007 reworded: CLI only where an invoice command exists (none today). |
| A2 | MEDIUM | Edge case "a cancelled commitment between review and confirmation" has no test. | Added to T005: the review goes stale and confirmation writes nothing. |
| A3 | MEDIUM | The spec relies on "existing input bounds", but `lines` has no upper bound in the MCP schema or in core. A 12-order collective invoice makes the unbounded list a real input. | New FR-010: at most 200 positions per invoice, the same bound as the billable-positions read; enforced in core and declared as `maxItems` in the MCP schema; proven in T001. |
| A4 | LOW | `billable_positions` built on `_order_line_billing` per line would issue queries per line. | T011 adds a statement-count proof that the read does not grow per order line. |
| A5 | LOW | The new blocker detail is server text; the web translates server strings by their English key. | T017 covers the detail string in four languages; no blocker code label exists in the web today. |
| A6 | LOW | German label for the feature. | T017 uses "Sammelrechnung" (German ERP vocabulary). |

## Constitution

All eight rows of the plan's Constitution Check hold after the resolutions; FR-010 adds a
bound, not a field. No exception is needed.
