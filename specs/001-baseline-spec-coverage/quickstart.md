# Quickstart: Validate the Specification Baseline

## 1. Policy and formatting

```bash
make spec-check
git diff --check
```

Expected: both commands pass and every numbered spec has required sections.

## 2. Coverage completeness

Inspect `docs/SPEC_COVERAGE_MATRIX.md` and confirm all feature documents, catalogued
business tables, backend test families, and thirteen capability specs have an owner or
explicit cross-cutting/exclusion classification. No `Verified as-is` row may lack
contract, implementation, or green test evidence.

## 3. End-to-end baseline review

Choose `003-tenant-access`. Verify business-oriented scope, evidence status per
requirement, tenant/service boundaries, material decisions, and human review state.
Expected: authority and evidence can be located in under five minutes.

## 4. No product behavior change

```bash
git diff --name-only -- backend/src backend/migrations frontend/src
```

Expected for isolated baseline commits: no output. Pre-existing unrelated working-tree
changes must be separated before applying this assertion.

## 5. Regression gates

```bash
make lint
make test
make frontend-build
cd frontend && npm run i18n:audit
```

Expected: Ruff, pytest, and build pass. The i18n audit currently reports missing
catalog entries but exits successfully; keep its report visible.

## 6. Owner review drill

Propose a representative future change. From the matrix, locate its baseline and
cross-cutting contracts and identify affected requirements in under five minutes.

Example: "Correct an existing manual DocumentLine." Start at the matrix table ownership,
open `006-documents-evidence`, locate the `FR-008` Documented gap, then read Constitution
principles I–V and the Data Model/Web Document contracts. The result is a new change spec
covering correction semantics, downstream Reality locks, audit, tenancy, confirmation,
and explanation before any implementation begins.
