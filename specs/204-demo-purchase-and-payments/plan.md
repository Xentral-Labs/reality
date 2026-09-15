# Implementation Plan: The demo company also buys and gets paid

## Technical Context
`demo/international.py` (authored settlement vocabulary), `services/demo_profile.py`
(the seed), `services/tenant_policy.py` (the profile authority). No schema, migration,
API or web change.

## Constitution Check
All principles PASS. Every payment and payable goes through the same posting services a
person uses, so the ledger stays the one authority and nothing is written around it.
Receipts are movements against the commitment they fulfil, and the received quantity
stays derived. The authority widening is explicit, minimal and still bound to an
initializing run of the canonical preset in one transaction. No new table or field.

## Design
`SETTLEMENT` states, per authored case key, what happened to a seeded sales invoice:
`paid`, `part` or `open`. The weekly series settles from the oldest week forward, so
the newest invoices are the open ones, which is what an order book actually looks like.

`PURCHASES` states the six purchase orders: their item, supplier, ordered quantity, how
much arrived and how far the supplier invoice got. The seed records each receipt as a
movement against the purchase commitment, builds the supplier invoice the way it
already builds a sales invoice — `create_manual_document_with_lines` with
`billed_document_line_id` on the line, then `post_supplier_invoice` — and records the
supplier payment against it. `record_supplier_invoice` is not used: it commits inside
itself, which the profile scope rightly forbids.

`_PROFILE_OPERATIONS` gains exactly the six operations these two chains turned out to
need, found by probing rather than guessing: `post_customer_payment`,
`record_customer_payment`, `post_supplier_invoice`, `post_supplier_payment`,
`record_supplier_payment` and `allocate_settlement`.

## Verification / rollback
Scenario tests first: payments per state and the resulting receivable, the six purchase
states with their payables and received quantities, stock after the new receipts, and
identical settlement across two companies. Then the profile, company setup, demo data
and finance suites, and the full PostgreSQL suite. Rollback is a code revert; existing
demo companies are never rewritten.
