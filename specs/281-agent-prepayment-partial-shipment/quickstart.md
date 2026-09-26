# Quickstart

Ask Chat to request prepayment for a future-dated order, inspect the pending invoice proposal, and confirm it as a human. Record and allocate payment. Then ask what quantity can ship now; inspect a bounded shipment proposal, change stock or payment before confirmation to prove stale refusal, refresh, confirm, and verify the remaining commitment quantity.

## Verification Record

- 42 focused Chat, scope-security and streaming tests passed.
- Both provider adapters expose readiness, sales-invoice proposal and shipment-dispatch proposal tools without approval or rejection tools.
- Lint, specification policy and generated catalog drift checks passed.
- The localhost Headless Chrome story passed for two customers, future dates, partial stock, prepayment evidence, projection freshness, exact Commitment Inspector trace, 390 px and 1440 px layouts, and no business mutation.
- The PostgreSQL business story proves that 4 stocked and reserved units can ship against 10 open units and that exactly 6 remain open.
- The public MCP story proves that invoice and shipment calls remain proposals with zero business effect until human confirmation; after full prepayment and a confirmed four-unit shipment, six units remain open on the future-dated order.
- The multi-customer matrix proves that agent reads distinguish a ready future order, a fully stocked but unpaid prepayment order, and an order with only four of ten units physically present and reserved.
- Sales Readiness now hands the exact order into the existing reviewed sales-invoice form and the server-derived shippable quantity into the existing reviewed shipment form; neither handoff executes a change.
- Localhost Chrome verified that the invoice dialog selects `doc-prepay`, the shipment dialog carries `commitment-partial` with quantity `4`, and opening either dialog causes no business mutation.
- After a confirmed action, the shared settlement event reloads Readiness and shows a visible notice that directs the operator to current blockers and projection freshness rather than claiming pending data is current.
- Readiness blocker cells now state projected evidence directly, including reserved/open quantity, physically available/open quantity and the remaining prepayment amount; raw blocker codes remain technical data rather than operator-facing copy.
- Prepayment-invoice preparation is offered only for `prepayment_invoice_missing`. If readiness already links an invoice, Browser and Chat explain received and remaining payment evidence instead of suggesting a duplicate invoice.
- Readiness actions are withheld for pending, failed, uninitialized or missing projection metadata. The last completed evidence and freshness warning remain readable until a current stored projection is available.
- After the four-unit partial shipment, a later six-unit supplier receipt and reservation feed a second agent proposal. It has zero effect before confirmation and closes the exact six-unit remainder after human approval.
- The complete PostgreSQL backend suite passed with 4,419 tests passed, 10 skipped and no failures; the complete Web contract suite passed with 406 tests and no failures.
- The production Web build, EN/DE/NL/ES localization audit, lint, specification policy, generated catalog drift and whitespace checks passed.
