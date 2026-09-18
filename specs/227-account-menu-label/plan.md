# Plan: Email-only account menu

Update `apps/web/src/unified/ProfileMenu.tsx` and `apps/web/src/localization.tsx` only for presentation. Reuse existing Account settings translations; add My account in German, Dutch and Spanish. Keep native popover, trigger geometry, account email, personal settings destination and all action handlers unchanged. Retain existing collapsed-sidebar selectors.

## Constitution Check
PASS: no business state, derived identity, schema, tenant boundary, services, API or MCP changes. Surface-only React changes follow the existing adapter. User has approved product scope. No exceptions.

## Verification and rollback
Inspect existing shell/profile browser assertions before implementation and adjust obsolete labels where needed. Run frontend contract tests, localization audit, production build and spec policy. Visually check full long-email wrapping, one-line trigger, keyboard/collapsed and mobile behavior. Backend and generated catalog gates are not required because no backend/catalog changes occur. Revert the presentation commit to roll back; no migration.
