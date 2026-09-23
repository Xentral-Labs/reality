# Feature Specification: Service Agency on the Existing Reality Model

**Feature Branch**: `252-service-agency-model`

**Created**: 2026-09-23

**Status**: Draft

**Language**: English

**Input**: User description: "Reality is currently strong for trade — orders, warehouse, purchasing. What if I wanted to model my own agency? Should that also use Commitment / Movement / Reservation, or should it be separate? Include analytics templates."

## Context and Intent

### Problem

Reality's domain model was proven on a trading business. Every fixture, every demo company and all thirty-nine operational exception classes describe goods that are ordered, stocked, shipped and invoiced. It is therefore not yet known whether `Commitment` / `Reservation` / `Movement` are genuine business structure or a trade schema wearing a domain vocabulary.

A service agency is the sharpest counter-example available: it sells no physical goods, its stock is time that perishes at the end of every week, and its resources are named people rather than fungible articles. If an agency can be operated on the existing records without new tables, the model is domain structure and can be shown to be. If it cannot, Reality is a trade system, and that is worth learning now rather than after a second industry has been promised to anyone.

### Intent

This feature is a **falsification test of the domain model**, carried out by operating a service agency on the existing primitives, together with the Analytics templates that make the result readable to the person running that agency.

The test is designed to be able to fail. A required new table is a **finding to be reported**, not a defect to be silently fixed.

### Scope

- A modelling convention that maps agency operations onto existing record types, expressed as a fixture and as services, without new business tables.
- One derived, read-time relation that expresses capacity coverage per period, following the precedent of `stock_position` and `customer_open_item`.
- A set of Analytics templates covering the recurring questions an agency owner asks.
- A measured report of which operational exception classes carry over to agency data with no new derivation.

### Non-Goals

- New tables for project, timesheet, capacity, skill, rate card, absence or employment.
- Project planning, scheduling optimisation, Gantt charts, forecasting or capacity simulation.
- Payroll, HR administration, absence approval or working-time-law compliance.
- A new demo company profile, a second demo queue or changes to the company setup and demo contract.
- A business-model switch, industry mode or tenant-level vertical configuration.
- Changing trade behaviour, contribution rules, costing, or any existing exception derivation.
- Inventory valuation of service items, or any accounting treatment of unsold capacity.
- Revenue recognition, percentage-of-completion accounting or work-in-progress postings.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md) — Principle II (documents own no derived state), Principle III (proven schema only), and the hard rule that a source's stated value is recorded and never recomputed.
- [Data model](../../docs/DATA_MODEL.md)
- `packages/reality-core/config/operational_exception_catalog.yaml` — the thirty-nine classes under test.
- `packages/reality-core/config/reporting_graph.yaml` — relations, measures and the `templates:` surface.
- [CEO contribution analytics templates](../244-ceo-contribution-templates/spec.md) — the template contract this feature extends.
- [Web specification](../../docs/WEB_SPEC.md)

## The Modelling Convention

The convention is the substance of this feature. It introduces no record type. Every row below names an existing table and an existing vocabulary value.

