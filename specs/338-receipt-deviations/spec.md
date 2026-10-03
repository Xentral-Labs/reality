# Feature Specification: Receipt and Shipment Deviations

**Feature Branch**: `338-receipt-deviations`

**Created**: 2026-10-03

**Status**: Approved

**Language**: English

**Input**: Sales-gap roadmap (`docs/scenarios/roadmap.md`), round 3. Close the gaps behind the journeys H04, H05, H06, H07, H17, G16 and D05, so the Business Journey Guide can state them as supported.

## Context and Intent

### Problem

Goods rarely arrive or leave exactly as ordered. Today Reality knows only the exact case:

- A receipt above the ordered quantity is refused, so an over-delivery cannot be recorded against its purchase, and the surplus can neither be kept nor sent back with a link.
- A receipt or shipment of another item than the line asks for cannot name that line. It is recorded unlinked and reads as an unexplained movement, and nothing says which line it was meant for.
- A substitute or successor item cannot be accepted for a purchase line.
- An inbound notice says that goods are coming, but not which purchases and how much. So advised and received quantities cannot be compared, and goods in transit per purchase cannot be read.

| Journey | Title | Status today |
|---|---|---|
| H04 | Over-delivery accepted | gap |
| H05 | Over-delivery rejected or returned | gap |
| H06 | Wrong item delivered | gap |
| H07 | Substitute/successor item delivered | gap |
| H17 | Advice says 100, 96 arrive | gap |
| G16 | Import by sea (8 weeks), one container, many purchases | gap |
| D05 | Picking error found by the customer | gap |

### Scope

- A receipt may state that it brings in more than the purchase line still expects. The surplus is reported until it is kept, by raising the line to what arrived, or sent back to the supplier against the same line.
- A receipt, shipment or return may name the order line it was meant for while carrying another item. This is a wrong-item movement: it does not fulfil the line, it is explained by the line, and it is reported until the wrong goods have gone back.
- A person may accept a substitute item for a purchase line. Receipts of the substitute then fulfil that line.
- An inbound notice may state, per purchase line, how much it advises. A receipt may be recorded into the shipment that was announced. The shipment then reads advised against received, and a purchase order reads what is still in transit per line.

### Non-Goals

- Substitutes for customer lines. A customer accepting another item is a revision of their order and stays out of scope.
- Changing the item of a purchase line. A substitute stands beside the ordered item, and the line keeps what was ordered.
- Parsing supplier advice files (DESADV, ASN). The advice is stated through the reviewed notice; interpreting a source format belongs to the EDI work of spec 311.
- Tolerances that accept an over-delivery automatically. Every surplus is stated by a person in the receipt's review.
- Anything that requires a document status field (Constitution II).

## Clarifications

### Session 2026-10-03

The owner delegated these decisions to the recommended options.

- Q: How is an over-delivery accepted? → A: The person receiving states it on the receipt (`beyond_order`). Without that statement the receipt is refused as before.
  - The surplus is derived at read time: received net of supplier returns, beyond the quantity in force.
  - It is reported as *Received beyond the order* until it is kept or sent back.
  - Keeping it is the existing reviewed revision of the line, raised at most to what was received. It is the one quantity revision a fulfilled purchase line takes, mirroring spec 313 for customers.
  - Sending it back is a supplier return against the same line, which the existing bound already allows up to what was received.
- Q: How does a wrong item name its line without fulfilling it? → A: The movement states `meant_for_commitment_id` instead of `commitment_id`. A wrong-item record links the movement to the line.
  - The movement still moves the item it carries, so stock is true.
  - The line's fulfilment counts only the ordered item, so the line stays open for the right goods.
  - A wrong-item movement must carry another item than the line asks for. A substitute accepted for the line is not wrong.
  - Goods going back name the same line in the same way: a supplier return for a purchase, a customer return for a sale. They are bounded by what of that item is still out on that line.
  - It is reported as *Wrong item delivered* until everything that went the wrong way has come back.
  - A picking error found by the customer (D05) is a correction of the recorded shipment. The existing reviewed movement correction replaces the shipment of the ordered item with a shipment of the item that actually left, naming the line it was meant for. The line is open again.
