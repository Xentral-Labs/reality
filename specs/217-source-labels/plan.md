# Plan
Change Origin to Source only in OrdersPage, MasterDataPage and DataSourcesPage column definitions. Keep RecordOrigin types, data-source-origin attributes and all APIs untouched. Use Source directly for MasterDataCard/MasterDataPage group headings and CatalogEntryDetails source fields to avoid ambiguous reverse-localization aliases. Edit direct source label catalog values in place; add Source/Sources to invariant vocabulary. Original source links inspect Source Records, so their translated captions explicitly name that record.

Constitution Check: PASS all eight principles. Presentation-only; source/tenant/service/schema boundaries unchanged. No new dependencies or research questions. Review shared key callers before edits.

Test-first: update existing provenance-labels tests for product labels and received-record links; observe red. Run frontend tests, format, language audits, build and spec policy; run existing record-provenance browser suite. No backend tests needed for label-only work. Rollback labels/catalog/allowlist/tests together.
