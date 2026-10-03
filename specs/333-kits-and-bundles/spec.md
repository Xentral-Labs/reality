# Feature Specification: Kits, Bundles and Light Assembly

**Feature Branch**: `333-kits-and-bundles`

**Created**: 2026-10-02

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), round 2. Close the capability gap behind the journeys K01, K02, K03, K04, K06 so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Kits and bundles do not exist:
- availability cannot be derived from components;
- a kit cannot be held back for one missing component;
- a component return gives no kit credit;
- assembly does not consume components;
- a bundle price is not split.

| Journey | Title | Status today |
|---|---|---|
| K01 | Kit sold, shipped from components | gap |
| K02 | One component missing, no partial kit allowed | gap |
| K03 | Return of a single component from a kit | gap |
| K04 | Light assembly: components consumed, finished item produced | gap |
| K06 | Bundle price split across components (revenue, tax) | gap |

### Scope

- **Bill of materials:** a kit is a stocked item with a stated bill of materials, the components and their quantities. Each component can optionally carry a stated share of the kit's price.
- **Availability:** kit availability per location is derived at read time. It is the free kits on hand plus what the free components build, and it names the component that limits it.
- **Assembly:** a reviewed assembly consumes the components and produces the kit at a location. It is all or nothing, and it refuses whole when a component is short. Packing a kit order assembles it, and a light assembly ahead of demand is the same action.
- **Split:** a kit's order or invoice line is split across its components at read time, by the stated shares. The split covers the line's stated net, tax and gross.

### Non-Goals

- Multi-level bills of materials, routings, capacity planning and production orders.
- Lot- or serial-tracked kits or components.
- Disassembling a kit back into components.
- Rolling the components' cost into the kit's cost. Inventory cost reviews refuse an item with assembly movements until a follow-up spec.
- Per-component tax rates. The line's stated tax is split; it is never recomputed.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-02

The owner delegated these decisions to the recommended options.

- **Q: Is a kit a stored item with its own stock (assembled ahead) or always exploded at shipment?**
  - **A:** It is exploded when it is packed.
    - A kit is a stocked item whose units come only from an assembly of its components.
    - Packing a kit order runs that assembly; the kit then ships, returns and is invoiced as itself.
    - Assembling ahead of demand (K04) is the same action.
  - Every promise, reservation, shipment, return and invoice reads goods on the promise's own item. Keeping the kit an item keeps all of them true without a second notion of "delivered".
- **Q: What is kit availability?**
  - **A:** It is read per location and never stored.
    - It is the kits on hand that are free (not reserved, not blocked), plus the whole kits the free components build.
    - The read names the component that limits the count.
  - The *Oversold* class counts the buildable kits as stock of the kit.
- **Q: How is a kit held back when one component is missing?**
  - **A:** By refusing the assembly whole.
    - It names the component, what is needed and what is free.
    - Nothing is consumed.
  - No partial kit can exist, so the kit order stays unready until whole kits are there.
- **Q: How are the components stated, and can they change?**
  - **A:** The components are stated once, through a reviewed definition, as a version of the kit's source stream:
    - the component items and their quantities in each component's stock unit;
    - optionally a share of the kit's price per component, which must total exactly 1.
  - A different set of components is a new kit item.
  - Components are stocked, untracked items. A component is never a kit itself and never the kit.
- **Q: How is a bundle price split?**
  - **A:** At read time, by the stated shares.
    - The split covers the line's stated gross and, where the line states them, its net and tax (spec 284).
    - Amounts are rounded to the cent. The remainder goes to the largest share, so the parts add up to the line exactly.
  - Without stated shares there is no split, and the read says so.
- **Q: How is a single returned component credited?**
  - **A:** The component comes back to stock as its own item, with a stated reason.
    - The credit for it is the per-piece share the kit's split gives that component.
  - A return names a promise of its own item only, so the component return is not linked to the kit delivery.
    - Goods coming back without a promise stay *Unexplained movement* (spec 314) until a person explains them.
    - The return and credit classes cannot pair the return with the kit's credit.
  - K03 stays partial with that finding.
- **Q: What does an assembly record?**
  - **A:** One assembly statement, a source record, at a stated time. Every movement carries it:
    - one `assembly_input` movement per component, out of the location;
    - one `assembly_output` movement of the kit, into the location.
  - Assembly movements are not corrected one by one.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sell a kit and ship it from its parts (Priority: P1)