| Agency concept | Existing record | Notes |
|---|---|---|
| A person who does the work | `Party` **and** `Location` | `Party` is the contractual counterparty; `Location` is where capacity sits and what a movement leaves. The same double role a consignment supplier already has. |
| A team | `Location` with `parent_location_id` | The existing location hierarchy. |
| Sellable work | `Item`, `item_type: service`, `unit: h` | Fungible by role ("Senior design hour"), not by person. |
| A fixed-price deliverable | `Item`, `item_type: service` | Non-stocked, sold as quantity 1. |
| Contracted capacity | `Commitment`, `type: supplier_delivery` | `from_party_id` = the person, `location_id` = the person's location, `quantity` = contracted hours, `due_at` = end of the period. The employment contract is the purchase order for time. |
| The engagement | `Document` with lines | A new `type` value on an existing table, carrying no fulfilment state. |
| A time-and-material promise | `Commitment`, `type: customer_delivery` | `item_id` = the hour item, `due_at` = the agreed date. |
| A fixed-price promise | `Commitment`, `type: customer_delivery` | Quantity 1 of the deliverable item. |
| Staffing a person to work | `Reservation` | Already points at the commitment only, with `item_id` and `location_id`. No new link. |
| Recorded time | `Movement`, `type: shipment` | `from_location_id` = the person, `to_location_id` = the engagement, `occurred_at` = the day worked. |
| Acceptance of a deliverable | `Movement`, `type: shipment` | Quantity 1 against the fixed-price commitment. |
| Subcontracted work | `Commitment` `supplier_delivery` + `Movement` `receipt` | Identical to receiving goods from a supplier. |
| Non-billable reason, instruction, scope note | `Fact` | An observation about a record, never operational state. |

Two consequences are load-bearing and are what the test actually probes:

1. **Capacity is not stock; it is an incoming commitment.** Availability is therefore derived from commitments minus active reservations, within a period window — the same coverage arithmetic trade already performs, bounded in time.
2. **Recorded time is a movement, so burn is derived.** No document and no engagement ever carries a "hours used" or "delivered" field.

## User Scenarios & Testing

### User Story 1 - Contracted Capacity and Staffing Without Overbooking (Priority: P1)

As an agency owner, I record what each person has contracted to provide per week and staff them onto client promises, and the system tells me when I have promised more of a person than that person has.

**Why this priority**: Overbooking is the failure an agency notices first and the one the existing reservation model should already catch. If it does not, the whole premise fails at the first step.

**Independent Test**: Load the agency fixture, reserve more hours of one person in one week than the capacity commitment states, and verify the capacity relation reports the excess for that person and week.

**Known finding — the existing class does not carry**: `reservation_exceeds_stock` sums *movements* of an item across the whole company, in minus out, and compares that against active reservations. Capacity is an incoming commitment and produces no movement until the hours are worked, so for a person the movement sum is zero or negative and the class both misses real overbooking and would fire spuriously on every person. Cover is also judged per item company-wide, which cannot distinguish one person from another. Overbooking of a person is therefore **not** covered by an existing class. This is recorded under FR-002 and is one of the results this feature exists to produce.

**Acceptance Scenarios**:

1. **Given** a person with a capacity commitment of 40 hours for a week, **When** reservations against customer commitments total 32 hours in that week, **Then** the remaining capacity for that person and week is reported as 8 hours.
2. **Given** the same person and week, **When** reservations total 44 hours, **Then** the capacity relation reports the excess, naming the person, the week and the amount.
3. **Given** agency data, **When** the existing `reservation_exceeds_stock` derivation runs, **Then** it reports nothing for service items and capacity locations, neither a false positive nor a missed overbooking silently attributed to it.
4. **Given** a capacity commitment revised from 40 to 32 hours, **When** coverage is read again, **Then** the later stated quantity is the one in force and the earlier one remains visible as a revision.
5. **Given** capacity in one week and a reservation in the next, **When** coverage is read, **Then** the unused capacity of the earlier week does not cover the later week.

---

### User Story 2 - Recorded Time Is Delivery (Priority: P1)

As an agency owner, I record worked time as what actually happened, and every statement about progress against a client promise is derived from those records rather than from a status somebody set.

**Why this priority**: This is the direct analogue of the trade claim that status is derived, not stored. It is the property that makes the agency answers trustworthy in the same way.

**Independent Test**: Record time entries against a time-and-material commitment and verify that open quantity, burn and fulfilment are computed from movements, with no field anywhere holding a consumed total.

**Acceptance Scenarios**:

