# Validation guide

Baseline: 140 passed 1486 backend tests (7 existing skips), 123 frontend contracts and the complete unified browser matrix.

Use disposable PostgreSQL and service-created fixtures: two items with different units, equal-label items, active/released reservations, receipt/shipment/correction history, two companies and an actual current exception resolved through canonical reservation. Prove exact item filters before paging, server totals, correction roles, customer-only case targets and no mutations from GETs.

Run focused tests before full suite (`PYTHONPATH=src ../../.venv/bin/pytest -q` from packages/reality-core). Run make lint/spec-check, frontend format/contracts/i18n/build, all unified browser harnesses and docs formatting/tests/build. Verify actual isolated preview on ports 5177/8007. Record results only after checks pass; no deployment or retirement is authorized by technical completion.

Pre-implementation analysis: eight requirements map to eleven tasks and executable evidence. Corrected two vocabulary mismatches during review: canonical exception severity is `normal`, and customer-return movement type is `return`; adjustment and consumed-reservation states remain available. No unresolved clarification, missing coverage or constitutional conflict remains. Built-in requirements checklist: 8/8 passed. No extension hooks configured.

## Implementation verification — 2026-09-07

- Final PostgreSQL suite: **1491 passed, 7 existing skips**, using two workers
  with load-scope distribution. Log: `/private/tmp/reality-141-full-final.log`.
- Focused warehouse and attention tests: **5 passed**. Initial red evidence
  recorded the missing attention module before implementation.
- Frontend contracts: **124 passed**. Localization: **1400/1400** covered in
  each of en/de/nl/es. Formatting and production build passed.
- Docs: formatting, **45 tests**, and production build passed.
- Python lint, spec policy and whitespace checks passed.
- Authenticated isolated sample preview: finding → explanation → Keller
  delivery → exact-item stock/reservations/movements → Inspector and reload
  passed. Synthetic fixture creation was confined to the dedicated preview
  database and tenant. No business data from another company was changed.

## Technical review

The review confirmed tenant-scoped exact-item joins, canonical stock and
exception semantics, customer-only case links, preservation of corrected
movement history and read-only navigation. A visual review identified missing
party context on delivery findings; the final implementation batch-loads the
linked customer/supplier and item, with service coverage for the displayed
context. Current guidance stays faithful to the existing catalog language.

Responses are bounded, but the existing exception engine derives the company
set before slicing. Movement correction roles reuse the canonical lookup per
returned row. Neither is presented as a new scalability guarantee. Advanced
warehouse mutations, Finance migration and legacy/Playground retirement remain
outside this increment. Product-owner visual acceptance remains distinct from
technical completion. The local preview remains available on ports 5177/8007.

The final operations browser run passed traversal, empty/error/resolved states,
company reset, Inspector reload/focus and absence of mutation requests, producing
64 screenshots. Desktop stock, mobile attention with party context and dark
movement history were visually reviewed. The existing foundation and delivery
harnesses also passed, including case/launcher/Chat entry, confirmation recovery
and their full locale/theme/viewport matrix. Logs:
`/private/tmp/reality-141-browser-final.log` and
`/private/tmp/reality-141-foundation-regression.log`.

The Analytics/master-data regression harness passed drill-down, all four
reference families, review/reload/confirmation, lost-response recovery without
replay, edit snapshots, retry, search and keyboard focus, with 64 localized
screenshots. Log: `/private/tmp/reality-141-workspace-regression.log`.

All eleven tasks are technically complete. No critical review finding remains.
The opt-in local preview is ready for owner review; no deployment, merge or
legacy/Playground retirement is claimed.

FR-009 explanation card: operations browser passes catalog loading/retry, expansion, search-empty state, Escape and focus return, retained finding flow and 64 localized screenshots. Shared catalog close handler ignores queued development-remount close events while the dialog is open. German desktop explanation card and catalog screenshot reviewed. 131 frontend contracts, production build, 1897-key localization audit, formatting, spec policy and diff checks pass. No backend or business data changes.
