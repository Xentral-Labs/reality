# Feature Specification: Demo order book spreads across customers

**Language**: English

**Created**: 2026-09-15
**Status**: Accepted scope (user: every order should state its own buyer, with two or
three regulars ordering more)

## Context and Intent
The canonical international demo profile seeds 34 sales orders, 24 sales invoices and
one credit note, and states the same buyer on every one of them. The remaining customers
exist as master data without a single document, so the first company a new account opens
reads as one customer's ledger rather than an order book. Party balances, customer
holds, delivery cases and the analytics workspace all collapse onto one counterparty.
The continuous Demo Data stream already spreads demand across the pool; only the seeded
baseline does not.

### Non-Goals
The arrival vocabulary, rate and skew of the continuous Demo Data stream; the number of
items, locations or documents in the profile; retroactive rewriting of demo companies
that already exist; the payload schema, profile version or source namespaces.

## User Scenarios & Testing
### US1 — Read a plausible order book (P1)
Someone who opens a fresh demo company sees orders, invoices and open items distributed
over the customer pool: a few regulars with repeat business and a long tail of buyers
with a single order each. No single customer holds the whole book.

### US2 — Compare like with like (P1)
Every authored comparison case keeps both of its windows on the same buyer, so a prior
and a current order state the same counterparty and a price, volume or currency
comparison still reads as one customer's changed behaviour.

### US3 — Follow one order to its money (P1)
An invoice states the buyer of the order it bills, and the credit note states the buyer
of the invoice it corrects, so party balances, open items and dunning stay consistent
with the operational documents.

### Edge cases
Existing demo companies keep the documents they have; nothing is rewritten or migrated.
A Sandbox that connects Demo Data after the profile reuses the profile's customers by
name instead of creating duplicates. Purchase orders state suppliers, never customers.

## Requirements
- **FR-001**: The canonical profile seeds the full customer pool as master data, so a
  demo company created without live simulation already holds every pool customer.
- **FR-002**: Every seeded sales order states an authored buyer. At least eighteen
  distinct customers appear across the seeded orders and no customer holds more than a
  sixth of them. Two or three regulars hold repeat business; the rest hold one or two
  orders.
- **FR-003**: Both windows of an authored comparison family (volume, price, decline,
  outlier, currency) state the same buyer.
- **FR-004**: A seeded sales invoice states the buyer of the order it bills; the seeded
  credit note states the buyer of the invoice it corrects; the order's
  `external_customer_reference` states that same buyer's catalog key.
- **FR-005**: The three seeded purchase orders state the supplier that fits their
  material instead of all naming the first supplier.
- **FR-006**: Assignment is authored versioned vocabulary, not a runtime draw: the same
  profile version seeds the same buyer for the same case key in every company.
- **FR-007**: The payload schema, `profile_version`, `preset_version`, source namespaces
  and case manifest keys stay unchanged, so existing companies, storylines and the
  Demo Data connection preview keep working.

## Success Criteria
A freshly created demo company reports at least eighteen distinct customers across its
34 sales orders, with the largest holding no more than five. Each comparison family
reports one buyer for both windows. Invoice and credit-note parties equal their order's
party. The three purchase orders report three distinct suppliers. Item stock, case
manifest, commitment counts and the ready status are unchanged.

## Assumptions and Dependencies
`demo/international.py` is the versioned vocabulary authority and already names twenty
customers for the Demo Data pool; the profile adopts that same pool so the two never
diverge. Catalog keys `C1`–`C20` and the existing customer names stay stable, which is
what lets a populated Sandbox match them on connection. No schema change, no migration,
no constitutional exception.

## Requirement Traceability
| Requirement | Proof |
|---|---|
| FR-001, FR-002, FR-005 | Scenario test over a created company: party count, distinct buyers, concentration bound, suppliers |
| FR-003, FR-004 | Scenario test over comparison families, invoices and the credit note |
| FR-006 | Two companies from the same profile report identical buyer-per-case mapping |
| FR-007 | Existing profile, Demo Data intake, storyline and company setup suites stay green |
