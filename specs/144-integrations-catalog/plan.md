# Implementation Plan: Integration preparation catalog

Branch: `feat/integrations-catalog`. Date: 2026-09-08. Spec: [spec.md](spec.md).

## Summary
Add a frontend provider catalog and session-scoped draft editor above existing source registers. Preserve server APIs and all source/evidence paths.

## Technical Context
React/TypeScript, existing Tailwind tokens and native dialog; sessionStorage keyed by authenticated user ID and tenant ID. No new dependencies or schema. Ten static provider definitions, up to 100 session drafts; names limited to 100 characters. Existing PostgreSQL/services remain untouched. Browser fixture tests, frontend contracts, localization audit, build, formatting and spec policy checks.

## Constitution Check
All gates PASS before and after design: I/II preserve Source/Evidence/Reality; III no schema; IV no alternate queries or writes, session drafts scoped by authenticated user and tenant; V accepted user scope plus test-first tasks; VI distinguish plans from source truth; VII reuse existing components; VIII no derived source authority. No exceptions.

## Project Structure
- `apps/web/src/unified/IntegrationPreparation.tsx`: catalog, draft cards and modal.
- `apps/web/src/unified/DataSourcesPage.tsx`: entry point and source separation.
- `apps/web/src/unified/UnifiedApp.tsx`: authenticated user ID plumbing.
- `apps/web/src/localization.tsx`: DE/NL/ES text.
- `apps/web/scripts/integrations-catalog-browser.mjs`: fixture journey and screenshots.
- `docs/WEB_SPEC.md`: durable UI contract.

## Implementation and Validation
Write fixture browser journey first and observe missing Add integration. Implement only adapter/presentation; domain/service/tool layers unchanged. Session JSON is validated before use; read/write errors visible. Native modal traps focus and restores trigger; company remount discards unsaved form. Review final diff and run gates. Revert frontend commit to roll back; no migrations or business records to undo.

## Footer regression correction
FR-007 restores Spec 137: remove the separate top pager for non-selectable tables and reuse the shared footer with conditional selection tools. Tests assert footer location for both received data and documents. No service or pagination semantics change. Constitution PASS; requirement/test coverage complete.

## Source-centered navigation
FR-008: remove the Documents tab and document-specific received-row shortcut. Existing document URLs remain functional. Extend shared delivery_evidence source reads with import status and up to 100 actual FK-linked Parties, Items, Locations, Movements, Documents, Facts, LedgerEntries and BusinessEvents per family. Events retain their shortest link to subjects; do not claim they created those subjects. Reuse Inspector sections and payload display. Service regression verifies tenant filtering and real links; browser regression verifies the two-tab entry and linked-record modal. No schema or mutations. Constitution PASS; all requirements covered before implementation.
