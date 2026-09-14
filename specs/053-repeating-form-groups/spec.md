# Feature Specification: Repeating Form Groups

**Feature Branch**: `053-repeating-form-groups`
**Created**: 2026-09-03  
**Status**: Approved  
**Language**: English for all repository artifacts  
**Input**: "Render typed list inputs such as order line items as usable repeated rows instead of raw JSON."

## Context and Intent

### Problem

The shared action form renders scalar and reference inputs, but structured arrays fall back to raw JSON. Operators should not need to understand transport payload syntax to create an order.

### Scope

- Add a reusable repeating-group field to the shared Web action form renderer.
- Render manual order lines as typed rows with item, quantity, unit, unit price, description, and requested date inputs.
- Support adding and removing rows, per-row required validation, mobile layout, and a readable confirmation summary.
- Submit the exact typed array expected by the existing manual-order Web adapter.

### Non-Goals

- Replacing intentional lossless Source payload JSON editors.
- Moving business validation or calculations into the browser.
- General-purpose JSON Schema rendering or a tenant-configurable form builder.
- Replacing revision-aware Document-line or Movement-correction workflows.

## User Scenarios & Testing

### User Story 1 - Enter order lines without JSON (Priority: P1)

As an order operator, I can add, edit, and remove recognizable order lines in the manual-order action without writing JSON.

**Independent Test**: Open manual order creation, add two lines, remove one, review the action, and verify the submitted request contains one typed line object.

**Acceptance Scenarios**:

1. **Given** the manual-order form opens, **When** it renders, **Then** one editable order line is present and no raw JSON field is shown.
2. **Given** one line exists, **When** the operator adds another line, **Then** the new row uses the declared defaults and independent state.
3. **Given** multiple lines exist, **When** one is removed, **Then** only that row is removed and at least one line remains.
4. **Given** a line lacks a required item, quantity, or unit price, **When** review is requested, **Then** browser validation prevents submission.
5. **Given** valid lines, **When** the action is reviewed and confirmed, **Then** the API receives a typed `lines` array and the canonical server service remains authoritative.

### User Story 2 - Reuse the list renderer (Priority: P2)

As a product maintainer, I can describe another typed list field through the same form metadata without creating another list-specific component.

**Independent Test**: A component contract renders a declared repeating group and serializes its rows without action-key-specific JSON parsing.

**Acceptance Scenarios**:

1. **Given** a repeating-group definition, **When** rendered, **Then** its child scalar, select, date, and reference fields use the shared controls.
2. **Given** a field is not a typed business list, **When** the form renders, **Then** it retains its existing scalar or intentional raw-payload control.

### Edge Cases

- The last remaining row cannot be removed when the minimum is one.
- A reference selection becomes inactive or belongs to another tenant before confirmation.
- A row contains optional blank values.
- Many rows exceed the visible dialog height on desktop or mobile.

## Requirements

### Functional Requirements

- **FR-001**: The shared action renderer MUST support a declarative repeating-group field with child field definitions, defaults, and a minimum row count.
- **FR-002**: Manual order lines MUST use the repeating-group field and MUST NOT expose raw JSON.
- **FR-003**: Operators MUST be able to add and remove independent rows while preserving the declared minimum.
- **FR-004**: Child fields MUST reuse shared scalar, select, date, and tenant-scoped reference controls.
- **FR-005**: Required child values MUST be validated before review and confirmation.
- **FR-006**: The confirmation view MUST summarize list rows in readable business terms.
- **FR-007**: Submission MUST serialize typed arrays without action-specific JSON parsing.
- **FR-008**: The dialog MUST remain keyboard-accessible, scrollable, and usable on mobile.

### Domain and Traceability Requirements

- **DR-001**: The browser MUST only collect and serialize inputs; the existing tenant-scoped application service remains authoritative.
- **DR-002**: The feature MUST add no schema or business-state fields.
- **DR-003**: Opaque IDs remain request identity while selectors display recognizable business labels.
- **DR-004**: Intentional lossless Source payload editors remain JSON and are not converted into typed business rows.

## Success Criteria

- **SC-001**: A user can create a two-line manual order without typing or editing JSON.
- **SC-002**: Automated contracts prove add, remove, minimum-row, required-field, review-summary, and typed serialization behavior.
- **SC-003**: Existing scalar action forms and all repository verification gates remain green.

## Requirement Traceability

| Requirement | Acceptance evidence | Tasks |
|---|---|---|
| FR-001, FR-003-FR-005 | Repeating-row renderer contract and required-control behavior | T002-T004 |
| FR-002, FR-007 | Manual-order request contains a typed `lines` array and no JSON parsing | T002, T005 |
| FR-006 | Review summary renders one readable entry per row | T002, T006 |
| FR-008 | Responsive styles, keyboard controls, and production build | T007-T008 |
| DR-001-DR-004 | Existing endpoint/service tests and final diff review | T008-T009 |

## Assumptions and Dependencies

- The manual-order endpoint and tenant-scoped suggestion endpoints from Feature 046 are available.
- The first implementation consumer is `order.lines`; later consumers require separate business approval when their workflows are revision-sensitive.
