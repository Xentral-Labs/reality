# Feature: Web Operations Cockpit

## Goal

Provide a browser UI over the exact same Reality services used by CLI and chat.

## Command

`reality web`

Creating a tenant in the web UI creates only the tenant record and redirects to
Chat. Loading either demo remains a separate, explicit and confirmed action.

## V0 pages

Home, Operational Exceptions, Commitments, Inventory, Open Items, Payments, Journal, Documents,
Timeline, Parties, Items, Locations, Chat, Explorer, Documentation.

## Acceptance criteria

- Tenant can be created and switched in the browser.
- Empty tenant offers the guided demo.
- Operations pages contain no direct persistence/business-rule implementation.
- Every operational detail offers a path to `Inspect`.
- Source-backed records can be traced to raw source payload.
- Web and CLI operations produce equivalent domain state.
- Explorer exposes every tenant-scoped business table plus the selected Tenant.
- Inventory, Operational Exceptions, Open Items, and Timeline appear separately as derived views,
  never as persisted tables.
- Journal is a bounded tenant-scoped read over immutable LedgerEntries. It exposes
  debit, credit, and derived balance controls plus account, posting, document, and
  source-evidence inspection paths; the browser stores no financial authority.
- Operational Exceptions, Commitments, Inventory, and Documents use one compact ERP register
  pattern: work header, small operational counters, searchable table, stable
  business columns, statuses, and Inspect/Explain drill-downs.
- Inspect/Explain opens an operational detail dialog on the current page. The
  Explorer remains available only as a secondary technical-record link.
- ERP registers for Documents, Parties, Items, and Locations link their primary
  business label to a dedicated detail page. Detail pages show related business
  records first and expose the Explorer only as a secondary technical action.
- Parties, Items, and Locations can be created and edited through shared
  application services. Existing master data is deactivated instead of deleted,
  remains visible for historical traceability, and can be reactivated.
- Documentation is generated from the live CLI command tree. Its embedded console
  accepts only `reality` commands, blocks nested web-server startup, and confirms
  mutations before invoking the same CLI implementation.
- Documentation also exposes an English Data Model area generated from
  `packages/reality-core/config/data_model.yaml`. The catalog covers every table and column and is checked
  against SQLAlchemy metadata for use by the web reference and future generators.
- Commands & Change Proposals and read-only Projections are individually explained from
  the composed catalogs under `packages/reality-core/config/`, including the shared service, adapters,
  read/write tables, calculation, and outputs.
