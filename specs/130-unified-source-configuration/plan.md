# Plan: Unified source definition management
## Technical Context
React/TypeScript adapter-only change. Existing FastAPI/SQLAlchemy services and PostgreSQL remain unchanged. Use existing api.integrations/createSourceSystem/setSourceSystemActive/setSourceCapabilityActive. No dependencies, schema or event changes.
## Constitution Check
| Principle | Evidence | Result |
|---|---|---|
| Provenance / Reality | Registry definitions do not invent payloads, documents or operational state | PASS |
| Received values | No amounts or derived authorities | PASS |
| Schema / simplicity | Existing read/write services; no new model | PASS |
| Tenant boundary | Existing member authorization, opaque selected IDs, component tenant keys | PASS |
| Explainability | Registry flags and interpreter declarations explicitly distinguished from transport | PASS |
| Test-first | Browser regression before component; existing service/API suite required | PASS |
## Design and sequence
SourceConfiguration.tsx is an inline selected-source panel or new-source form. Source cards open it using existing selection.entry while data_view=systems; entry=new opens creation. The company-keyed parent resets visible state. The existing integrations read supplies current definitions and interpreter availability; selected capabilities display 25 per page. It currently materializes the full registry server-side; this feature does not claim server pagination for that endpoint.
Review stores a fixed action value; single-flight confirmation calls existing API. A tenant-keyed sessionStorage unresolved marker is written before mutation and cleared only after known response or successful explicit current-state check. Reload never auto-writes. Recovery shows current matching definition without claiming creation attribution. Initial/read failures and foreign IDs disable mutations. Known 4xx retains form and permits revised review; generic/transport failures remain blocked. Stop exposing the legacy source configuration link for these selected capabilities; technical Explorer remains.
No domain/service/tool changes are needed because semantics are unchanged. Implement adapter and browser tests, localization and docs. Register search/paging remains in DataSourcesPage; selected detail is not a second overview table.
## Validation and rollback
Stateful intercepted browser tests cover registration, cancel, duplicate, source/type flags, metadata explanation, unknown response/reload/check failure, tenant switch, empty types and four-language responsive light/dark views. Existing source browser and item import regression, full backend suite, build/contracts/i18n/audit/format and root lint/spec/diff checks required. No real shared writes. Rollback restores old navigation; records remain compatible.
