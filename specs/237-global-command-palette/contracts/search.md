# Search and Resolution Contracts

## Shared service and Web adapter

Planned service signatures:

- `search_company(session, tenant_id, principal, request) -> SearchPage`
- `resolve_search_targets(session, tenant_id, principal, references) -> ResolvedTargets`

Both are read-only, operate without autoflush, and never commit, emit business events or prepare proposals. Trusted local mode follows existing policy explicitly; absent browser identity must never silently select trusted mode. Use the existing authentication boundary and shared membership/lesson checks before search or resolution. Private report reads always require a real authorized owner context.

Planned tenant endpoints:

- `POST /api/tenants/{tenant_id}/search/query`: typed SearchRequest body excluding tenant/principal. POST is used for bounded context hints and to keep query text out of URL access logs; it is a read operation.
- `POST /api/tenants/{tenant_id}/search/resolve`: at most forty typed references, no query; read-only identity resolution for labels and launch targets.

The adapter validates transport input, derives principal from the authenticated request and invokes the service. No ORM query or permission interpretation in the endpoint. No new public MCP or CLI command is required by this UI feature; shared service contracts remain callable by application adapters.

Provider enum: `partners`, `items_locations`, `orders`, `finance`, `shipping`, `reality`, `reports`. Families are an explicit subset per provider. An unknown field, family/provider mismatch, invalid limit/cursor or >500-character query returns validation failure; no silent truncation. Empty record query returns an empty page without scanning business tables. Client displays a clear length error while retaining text, and Ask in chat remains subject to its existing 4000-character handoff limit.

A valid but inaccessible tenant/target is not found. Access failure is not a zero-hit success. Provider timeout/unavailability has a safe retryable response; SQL/internal payload details are not exposed. On whole-session expiry, the UI clears protected results and invokes existing authentication handling. POST does not confer write permission or bypass existing CSRF/transport protections.

## Family-to-authority mapping

| Provider/family | Candidate identity and searched fields | Bounded hydration / existing detail |
|---|---|---|
| partners/party | Party.id/name/accounting_code; role rows are metadata, not duplicate hits | `core.party_detail`; current roles from PartyRole; MasterData detail |
| items_locations/item | Item.id/sku/name, including inactive | `core.item_detail`; MasterData |
| items_locations/location | Location.id/name | `core.location_detail`; MasterData |
| orders/customer_order, supplier_order | Document.id/number/customer_reference; sales_order/purchase_order; joined Party.name and directly linked SourceRecord.external_id | `core.document_detail`; OrdersPage existing order preview independent of current list |
| finance/customer_invoice, supplier_invoice, customer_credit, supplier_credit | Document.id/number/customer_reference, related Party.name; types sales_invoice/supplier_invoice/credit_note/supplier_credit_note | `core.document_detail`; Finance selected detail or exact document Inspector; optional canonical financial state |
| finance/payment | Cash LedgerEntry.id eligible under the existing `_payment_rows` selector; linked held Document.number/customer_reference and Party.name | `_payment_rows(cash_entry_ids=...)` and payment Inspector; no new payment identity |
| shipping/shipment | Shipment.id, directly linked SourceRecord.external_id, package tracking_number, related counterparty name | `services/shipments.py:shipment_explain`; exact shipment Inspector |
| reality/document | Document.id/number for remaining evidence types; typed order/finance documents use their canonical family | `core.document_detail`; exact document Inspector |
| reality/source_record | SourceRecord.id/external_id, including every retained version | Existing source Inspector; distinguish source/type/version/received time |
| reality/commitment, reservation, movement, fact, ledger_entry | Exact own ID only; cash entries use canonical payment presentation | Existing exact Inspector via service readers; ledger entries retain ledger identity |
| reports/private_report | AnalyticsReport.id/name, tenant + active owner + supported kind, not deleted | `services/analytics/reports.py:get_report/owned`; existing graph editor |

Do not search payload JSON, Fact.value or arbitrary cast-to-text columns. Every joined alias is tenant-constrained. A related partner name adds a match only for its explicitly listed families. Human names/references are not assumed unique.

Canonical object keys use the actual stored model kind and ID: an invoice key is `document:<id>`, a payment key is `ledger_entry:<id>`. Its display family/Inspector target may differ. A physical record has one canonical provider in All; selecting a more technical Inspector representation must not create another search hit. Known document-type and payment eligibility selectors determine this assignment centrally. All document aliases are therefore deduplicated without collapsing source versions or unrelated records.

## Matching and ranking

1. Raw exact opaque identity or held business reference (trimmed input, no fuzzy correction).
2. Case/diacritic-normalized exact reference or human label. Preserve separate exact raw tier so a normalization collision never hides the literal match.
3. Exact/prefix word matches: every query token must match an allowed field token, respecting identifiers as complete/prefix strings rather than fuzzy words.
4. Approximate human-word matches: every token matches exactly/prefix or by the single-edit rule, with at least one approximate token. Query tokens shorter than five characters cannot be approximate. Identifiers never participate in this tier.

