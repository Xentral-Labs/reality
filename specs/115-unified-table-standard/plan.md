# Implementation Plan

## Technical Context
React19/TypeScript/Tailwind; existing Python SQLAlchemy/PostgreSQL read services. No new dependency or schema. Owner-approved ERP defaults apply to the unified feature-flag surfaces only.

## Architecture
Introduce a shared semantic `RegisterTable.tsx` that decorates explicit table header/body content and centralizes sizing, sticky scroll region, column controls, density, resize and row navigation. Existing row renderers retain canonical values and actions. Facts/master data become table renderers while keeping their detail/action components. A provider in UnifiedApp carries URL-backed size/sort state and per-user register identity; client methods accept optional trailing query options. A validated browser preference helper persists only layouts, versioned per user/table variant; storage failure falls back to defaults.

SQL ordering uses a small `db/query_order.py` resolver over explicit per-service maps, nulls-last and opaque-ID tie-breaks. Extend existing read functions and API routes, retaining defaults and size1–100 compatibility. Only existing SQL-expression columns advertise sort: do not sort hydrated labels or derived post-page controls. Projection money uses Numeric casts. No alternate business derivation. Existing filter toolbars remain reachable from a header filter control; URL q and typed filters stay authoritative.

## Constitution Check
| Principle | Result | Evidence |
| --- | --- | --- |
| Source/Evidence/Reality | PASS | Existing exact record navigation retained |
| Operational authority | PASS | Sort existing SQL expressions, no document operational status |
| Schema proof | PASS | No schema changes; browser UI preferences only |
| Tenant/service boundary | PASS | Existing scoped reads; allowlisted SQL ordering |
| Spec/tests | PASS | Owner approved proposal; backend/component/browser regression tasks precede changes |
| Explainability | PASS | Inspector/cases and actions preserved |
| Simplicity | PASS | Native table/React and small query helper, no grid dependency |
| Received values | PASS | No recomputation or translation of originals |

## Test Plan and Rollback
Backend global numeric/text ordering, invalid sort, deterministic ties, tenant scope and size; frontend preference validation/user separation/URL reset; browser44/36px geometry, sticky scroll, visible columns/reset/resize persistence, keyboard/row/nested action, all variants and four-language light/dark responsive coverage. Run all1499+ backend tests, all frontend/browser/docs gates and lint/spec policy. Existing feature flag disables unified surface for rollback; query defaults preserve old clients. No data migration.

## Research
Skill-directed read-only research audited every backend register. See research.md. No unresolved clarification or constitutional exception.
