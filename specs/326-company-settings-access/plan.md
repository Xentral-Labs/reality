# Implementation Plan: Company Settings Access

## Technical Context
Python 3.12/SQLAlchemy/PostgreSQL/FastAPI; TypeScript/React/Vite; existing MCP SDK. No new dependencies, schema or infrastructure. Isolated branch `codex/fix-account-settings`; feature directory `326-company-settings-access`.

## Constitution Check
| Principle | Status | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | No business records changed. |
| Reality authority / shortest links | PASS | Existing memberships remain authority; no duplicated relationships. |
| Proven schema | PASS | No fields, tables or migrations. |
| Tenant/service boundaries | PASS | Shared report service enforces membership; author/tenant detail denial unchanged. |
| Specification/test evidence | PASS | Explicit owner authorization; regression tests first and full CI required. |
| Explainable Web | PASS | Truthful absence of membership; localized explanation. |
| Simplicity/storage | PASS | Existing config helpers and components; no new infrastructure. |
| Received values | PASS | No stored values replaced or recomputed. |

Post-design review: all rows PASS. No exceptions.

## Design
1. Infrastructure configuration: `reality/mcp/config.py` public URL helper validates only MCP_URL; runtime retains listener/issuer validation and uses canonical API_URL fallback (spec265 FR-023).
2. Shared analytics service: `require_author` gains a keyword-only list-context explanation flag; only `list_reports` requests membership-specific AnalyticsError. Details and changes retain generic NotFound.
3. API: existing settings adapter benefits from helper correction without new business rules. Its existing owner guard and platform-administrator/development-auth exceptions remain unchanged. Existing analytics adapter exposes structured error.
4. Web: CompanySettings uses explicit three-state role presentation; ReportLibrary maps retained error code to localized explanation. Existing owner actions remain unchanged.
5. Localization dictionaries and long-lived Web/MCP contracts describe restored semantics.

## Test Plan / Traceability
| Requirement | Proof |
|---|---|
| FR-001/FR-002/DR-001/DR-002 | Config independence, production API_URL fallback, invalid origins, owner settings API under Helm-like environment. |
| FR-003/FR-006 | Existing settings browser adds missing-role card; owner/member behavior remains. |
| FR-004/FR-005 | Service + HTTP list denial, active members, report detail/change non-disclosure; browser membership error and tenant switching. |
| FR-005 | Existing company settings owner guards and graph private scope suites. |

## Migration / Rollback
None. Revert code commit if needed. No credential rotation, token creation or live data changes. Run config, service/API, frontend/browser, lint, spec, docs and hosted full CI before merge; deploy and inspect actual logged-in dialogs.

## Review Risks
Avoid broadening private author access, labeling platform admin as member, weakening HTTPS checks, or hiding unrelated errors. Root cause directly reproduced with production environment and no database.
