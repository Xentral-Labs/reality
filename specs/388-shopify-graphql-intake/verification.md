# Verification and limits

2026-11-09 isolated implementation lane; no provider calls or owner/company database access.

- Spec policy passed. In-source business annotations passed (675 described functions; no missing root bindings).
- Package-scoped Ruff0.16.7 passed initially. CI latest0.17.4 exposed a pre-existing unused DTZ001 noqa in test_cost_census_serialization.py; the obsolete annotation was removed without changing the intentionally naive timestamp or its refusal assertion, and latest Ruff passed.
- Focused PostgreSQL suite:90passed,2skipped across GraphQL intake, legacy Shopify intake/update guards, actual MCP, action discovery and tenant isolation families. Original entity and source hash/line traceability retained; preparation never applies effects.
- Additional migration-related finance regressions:71passed in repository-required package cwd.
- Generated catalog/guide/Product Advisor artifacts regenerated with maintained formatter. Reference-generator unit tests16passed.
- Complete backend attempt:690passed and one action-reference fixture mismatch before interruption. Existing fixture generator repaired that new-command dependency; its focused regression subsequently passed. CI then required formatting that generated Web fixture, now corrected with maintained Prettier. The complete suite was not rerun to completion and is not claimed green. Full CI/reviewer gate remains open.
- Borrowed owner environment initially lacked declared MCP2 SDK; it was not modified. An isolated worktree venv installed declared dependencies for final focused proof. All database tests used an owned disposable PostgreSQL container and temporary test databases, never an existing company database.

## Deployment limit

This candidate targets current Reality code/schema. It is not a drop-in update for historical0099 deployments: current reviewed preparation unconditionally needs CompanyTimeZone (0138), and source-unstated amounts rely on0141 constraints. Do not upgrade or migrate an existing database implicitly. A separately reviewed missing-buyer capture/refusal compatibility overlay is distinct scope and cannot claim current full proposal support.
