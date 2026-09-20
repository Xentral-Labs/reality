# Feature Specification: CEO Contribution Analytics Templates

**Feature Branch**: `244-ceo-contribution-templates-refresh`

**Created**: 2026-09-20

**Status**: Approved from owner request

**Language**: English

**Input**: User description: "Offer selectable DB1 and DB2 templates in Analytics, covering the typical contribution questions a CEO wants to answer."

## Context and Intent

### Problem

Reality can calculate confirmed DB1 and DB2 in Analytics, but a business leader must currently assemble the question from the model. The existing template surface should provide safe, useful starting points for the recurring executive questions without choosing a financial cost basis implicitly or treating incomplete contribution coverage as zero.

### Scope

Add a small set of selectable contribution-margin templates to the existing Analytics template catalog. They cover an executive overview, monthly development, sales-channel comparison, and margin leakage. Adopting a template prepares the question; the user must still select an explicit confirmed contribution basis before execution.

### Non-Goals

- A separate CEO dashboard, scheduled report, forecast, budget, target, or benchmark.
- Automatic selection of the latest, current, or otherwise preferred cost basis.
- Customer- or article-name joins, new stored contribution facts, schema changes, or a second DB1/DB2 calculation.
- Summing currencies, units, percentages, or incomplete final margins incorrectly.
- Changing the existing contribution review, confirmation, capture, or company-generation workflow.

### Existing Contracts

- [Retained inventory cost and contribution](../242-inventory-cost-contribution/spec.md)
- [Public analytics model explorer](../238-public-analytics-model/spec.md)
- [Web specification](../../docs/WEB_SPEC.md)

## User Scenarios & Testing

### User Story 1 - Start with an Executive Contribution Overview (Priority: P1)

As a CEO or Head of Operations, I can select a contribution overview template and see revenue, cost of goods, DB1, DB1 rate, DB2, DB2 rate, and coverage for an explicitly selected confirmed basis.

**Why this priority**: It answers the first executive question—whether contribution is healthy and whether the answer is complete—without requiring model knowledge.

**Independent Test**: Open Analytics, select the overview template, choose a confirmed contribution basis, and verify the resulting currency/unit-separated totals and coverage against the shared contribution service.

**Acceptance Scenarios**:

1. **Given** contribution data exists, **When** the user adopts the overview template, **Then** no financial result executes until the user selects an explicit eligible contribution basis.
2. **Given** a selected complete basis, **When** the overview executes, **Then** revenue, goods cost, DB1, DB1 rate, DB2, DB2 rate, and DB1/DB2 coverage are shown separately by currency and base unit.
3. **Given** incomplete DB2 coverage within the selected basis, **When** the overview executes, **Then** final DB2 and its rate remain unknown while the known subtotal and covered/required counts expose the gap.

---

### User Story 2 - Compare Contribution Development and Channels (Priority: P2)

As a business leader, I can start from templates that compare contribution by month or sales channel while retaining the same confirmed population and completeness rules.

**Why this priority**: Trend and channel mix are the common next questions after the overall position.

**Independent Test**: Adopt the trend and channel templates against a confirmed demo basis and verify grouping, ordering, units, percentages, and coverage against direct shared-service queries.

**Acceptance Scenarios**:

1. **Given** a confirmed basis with multiple economic months, **When** the monthly template executes, **Then** it reports revenue, DB1, DB1 rate, DB2, DB2 rate, and coverage by month, currency, and base unit in chronological order.
2. **Given** a confirmed basis with multiple sales channels, **When** the channel template executes, **Then** it reports the same executive measures per channel, currency, and base unit, ordered by revenue.
3. **Given** more than one currency or unit, **When** either template executes, **Then** unlike amounts never collapse into one total and rates are recomputed from grouped totals rather than summed.

---

### User Story 3 - Find Margin Leakage (Priority: P3)

As a business leader, I can select a margin-leakage template that ranks the weakest complete DB2 groups and still makes incomplete groups visible through coverage rather than presenting them as profitable or unprofitable.

**Why this priority**: Executives need a fast route from aggregate position to the areas that deserve investigation.

**Independent Test**: Run the leakage template against positive, low, negative, and incomplete demo cases and verify that complete weak DB2 groups sort first without converting unknown DB2 to zero.

**Acceptance Scenarios**:

1. **Given** complete positive and negative channel groups, **When** the leakage template executes, **Then** groups are ordered from the lowest DB2 rate upward with revenue, DB1, DB2, rates, and coverage visible.
2. **Given** an incomplete group, **When** the leakage template executes, **Then** its final DB2/rate remain unknown and its covered/required counts identify why it cannot be ranked as a complete result.

