# Plan: Consistent Page Title Counts

Use the existing PageCount portal and shared badge styling. Add a shared record-count presenter in PageHeading.tsx; RegisterToolbar uses it by default. InspectorCatalog accepts an explicit local placement for the nested Technical record overview in RealityInspectorPage.tsx. Standalone surfaces without a page target keep their local count. No backend or schema changes.

Constitution Check: PASS for Source → Evidence → Reality, shortest links, tenant/service boundaries, received values and proportional verification. This is display-only; count provenance remains the existing service response. No domain/service/tool changes are needed before this adapter change.

Tests planned before implementation: browser matrix for all register families, zero/filter/tab/navigation updates, nested technical catalog, existing daily-work counts, and mobile geometry. Run frontend gate, spec policy, Ruff and focused page-chrome browser proof. The previous full backend suite passed 1976 tests; this display-only change does not require another backend execution beyond CI.

Rollback: restore the prior web image. Deploy only web into the existing local project, preserving the Finance backend and database.

## Page tabs refinement
Move the RegisterHeader portal target to a dedicated slot after the page introduction. RegisterHeader renders only its existing children; the introduction becomes h1. Remove the old global page-title slot and scope shared tab styling to the content slot. Preserve shared header responsiveness and current route handlers. Update page-chrome/footer expectations and exercise all ten tab groups at desktop/mobile widths. Constitution Check: PASS; presentation-only, no schema, queries or new service logic.

## Single-row header refinement
Move the existing title/count/action portal targets into the compact 60px global header. Render the localized description as an always-visible, truncating second line and use one mounted controls panel, shown inline on desktop or as a compact menu at narrow widths. Preserve page tabs in main and existing action handlers. Test fixed height, overflow, visible descriptions and mobile controls before rollout. Constitution Check: PASS; no service/data changes.
