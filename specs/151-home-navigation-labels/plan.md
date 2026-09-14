# Plan: Consistent Home and navigation categories

Use shared dailyWork.ts label/total/selection definitions from Shell.tsx and HomePage.tsx.
Add the commitments shortcut below Home, localize category labels and the open qualifier.
Preserve existing API totals and URL serialization. Update docs/WEB_SPEC.md.
Implementation touches only adapters; no domain, service, tool or persistence changes.

## Constitution Check
All principles PASS: existing Source → Evidence → Reality and tenant-scoped reads remain;
no schema, authority, mutation, confirmation or business calculation changes.
User approved scope; all requirements map to tasks and acceptance scenarios.

## Verification and rollback
Run existing frontend contracts, TypeScript/Vite build, four-language localization audit
and spec policy. Verify shared destination serialization against stale filters.
No new automated tests for reversible copy/navigation changes; existing routing contracts
cover serialization and direct runtime checks cover the selections. Review the isolated diff.
Rollback reverts this UI commit; no migration or data operation.
