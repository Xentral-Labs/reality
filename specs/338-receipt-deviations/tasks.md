# Tasks: Receipt and Shipment Deviations

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Phase 1: Setup

- [ ] T001 Migration `0130_receipt_deviations`, models `Misdelivery`, `CommitmentSubstitute` and `ShipmentAdviceLine`, data model, isolation catalog and FK indexes.

## Phase 2: Over-delivery (FR-001, FR-002)

- [ ] T002 Tests first: a receipt beyond the order is refused without `beyond_order` and accepted with it; the surplus is reported; a revision to what was received clears it and one beyond is refused; a supplier return clears it.
- [ ] T003 `beyond_order` in `_append_movement`, `record_movement` and the receipt reviews; purchase lines in `_keeps_what_was_shipped`; the `received_beyond_order` class.

## Phase 3: Wrong item and substitute (FR-003, FR-004, FR-005)

- [ ] T004 Tests first:
  - a wrong-item receipt does not fulfil, is explained and reported, and its supplier return clears it;
  - wrong goods going back are bounded;
  - a same-item `meant_for` is refused;
  - a corrected customer shipment becomes a wrong item and the line opens;
  - a substitute is accepted and fulfils the line, including through a correction of a wrong-item receipt.
- [ ] T005 `services/receipt_deviations.py` for wrong items and substitutes; `meant_for_commitment_id` in `_append_movement`, `record_movement`, the correction and its preview, and the shipment reviews; the substitute check; the `misdelivery_outstanding` class; the unexplained-movement skip; the movement explanation.
- [ ] T006 `commitment_substitute_accept`: application tool, review, MCP, CLI and catalogs.

## Phase 4: Advice (FR-006)

- [ ] T007 Tests first: advised lines on a notice; a receipt into the shipment; advised, received and short in the shipment read; in transit per purchase line until received; the refusals.
- [ ] T008 `advised` on the notice and `shipment_id` on the receipt, through service, reviews and MCP schemas; the shipment read; `in_transit` and `substitutes` in the three-way match.

## Phase 5: Stories and Guide (FR-007, FR-008)

- [ ] T009 Stories H04, H05, H06, H07, H17, G16 and D05; adapter tests.
- [ ] T010 Promote the journeys: catalog, coverage, roadmap, coverage matrix, translations, `make docs-generate`.

## Phase 6: Verification

- [ ] T011 The relevant backend suite, the migration tests serially, `npm run test:i18n`, the spec-policy check, CI green.