1. **Given** a customer commitment for 40 hours, **When** 12 hours are recorded across three days, **Then** 28 hours remain open and the remainder is derived from the movements.
2. **Given** recorded time, **When** the engagement document is inspected, **Then** it carries no delivered, consumed or remaining field.
3. **Given** a time entry recorded against no commitment, **When** utilisation is read, **Then** the hours count as delivered capacity but not against any client promise.
4. **Given** a time entry that is later corrected, **When** burn is read again, **Then** the correction appears as a compensating movement and the original remains visible.

---

### User Story 3 - Analytics Templates for the Recurring Agency Questions (Priority: P1)

As an agency owner, I can start from prepared Analytics templates that answer the questions I ask every week, without assembling them from the model myself.

**Why this priority**: Explicitly requested, and it is the only part of this feature the owner of an agency ever sees. A modelling convention nobody can read proves nothing.

**Independent Test**: Adopt each template against the agency fixture and verify its result against direct shared-service queries, including unit and currency separation.

**Templates**:

| Key | Label (en) | Label (de) | Answers |
|---|---|---|---|
| `agency_capacity_by_person_week` | Capacity and staffing by person and week | Kapazität und Reservierung je Person und Woche | Who is free, who is full |
| `agency_utilisation_by_month` | Utilisation by person and month | Auslastung je Person und Monat | Delivered hours against contracted hours |
| `agency_delivered_not_billed` | Delivered hours not yet billed | Geleistet, nicht fakturiert | Where the money is leaking |
| `agency_burn_against_promise` | Burn against promise by engagement | Verbrauch gegen Zusage je Auftrag | Which engagements are running over |
| `agency_idle_capacity_by_month` | Unsold capacity by month | Unverkaufte Kapazität je Monat | What perished unsold |
| `agency_subcontracted_hours` | Subcontracted hours by supplier | Fremdleistungsstunden je Lieferant | What was bought in |

**Acceptance Scenarios**:

1. **Given** the agency fixture, **When** the capacity template executes, **Then** contracted, reserved and remaining hours are reported per person and calendar week, ordered by week.
2. **Given** hours recorded against a customer commitment whose engagement has no invoice line covering them, **When** the delivered-not-billed template executes, **Then** those hours are listed per engagement and customer, and hours already billed are absent.
3. **Given** hours and deliverables in the same engagement, **When** any template executes, **Then** hours and pieces are never added together and each unit is reported separately.
4. **Given** a month in which a person delivered fewer hours than contracted, **When** the idle-capacity template executes, **Then** the unsold remainder is reported for that month and does not carry forward.
5. **Given** a template that needs the capacity relation, **When** the relation is unavailable, **Then** the template does not execute and says what is missing rather than reporting zero.

---

### User Story 4 - Fixed Price and Time-and-Material Without a Second Mechanism (Priority: P2)

As an agency owner, I sell both fixed-price deliverables and time-and-material work, and both are fulfilled by the same mechanism.

**Why this priority**: The point at which the trade analogy is most likely to break. Hours fulfil a T&M promise; for a fixed price they are cost, and acceptance fulfils. If this needs a second fulfilment path, that is a significant finding.

**Independent Test**: Run one fixed-price and one time-and-material engagement through the fixture and verify that both are fulfilled by movements against commitments, differing only in the item and quantity.

**Acceptance Scenarios**:

1. **Given** a fixed-price commitment for one deliverable, **When** 60 hours are recorded on the engagement, **Then** the commitment remains unfulfilled and the hours are visible as cost against the engagement.
2. **Given** the same commitment, **When** acceptance is recorded, **Then** the commitment is fulfilled by that movement and by nothing else.
3. **Given** a fixed-price engagement whose recorded hours exceed the sold amount at the stated internal rate, **When** the engagement is read, **Then** the overrun is visible without a stored margin field.

---

### User Story 5 - Subcontractors Are Suppliers (Priority: P2)

As an agency owner, I buy hours from freelancers and see what they owe me and what I owe them exactly as I would with a goods supplier.

**Why this priority**: Confirms that the incoming side of the model needs no agency-specific treatment, and exercises the supplier exception classes on service data.

