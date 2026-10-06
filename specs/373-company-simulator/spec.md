# Reactive company simulator

**Language**: English

## Context and Intent
Replace prescribed operator replay with a bounded reactive world. Retain spec 372 as a separate regression fixture. The user approved implementation of a shared simulator with general-company and eventual Shopify profiles.

## User Scenarios & Testing
Compare prompt, delayed and idle operators against the same released customer demand. Delayed purchases shift supplier arrivals; late shipping shifts customer arrivals. Correct bookings remain correct even when customer goals fail.

## Requirements
- **FR-001**: Support an explicitly confirmed, fresh empty Sandbox run with a configurable 1–30 day horizon.
- **FR-002**: Release authored customer requests at their day; operator views exclude future demand and private oracle state.
- **FR-003**: Schedule supplier receipt only after an accepted purchase; schedule customer arrival only after accepted dispatch.
- **FR-004**: Reconcile independent stock, reservations and customer/supplier open quantities after each day through read-only observation; stop on discrepancy.
- **FR-005**: Report business outcomes separately from booking correctness, preserving event times and exact tool receipts.
- **FR-006**: Provide deterministic prompt, delayed and idle bounded test operators and a read-only operator view interface. Do not grant arbitrary AI approval authority.
- **FR-007**: Keep Shopify profile pending authentic source examples; no external connections or invented native payload contract.

## Success Criteria
Prompt operator delivers released requests by deadline; delayed operator misses some while maintaining a correct core. Purchasing is demand dependent, not a predefined calendar. Two runs have different tenant IDs.

## Requirement Traceability
FR-001–FR-006: tests/scenarios/test_company_simulator.py, scenarios/company_simulator/controller.py. FR-007: profiles/shopify_company/README.md.

## Non-Goals
This first operational slice does not cover financial postings, returns, cancellation, real email transport, arbitrary AI operators, destination/package proof, durable resume or an unlimited producer. Subsequent slices must extend independent oracles, not disguise missing coverage.

## Assumptions and Dependencies
Application time stays real; simulator ordinal days are recorded separately. Existing proposal tools and Sandbox creation are reused. Supplier quotes are fixed integer packs with author-stated amounts. Simulated arrivals are world evidence, not carrier integration proof.
