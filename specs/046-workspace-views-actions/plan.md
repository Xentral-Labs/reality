# Implementation Plan: Workspace Views and Actions

**Branch**: `046-workspace-views-actions` | **Date**: 2026-09-03 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Add one validated presentation catalog that classifies canonical register routes and existing application commands under the five workspace views. Compose that metadata into the existing application reference, render `Views` and `Actions` from it in the React sidebar, and use focused dialogs that call existing tenant-scoped Web/API endpoints. Show at most the first two ordered actions directly in every actionable workspace and expose its complete set through one shared searchable launcher. Reuse existing service confirmation flows and add no tables, domain fields, or browser business rules.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript 5 / React 18
**Primary Dependencies**: SQLAlchemy 2, PostgreSQL, Pydantic v2, FastAPI, React/Vite, Tailwind `br-*` primitives
**Storage**: PostgreSQL for existing authoritative records and disposable projections; version-controlled YAML for presentation metadata
**Testing**: pytest catalog/API/service/business stories; Node contract tests; TypeScript/Vite production build; strict localization audit
**Project Type**: shared Python application core and API plus independent React frontend
**Constraints**: Decimal quantities; UTC; opaque IDs; strict tenant scope; no direct ORM writes from adapters; all Web mutations confirmed; preserve the user's existing uncommitted sidebar/style work
**Scale/Scope**: Five fixed workspace definitions, existing bounded register endpoints, canonical action ordering, and one shared searchable launcher; no tenant-configurable navigation and no schema migration

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Existing reservation, movement, correction, hold, and identity services retain their current provenance behavior; the catalog adds no write path. | PASS |
| Reality owns operational state | Views read existing authoritative services or disposable projections; no status is added to Document or navigation metadata. | PASS |
| Proven schema only | Workspace classification is version-controlled application metadata. No PostgreSQL table or business field is added. | PASS |
| Tenant + shared service boundaries | Forms call existing tenant API routes, which call shared services and tenant-scoped selectors. Catalog metadata itself contains no tenant data. | PASS |
| Spec/test traceability | FR/DR coverage is mapped below; catalog and UI contract tests precede implementation changes. | PASS |
| Explainable web behavior | Success results link to existing register/Inspector targets; correction retains the server preview and trace chain. | PASS |
| Smallest coherent design | One presentation catalog avoids duplicating workspace membership across Command, Projection, API, and frontend catalogs while referencing their stable keys. | PASS |

Post-design re-evaluation: all rows remain PASS. No schema, alternate service, or constitutional exception was introduced by the detailed contracts.

## Repository Structure and Layer Changes

```text
packages/reality-core/config/workspace_catalog.yaml
packages/reality-core/src/reality/catalogs.py
packages/reality-core/src/reality/web/api.py
packages/reality-core/tests/test_application_catalog.py
packages/reality-core/tests/test_http_boundary.py
apps/web/src/api.ts
apps/web/src/App.tsx
apps/web/src/localization.tsx
apps/web/src/tailwind.css
apps/web/scripts/workspace-actions-contract.test.mjs
docs/WEB_SPEC.md
specs/046-workspace-views-actions/
```

Dependency direction remains catalog → application reference → API transport → React presentation. Domain and service layers are unchanged unless a failing test proves an existing action endpoint bypasses a required confirmation rule.

## Design

### Reality flow

- Reservation action: existing Commitment → Reservation shortest link; item/location are validated service inputs, not duplicated ancestry.
- Movement action: optional existing Source Evidence → append-only Movement → affected Commitment reconciliation and Business Event where currently defined.
- Movement correction: original Movement → exact compensating Movement → optional replacement, through the existing correction relation and server preview fingerprint.
- Hold/release: Commitment → CommitmentHold; current restriction is derived from active holds.
- Handling unit, lot, and serial creation: typed operational identities only; current stock/location remains derived from Movement legs.
- Workspace/View/Action definitions are application metadata and never enter Source, Evidence, or Reality storage.

### Service and adapter flow