**Independent Test**: Record a freelancer commitment, receive hours against it, and verify that the existing overdue-supplier and receipt-not-invoiced derivations behave as they do for goods.

**Acceptance Scenarios**:

1. **Given** a freelancer commitment for 20 hours by a date, **When** the date passes with 12 hours received, **Then** the existing overdue incoming commitment derivation reports the shortfall.
2. **Given** received freelancer hours with no supplier invoice, **When** exceptions are derived, **Then** the existing receipt-not-invoiced class reports them.

---

### User Story 6 - The Measured Carry-Over Report (Priority: P1)

As the owner of this repository, I get a report stating, per operational exception class, whether it fires on agency data with no new derivation, and why not where it does not.

**Why this priority**: This is the evidence the feature exists to produce. Without it the exercise is an anecdote.

**Independent Test**: Run the exception derivation over the agency fixture and compare the produced classes against the catalog, with a pinned expected count.

**Acceptance Scenarios**:

1. **Given** the agency fixture, **When** every exception class is derived, **Then** the report states for each of the thirty-nine classes: carried, not applicable, or requires change.
2. **Given** a class that requires change, **When** the report is produced, **Then** it names the specific structural reason rather than a general remark.
3. **Given** the report, **When** a later change alters the carried count, **Then** the pinned count fails until the report is updated deliberately.

---

### User Story 7 - Capacity Perishes (Priority: P3)

As an agency owner, I see that capacity nobody sold in a past week is gone, not available.

**Why this priority**: The single genuine semantic difference from trade. It is last because the earlier stories already require the period window; this story makes the consequence explicit and visible.

**Independent Test**: Read capacity for a past period with unused hours and verify the remainder is reported as idle and is not added to any later period.

**Acceptance Scenarios**:

1. **Given** a past week with 40 contracted and 30 delivered hours, **When** current availability is read, **Then** the 10 unsold hours appear as idle for that week and increase no later week.
2. **Given** a future week, **When** availability is read, **Then** contracted capacity is available regardless of any earlier shortfall.

### Edge Cases

- A time entry recorded into a period whose financial close has passed.
- A capacity commitment revised downward after reservations already exceed the new quantity.
- A person leaving mid-engagement while reservations for future weeks remain active.
- Time recorded with no commitment at all: internal work, sales, training, holiday.
- Part-time and absence: capacity must be a **stated** quantity, never one Reality computes from a calendar.
- An engagement mixing hours and deliverables, where totals must stay separated by unit.
- A service item reaching inventory valuation or stock positions, which must be impossible.
- A subcontractor who is also a customer.
- A deliverable accepted in part, which the model must either express as separate commitments or report as unsupported.
- Recorded time exceeding the contracted capacity of the person for that week.

## Requirements

### Functional Requirements

**Modelling convention**

- **FR-001**: The feature MUST operate the agency scenario using only existing business tables. No new business table may be added.
- **FR-002**: If a scenario cannot be expressed without a new table, the system MUST record that as a documented finding naming the scenario and the missing structure, and the scenario MUST be reported as not carried rather than enabled by a schema change.
- **FR-003**: Contracted capacity MUST be recorded as a `supplier_delivery` commitment from the person, carrying the stated quantity and the period end, and MUST NOT be computed from a working-time calendar.
- **FR-004**: A person MUST be representable as both a party and a location without either role duplicating the other's attributes.
- **FR-005**: The engagement MUST be a document that carries no delivery, consumption, billing or fulfilment state.
- **FR-006**: Recorded time MUST be a movement with the worked day as its occurrence, linked to a commitment where the work is against a client promise and unlinked where it is not.
- **FR-007**: Staffing MUST be a reservation referencing its commitment only, consistent with the existing shortest-relationship rule.
- **FR-008**: Corrections to recorded time MUST use the existing compensating-movement mechanism; a time entry MUST NOT be edited in place.

**Capacity coverage**

