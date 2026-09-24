# Verification Evidence

**Date**: 2026-09-24
**Scope**: Local Spec 257 implementation, regression verification and fresh external qualification
**External qualification**: Completed twice; the final follow-up run is recorded in
[final qualification follow-up](final-qualification-follow-up-2026-09-24.md).

## Qualification follow-up gates — 2026-09-24

- Focused affected backend suites: `219 passed, 2 skipped`.
- PostgreSQL migration verification: passed from the package working directory.
- Web contracts and production build: `363 passed`; build passed.
- Documentation contracts and production build: `85 passed`; build passed.
- Spec policy, Ruff, generated documentation freshness and `git diff --check`: passed.
- The API and MCP services were rebuilt from the current worktree and reported healthy on the new
  images before the fresh tenant was created.
- Fresh tenant: `ten_e19e802603`, company
  `CanisPro Tiernahrung Finalqualifikation 2026-09-24`.
- The external agent first verified the exact tenant with one read-only call, then used public MCP
  tools and authenticated Web owner review only.
- External protocol:
  `/Users/benediktsauter/Downloads/reality-mcp-testprotokoll-canispro-2026-09-24-finalqualifikation.md`.

The run qualifies FR-031, FR-032 and FR-035. FR-037 is qualified for order-backed purchase and
sales invoices. It also proves that additional deterministic failure families, the deployed schema
surface and free/credit-document finance evidence remain incomplete. These are not hidden as spec
257 completion; they are bounded by spec 267.

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

## Remaining product work

The external gate is complete. Reproducible residual findings are specified in
`specs/267-agent-qualification-gaps/spec.md`; they include proposal failure recovery, contribution
approval, shipment occurrence semantics, complete finance evidence, deployed schema fidelity and
read/Web explainability. Spec 257 requires no further implementation task.
