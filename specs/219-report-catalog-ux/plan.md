# Plan
## Technical context
React/TypeScript frontend; existing ApplicationReference catalog and ProjectionDataDialog. No new dependencies or services.
## Constitution Check
All eight principles PASS before and after design: presentation only; immutable source/evidence/reality unaffected; no schema or authority changes; tenant-scoped readers reused; technical traceability retained; tests before implementation. No complexity exceptions.
## Design
Add reportCatalogEntries.ts for presentation metadata and grouping by exact data target, preserving authoritative live registers separately from stored snapshots. ReportCatalog.tsx supplies list, search and workspace filters using shared RegisterWorkbench. Extend ProjectionDataDialog with optional report title/summary and secondary details; default callers unchanged. Replace only the views branch in RealityInspectorPage. Translation copy stays in localization.tsx. No domain/service/tool changes required.
## Validation
Write grouping/filter tests first. Browser verifies catalog scanning, filtering/search, data open/close, technical details, price details-only, unknown entries, four languages, keyboard and mobile. Run spec-check and full web-build gate.
## Rollback and risks
Revert frontend commit; no migration. Exact-target grouping avoids conflating live and stored readings. Unknown entries retain original catalog labels/description. Price resolution must never invoke unsupported unparameterized read. Report details retain all catalog aliases and application links.
