# Implementation Plan

## Constitution Check
All eight principles PASS: existing evidence/Reality identity links; derived state
only at read time; no schema additions; tenant-scoped shared finance services; approved
scope and tests first; existing builder controls and traceability; registered narrow
service adapter with no dependency; received dates/amounts never rewritten.

## Design
Add a registered finance.aging node derivation for document-backed customer/supplier
position nodes. Derive once per traversal with canonical aging_register; join an
in-memory typed relation to documents by opaque ID. SQL still handles grouping,
filters, having and fanout safeguards. Add optional bounded document_ids to the
canonical aging service. Count reads on this connection for derived executions and
set timeout before derivation. Bound candidate documents at 20,000 with explicit
refusal. Expose real document-to-party links. Do not implement ambiguous party net
balance: unused credits are distinct from invoice remaining amounts.

Declare calendar-date semantics on document_date properties without schema changes.
Compile guarded ISO-date parsing; malformed source values become NULL. Send date-only
period bounds as YYYY-MM-DD, timestamps as ISO instants. Native date fields also get
date-only metadata. Apply debit/credit sign before SQL aggregation.

## Files and Order
Domain reporting_graph metadata; canonical core aging API and analytics derived
adapter/compiler/catalog; reporting_graph.yaml; api.ts and GraphSteps/GraphTemplates;
backend finance/date regression tests and web contract tests; durable analytics docs.

## Verification and Rollback
Tests first, reporting+finance suites, Ruff, full backend suite, web contracts/build/
format/i18n, spec policy and generator checks; Chrome inspection. Revert feature
metadata/adapter/UI; no migration. Reports using removed new nodes explicitly refuse.

## Risks
Service-backed queries use bounded bulk reads, not the original one-statement claim;
count is measured honestly. Current open amounts are not historical trends. The
20,000 bound is explicit, never silent truncation. Calendar unknowns retain source
traceability. No external calls or business mutations.
