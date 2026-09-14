# Feature Specification: Complete unified business journey
**Created**: 2026-09-08
**Status**: Complete; verified locally
**Language**: English
**Input**: Owner approved testing the complete new-app business journey and fixing demonstrated gaps before moving setup or retiring old presentations.

## Context and Intent
### Problem
Separate service tests and browser fixtures do not prove that an operator can complete the actual linked workflow across the new app.
### Scope
Validate order → reservation → partial delivery → partial invoice → payment → invoice credit → partial refund → reversal using real persisted data and the unified forms. Repair demonstrated integration or usability defects within these existing capabilities.
### Non-Goals
New commercial policy, tax calculation, bank execution, setup migration, supplier/physical return entry, schema changes, shared-company test mutations, deployment or old-app/Playground retirement.
### Existing Contracts
- docs/WEB_SPEC.md
- specs/139-unified-app-foundation/spec.md
- specs/119-unified-order-entry/spec.md
- specs/124-partial-invoicing-rebilling/spec.md
- specs/125-unified-invoice-credit/spec.md
- specs/126-unified-customer-refund/spec.md

## User Scenarios & Testing
### User Story 1 - Complete one real operating case (Priority: P1)
An operator enters an order, reserves its goods, ships a partial quantity, invoices part of that quantity and records payment. They then credit part of the invoice and record a partial refund.
**Independent Test**: A real browser completes all stages against an isolated real company and every result is visible in the next applicable workspace.
**Acceptance Scenarios**:
1. Given opening stock20, when order10 is reserved10 and shipped6, then stock14, reserved4 and delivery open4 are visible; invoice4 leaves6 billable.
2. Given invoice400, when payment400, credit200 and refund75 are recorded, then invoice open0 and credit open125; stock and delivery quantities remain unchanged by money actions.
3. Given a prepared change at any stage, then financial/operational effects occur only after explicit confirmation; reloading opens the original verified receipt.
### User Story 2 - Correct and explain the same case (Priority: P1)
The operator reverses the recorded refund and follows links through its credit, invoice, order and source.
**Independent Test**: Reversing refund75 reopens credit to200 while the original refund receipt remains verifiable; no stock effect occurs.
**Acceptance Scenarios**:
1. Given the recorded refund, when its posting is reversed, then the current credit is200 and its historical evidence still exists and verifies.
2. Given linked results, when inspected, then the shortest true links retain the original stated values and identities.
3. Given a demonstrated broken form, handoff, read model or evidence link, when repaired, then a failing regression proves the defect before the fix where practical.
### Edge Cases
Partial quantities; missing next-step selection; stale reads after confirmation; duplicate confirmation/reload; no open invoice after payment; credit/refund reversal and remaining balances; invalid tenant; no shared company writes.

## Requirements
### Functional Requirements
- **FR-001**: The complete existing journey MUST be executable through unified forms against real persisted business data, including partial shipping, invoicing and refunding.
- **FR-002**: Each stage MUST show the current applicable quantities/balances and make the recorded evidence available to the next stage without inventing source amounts.
- **FR-003**: Each mutation MUST require review and confirmation; recorded proposals remain recoverable and verifiable after reload and later correction.
- **FR-004**: Reversing the refund MUST restore credit capacity while preserving historical receipt and all stock/delivery quantities.
- **FR-005**: Demonstrated defects within this existing journey MUST have scoped regression evidence and be repaired without migrating unrelated legacy features.
### Domain and Traceability Requirements
- **DR-001**: Order source→order lines→commitments/reservations/movements and invoice→order line, credit→invoice line, refund allocation→credit ledger links MUST remain inspectable and tenant-scoped.
- **DR-002**: All actions MUST pass through shared services/tools; browser testing MUST use an isolated database and dedicated processes with cleanup, never shared users/tenants/business records.

## Success Criteria
- **SC-001**: One real-browser end-to-end run completes every stage and verifies exact expected quantities, amounts, links and receipts.
- **SC-002**: The service story and all required regression gates pass; every defect and repair has recorded evidence.

## Assumptions and Dependencies
The existing capabilities and stated-value policy remain authoritative. The approved task authorizes bounded repairs revealed by the journey. Temporary identity setup is test scaffolding. A real-browser proof supplements existing isolated service and intercepted-UI tests; it does not depend on an AI provider or payment processor. No schema expansion is needed.

## Requirement Traceability
| Requirement | Scenario | Evidence |
|---|---|---|
| FR-001, FR-002 | US1.1–2 | Real-browser journey plus service story |
| FR-003 | US1.3 | Review/no-effect, confirmed receipt and reload assertions |
| FR-004 | US2.1 | Refund reversal and historical proof assertions |
| FR-005 | US2.3 | Failing regression for each discovered defect |
| DR-001 | US2.2 | Database and Inspector traversal assertions |
| DR-002 | All | Real API boundary, isolated database/process lifecycle |