Labels include authorized original names and translated catalog vocabulary. Canonical synonyms apply to capability/page/worklist/report metadata and family recognition, never alter held identifiers or attach unrelated business records.

Sort tuple: `(tier, context_preference, recent_preference, family_order, normalized_label, physical_kind, opaque_id)`. Context/recents operate within a tier only. Freeze supplied preferences across continuation; fingerprint them along with query, language, provider, family, tenant and principal. The browser uses the same tier semantics for local metadata and provider merging; it must never demote raw exact matches beneath a contextual action.

SQL applies authorization, complete matching and tier exclusion before order/limit. Each provider returns `limit + 1` evidence internally and at most `limit` hits externally. Higher tiers may fill a page before executing expensive lower tiers. Continuation covers all lower tiers and does not silently truncate a candidate pool.

Cursor integrity is validated; a malformed or mismatched cursor is invalid, never an opportunity to remove tenant predicates. Cursors contain only previously authorized sort data and expire on session/context change. Results are read-time pages, not a historical snapshot: updates between pages may move a record. Client deduplicates by canonical key, and Refresh restarts from the first page. No complete historical result or exact total is claimed.

## Providers and Visible Result Groups

The UI taxonomy is authoritative in spec.md §Result Groups and Search Filters. Provider-to-group mapping is `partners` -> Business partners; `items_locations` -> Items and locations; `orders` -> Orders; `finance` -> Finance; `shipping` -> Shipping; `reality` -> Reality and evidence; `reports` -> Reports. Local calculated views and templates also belong to Reports. Local navigation/worklist entries belong to Pages; other non-report/non-navigation capabilities to Actions; authorized company names to Companies; help links to Help. A provider is an internal retrieval boundary, not an extra display group or result budget.

Each hit carries one stable group key: `partners`, `items_locations`, `orders`, `finance`, `shipping`, `reality`, `actions`, `pages`, `reports`, `help` or `companies`. Broad filter and record-family refinement select eligible groups/hits without renaming them. Named worklists use Pages even when their existing target is a report reader. Deduplicate equivalent metadata entry points before applying limits.

Reports Show all uses one merged ordering over the finite local metadata sources and cursor-paged private reports. Keep independent source cursors plus unconsumed lookahead while producing at most fifty unique hits per visible page; request further source pages only as needed. Do not discard a fetched but unrendered hit when advancing a cursor. Freeze the local metadata/ranking context during a paging sequence; refresh restarts it. Other groups page their corresponding provider or finite local entries. Partial provider failure labels the group incomplete and leaves successful sources accessible; retry restarts group pagination to restore global ordering without claiming completeness.

## Bounds and failure isolation

- Client debounce: 150ms for business search; local metadata matching is immediate.
- At most three provider requests in flight, cancelled on query/company/user/filter change. Request sequence and scope checks are also mandatory because abort alone does not prevent stale responses.
- Nonempty All and broad-filter previews show max twelve merged hits overall and max four per visible result group, after deduplication/ranking. Every group with hidden known hits or provider `has_more` retains a labeled Show all affordance, including groups omitted by the overall cap. Show all opens only that group's pageable palette mode with max fifty merged rows; provider/source limits cannot multiply it. Utility controls are excluded from hit counts. No new application-wide results page is needed.
- Provider pages are independently retryable. Successful provider content is retained, including other sources in the same visible group; pending/partial/error groups are labeled, not counted as empty.
- Empty palette does not perform an unfiltered record search. It resolves at most forty stored references and offers permitted metadata/context suggestions.
- Database work is bounded by a read timeout and transaction cancellation. A timeout produces unavailable, never a misleading truncated success. Timing/query-plan evidence must meet SC-003 before completion.

## Worklist integration

| Worklist | Target and authoritative membership |
|---|---|
| Outstanding customer/supplier invoices | Finance open-items, receivable/payable, existing outstanding filter |
| Overdue customer/supplier invoices | Same register plus new explicit overdue flag; shared aging observation and outstanding invoice population, applied before pagination and count |
| Blocked outbound commitments | Existing fulfillment-blockers calculated-view reader, with explicit outbound scope and freshness; no hold-only approximation |
| Open outbound/inbound commitments | Existing delivery-work register, customer_delivery/supplier_delivery, open |
| Exceptions | Attention findings; no invented severity filter |
| Pending decisions | Decisions, existing pending proposal reader |

Place the finance filter behavior in a shared application reader (`services/finance/worklists.py` planned), composing existing canonical aging/financial selection. Existing Web read models delegate rather than own an alternate rule. Test result membership, pagination/count parity, boundary dates, unknown due dates, partial/settled invoices and both financial sides. Projection-based blockers retain existing readiness failure semantics.