- Q: How is a substitute accepted? → A: Through a reviewed action on the purchase line: the substitute item and a reason.
  - Only for a supplier promise that is not cancelled.
  - Only a stocked item in the same unit as the ordered item.
  - Once per line and item.
  - Receipts of the substitute name the line as usual and fulfil it.
  - A substitute that already arrived as a wrong item is moved onto the line through the existing movement correction, which then clears the wrong-item finding.
- Q: How are advised quantities stated, and what counts as received for an advice? → A: The inbound notice for a supplier delivery may state lines: a purchase promise of that supplier and a quantity.
  - A receipt may be recorded into the announced shipment (`shipment_id`). What was received for the advice is what was received into that shipment.
  - While nothing has been received into the shipment, its advised quantities are in transit.
  - Once goods were received into it, what is advised and not received is a shortfall of that delivery, not still in transit.
- Q: Is a short advice reported as a finding? → A: No. The shipment read shows advised, received and the difference per line, and the purchase order's three-way match shows what is in transit. A missing quantity after a delivery already surfaces through the open purchase line and its overdue finding.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Over-Delivery Kept or Sent Back (Priority: P1)

As a goods receiver, I record the 105 pieces that arrived for a purchase of 100. Purchasing then decides whether we keep the five or send them back.

**Why this priority**: The most frequent receipt deviation. Today it cannot be recorded at all.

**Independent Test**: A purchase of 100 receives 105 with `beyond_order`; the surplus is reported; raising the line to 105 clears it. A second purchase receives 110 and returns 10 against the line, which clears it.

**Acceptance Scenarios**:

1. **Given** a purchase line of 100, **When** 105 are received without stating `beyond_order`, **Then** the receipt is refused as before.
2. **Given** the same line, **When** 105 are received with `beyond_order`, **Then** stock rises by 105, the line is fulfilled, and *Received beyond the order* reports 5.
3. **Given** that finding, **When** the line is revised to 105, **Then** the finding clears. A revision to 106 is refused.
4. **Given** 110 received on a line of 100, **When** 10 go back to the supplier against the line, **Then** the finding clears and the supplier return is linked to the line.

### User Story 2 - Wrong Item, Substitute and Picking Error (Priority: P1)

As a goods receiver, I record that the supplier sent the wrong article for an order line. As a buyer, I accept a successor article instead of the ordered one. As customer service, I record that the customer received another article than we booked.

**Why this priority**: Without a link, wrong goods are invisible except as unexplained movements.

**Independent Test**: Receipt, return and correction stories for each case, each with a positive control.

**Acceptance Scenarios**:

1. **Given** a purchase line for item A, **When** item C arrives and is received meant for that line, **Then** stock of C rises, the line still expects A, *Wrong item delivered* names the line, and the receipt is not an unexplained movement.
2. **Given** that receipt, **When** C goes back to the supplier meant for the same line, **Then** the finding clears.
3. **Given** a purchase line for item A, **When** the buyer accepts successor B for the line and B is received against it, **Then** the line is fulfilled and its three-way match names the substitute.
4. **Given** B already received as a wrong item, **When** B is accepted and the receipt is corrected onto the line, **Then** the line is fulfilled and the wrong-item finding clears.
5. **Given** a shipment recorded as item Y on a customer line, **When** the customer reports receiving item X and the shipment is corrected to X meant for the line, **Then** the line is open for Y again, stock of Y is back and stock of X is down, and *Wrong item delivered* names the line until X comes back.

### User Story 3 - Advised Against Received, In Transit per Purchase (Priority: P2)

As a buyer, I see what a supplier's advice announced for each purchase, what arrived with it, and what is still on the water.

**Why this priority**: Visibility for long lead-time imports; no new finding.

**Independent Test**: A notice advises 100 on one line; 96 are received into the shipment; the shipment reads 100 advised, 96 received, 4 short. A container notice advises lines of three purchases; each purchase reads its advised quantity as in transit until the container is received.

