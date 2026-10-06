# Research decisions

## Permission boundary
The original operational Sandbox does not admit outbound_delivery_plan; the first failing extended test proved PlaygroundOperationDenied at its exact approval. Use a named ordinary local test company through create_company, requiring active owner admission. Preserve all Sandbox policy. This is a local test lab, not an external shop connection.

## Financial source chain
Invoice tools post automatically. Payment/refund tools may legitimately omit a source unless supplied; retain a separately authored simulated_bank_transaction via source_record_ingest and pass its exact source ID. Source values remain explicit profile amounts. Verify per-action two-sided postings, exact party/document/account/amounts, settlement allocations and open balances. Cash balance alone is insufficient; provider clearing and bank account IDs need separate expectations.

## Logistics
Outbound plans preserve recipient/address at dispatch. Every package needs carrier-delivered evidence. Structured undeliverable failure restores stock and reopens commitments; tracking exceptions alone do not. Existing shipment_receive rejects return_announcement_id in packaged movement fields; use the supported movement_create return payload to retain the actual announcement link. A return does not undo fulfilled quantity; a credit does not move inventory.

## Shopify evidence
Existing order_10473.json and intake examples are synthetic. Use authored synthetic orders/refunds with explicit line/header totals and existing reviewed intake; original source payloads remain intact. Provider payout statements use production payout_statement authority, not an invented Shopify Payments native format. Customer refund settlement references the original invoice to find its related credit, not a credit number mislabeled as invoice_number. Audit event cutoff may advance on replay; accepted record IDs, quantities and postings must not.

## Custom operator
A copied released-world view plus actual Reality/financial observations feeds a callable. Built-in finite policies are explicitly confirmed fixtures. Custom exact proposals require a review callback returning a real launch principal and normal service confirmation. Boolean approval/read access does not confer that authority. Without review, halt with the concrete pending proposal and preserve accepted evidence.

## Observation correction proved by production behavior

Provider charges must be exogenous, not conditional on an agent invoice. Payout planner records known-customer funds even without an invoice; these are held/unallocated payments, not unmatched source lines. Unknown shop references remain unmatched. The idle profile consequently observes the same bank deposits with independently expected held payment/refund balances. Use canonical payment_rows for payment allocation state; open_invoice_amount rejects payment documents as non-settleable targets. A deliberate unknown EUR10 charge explains clearing -10; prompt last invoice open10 and idle held incoming80/refunded10 are separate checkpoints.

## Local correspondence extension

Decision: keep the existing arbitrary-source simulator boundary and add explicit local synthetic message/thread references, rather than implementing mailbox transport or pretending production email approval/claim/report ran. Canonical `email_workflow()` v5 and the email handoff contract were read. Rationale: the requested rehearsal needs observable scripted dialogue, while real dispatch requires a separate exact reviewed authorization and outcome contract. Alternatives: fabricated UI-only replies would have no retained Source; production provider integration would expand the requested scope.

Supplier notices depend on accepted purchases and release one ordinal day later; delay schedules become visible only through that source. Receipt notices depend on actual accepted warehouse receipts. Baseline replies are finite fixture actions; idle/custom agents receive no auto-generated answers. Custom replies preserve their exact subject/body as unsent draft evidence. Existing source ingest and viewer party association suffice; no schema, model provider or new scheduler is needed.