- **FR-010**: The system MUST provide a derived, read-time capacity relation reporting, per person and period, the contracted, reserved, delivered and remaining quantities.
- **FR-011**: Capacity coverage MUST be computed within a period window; capacity of an elapsed period MUST NOT cover a later period.
- **FR-012**: The capacity relation MUST NOT be stored as a new authority and MUST be recomputed from commitments, reservations and movements on read.
- **FR-013**: Overbooking of a person in a period MUST be reported by the capacity relation, naming the person, the period and the excess. The existing `reservation_exceeds_stock` class MUST NOT be relied on for this: it compares reservations against summed movements company-wide per item and cannot express per-person capacity. Whether the shortfall warrants its own exception class is a decision for the plan, not an assumption of this specification.
- **FR-014**: Service items and capacity locations MUST be excluded from `reservation_exceeds_stock` so that agency data produces neither a false positive nor a silent miss.

**Analytics templates**

- **FR-020**: The system MUST provide the six templates named in User Story 3 in the existing template surface, each with an English and a German label and description.
- **FR-021**: Every template MUST resolve against declared relations and measures at model load, so an unresolvable template fails at load rather than at execution.
- **FR-022**: Templates MUST separate quantities by unit and amounts by currency, and MUST NOT sum unlike units or average rates.
- **FR-023**: The delivered-not-billed template MUST derive billed coverage from invoice lines and movements and MUST NOT read a billing flag.
- **FR-024**: A template whose required relation or input is unavailable MUST decline to execute and state what is missing, and MUST NOT report zero.
- **FR-025**: German labels MUST use the ERP vocabulary already established in the resource catalog.
- **FR-026**: The new templates MUST NOT alter, reorder or rename any existing template.

**Carry-over measurement**

- **FR-030**: The system MUST produce a report classifying every operational exception class against the agency fixture as carried, not applicable, or requires change.
- **FR-031**: The carried count MUST be pinned by a test so that later drift is visible.
- **FR-032**: A class reported as requiring change MUST name the structural reason.

**Guards**

- **FR-040**: Service items and capacity locations MUST NOT enter inventory valuation, stock positions, stock-cover derivations or costing bases.
- **FR-041**: Capacity, delivered hours and deliverable pieces MUST NEVER be added together.
- **FR-042**: The feature MUST NOT change the behaviour of any existing trade scenario, and the existing suites MUST remain green.
- **FR-043**: The fixture MUST be a test fixture only and MUST NOT introduce a demo company profile, a setup flow change or a scheduled job.

**Fixture**

- **FR-050**: The fixture MUST contain at least five people across two teams, one time-and-material engagement, one fixed-price engagement, one subcontractor, and at least one full quarter of weeks so that period windows and perishability are exercised.
- **FR-051**: The fixture MUST include at least one overbooked person, one engagement with delivered and unbilled hours, and one engagement running over its promise, so that the carry-over report has something to find.

### Key Entities

