# Feature Specification: Customer Pickup and Late 3PL Confirmations

**Feature Branch**: `312-shipping-modes`

**Created**: 2026-09-29

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), tier 2, rank 18. Close the capability gap behind the partial journeys D15, D12 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

- **D15:** a customer who collects the goods can be recorded today only as a shipment without a carrier, which cannot be told from "carrier unknown". Nothing says who collected.
- **D12:** when a 3PL confirms a shipment late, `shipment_dispatch` keeps the stated time only on the notice, while the stock movements are dated at recording. When the goods left and when the 3PL confirmed it cannot be told apart.

| Journey | Title | Status today |
|---|---|---|
| D15 | Customer pickup instead of shipping | partial |
| D12 | 3PL confirms shipment late | partial |

### Scope

- **Pickup:**
  - A shipment states its delivery mode, `carrier` or `pickup`.
  - A pickup takes no carrier or tracking number and may name who collected.
  - Reads show the mode and the collector.
- **Stated time:**
  - `shipment_dispatch` and `shipment_receive` apply their stated `occurred_at` to the movements they record.
  - A time in the future is refused.
  - The shipment read shows when the goods moved, when the shipment was recorded, and the confirmation lag between them.

### Non-Goals

- 3PL integrations and source interpreters for 3PL messages.
- A finding for late confirmations; the lag is shown, and the existing stalled and overdue findings apply.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-02

The owner delegated these decisions to the recommended options.

- Q: Is the collector's name needed, or only the mode? → A: The mode is stated, and the name is optional. The mode is a typed field because reads filter and refuse on it; the name is a stated text kept with the shipment's notice, which nothing calculates on.
- Q: Which time do a late confirmation's movements carry? → A: The stated time when the goods moved. The recording time stays on the shipment's events and the movements' business events. Future times are refused.
- Q: Is a late confirmation a finding? → A: No. The shipment read shows the lag, and the stalled and overdue findings clear when the confirmation is recorded.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Customer Pickup (Priority: P1)

As a warehouse clerk, I record that a customer collected an order.

**Why this priority**: Rank 18 of the sales-gap roadmap: it comes up in many specialised evaluations.

**Independent Test**: A business story per journey in scope, through reviewed tools, with a positive control for every "no finding" assertion.

**Acceptance Scenarios**:

1. **Given** an order ready to go, **When** the customer collects it, **Then** the shipment is recorded as a pickup, with who collected, and the promise is fulfilled.
2. **Given** a pickup, **When** a carrier or tracking number is stated, **Then** it is refused.

### User Story 2 - Late 3PL Confirmation (Priority: P1)

As an operations lead, I see when goods left and when the 3PL told us.

**Acceptance Scenarios**:

1. **Given** an order that is stalled, **When** the 3PL confirms on Thursday that the goods left on Monday, **Then** the movements carry Monday, the shipment shows the recording time and a lag of three days, and the stalled finding clears.

### Edge Cases

- Tenant isolation: nothing crosses companies.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).
- A pickup is a customer delivery only.
- Shipments recorded without a mode read as carrier when they name a carrier, and as unknown otherwise.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A shipment MUST be able to state pickup as its mode, and optionally who collected.
- **FR-002**: Goods-left time MUST be distinct from confirmation time.
- **FR-003**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-004**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide.

## Assumptions and Dependencies

- Builds on the shipment model (spec 095) and the reviewed shipment tools.

## Open Questions

None; see Clarifications.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001 | US1 | Story D15 and shipment tests (planned) |
| FR-002 | US2 | Story D12 and shipment tests (planned) |
| FR-003, DR-001, DR-002 | All | Adapter tests and diff review (planned) |
| FR-004, SC-001, SC-002 | All | Catalog tests and Guide questions (planned) |