As an e-commerce merchant, I sell a set and ship it from its parts.

**Why this priority**: The core of the gap. K01 and K02 depend on it.

**Independent Test**: A kit order is assembled, reserved and shipped through reviewed tools. Availability is read before and after. A missing component refuses the assembly whole.

**Acceptance Scenarios**:

1. **Given** a kit of 1 frame and 2 wheels, with 3 frames and 4 wheels free, **When** availability is read, **Then** 2 kits are available, limited by the wheels.
2. **Given** a kit order of 2, **When** 2 kits are assembled, reserved and shipped, **Then** the promise is fulfilled, 1 frame is left, no wheels are left, and no *Oversold* finding is reported before the assembly.
3. **Given** a wheel missing for one kit, **When** the assembly is reviewed or executed, **Then** it is refused, naming the wheel, and no frame or wheel leaves stock. **Given** the wheel arrives, **Then** the same assembly succeeds and the kit ships whole.

### User Story 2 - Assemble ahead of demand (Priority: P2)

As a warehouse lead, I assemble finished items from components before orders arrive.

**Independent Test**: An assembly ahead of demand yields paired movements under one statement.

**Acceptance Scenarios**:

1. **Given** components in stock, **When** 3 kits are assembled, **Then** each component leaves by its quantity × 3, 3 kits enter, and every movement names the same assembly statement.
2. **Given** an assembly movement, **When** a correction of it is requested, **Then** it is refused.

### User Story 3 - Split a bundle price and credit a component (Priority: P2)

As a bookkeeper, I see what share of a bundle's price, revenue and tax each component carries, and what to credit for one returned component.

**Independent Test**: The split of an invoiced kit line is read, and a single component is returned.

**Acceptance Scenarios**:

1. **Given** a kit line of 100.00 gross, 84.03 net and 15.97 tax, with shares of 0.6 for the frame and 0.2 per wheel, **When** the split is read, **Then** each component's net, tax and gross is given, and the parts add up exactly to the line.
2. **Given** a shipped kit, **When** the customer returns one wheel with a reason, **Then** the wheel is back in stock and the split gives the wheel's per-piece credit. The return reads as *Unexplained movement*, which is the recorded K03 finding.

### Edge Cases

- Tenant isolation: another company's kits, components and splits are never read.
- A kit with no stated shares has no split. The read says so rather than dividing evenly.
- A component that is a kit, a tracked item or the kit itself is refused at definition.
- A second definition of the same kit is refused.
- Assembling a kit that has no components is refused.
- A source-stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A kit MUST name its components and quantities, stated through the review, once. Optional shares MUST total exactly 1.
- **FR-002**: Kit availability MUST be derived from free kit stock and free component stock at read time, per location, naming the limiting component.
- **FR-003**: A reviewed assembly MUST consume each component and produce the kit at one location, all or nothing. It MUST refuse whole when a component's free stock is short. A kit order is shipped by assembling it and shipping the kit.
- **FR-004**: A kit line's stated gross, net and tax MUST be split by the stated shares at read time. The parts MUST add up exactly to the line.
- **FR-005**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-006**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence, as specs 292 to 294 did. A journey not fully proven MUST be recorded as partial, with its finding.

### Domain and Architecture Requirements

- **DR-001**: New typed fields or tables MUST be justified by repeated calculation, filtering or action on them (Constitution III) in the plan.
- **DR-002**: Derived states (availability, split) MUST be read from Reality records at read time and never stored as a new authority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every journey in scope has a passing business story, or a recorded finding for what remains.
- **SC-002**: K01, K02, K04 and K06 are `supported` in the Business Journey Guide; K03 is `partial` with its finding.

## Assumptions and Dependencies

- Builds on reservations, stock blocks (spec 304), shipments, stated invoice net and tax (spec 284), and the *Oversold* class (spec 300).

## Open Questions

None; see Clarifications.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, FR-002, FR-003 | US1, US2 | `tests/test_kits.py`, stories K01, K02, K04 |
| FR-004 | US3 | `tests/test_kits.py`, stories K06, K03 |
| FR-005 | All | `tests/test_kit_adapters.py` |
| FR-006, SC-001, SC-002 | All | Catalog tests and Guide questions |
| DR-001, DR-002 | All | Plan and diff review |