### Edge Cases

- No eligible contribution basis exists: the prepared template remains unexecuted and the existing selector explains the missing prerequisite.
- A basis has no rows in the selected period: the result is empty, not a zero-margin assertion.
- Revenue is zero: percentage measures follow the canonical contribution service's undefined-rate behavior.
- A group spans currencies or base units: required axes keep them separate.
- A captured or company contribution generation is selected: the template uses that explicit immutable context through the existing selector.

## Requirements

### Functional Requirements

- **FR-001**: Analytics MUST offer selectable templates for contribution overview, monthly contribution development, contribution by sales channel, and margin leakage.
- **FR-002**: Each template MUST use the canonical confirmed-contribution analytics node and measures; no browser-side DB1 or DB2 calculation is permitted.
- **FR-003**: Adopting a contribution template MUST prepare the question without executing it until an explicit eligible contribution cost context is selected.
- **FR-004**: No template MUST encode or infer a tenant-specific action, generation, latest basis, or preferred basis.
- **FR-005**: Every template MUST keep currency and base unit as required grouping axes and MUST expose DB1/DB2 coverage counts alongside final margins.
- **FR-006**: The overview MUST include revenue, goods cost, DB1, DB1 rate, DB2, DB2 rate, DB1 known subtotal, DB2 known subtotal, and covered/required position counts.
- **FR-007**: The monthly template MUST group by economic month, currency, and base unit and order months chronologically.
- **FR-008**: The channel template MUST group by sales channel, currency, and base unit and order by revenue descending.
- **FR-009**: The leakage template MUST group by sales channel, currency, and base unit and order by DB2 rate ascending without filtering unknown final DB2 to zero.
- **FR-010**: Template names and explanations MUST be available in English and German and state that an explicit confirmed cost basis is required.
- **FR-011**: Every offered template MUST validate against the reporting model and execute through the existing tenant-scoped graph service after context selection.
- **FR-012**: Existing non-contribution templates, saved analyses, command-palette entries, and direct graph questions MUST retain their behavior.

### Domain and Traceability Requirements

- **DR-001**: Templates are questions, not answers or financial authority; DB1 and DB2 remain read-time observations from retained confirmed evidence.
- **DR-002**: Incomplete costs MUST suppress final margins and rates exactly as the canonical contribution service defines; missing is never zero.
- **DR-003**: Template execution MUST retain tenant scope and the explicit cost-basis identity selected by the user.
- **DR-004**: Amounts, rates, and coverage MUST preserve their declared additivity and required-axis rules.

### Key Entities

- **Contribution analytics template**: A localized, validated starting question with no tenant-specific cost context or result.
- **Contribution cost context**: The explicit confirmed review, captured report generation, or verified company generation selected before execution.
- **Contribution result group**: A currency- and base-unit-safe aggregate whose final margins depend on complete coverage.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A user can reach each of four executive contribution questions from Analytics by selecting one template and one explicit cost basis.
- **SC-002**: All four templates produce the same values and incompleteness behavior as equivalent direct canonical graph questions.
- **SC-003**: No contribution template executes or saves a result with an implicit cost basis.
- **SC-004**: Every template is localized in English and German, resolves against the declared model, and remains discoverable through the existing template surface and command palette.
- **SC-005**: Existing analytics templates and saved-report behavior pass unchanged.

## Assumptions and Dependencies

- The four requested starting points represent the smallest useful CEO set: position, trend, channel mix, and leakage.
- Sales channel is the available business-readable segmentation axis that does not require a new relationship or schema field; customer and article profitability remain possible custom analyses but are outside this slice.
- Existing contribution selectors support confirmed review actions, captured reports, and verified company generations.
- The current Analytics template list and command palette consume the same server-provided template catalog.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-010 | US1-US3 | Catalog localization and exact-key contract tests |
| FR-002, DR-001 | US1-US3 | Model-resolution and shared-service parity tests |
| FR-003, FR-004, DR-003 | US1 scenario 1 | Browser adoption/context-selector regression test |
| FR-005, FR-006, DR-002, DR-004 | US1 scenarios 2-3 | Overview complete/incomplete aggregate tests |
| FR-007 | US2 scenario 1 | Monthly grouping and ordering test |
| FR-008 | US2 scenario 2 | Channel grouping and ordering test |
| FR-009 | US3 scenarios 1-2 | Leakage ordering and unknown-margin test |
| FR-011 | US1-US3 | Tenant-scoped graph execution tests |
| FR-012 | All | Existing reporting-graph and web regression suites |
