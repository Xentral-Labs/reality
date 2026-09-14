# Source and import migration assessment

**Date:** 2026-09-08
**Status:** Assessment complete; proposed first implementation slice, not implementation approval.
**Spec impact: none.** This audit records existing behavior and a proposed scope. No product code, schema, live source configuration or shared business data is changed. Implementation requires its own specification/review/plan/tasks/analysis.

## Recommendation

Start with one reviewed **CSV import of new items** into unified Data & sources. Finish the underlying transaction, replay and error semantics first. Reuse original-file storage and the existing application-tool boundary; add the missing web entry and result inspection. The first slice is not a generic vendor connector, arbitrary mapping workbench, order import or bank import.

This is useful for ordinary operators and technically explicit for operations specialists: select a source, provide a CSV, identify columns, review proposed new items, confirm once, then inspect results and the original file. Source registration itself must never be labeled a working external connection.

## Current capability assessment

| Area | Evidence and actual capability | Migration decision |
|---|---|---|
| Unified source/evidence registers | `apps/web/src/unified/DataSourcesPage.tsx`, `web/source_reads.py`: bounded origin, received-version and evidence reads, existing Inspector links | Keep and extend with contextual entry/result actions |
| Source registry | `core.py`: create source system/capability and toggle active flags; existing React forms and JSON API | Reuse identity registration with explicit meaning; do not infer transport health or an ingestion gate from an active flag |
| Vendor templates | `config/connector_catalog.yaml` calls itself Mock Connector Shells, explicitly without credentials, transport, mapping or API calls; `install_connector_shell` creates definitions only | Do not present the logo/template catalog as live integrations; defer broad catalog UI |
| Raw JSON intake | `SourceDropModal`, `POST /sources`, `enqueue_source`: preserve/version object and enqueue or mark unmapped | Preserve as an advanced diagnostic capability when needed; not the primary ordinary-user entry |
| Object interpretation | `SOURCE_INTERPRETERS` contains only `('shopify', 'order')`; requires supplied party/location context. Shopify update/review behavior has dedicated tests | Retain as a specialized supported interpreter; it is not Shopify transport or support for every template/type |
| Source instance resolution | Interpreter lookup uses exact source code/type; a registered name such as `shopify_de_orders` is not automatically routed to `shopify/order` | Resolve explicitly before promising multiple connected shop instances |
| File storage | `services/artifacts.py`: staged immutable bytes, hash, per-tenant deduplication, local/S3 adapter; service tests | Reuse, with web authorization, limits and lifecycle specified |
| File processing | `file_interpreters.py`: item, party, location, sales_order, inventory_snapshot, bank_statement profiles; CSV/TSV/JSON/JSONL parsers | Working happy paths exist; not uniformly ready for operational exposure |
| Current file upload UI | Current React API/client and mounted web modules expose no artifact staging/mapping upload path. Old `/imports/stage`/`map` UI tests are skipped for the retired server-rendered UI | Build a narrow current web adapter; do not count historical upload screens as current working functionality |
| Processing and retry | Existing tenant-scoped job read/retry/work JSON endpoints and `reality imports work`; no import-worker service in current compose configuration (invitation worker is separate) | Specify a real processing trigger and recovery before saying files process automatically |
| Interpretation status | A job can be `completed` while its interpretation outcome is `needs_review`; coverage service distinguishes unsupported, failed, conflict, stale, interpreted and review | Explain technical completion separately from business adoption; use existing interpretation evidence |
| Chat integration | Shared `source_ingest` proposal tool exists, but requires an already staged artifact. Current unified action cards have no complete file-import review flow | Reuse one reviewed service path for form and later Chat entry; do not introduce a second import engine |

## Verified gaps before exposing file imports

### Replay and transaction safety — reproduced

Temporary assessment probes in isolated PostgreSQL reproduce the following existing behavior:

1. Process a one-row item CSV successfully, then call `process_import_job` again for the completed job: item count for the imported SKU increases from one to two.
2. Process a two-row item CSV whose second row has a missing name: the job raises an error but the first item remains stored.
3. Retry that file job with `retry_import_job`: status becomes `unmapped`, because retry checks only the object-interpreter registry, unlike initial file processing.

The code explains these results: the completed-job branch re-invokes the file interpreter; its per-row `create_item` calls use the default committing behavior; retry does not consider artifact target profiles. These probes reproduce defects; passing probes are not evidence of desired behavior or a fix.

### Further findings from code inspection — not separately reproduced

