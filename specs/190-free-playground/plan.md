# Implementation Plan: Free Playground

**Branch**: `190-free-playground` | **Date**: 2026-09-14 | **Spec**: [spec.md](spec.md)

## Summary
Reuse authenticated account entry and canonical company setup. Persist signup consent in security audit events, create with a stable owner request key, and recover using existing PlaygroundRun receipts. Reuse current operational readers for starter tasks. Reserve daily managed AI dispatches atomically with an account lock and existing security events. No business schema or new worker infrastructure.

## Technical Context
Python 3.12+, SQLAlchemy 2/PostgreSQL, FastAPI/Pydantic; React/TypeScript/Vite. Tests: pytest PostgreSQL service/API stories, Node routing/contracts, browser scenarios and production builds. Target: existing hosted web deployment. Scope: verified-account entry, three read-only tasks, voluntary browser-persisted prompt and 20-question daily allowance. No dependencies added. Daily usage query uses existing indexed account/event/time fields; lock is held only through reservation commit, never across provider latency.

## Constitution Check
| Gate | Result | Evidence |
| --- | --- | --- |
| Source → Evidence → Reality | PASS | Canonical profile and existing demo intake services only. |
| Operational authority / shortest links | PASS | Existing attention, delivery, finance readers and opaque IDs. |
| Proven schema | PASS | No schema change; account orchestration/security usage events use existing records. |
| Tenant and service boundaries | PASS | Account consent/usage scoped by trusted principal; demo receipt owner scope; tenant readers unchanged. |
| Spec/test first | PASS | Approved product scope, regression tests before implementation, full gates planned. |
| Explainable Web | PASS | Existing operational pages retain evidence links and confirmations. |
| Simplicity/storage | PASS | PostgreSQL atomic account lock; shared scheduler; no timer ingestion. |
| Received values | PASS | No source calculations added. |

Pre-research and post-design checks PASS. No exceptions or unresolved clarifications.

## Project Structure
- `packages/reality-core/src/reality/services/free_playground.py`: consent status, confirmed entry, managed allowance reservation/read.
- `services/company_setup.py`, `services/playground.py`: canonical setup/default enable policy reuse.
- `services/core.py`, `services/playground_chat.py`: shared managed dispatch boundary.
- `web/auth.py`, `web/company_setup_api.py`, `web/api.py`: thin authenticated adapters.
- `apps/web/src/unified/FreePlayground.tsx`: recoverable entry and starter/prompt UI context; `UnifiedApp.tsx`, operational pages, `ChatPage.tsx`, `ChatComposer.tsx` integrate.
- `provider-site/src/LandingPage.tsx`, header/platform and both localization catalogs: truthful offer.
- `packages/reality-core/tests/test_free_playground.py`, existing setup/access/chat tests; `apps/web/scripts/free-playground.test.mjs`: regression evidence.

## Test-first Plan
Prove explicit consent, active verification and owner-private idempotent entry; disabled/manual/invited/historical cases; archived receipt and pause replay; 20 slots, concurrent final-slot requests, UTC reset, own-provider exemption, no provider invocation on rejection; service parity for legacy companion. UI tests cover routing/filter reset, loaded-result success and local preference scope. Existing full backend suite, lint/spec, web/site/docs gates must pass. Review business traceability and deployment settings separately.

## Migration and Rollback
No migration. Reverting code stops new entry/allowance behavior and preserves canonical companies and historical audit events. Existing explicit false/zero policy values remain. Deployed services must share PostgreSQL and UTC semantics. No remote rollout or payment settings changed in this work.

## Verification refinements

The implementation review clarified that free-signup account allowance also applies to ordinary companies subsequently created by that account, preventing a company-type bypass. Existing non-trial business accounts are unchanged. Trial entry remains mounted across navigation to preserve first-task state, reads archive state, and recovers incomplete live setup on root reload. The legacy companion rebinds read-only authority after the quota commit; its existing policy tests prove the transaction boundary.

Trial quota enrollment is recorded for every new public signup independently of the optional demo-consent flag. This closes an API-level opt-out while preserving the original consent rule for company creation.

## Loading feedback refinement

