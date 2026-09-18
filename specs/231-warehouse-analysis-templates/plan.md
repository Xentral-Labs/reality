# Implementation Plan

## Constitution Check
All eight principles PASS: retain Reality movements/reservations and original item
identity; reuse core.inventory_rows; no schema, no stored derived authority; tenant
scope at preflight, service and join; approved scope with tests first; explainable
labels and existing UI; bounded registered adapter with exact quantities.

## Design
Add a warehouse.inventory registered derivation for a new stock_position item-backed
node, preserving the existing plain item node. Use the same typed JSON relation pattern
as finance. Derive once per requested service per traversal, not per row. Generalize
only the tiny fixed registry for two known services, so finance paths remain compatible.
Expose physical/reserved/available measures and fields. Add identity-based stock→item
edge for tracing to movements/reservations. All quantities are current/all locations.
No inventory arithmetic in graph SQL or browser.

The adapter preflights bounded tenant inputs before core.inventory_rows. Ordinary
queries retain single SQL aggregation; service paths report measured read counts.
Use existing unit and time-bucket guards. Six declarative templates retain identity,
unit/currency axes and use HAVING for positive reserved/negative available/positive
open amounts. No new interface, package or migration.

## Verification and Rollback
Tests before implementation, canonical and warehouse parity; reporting/finance/stock
suite, full backend, web/build/i18n/format, lint/spec/docs and Chrome. Rollback removes
new declarations/adapter; dependent reports refuse explicitly, no data rollback.
