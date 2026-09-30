# Sales-Gap Roadmap

Spec impact: none. This orders the partial Business Journey Guide entries by sales relevance and links
one short draft specification per capability package. Each draft is clarified and accepted before it is
planned; the Guide promotes a journey only when a business story proves it (specs 292 to 294).

Ordered on 2026-09-29 against the catalog on `main` (92 supported, 59 partial, 74 missing, 3 out of
scope). The order is a judgment of how often a prospect from German trade or e-commerce asks, and
whether the gap can lose a deal; it is not measured. Seven journeys whose feasibility is uncertain
(F04, F08, H09, P02, P05, P08, B09) are left for a test round of their own.

## Tier 1: comes up in almost every demo

| Rank | Tier | Specification | Journeys |
|---|---|---|---|
| 1 | 1 | [295 Dunning Run and Escalation](../../specs/295-dunning-run/spec.md) | N04 (implemented; supported) |
| 2 | 1 | [296 Shop Order Changes and Refunds](../../specs/296-shop-order-changes/spec.md) | L04, L05, A16, A09, F12, A17 (implemented; supported) |
| 3 | 1 | [297 Chargebacks, Returned Direct Debits and Payment Fees](../../specs/297-payment-returns-fees/spec.md) | C15, E08 (implemented; supported) |
| 4 | 1 | [298 Automatic Credit Hold](../../specs/298-automatic-credit-hold/spec.md) | C07, C08, R08 |
| 5 | 1 | [299 Invoiced Not Shipped, Down-Payment and Pro-Forma Invoices](../../specs/299-invoiced-not-shipped/spec.md) | E03, Q01, E11, C14 |
| 6 | 1 | [300 Multichannel Oversell, Deadlines and Peak Intake](../../specs/300-multichannel-oversell/spec.md) | B14, L02, L07 |
| 7 | 1 | [301 Unit Conversion Between Purchase and Sales Units](../../specs/301-unit-conversion/spec.md) | O05 |
| 8 | 1 | [302 Reorder Point and Replenishment Proposal](../../specs/302-reorder-point/spec.md) | G02 |
| 9 | 1 | [303 Orders Served From Several Warehouses](../../specs/303-multi-warehouse-orders/spec.md) | A02, B06, D02 |
| 10 | 1 | [304 Blocked Stock and Best-Before Dates](../../specs/304-blocked-stock/spec.md) | B05, J05, H08, H15 |

## Tier 2: important for specific customers or in depth

| Rank | Tier | Specification | Journeys |
|---|---|---|---|
| 11 | 2 | [305 Serving Backorders on Receipt](../../specs/305-backorder-allocation/spec.md) | B08, H16, B07, R02, G13 |
| 12 | 2 | [306 Ship-Complete and No-Partial-Delivery Rules](../../specs/306-ship-complete/spec.md) | B10, M06 |
| 13 | 2 | [307 Stock Count Sessions](../../specs/307-stock-count/spec.md) | J02, R07, J03 |
| 14 | 2 | [308 Customer Item Numbers](../../specs/308-customer-item-numbers/spec.md) | M02 |
| 15 | 2 | [309 Foreign-Currency Purchasing](../../specs/309-foreign-currency-purchasing/spec.md) | G08, R06, I11 |
| 16 | 2 | [310 Supplier Confirmations, Minimum Quantities and Three-Way Match](../../specs/310-purchasing-depth/spec.md) | G09, G06, G12, I01 |
| 17 | 2 | [311 EDI Order Changes](../../specs/311-edi-order-changes/spec.md) | M04, R05 |
| 18 | 2 | [312 Customer Pickup and Late 3PL Confirmations](../../specs/312-shipping-modes/spec.md) | D15, D12 |
| 19 | 2 | [313 Over-Billing and Quantity Lowered Below Delivered](../../specs/313-billing-deviations/spec.md) | A05, E07 |

Some packages also cover a journey that is missing today rather than partial (D02, H08, H15, M06,
J03, I11), because the same capability closes it.

## Tier 3: rare or deliberate, no specification

| Journey | Title | Why |
|---|---|---|
| M09 | Annual rebate at year end | deliberately outside Reality |
| R01 | Combined story with a released prepayment | by design (spec 275 FR-005) |
| J09 | Consignment from the supplier | rare |
| P06 | Two systems contradict each other | rare, general mechanism |
| Q05 | Company time zone | rare |
| D18 | Duplicate shipment reports from outside | needs a shipment source first |

## Working through it

1. Pick the next draft by rank, clarify its open questions with the owner and set it to Approved.
2. Plan and task it as usual (`docs/SPEC_DRIVEN_WORKFLOW.md`), including the Guide promotion.
3. After merge, update `docs/scenarios/coverage.md` and this roadmap.