- **Person**: A party for contractual facts and a location for where capacity sits and from where work flows.
- **Capacity commitment**: An incoming promise from a person to the company for a quantity of an hour item within a period.
- **Engagement**: A document and its lines, from which customer commitments hang. Holds no state.
- **Work item**: A service item measured in hours, or a deliverable item sold as a piece.
- **Staffing reservation**: An existing reservation holding capacity of a person against a customer commitment.
- **Time entry**: An existing movement from a person to an engagement on a worked day.
- **Capacity position**: A derived, per-person, per-period view of contracted, reserved, delivered and remaining hours. Never stored.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The complete agency scenario runs with **zero new business tables**; any exception to this is recorded as a named finding rather than as a schema change.
- **SC-002**: At least **20 of the 39** operational exception classes are classified as carried or not applicable for structural reasons unrelated to the model, with the exact carried count pinned by a test.
- **SC-003**: An agency owner can answer all six questions in User Story 3 from prepared templates without writing a query.
- **SC-004**: No engagement, document or party holds a delivered, consumed, remaining, utilisation or billing field; verified by a schema assertion.
- **SC-005**: Every existing trade suite remains green and no existing template, exception class or derivation changes behaviour.
- **SC-006**: Capacity of an elapsed period never contributes to a later period, verified by a dedicated test over at least one quarter of fixture data.
- **SC-007**: No service item or capacity location appears in any inventory valuation, stock position or costing basis, verified by a negative test paired with a positive control on a stocked item.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-002 | All | Schema-diff assertion that no business table was added, plus the findings report |
| FR-003, FR-004 | US1 scenarios 1, 4 | Fixture construction test: capacity as a stated supplier commitment, person as party and location |
| FR-005 | US2 scenario 2 | Negative schema assertion on engagement documents, paired with a positive control on a stocked order |
| FR-006, FR-008 | US2 scenarios 1, 3, 4 | Movement-based burn tests including an unlinked entry and a compensating correction |
| FR-007 | US1 scenario 1 | Reservation-shape test asserting no duplicated document, line or source links |
| FR-010, FR-012 | US1 scenarios 1-2, US7 | Capacity relation unit tests; a storage assertion that nothing is persisted |
| FR-011 | US1 scenario 5, US7 scenarios 1-2 | Period-window tests across at least one quarter of fixture data |
| FR-013 | US1 scenario 2 | Overbooking reported by the capacity relation with person, period and excess |
| FR-014, FR-040 | US1 scenario 3 | Negative tests on stock cover, valuation and costing for service items, each with a stocked positive control |
| FR-020, FR-021, FR-025, FR-026 | US3 | Template catalog load, localization and exact-key contract tests |
| FR-022, FR-041 | US3 scenario 3 | Unit and currency separation tests across hours and pieces |
| FR-023 | US3 scenario 2 | Delivered-not-billed parity test against the shared services, with no billing flag read |
| FR-024 | US3 scenario 5 | Declining execution test when the capacity relation is unavailable |
| FR-030, FR-031, FR-032 | US6 | Carry-over report over the fixture with the pinned carried count |
| FR-042 | All | The existing trade suites, unchanged and green |
| FR-043 | All | Assertion that no demo profile, setup flow or scheduled job changed |
| FR-050, FR-051 | US1-US7 | Fixture shape test covering people, engagements, subcontractor and one quarter of weeks |

## Assumptions and Dependencies

- Contracted capacity is a **stated** quantity coming from an employment or freelance agreement, not something Reality derives from a working-time calendar, holiday plan or absence record.
- The agency bills in one currency per engagement; multi-currency engagements are out of scope for this test but must not be silently mis-added.
- A week is the natural capacity period for the fixture; the derivation takes the period as an input rather than fixing it, so a month can be used without a model change.
- Internal cost per hour, where needed for overrun visibility, is read from the existing costing surfaces and is not introduced by this feature.
- Partial acceptance of a fixed-price deliverable is modelled as separate commitments; if the fixture shows this to be insufficient, that is a finding under FR-002.
- The existing template surface, its execution path and its German edition remain unchanged apart from the six added entries.
- This feature does not position Reality for a services market. It produces evidence about the model. Any product decision that follows is a separate specification.

## Open Questions

- **Q1**: Should the capacity relation be a general period-windowed coverage relation reusable by trade (for perishable stock and shelf life), or a capacity-specific one? A general one is more truthful to the model but a larger change. *Recommendation: capacity-specific in this feature, with the generalisation recorded as a candidate.*
- **Q2**: Should the engagement document type be one value (`service_agreement`) or split by commercial model (fixed price versus time and material)? *Recommendation: one value, with the commercial model expressed by the commitments, so the document keeps no state.*
- **Q3**: Does a carried count below the SC-002 threshold end the feature, or is it the result? *Recommendation: it is the result. The report is the deliverable; the threshold is a statement of expectation, not a gate on merging.*
