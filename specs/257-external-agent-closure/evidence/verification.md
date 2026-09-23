# Verification Evidence

**Date**: 2026-09-23
**Scope**: Local Spec 257 implementation and regression qualification
**External qualification**: Not included; the fresh deployed CanisPro run remains T075.

## Backend and PostgreSQL

- `make test`
  - Result: `4139 passed, 9 skipped, 1 warning in 2349.88s (0:39:09)`.
  - The warning is the existing SQLAlchemy transaction-deassociation warning in
    `test_storyline_library_api.py`; it did not fail the suite.
- `make lint`
  - Result: passed after Ruff organized imports using the package configuration.
- Focused costing and demo story:
  - Result: `129 passed in 294.54s`.
- Focused clean-proposal and public-read story:
  - Result: `19 passed, 104 deselected in 2.77s`.
- Focused return and invoice-linked credit story:
  - Result: `14 passed, 219 deselected in 5.26s`.
- Focused finance closure story:
  - Result: `47 passed in 24.61s`.
- Fresh-tenant evidence harness:
  - Result: `5 passed in 4.71s`.

The complete suite initially identified two stale assertions: owner authority was expected during
an effect-free carrying-value preview, and the application-reference event count did not include
the two new dunning events. Both assertions were corrected to the reviewed contracts, their
focused rerun passed (`2 passed in 12.32s`), and the complete suite then passed as recorded above.

## Web

- `make web-build`
  - Prettier: passed.
  - Node contracts: `341 passed`.
  - Localization audit: `en`, `de`, `nl`, and `es` passed with zero missing or invalid entries.
  - TypeScript and Vite production build: passed.
  - Vite retained the existing large-chunk advisory; it is not a build failure.
- `npm run test:cost-explanation-contract`
  - Result: `5 passed`.
- Focused browser journey:
  - `npm run test:cost-explanation-browser` passed against the local production-facing Web
    surface with Chrome and a temporary Playwright Core installation.
  - It verified exact retained values, stale and uninitialized guidance, Inspector linkage,
    tenant switching, and GET-only cost-query behavior.

## Specification and documentation

- `make spec-check`: passed.
- `git diff --check`: passed.
- `make docs-generate`: passed and refreshed the English/German Tool Usage artifacts and JSON
  reference.
- `node --test apps/docs/scripts/docs-contract.test.mjs`: `47 passed`, including the live MCP
  comparator contract for names, required fields, enums, and nested input shapes.
- `make docs-catalog-check`: passed after commit `1026c84b`; regeneration produced no diff in the
  checked generated documentation paths.
- Deployed MCP comparison was not run because no redacted deployed `tools/list` capture was
  supplied. T074 remains open.

## Remaining external gates

- T074: compare a redacted deployed `tools/list` capture with the generated reference.
- T075–T076: execute the fresh public-surface CanisPro workflow and populate the final closure
  matrix from its mutation receipts and independent reads.
- T081 found no CRITICAL cross-artifact or Constitution issue. The final release decision remains
  dependent on the external evidence above.
