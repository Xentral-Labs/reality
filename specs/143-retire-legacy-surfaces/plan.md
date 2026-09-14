# Implementation Plan: Retire legacy browser surfaces

## Technical Context
React 19, TypeScript and Vite in apps/web; existing authenticated Python API unchanged. New work is adapter-only. No new dependency, schema, service rule or infrastructure.

## Constitution Check
| Principle | Result | Evidence |
| --- | --- | --- |
| Source → Evidence → Reality; operational authority | PASS | Records and derivations unchanged |
| Proven schema and shortest links | PASS | No migration or persistence changes |
| Tenant/service boundaries | PASS | Existing AuthGate and API enforcement retained |
| Spec/test evidence | PASS | Owner authorized scope; route tests precede removal |
| Explainable Web | PASS | Shared Inspector exception catalog extracted before deletion |
| Simplicity/storage | PASS | Removes duplicate presentation; PostgreSQL unchanged |
| Received values | PASS | No calculations or stored values changed |

## Design
1. Add a pure allowlisted bookmark resolver in apps/web/src/entryRouting.ts. Preserve tenant and selected read parameters, map legacy register tabs explicitly, reject unknown app paths. Never interpret query values as destinations or execute mutations.
2. App.tsx renders UnifiedApp unconditionally after auth; retirement/unavailable messages replace obsolete entrypoints. Auth.tsx uses bounded local account-return helpers, preserving normal approval and invitation behavior. Playground retirement is an informational page, not a sandbox workspace.
3. Move ExceptionCatalog.tsx into unified/. Delete legacy/ and playground/ presentation and legacy-only root styles. Keep shared Tailwind, auth, theme, localization and API types used by the remaining app; remove orphan Playground client methods/types where no retained reader uses them.
4. Retire legacy source-shape and Playground browser tests; retain independent proxy/localization tests and current unified coverage. Add executable bookmark tests and browser acceptance covering auth, retirement, redirects, unknown routes, current shell and catalogs.
5. Remove build switch and update Site/Docs/current development instructions. Historical specifications remain archival; mark superseding contract in WEB_SPEC and completion plan.

## Validation
Node route tests first, then all retained frontend contracts, formatting, localization audit and production build. Browser fixtures assert no writes and correct tenant/register selection. Full backend suite verifies unchanged data/service contracts; docs/site checks verify entry links. Spec policy and diff review finish before PR publication.

## Migration and Rollback
No database migration, data deletion, or live deployment. Roll back the commit or deploy the previous image. Keep backend Playground services/endpoints and historical tests because stored runs and outcomes still exist; deleting them would be a separate compatibility/data-lifecycle decision.

## Risks
Legacy selectors sometimes have different names: map only known equivalents and do not carry action arguments. Some old pages have no retained equivalent: show unavailable rather than pretend parity. Existing pending Playground users receive retirement information but cannot enter production without approval. Current sandbox-company guard remains authoritative.

## Profile menu follow-up design
Reuse the existing native popover pattern from CompanySwitcher in a new unified/ProfileMenu.tsx. Pass AuthUser from UnifiedApp through Shell; place the trigger in a sticky sidebar footer. Move Documentation into this disclosure alongside configured Site URL. Use api.logout, disable duplicate submissions, retain failures, and navigate to /login only after success. No backend or persistence change. Constitution check remains PASS; owner explicitly requested scope. FR-007 maps to T012–T014 with browser interaction/error verification before completion; analysis found no uncovered requirement or critical issue.

FR-008 follow-up: keep the existing settings route/query contract but separate presentation. Personal settings have their own RegisterHeader and no company tabs. Company navigation always selects company settings and is inactive for the personal view. Unknown/default settings query resolves to company. No new account endpoint. Owner clarified this split; review found no unresolved issue.

## Company list follow-up
Reuse bootstrap.tenants via UnifiedApp → SettingsPage → CompanySettings. Switch through the existing context callback and clear action selection, preserving tenant isolation and sandbox guards. Render accessible companies with current-company badge and name/ID/role; put creation below a divider in a labeled section. No new service, storage or dependency. Tests first: browser list, switch, reload, separated creation and no writes. Constitution check PASS; review/analysis finds complete FR-009 coverage and no unresolved clarification.

FR-010 reviewed: add agents settings selection and render existing AISettings token controls separately from provider controls. Existing owner guard and API remain authoritative; member is not relabeled guest. Company shortcuts use companySelection before selecting a management tab. Test role-specific visibility, target tenant and member denial. Constitution PASS; no unresolved findings.

Creation placement follow-up: reuse CreateCompany with optional native-dialog presentation, top heading action, existing creation state and guarded dismissal. Browser checks opening, Escape/focus restoration and no writes before confirmation. No domain change; reviewed against FR-009 with no unresolved finding.

FR-011 UX review: use local management target/view state in SettingsPage, with a native modal containing only the requested task; no secondary app tabs. Resolve target against authorized bootstrap companies, pass its ID to existing MemberAccess/AISettings, and retain owner checks. Add optional busy/uncertain callbacks to prevent dismissal during unresolved writes. Preserve explicit company switch callback. Existing management query links render the equivalent modal and close back to the list. Browser tests assert no context/URL changes and tenant-correct requests. Constitution PASS; no unresolved clarification or critical finding.

Commitment wording follow-up: change only presentation strings across Home, Your work and commitment links; clarify customer-delivery scope. Update existing browser selectors, verify frontend contracts/localization/build and local browser wording. Constitution review PASS; no schema or business behavior changes.

FR-012: initialize after the current list succeeds; a per-mount ref prevents reselection after explicit deselection. Reuse company-context navigation with an optional replace-history mode for this automatic selection. Explicit IDs win, empty/errors remain unselected. Browser acceptance before implementation covers initial selection, empty result, explicit foreign ID and mobile back. Constitution check PASS; API/domain unchanged and no unresolved findings.

FR-013 reviewed: keep OrdersPage and its register mounted while showing DeliveryCase for selection.commitment; capture/restore register scroll. Use existing table row activation. Remove work navigation, point Home/Exceptions to Orders, and retain a replace-navigation compatibility component for old work links. Generalize DeliveryCase labels/actions using existing customer/supplier type; use the existing receipt launcher. Update browser scenarios for row/keyboard/detail/back/filter/deep-link compatibility and no business writes. Constitution PASS; no unresolved findings.

FR-014 is a presentation-only correction in the retained unified shell. Add a source contract before changing the visible wordmark. Do not alter lowercase technical identifiers, persistence, routes, localization or business behavior. Constitution PASS; no unresolved findings.
