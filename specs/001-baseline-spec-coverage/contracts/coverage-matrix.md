# Contract: Specification Coverage Matrix

The canonical matrix will live at `docs/SPEC_COVERAGE_MATRIX.md`. It is a discovery
index, not a replacement for feature specifications.

## Capability summary

| Baseline | Status | Primary contracts | FR verified/gap/intended | Open decisions | Last reviewed |
|---|---|---|---|---:|---|
| `003-tenant-access` | Draft/Reviewed | links | counts | count | date |

## Source coverage

| Source | Type | Primary baseline or authority | Coverage | Notes |
|---|---|---|---|---|
| `docs/features/tenancy.md` | contract | `003-tenant-access` | Covered/Gap | detail |

Source types are `contract`, `catalog`, `service/tool`, `adapter/UI`, and `test`.
Coverage values are `Covered`, `Gap`, `Cross-cutting`, and `Excluded` with a reason.

## Deterministic source boundaries

The coverage inventory MUST scan these repository sources:

- Durable contracts: `AGENTS.md`, `.specify/memory/constitution.md`, `docs/*.md`,
  `docs/decisions/*.md`, and `docs/features/*.md`.
- Catalog concepts: every table key in `backend/config/data_model.yaml` and every
  application/tool entry in `backend/config/application_catalog.yaml`.
- Shared behavior: public functions in `backend/src/reality/services/` and registered
  tools in `backend/src/reality/tools/`.
- Adapters and product surfaces: commands/routes under `backend/src/reality/cli/`,
  `backend/src/reality/web/`, `backend/src/reality/mcp/`, and routed pages/operations
  under `frontend/src/`.
- Executable proof: every `backend/tests/test_*.py`,
  `backend/tests/scenarios/test_*.py`, and frontend test file when present.

Generated bundles, caches, build metadata, vendored dependencies, fixtures without
behavior assertions, private helper functions, and deployment-only files are excluded.
Every exclusion discovered inside an included source family requires a matrix row and
reason. Public means callable through a registered service/tool/adapter boundary or
observable through a routed product surface; filename presence alone is not public
behavior.

## Requirement evidence table

Every baseline spec contains:

| Requirement | Status | Contract | Implementation | Executable proof | Decision/gap |
|---|---|---|---|---|---|
| `FR-001` | Verified as-is | path/section | path/symbol | test path/name | — |

Paths are repository-relative and name a section, symbol, or test where practical. A
row cannot say `Verified as-is` if any evidence column is missing or its test is red or
skipped.

## Review state

- `Draft`: evidence collection or owner decisions remain.
- `Reviewed`: scope and all material decisions are owner-approved. Evidence gaps may
  remain; Reviewed does not mean fully implemented.

Update the matrix whenever a baseline, durable contract, catalog concept, or public
capability family is added, removed, or reassigned.