- File parsing materializes all rows before processing. Streamed original-file upload is not proof of bounded processing memory.
- Item creation has no file-level replay guard or explicit existing-item update/conflict policy. Mapping changes also need explicit treatment: original bytes, interpretation configuration and a user's reviewed attempt must not silently collapse into an earlier job.
- CSV sales-order processing calculates header totals and stored line amounts from quantity and price. That conflicts with the repository rule against persisting recomputed source authority. It also commits within the import path. Keep this profile out of the first slice pending a separate specification and repair.
- Inventory snapshot and bank profiles create stock/financial effects and need their own effect review and retry guarantees; a generic file upload confirmation is insufficient product detail for those operations.
- Registry activation flags are writable, but the common enqueue/interpreter paths inspected do not consult them. Their intended operational enforcement must be specified before exposing them as ingestion stop/start controls.

## Proposed first slice: new items from CSV

1. **Entry:** Data & sources → Import items. A simple source identity or existing source selection; no vendor connection claim.
2. **Original:** Stage a bounded CSV and show filename, source, row count and detected columns. Preserve original bytes. Staging creates no items.
3. **Columns:** Required SKU and name; unit explicit or an explicitly shown default. Suggest matching columns deterministically and let the user confirm. No AI provider required.
4. **Review:** Validate the entire accepted file against a small, declared profile. Show proposed new items and row-specific problems. Proposed first policy: reject existing/duplicate SKUs and invalid files before any item writes; no silent update, merge or partial import.
5. **Confirm:** Bind the reviewed file, mapping, source, defaults and target company to one shared application operation. Revalidate concurrent conflicts. Ensure atomic item creation and replay-safe recorded results.
6. **Result:** Show created count and exact item links, original-file/source link and any interpretation outcome. Lost response recovery reads the same attempt; no blind second submission. Master-data records use their existing direct source links; do not invent Documents solely to pad the provenance chain.
7. **Technical detail:** Expose artifact/source/job IDs and errors contextually. Reading/explaining may be offered in Chat once this same result is usable there; executing must use the same confirmed operation.

### Acceptance gates to plan before implementation

- Full file valid versus bad later row: all-or-nothing item changes, original retained.
- Same confirmation, completed-job replay, duplicate upload and lost response: no duplicate items.
- Existing SKU, duplicate rows, concurrent imports and changed mapping have explicit outcomes.
- Failed processing can be recovered without becoming incorrectly unmapped.
- Source/company authorization applies to upload, preview, confirmation, processing and original-file access; foreign IDs reveal nothing.
- Required fields, defaults, file size/encoding and row limits are declared; no silent data loss or implicit numeric authority.
- No-provider workflow, keyboard/mobile/dark layouts and four-language copy work.
- Actual isolated browser → API → service → PostgreSQL import proof; fixture-only UI tests do not suffice for cutover.

## Keep, defer, retire

- **Keep:** immutable originals/versioning, bounded source/evidence reads, existing Inspector, shared tool confirmation, explicit interpretation outcomes.
- **Complete first:** item CSV safety, current web upload/review adapter and a reliable processing/result loop.
- **Defer:** live vendor connections, multi-source routing, general column-mapping workbench, automated update/merge, bulk reprocessing, inventory and financial file imports.
- **Omit from ordinary navigation:** raw JSON testing and projection internals. Preserve necessary technical investigation contextually when removing old screens.
- **Retirement condition:** every retained file/source path has current service and browser evidence. Skipped historical UI tests, catalog entries and demo success are not sufficient.

## Verification evidence

- Existing source/file/Shopify/interpretation suites: **32 passed**, `/private/tmp/reality-source-audit-tests.log`.
- Temporary defect probes: **2 passed**, `/private/tmp/reality-source-audit-probes.log`; code `/private/tmp/reality_source_audit_probes.py`. They assert the observed broken behavior, are not added to the repository acceptance suite and must be rewritten toward desired outcomes during implementation.
- Connector/registry suite: **2 passed, 4 skipped**, `/private/tmp/reality-source-audit-integrations.log`. Skips belong to the retired server-rendered UI; their skip description is not proof of a current artifact-upload JSON API.
- All runs use isolated PostgreSQL fixtures and temporary artifact directories. No real external requests, credentials changes, imports, messages or company mutations.

## Spec 129 follow-through

The first new-item CSV slice now implements reviewed upload/mapping/confirmation in
Data & sources, original-file attachment access and inspectable exact item receipts.
The item-target partial-commit, completed replay and file retry defects above have
regressions and repairs. The original assessment and temporary defect probes describe
the pre-repair state; use the committed Spec 129 acceptance tests for current behavior.
Other profiles, connector transport, broad configuration and retirement remain open.
