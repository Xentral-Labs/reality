# Implementation Plan

## Constitution Check
All eight principles PASS. Existing immutable movement/ledger/allocation evidence and
canonical settlement services remain authority. No schema or stored observation. New
read-time position identity separates backing anchors from multi-dimensional grain.
Owner approved scope; tested cutoff extensions precede graph/UI adapters. Tenant and
unit/currency filters remain mandatory. Unsupported history is explicitly refused.

## Design
Extract party_balance_rows from existing paginated finance wrapper. Propagate optional
effective_before through existing control/balance/reversal/allocation/credit helpers;
current defaults stay unchanged. Historical balance rows omit aging and use ledger
party/currency identity. Add a canonical inventory detail service and shared movement-leg
helper, exact null grouping and current-only reservations. Historical physical rows
read movement effects only and enforce imported opening coverage.

Extend the fixed derivation registry for current balances, detail stock and their
historical variants. Separate table anchor id from derived position_id. Derived node
keys/units/edges validate against registered columns. All data travels as bound typed
JSON, once per required service. Cutoff comes from validated snapshot_date equality
filters; all aliases of one historical service must agree. No new traversal syntax.

Expose Property.input=date for cutoff editing, exclude parameters from generic period
controls, and retain explicit cutoff conditions through templates/chat/Cypher. Historical
nodes lack reserved/available/overdue metrics. Current and historical templates include
opaque identity plus real unit/currency axes. Input families have explicit caps before
materialization, including financial allocations/ledger groups and inventory movement
and reservation detail counts.

## Validation and rollback
Tests first; service, reporting, finance, tracking/history tests; full backend, web
contracts/build/format/i18n, Ruff/spec/docs and native Chrome. Revert declarations,
optional parameters and adapters; no data rollback. Existing analyses retain keys.