```text
workspace_catalog.yaml
  -> catalogs.application_reference() validation/composition
  -> GET /api/tenants/{tenant}/application-reference
  -> React Sidebar (Views / Actions)

Warehouse Action click
  -> focused React dialog + bounded tenant selectors
  -> explicit confirmation
  -> existing FastAPI tenant endpoint
  -> existing application service
  -> authoritative records/event
  -> affected route + existing Inspector
```

The catalog contains stable workspace/view/action keys, canonical English labels, ordering, routes, technical view kinds, command service references, prerequisite hints, and confirmation modes. It contains no executable code and does not decide domain eligibility.

Every actionable workspace shows its first two catalog entries directly and always offers `More actions`, which searches the full classified set. For Order Operations this includes document-level commitment holds and party delivery holds. Commands without a direct Web boundary remain absent rather than appearing as dead options.

The final adapter-completeness slice adds four explicit HTTP handlers that delegate directly to existing application services: manual order creation, Fact observation, customer payment posting, and supplier payment posting. Request models mirror service inputs, tenant lookup remains server-owned, and results return authoritative opaque record references. The manual-order endpoint calls `create_manual_order` atomically and never substitutes the existing Document-only endpoint.

### Data and migration impact

No database schema or migration. The new YAML structure is validated at process/test startup. Rollback removes the catalog consumer and returns the sidebar to its prior static list without touching tenant state.

### Failure, security, and tenant behavior

- Unknown routes, workspace keys, command services, Projection names, duplicate keys/order, or unsafe mutation confirmation modes fail catalog validation.
- The application-reference route remains membership protected and returns only product metadata.
- Action selectors reuse bounded tenant-scoped registers; exact IDs are revalidated by services at mutation time.
- All workspace-launched mutations require a distinct confirmation step. Movement correction retains its exact preview fingerprint and stale refusal. Other existing atomic actions show an exact input summary before submission; no optimistic domain calculation is performed in the browser.
- Failed requests keep the dialog open, render shared feedback, and do not manufacture a success state.
- Successful requests navigate to or refresh the affected canonical register and expose its existing Inspect affordance.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001-FR-009, FR-015, FR-018 | unit/contract | `packages/reality-core/tests/test_application_catalog.py` workspace catalog validation/composition cases | No workspace catalog/reference exists. |
| FR-009-FR-014; DR-001-DR-006 | API/service/story | focused additions to `test_http_boundary.py`, existing inventory/hold/handling/correction suites | Some catalog actions are not declared Web-eligible and frontend flows are absent. |
| FR-004-FR-008, FR-017 | frontend contract | `apps/web/scripts/workspace-actions-contract.test.mjs` | Sidebar is a static single group with no action launcher. |
| FR-005, FR-016 | localization contract | strict localization audit and localization contract | New labels and states do not exist in all catalogs. |
| FR-010, FR-013-FR-014 | frontend/API contract | confirmation, error, success-route, correction-preview assertions | Workspace-launched confirmation/result behavior is absent. |
| SC-001-SC-006 | acceptance | scenarios in `quickstart.md`, desktop/mobile visual verification | Current UI cannot expose or complete the requested workspace actions. |
| SC-007-SC-008 | repository gates | `make spec-check`, focused pytest, `make lint`, `make test`, `make web-build` | New artifacts/tests initially fail until implementation is complete. |

Tests are added before their implementation where practical. Existing service suites are reused instead of duplicating domain assertions in browser tests.

## Rollout and Rollback

Ship catalog validation, application-reference expansion, API client types, UI rendering, translations, and action flows in one repository release. There is no data backfill. A code rollback restores the old sidebar and removes the additional reference fields; existing action endpoints and all created business records remain valid authoritative history. Catalog-load failures are deployment-blocking rather than silently falling back to stale static navigation.

## Review Risks

- The current `App.tsx`, localization, and style files contain user changes in the same sidebar area; edits must be minimal and preserve that work.
- A catalog-driven action must not be mistaken for generic execution: only explicitly classified, Web-eligible commands appear.
- Simple actions lack snapshot previews today; confirmation must accurately summarize inputs without pretending to predict server-owned outcomes.
- Bounded selector endpoints may not expose every handling identity combination; exact service refusal remains authoritative.
- Navigation labels must stay canonical across four languages while technical names remain available in reference detail.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