**Acceptance Scenarios**:

1. **Given** a notice advising 100 for a purchase line, **When** 96 are received into that shipment, **Then** the shipment reads advised 100, received 96 and short 4 for the line.
2. **Given** a notice advising lines of three purchase orders, **When** each order's three-way match is read, **Then** each line shows its advised quantity in transit. **When** the container is received, **Then** nothing is in transit.

### Edge Cases

- A wrong-item movement must carry another item than the line, and not an accepted substitute. Otherwise it is refused, because it is simply a normal movement.
- A wrong-item movement names one line and no `commitment_id`. A purchase line takes receipts and supplier returns; a customer line takes shipments and returns.
- Wrong goods going back cannot exceed what of that item is still out on that line.
- `beyond_order` is allowed on receipts for a purchase line only.
- A substitute cannot be accepted for a cancelled line, for the ordered item itself, for a non-stocked item, or for an item in another unit.
- An advice line must name an open or fulfilled supplier promise of the notice's supplier, with a positive quantity. One promise appears at most once per notice.
- A receipt into a shipment must match its direction, purpose and counterparty.
- Tenant isolation: nothing crosses companies.
- A stated value is recorded as stated and never recomputed (Constitution VIII).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A receipt MAY state `beyond_order` to bring in more than its purchase line still expects. *Received beyond the order* MUST report the surplus until the line is raised to what was received, net of supplier returns, or the surplus goes back against the line.
- **FR-002**: A fulfilled purchase line MUST accept one quantity revision up to what was received net of supplier returns, and refuse anything beyond it.
- **FR-003**: A receipt, shipment, return or supplier return MAY name the line it was meant for, carrying another item. It MUST NOT fulfil the line. *Wrong item delivered* MUST report it until the wrong goods have gone back, and it MUST NOT be reported as an unexplained movement.
- **FR-004**: The reviewed movement correction MUST be able to replace a movement with a wrong-item movement, and a wrong-item receipt with a receipt on the line once a substitute is accepted.
- **FR-005**: A person MUST be able to accept a substitute item for a purchase line through a reviewed action. Receipts of the substitute MUST then fulfil the line, and the purchase order's three-way match MUST name the substitute.
- **FR-006**: An inbound supplier notice MAY state advised quantities per purchase promise. A receipt MAY be recorded into the announced shipment. The shipment read MUST show advised, received and the difference per line. The three-way match MUST show what is in transit per line.
- **FR-007**: Every mutation this feature adds MUST use the reviewed, tenant-scoped application tools shared by Web, Chat/MCP and CLI.
- **FR-008**: When the journeys in scope are proven by a business story, the Business Journey Guide MUST promote them with executable evidence.

### Domain and Architecture Requirements

- **DR-001**: New tables are justified in the plan by repeated calculation, filtering or joining (Constitution III).
- **DR-002**: Surplus, wrong goods still out, advised against received and in transit are derived at read time and never stored.
- **DR-003**: Fulfilment of a line counts only movements that name it with `commitment_id`. A wrong-item link never adds to it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each of the seven journeys has a passing business story, or a recorded finding for what remains.
- **SC-002**: The journeys proven here are `supported` in the Business Journey Guide.

## Assumptions and Dependencies

- Builds on the reviewed receipt and shipment tools (spec 314), the movement correction, and the purchase revision (spec 310) and its fulfilled-line allowance (spec 313).
- The three-way match of spec 310 is the purchase order's read.

## Requirement Traceability

| Requirement | Scenario(s) | Evidence |
|---|---|---|
| FR-001, FR-002 | US1 | `tests/test_receipt_deviations.py`; stories H04, H05 |
| FR-003, FR-004 | US2 | `tests/test_receipt_deviations.py`; stories H06, D05 |
| FR-005 | US2 | `tests/test_receipt_deviations.py`; story H07 |
| FR-006 | US3 | `tests/test_receipt_deviations.py`; stories H17, G16 |
| FR-007 | All | `tests/test_receipt_deviation_adapters.py` |
| FR-008, SC-001, SC-002 | All | Catalog tests and Guide questions |