Reuse one frontend-only entry progress component for authentication, lazy module loading, bootstrap, policy reads and demo preparation. Keep operational skeletons unchanged. Guard verification submissions and preserve signup language through navigation. Tests first: delayed HTTP browser fixtures assert visible status during every wait, disabled submission, retry after refusal and preserved language. Then web contracts, localization, TypeScript/build, existing trial browser suite, local Docker rebuild and live smoke check. Constitution Check: PASS; no schema, business/service rule or new external effect.

The delayed verification browser test also reproduced competing navigation: updating AuthGate state and assigning location triggered two redirects. Verification now performs one full navigation and lets the destination re-read its session. Authentication semantics remain unchanged.

## Current hosted offer refinement

Update only PlatformPage copy, remove unused price/capacity presentation variables and banner, and add four-language translations. Preserve backend policies and self-hosted card. First update the site contract and observe failure; then implement, run site tests/i18n/build and visually inspect narrow and desktop rendering. Constitution Check: PASS; no schema or service changes.

## Packages page focus (FR-012)

Remove only the agent-ecosystem section from PlatformPage. Update the existing page contract before implementation; verify site tests, localization/build and desktop/mobile section absence. Constitution Check: PASS; presentation-only removal, no services, schema or new content elsewhere.

## Header design trial (FR-013)

Use a scoped shared-header stylesheet and existing navigation component. Remove the brand subtitle, shorten Docs, rename Packages, neutralize Docs styling and reduce header/logo dimensions. Preserve route helpers and mobile menu. Update existing contracts, run site checks and inspect desktop/mobile across locales before local deployment. Constitution Check: PASS; no business or schema impact.

## Hero alignment correction (FR-014)

Remove the hero container’s centered narrow width while preserving heading/description line lengths. Verify browser bounding boxes for eyebrow, h1, description and offer at desktop/mobile widths, plus site formatting/build. Constitution Check: PASS; CSS-only behavior change with no schema or service impact.

## Visual polish (FR-015)

Add a shared presentation stylesheet using scoped selectors, preserve heading font sizes, relax tracking/line height, standardize section spacing, and unify existing signup CTA colors and wording. Keep footer signup as a text link. Verify site contracts/localization/build, then all three routes and four locales on desktop/mobile for overflow, heading and CTA styles, retained alignment and screenshots. Constitution Check: PASS; no services/schema changes.

## ERP Lite product screenshot preview (FR-016)

Use the existing confirmed demo read-only. Capture the delivery-detail card header and quantity tiles with browser screenshots in all four languages, desktop and narrow layouts. Add a responsive localized picture and adjacent static example explanation to ERP Lite, with a demo-data caption. Keep live app/auth/session information out of static assets. Verify 5 promised, 3 fulfilled, 0 reserved, 2 open against the actual card, then site tests/i18n/build and desktop/mobile browser review. Constitution Check: PASS; no schema, service or product-UI mutation.

## Analytics product preview (FR-017)
Use read-only Explore, sales order lines grouped by week, order count, four completed weeks in UTC. Capture the real chart and corresponding table without account identity. Reuse the ERP preview visual treatment. Constitution check: passes; no service, source, schema or authorization changes. Verify actual values before capture; then site tests, localization, build, formatting, spec policy and desktop/mobile visual and overflow checks in every language.

## Shorter How it works (FR-018)
Reorder existing sections and use native details/summary for optional background, vocabulary, finance, corrections and FAQ. Keep the main example, uncertainty and proposal/confirmation explanation visible. No content or service semantics change. Constitution check PASS. Validate existing content contracts, build, localization, formatting and spec policy; compare collapsed page heights before/after, open disclosures with keyboard and verify content access, anchors and no overflow in four languages at desktop/mobile widths.

## FR-019
Add the configured-app return link to the existing mail renderer; restore the email fragment in Verify and provide editable email/resend controls. No schema or authentication-policy change. Constitution check PASS. Plan tests for plus-address encoding, no code in links, fresh-tab and stale-tab restoration, URL cleanup, explicit submission and resend behavior; run web contracts, i18n, build and scoped mail tests.
