# Implementation plan

Extend generate-catalog-reference.py through analytics_model_reference.py; call the
validated reporting_catalog and reporting_templates for en/de, without a session.
Expose declaration details for complete source/derivation semantics. Embed the result
in the existing tool-usage.json. Add AnalyticsModelExplorer.vue and a sibling tab in
ToolUsage.vue, reusing parent search and hash/history navigation. Link both guides.

Constitution Check: PASS for all eight principles. This is a static documentation
adapter reading the same model; no business authority, database schema, tenant query,
mutation, source reinterpretation or new dependency. Tests precede implementation.
Rollback removes the extra tab/data field, leaving existing model routes intact.

Risks: snapshot staleness, hidden fields from terse labels, history interaction,
large generated data and mobile overflow. Verify exact declaration coverage and
repeat generation for deterministic output. Existing unrelated workspace edits remain.

FR-006: separate canonical labels from localized prose in explorer components.
For Analytics, generated public labels use the English catalog while localized
meanings remain; preserve translated names as search terms. Runtime catalogs stay
unchanged. Constitution Check: PASS. Test label parity and retained German descriptions.
