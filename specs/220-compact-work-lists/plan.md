# Implementation Plan: Compact Daily Work Lists

## Technical Context
Presentation-only React/TypeScript and shared CSS change. Existing WorkRow is used by CommitmentsPage, AttentionPage and DecisionsPage. Keep the current 14px title and 12px supporting text. Use a named CSS container on each work list: at 720px available width place title and context in aligned columns; below that stack them. Rows retain a 44px minimum target and native buttons. Reduce group heading and outer spacing. Toolbar filters share the search row only with enough container width.

## Constitution Check
All principles PASS before and after design: Source/Evidence/Reality and received values are unchanged; no schema, domain, persistence, service, tenant or confirmation changes. Existing previews preserve explainability. Specification and browser proofs precede implementation. No dependencies or infrastructure added.

## Scope Review
The user's requested scope is precisely the three named lists; presentation choices implement that scope. No unresolved clarification or constitutional exception.

## Implementation Order
Domain, services and tools: no changes required. Adapter: shared WorkList.tsx and tailwind.css, then the three page wrappers/toolbars. Existing data hooks and handlers stay intact.

## Verification
Extend apps/web/scripts/daily-work-browser.mjs before implementation to measure row height/alignment and exercise keyboard activation. Run it against local Vite with existing HTTP fixtures in EN/DE, mobile/desktop and light/dark. Retain paging, filtering, previews and no-write assertions. Run frontend contract tests, build, i18n audit, spec-check and diff whitespace check. Backend and migration suites are not required for this CSS/markup-only change because no backend or schema files change. Review screenshots for all three pages.

## Migration and Rollback
No migration. Revert the presentation diff to restore prior spacing. Main risks are clipped long strings, squeezed filters with chat open and lost row separators; verify container-relative behavior and native keyboard controls.
