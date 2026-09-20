# Retained costing record inspection

Approved next slice T078, FR-016/023/027 and SC-003/005. Add one shared read-only
cost_record service/application cost.record.get/MCP cost_record_get and CLI cost-record.
It reads a fixed allowlist of the 24 existing costing authority/membership tables, plus
narrow financial_component, action, movement_correction and interpretation_outcome bridges.
No arbitrary table names, schema expansion, margin calculation or current-completeness
claim. All direct/linked/member queries include tenant, and absent/foreign IDs produce
the same NotFound. Unknown kinds refuse without reflecting database metadata to callers.

Return the standard Inspector shape plus exact typed fields, semantic record name,
opaque identity, and explicit retained-record meaning. Keep original reasons and values;
Decimal values remain exact strings, dates remain UTC with presentation metadata. English
and German labels are centralized; other supported UI languages fall back to English.
Bridge records expose only approved columns; actions expose status/time/actor IDs but
never arbitrary proposal input/output. Link only to kinds actually supported by the
existing Inspector or this new service, checking referenced scope first. Financial
components link to their received Document/DocumentLine; interpretation to SourceRecord;
corrections to actual Movement; decisions to Action and BusinessEvent. No duplicate FKs.

Owned review/manifest/attribution children are paginated as a single stable ordered list
of (child kind, child ID), 25 rows per page, requested page1..10000. Explicit count and
has-next/previous accompany the page. These are exact retained child memberships, not
current cost values or a live whole-tenant history. The web Inspector provides page
controls and resets pagination when following/backtracking a record; ignore stale
responses from a different target/page/company. Other Inspector layouts stay compatible.
The Inspector register adds costing families for discovery, using existing tenant-scoped
paging and search. No record read flushes pending objects, writes data or queues jobs.

Tests first: fixed allowlist coverage of all 24 costing kinds, inspection of actual
fixture authority and its bridges, foreign and absent scope parity, bridge redaction, source links, shared tool/MCP/CLI/web parity, exact money,
retained membership pagination and invalid pages/kinds, pending-write protection, and
record/history navigation UI contract. Preserve older costing arithmetic/migrations.
Update catalogs, tenant evidence, German ERP tool label, generated docs and long-lived
feature contract. Run affected/full backend, frontend type/build/catalog checks, scoped
and global lint, docs generation/idempotence and spec policy. No new migration needed.


T080 storage integration adds three explicitly excluded disposable caches:
`cost_inventory_generation`, `cost_inventory_snapshot`, `cost_inventory_publication`.
They are not recorded financial authority and do not widen this fixed public allowlist.
Stored inventory reads return the original review identity for evidence inspection;
passing an actual cache ID/kind to cost.record.get still refuses. The exact cache names
are classified in the authority-coverage test so unrelated future tables cannot hide
behind a cost-prefix exemption. Their graph aggregation is explicitly deferred to T081.

Later retained-context integration adds inspectable captured-basis, company-census,
company-manifest and fixed company-generation headers plus their retained input/member
records. These records explain opaque identities already returned by shared analysis and
generation reads; inspection does not promote them to a common accounting policy. Derived
snapshot/generation result rows and mutable publication pointers remain explicitly refused.
The coverage test keeps the complete refused-table set literal so every future costing
table requires a reviewed classification.
