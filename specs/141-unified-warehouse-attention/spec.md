# Feature Specification: Unified Warehouse and Attention

**Feature Branch**: `139-unified-app-foundation` (additive increment in the isolated checkout)
**Created**: 2026-09-07
**Language**: English
**Status**: Owner-authorized continuation of the new-design migration; bounded warehouse and exception investigation increment.
**Input**: Continue after Analytics and Master data, preserving the coherent new App and selecting only useful existing capabilities.

## Context and Intent

### Problem
Delivery cases are usable, but stock investigation and current exceptions still send operators to the previous presentation. Operations staff need one understandable place to inspect the stock behind a delivery and investigate what needs attention.

### Scope
Add Warehouse with stock, reservations and recorded movement registers. Add Exceptions with current findings, severity/search filters, explanation and exact supporting records. Connect Home, delivery cases, master data and existing reviewed delivery actions through these destinations.

### Non-Goals
No new business rules, stock editing, receiving/transfer/release/correction forms, automatic resolution, dismissal of derived findings, monetary totals, forecast, schema expansion, practice-policy changes, Finance migration, legacy retirement, deployment or merge. Advanced warehouse actions and unsupported proposal handling keep their existing supporting routes.

## User Scenarios & Testing

### User Story 1 — Understand warehouse position (Priority: P1)
An operator finds an item, compares physical, reserved and available stock, then inspects its reservations and movement history.

**Independent test**: A received item reserved to a customer delivery shows the same quantities as the shared inventory observations. Exact-item reservation and movement filters survive paging and reload.

**Acceptance scenarios**:
1. Stock is company-wide by item, with explicit units and scope. No sum combines different units, and no displayed incoming/projected value implies unsupported readiness.
2. Search and stock-state filtering precede pagination. Selecting an item filters reservation/movement registers by its exact identity.
3. Reservations show quantity, item, location, state and their actual commitment. Movements show quantity, direction, item, locations, time and correction role, retaining originals and compensations as history.
4. Important records open the existing Inspector. Customer-delivery references open the existing case and its reviewed actions; supplier commitments remain inspectable without being presented as customer cases.
5. Reads and inspection never create proposals or business effects. Empty, unavailable and foreign-record states are explicit.

### User Story 2 — Investigate current exceptions (Priority: P1)
An operator enters from Home or the sidebar, filters current findings and opens the existing explanation and supporting records.

**Independent test**: A reservation shortfall appears using the existing derivation, leads to its delivery case and disappears when authoritative records resolve it.

**Acceptance scenarios**:
1. Findings retain canonical identity, severity order, cause, impact and trace. Search and severity filtering precede result counts and pagination.
2. Selecting a finding opens its current explanation, canonical resolution guidance and supporting record links. A resolved or foreign finding is unavailable; no fabricated persisted task remains.
3. Customer-delivery findings lead to the exact case. Other findings open the appropriate Inspector without inventing relationships or generic mutation controls.
4. Home's attention count links to this destination. Unsupported legacy proposal handling remains reachable separately.

### User Story 3 — Stay in the same App (Priority: P2)
Warehouse, Exceptions and their selected records share company context, navigation, localized controls and accessible presentation.

**Independent test**: Navigate Home → Exceptions → delivery → Warehouse → reservations, reload, switch company and use keyboard-only inspection at both widths/themes.

### Edge Cases
Zero/negative available stock; equal labels with different IDs; mixed units; inactive referenced items; released reservations; corrected and compensating movements; non-customer commitments; resolved exceptions; stale selected IDs; out-of-range pages; missing sources; unavailable reads; company changes; absent AI provider.

## Requirements

- **FR-001**: Add Warehouse and Exceptions within the opt-in unified shell, retaining existing supporting paths and authorization boundaries.
- **FR-002**: Display shared company-wide physical/reserved/available stock per item and unit, with server-side search, stock-state filtering and bounded pagination.
- **FR-003**: Display bounded reservations and recorded movements with exact-item filters, business labels, timestamps, correction roles and server totals.
- **FR-004**: Reuse canonical current exception derivation and explanation, with server-side search/severity filtering before pagination and canonical ordering.
- **FR-005**: Trace selected quantities and findings through Inspector and exact customer-delivery cases; reuse existing action review rather than adding mutation paths.
- **FR-006**: Preserve company, tab, exact item/record, query, filter and page in allowlisted navigation/reload state; company changes clear record context.
- **FR-007**: Enforce tenant scope and ordinary-company access, with explicit empty, unavailable, resolved and foreign states and no effects from reads.
- **FR-008**: Localize controls in en/de/nl/es and verify both themes, 390/1440 px, keyboard focus, safe rendering and clear semantic table labels. Canonical catalog guidance remains faithful to its source language.

## Key Entities
Existing Item, Location, Commitment, Reservation, Movement, MovementCorrection and derived OperationalException. No new persistent entity or operational document status.

## Assumptions and Dependencies
The owner's continuation authorizes the next bounded implementation step within the established migration direction. Warehouse investigation and exception triage follow the agreed information architecture. Existing read models, correction semantics, exception catalog, Inspector and delivery review services remain authoritative. Stock is aggregated company-wide by item; location-specific explanation remains in the Inspector. Existing exception derivation currently evaluates company records before slicing; this increment bounds responses and does not claim a new scalable derivation engine.

## Success Criteria
- Stock values match the existing shared reads for every acceptance fixture.
- Exact-item register results and filtered exception totals remain correct beyond the first page and exclude foreign company records.
- Operators reach each selected finding's evidence or delivery case without leaving the new shell for supported cases.
- All supported surfaces pass four-language, two-theme and two-width browser journeys without horizontal page overflow.
- No read or navigation creates a proposal, stock movement, reservation or stored exception.

## Requirement Traceability

| Requirement | Scenarios | Planned evidence |
| --- | --- | --- |
| FR-001, FR-006 | US3 | Route contracts and operational browser journey |
| FR-002, FR-003 | US1-1 to US1-3 | Warehouse adapter/shared-read tests |
| FR-004 | US2-1, US2-2 | Exception service/filter/explanation tests |
| FR-005 | US1-4, US2-3, US2-4 | API links and browser traversal |
| FR-007 | US1-5, US2-2 | Tenant/practice/no-effect tests and read failures |
| FR-008 | US3 | Localization audit, keyboard and visual matrix |

## Exception explanation card
- **FR-009**: Attention shows a separate explanation card below its finding detail/empty prompt: how findings arise from existing records (for example overdue deliveries or missing reservations), and clear when causes change. A link opens a searchable list of all currently catalogued exception classes, their descriptions, responsible areas and resolution guidance. Clearly distinguish possible classes from active company findings. Reuse the existing authenticated global catalog read; no business mutations or manually maintained duplicate list. Support close/Escape, focus return, errors/retry and four languages.
FR-009 maps to the operations browser catalog/open/search/retry/close test and existing catalog service contract.
