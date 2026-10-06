# Implementation plan

## Constitution Check

| Boundary | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Normal source ingest, order/invoice/movement proposals and canonical reviewed Shopify intake retain opaque receipts and sources. |
| Tenant and admission | PASS | Named ordinary local test company through create_company; active admitted owner required. Existing Sandbox restrictions remain intact. |
| Received amounts | PASS | Profile states order/invoice/credit/payment/fee/payout amounts explicitly; no source total is computed from live records or inferred price×quantity. |
| Shortest true links | PASS | Return movement → announcement → original commitment; invoices bill order lines; allocations link ledger entries; no new database links/status fields. |
| Approval | PASS | Finite built-in fixture confirmed at launch. Live custom operator requires exact review returning launch principal and normal service approval. |
| Independent evaluation | PASS | Authored sources and verified receipts create expected per-order quantities/postings; observation never supplies expected amounts or balances. |
| Schema/scheduler | PASS | No schema, migrations, production queues or business-rule changes. Local finite ordinal controller, real application clock. |

## Design and layering

`profiles/general_company/complete.yaml` is the central source script; `complete_world.py` owns released requests, private future reactions, expected stock and explicit posting/settlement state. `bridge.py` uses normal proposals and rejects preparation effects or unreviewed live decisions. `complete_observer.py` reads tenant-scoped stock lineage, exact posting groups/allocations/open balances and preserved shipment/package evidence. `complete.py` coordinates the finite month and scores actual correct-destination on-time quantities independently of core correctness.

`shopify.py` and its clearly synthetic profile use existing reviewed order/refund intake and generic provider payout settlement. Statements are exogenous. Known-customer funds without invoices are held/unallocated, while an unknown shop reference remains unmatched; bank and clearing have independent per-account oracles. Canonical payment_rows measures held funds separately from settleable invoices/credits.

Existing spec373 small Sandbox and spec372 fixed day/week remain regression profiles. Default CLI selects the extended profile; custom policy modules are trusted local decision code with interactive exact-action review. No model provider is chosen or automatically enrolled.

## Verification and rollback

Tests written before implementation; initial missing implementation observed failing. Cover full prompt month including independently hand-checked final quantities/cardinalities/balances, delayed/idle/wrong-address outcomes, partial/cancel/return/credit/refund checkpoints, corrupted financial observation, exact principal approval, detached views and private future supplier/customer isolation. Shopify proofs cover preserved reviewed sources, fees/deposits/unknown lines, unallocated funds without invoices, real package proof and no-effect statement replay.

Tests use temporary PostgreSQL companies rolled back by existing fixtures. CLI creates a fresh named local company rather than modifying a baseline. Unknown execution is not automatically repeated; durable recovery/resume is unsupported and requires receipt reconciliation. No migration/catalog/web gate is needed because production schema, vocabulary and interfaces are unchanged. Run complete backend, targeted final acceptance, lint, spec and whitespace checks. Retain XML/logs, hashes and comparison journals.

## Correspondence extension (FR-009)

User authorization: add missing supplier emails and agent replies to the existing scenario. Scope is local synthetic correspondence for the complete profile; Shopify keeps its existing synthetic source semantics. Constitution Check: PASS for source preservation, explicit tenant-scoped opaque references, no schema or external effects, authored notice timing and unchanged booking oracle. The normal source ingest tool archives payloads; no production mail approval/claim/report is asserted.

Add a small correspondence adapter with deduplicated message identities, released thread context and configured templates in the versioned YAML. Emit customer follow-ups and supplier notices before operator decisions; emit built-in responses only after accepted business effects. Custom reply commands store explicitly proposed drafts, not sent mail. Use existing viewer message state rendering and explicit party filtering. No dependencies, migrations, product UI or scheduler changes.

Tests first: actual complete month communication/source/viewer linkage; idle and custom no invented replies; draft reply validation; future supplier timing and unchanged final stock/finance. Existing core corruption and approval regressions remain required. Browser proof includes a new communication journal. Rollback removes this local adapter/configuration without altering accepted business records.
