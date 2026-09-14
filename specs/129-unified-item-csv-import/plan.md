# Plan: Reviewed item CSV
**Language**: English
## Technical Context
Python/SQLAlchemy/PostgreSQL, React/TypeScript, existing artifact storage and application tools. No new dependency, schema or event family.
## Constitution Check
| Principle | Evidence | Result |
|---|---|---|
| Provenance | Original artifact → immutable source → items; existing attributable source/item events | PASS |
| Reality | Master-data import does not invent operational document status | PASS |
| Schema | Existing artifacts, sources, proposals, items, outcomes sufficient | PASS |
| Tenant/services | Scoped service and common item_create tool; HTTP only adapts | PASS |
| Tests first | Parser/atomicity/replay/API regressions before implementation | PASS |
| Explainability | Reviewed rows/defaults and exact source/file/item links | PASS |
| Received values | SKU/name/unit preserved; defaults disclosed; no amounts | PASS |
| Simplicity | Synchronous bounded import; shared proposal lifecycle, no new worker | PASS |
## Design
services/item_imports.py owns strict CSV preview, immutable review intent, atomic recording and durable item-event receipt verification. Reuse item_create with import_file metadata and existing delivery_actions review/reconcile lifecycle; ordinary item_create remains unchanged. Add create_item/create_items to common tenant serialization set. Source construction uses store_source_record without commit; item creation uses _commit=False; one final transaction records source/items/events/attachment.
Repair existing item branch of file_interpreters separately: validate all rows/conflicts before writes, create without per-row commit; core completed artifact item job returns existing item IDs, retry recognizes file profiles. Do not claim repair of other financial/order profiles.
API: bounded raw CSV body upload to tenant-scoped item-imports/artifacts; metadata/preview; prepare via shared action service; existing confirmation/detail/reconcile; attachment download with materialize scope held during iteration. No unauthenticated paths or storage metadata.
Web: ItemImportPanel in DataSourcesPage, mapping/review/results, proposal in explicit import_proposal URL state, exact-ID recovery; no generic ActionCard confusion. New type/client only for this flow. Four language translations and shared controls.
## Verification
Service tests cover limits/encoding/headers, mapping, inert preview, stale/altered review, duplicates/inactive SKU, atomic failure, replay, source proof and tenant scope. API tests cover authorization/upload/prepare/confirm/download. Independent concurrent transactions cover imports versus master creation/update. Real browser test runs isolated migrated DB/API/Vite and uploads real bytes, maps, reviews, confirms, reloads and verifies exact result/download. Complete backend suite after source freeze; web build/contracts/i18n/format/browser and root lint/spec/diff checks.
## Risks / rollback
Staged originals persist even on cancellation; no business effects until confirm. Bounded synchronous files avoid worker deployment dependency. CSV is untrusted text, no formula execution. Invalid context after execution claim remains safely unresolved unless durable receipt proves completion. No automatic retry of uncertain mutation. Revert UI/service increment without schema rollback; preserve recorded source/item history.
