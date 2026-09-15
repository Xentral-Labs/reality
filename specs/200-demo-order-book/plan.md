# Implementation Plan: Demo order book spreads across customers

## Technical Context
Python service seeding only: `demo/international.py` (versioned authored vocabulary)
and `services/demo_profile.py` (the canonical seed). No schema, migration, API, job or
web change. The continuous stream in `integrations/demo_data.py` keeps its own draw.

## Constitution Check
All principles PASS. The change states authored source values on synthetic source
records and lets Documents and Commitments carry the counterparty they already carry;
nothing new is derived, stored or recomputed. Tenant scope, source lineage
(`demo_profile`), idempotent creation and confirmation boundaries are untouched. No
schema expansion, no second demo queue, no direct ORM write outside services.

## Design
`international.py` becomes the single customer authority: `CUSTOMERS` names the full
pool of twenty, and `DEMO_DATA_CUSTOMERS` derives from it, so the profile and the
stream can no longer diverge. Two authored tables state the buyer: `ORDER_CUSTOMERS`
maps operational case keys (`O01`–`O10`) and comparison families (`volume`, `price`,
`decline`, `credit`, `outlier`, `zero`, `usd`) to a catalog key, and
`WEEKLY_CUSTOMERS` states the buyer of each of the twelve weekly history orders. A
comparison family resolves once, so its prior and current window share a buyer.
`SUPPLIER_ITEMS` maps the three purchased materials to the supplier that makes them.

`demo_profile.order()` takes the resolved catalog key instead of the hardcoded `C1`/`S1`
and states it in both the party reference and `external_customer_reference`. The history
loop resolves the family from the case key and passes the same key to the invoice and,
for the credit case, to the credit note. `seed_profile` seeds the full pool, which raises
the profile's party count from eight to twenty-four.

Catalog keys and names stay identical, so `demo_data.preview()` keeps matching profile
customers by name and keeps adding only what is missing.

## Verification / rollback
Scenario tests first, extending `tests/scenarios/test_international_demo.py`: distinct
buyers, concentration bound, family consistency, invoice/credit party equality,
three distinct suppliers, and a stable mapping across two companies. Then the existing
company setup, demo profile history, demo data intake, storyline and analytics suites,
and the full PostgreSQL pytest run. Counts pinned in the profile contract and feature
documentation are updated in the same change. Rollback is a code revert: existing demo
companies are never rewritten, and no migration exists to undo.
