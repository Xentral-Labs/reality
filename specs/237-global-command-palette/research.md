# Research: Global Command Palette

**Date**: 2026-09-18
**Evidence**: Repository inspection, including bounded backend-search and frontend-navigation research. This is design evidence, not a performance or runtime acceptance report.

## 1. Search ownership

**Decision**: Add `services/global_search.py` over explicit query builders in `db/search.py`, with pure matching/result contracts in `domain/search.py`. Thin Web endpoints expose the same shared application service. Do not add a separate MCP command merely for the palette; existing Tools capabilities keep their tools and dispatch.

**Rationale**: `web/api.py:suggestion_list` sometimes materializes lists and limits commitments before filtering. `services/order_journey.py:search_order_journeys` covers sales orders only and has a selector limit. `services/inspector_register.py:inspector_records` is a technical register with different fields and ordering. None proves the required global coverage.

**Alternatives rejected**: Fetching each register and filtering its first page loses records; downloading full collections violates the scale requirement; copying ORM reads into the Web route violates the service boundary.

## 2. Complete matching before limiting

**Decision**: Use migration-owned PostgreSQL functions for deterministic display-word normalization and the bounded single-edit predicate; no PostgreSQL extension dependency. Keep raw identity/reference equality separate. Rank/filter in SQL before `LIMIT`, paginate by a deterministic tuple, and hydrate only returned identities.

Normalization contract: Unicode compatibility decomposition, removal of combining marks, case normalization, explicit expansions for supported-language edge cases such as sharp-s and ligatures. A versioned fixture corpus defines identical Python, SQL and browser outcomes. Do not strip punctuation from identifiers. Search words may match word prefixes; approximate matching allows one insertion/deletion/replacement/adjacent transposition, only for natural-language query tokens with at least five normalized characters. Identifiers, SKUs, document numbers and tracking references never receive fuzzy matching.

**Rationale**: Trigram candidate caps can discard a valid single-edit match; application-side limited reranking cannot prove full coverage. A length-difference bound of one for typo words is safe, while an arbitrary first-N candidate cap is not. Exact and label tiers can stop before lower tiers when the requested page is full, but continuation must eventually traverse the remaining tiers.

**Alternatives rejected**: New search service/index authority, extension-dependent approximate semantics, fuzzy whole-identifier matching and client-only ranking over database samples.

**Validation obligation**: PostgreSQL/browser normalization parity, complete predicate before limit, duplicate-reference coverage and cold/warm 100,000-record measurements. Typo scans are the main CPU risk. The algorithm is selected; performance is an implementation gate, not an unresolved product decision. Failure requires optimization or a reviewed design revision, never silently weakening coverage.

## 3. Held fields and shortest relationships

**Decision**: Use only the explicit family mapping in `contracts/search.md`.

- `Party` holds `accounting_code`, not independent customer/supplier numbers; `PartyRole` supplies multiple roles.
- `Location` has a name and ID, not a separate code column. Do not promote codes out of payloads.
- Orders/invoices/credits are `Document` identities. `customer_reference` and directly linked source external identity can be searched where held. Related party names join by the actual tenant-scoped FK.
- A payment is a cash `LedgerEntry.id`, not a payment document or posting-group identity. Extract/reuse the eligibility selector from `services/core.py:_payment_rows`; its `cash_entry_ids` parameter supports bounded hydration.
- A shipment is `Shipment.id`; tracking numbers belong to `ShipmentPackage`. Use tenant-scoped `EXISTS` to match packages without duplicating their shipment.
- Source versions remain separate `SourceRecord` identities. No current-version-only filter is implicit.

**Alternatives rejected**: Human-number identity, shipment/payment surrogate identities, payload flattening and status copied onto documents.

## 4. Exact navigation independent of list pages

**Decision**: Introduce a typed palette target dispatcher, route-backed exact selections and selected-detail regions independent of the current page's rows. Reuse existing detail readers/components; use existing Inspector for unsupported dedicated detail surfaces.

**Evidence**: MasterDataPage loads exact details but renders them under a listed row. OrdersPage, FinancePage and ShipmentsRegister also gate inline previews on current rows. InspectorRecordsPage stores selected target locally. AnalyticsPage stores selected saved report/template locally. Merely setting `entry` or `q=id` is insufficient.

**Design**: Native master/order/finance details retain their existing workspace but can render an exact selected record outside the list when off-page/filtered. Inspector gets explicit kind/ID route inputs. Saved reports, templates, calculated reports and capability details get explicit route selections and existing reader hydration. Preserve Back/reload behavior and clear all new target fields on company switch.

**Alternatives rejected**: New business-detail pages, trying to guess a row's page, using search text as identity, or creating a second detail renderer.

## 5. Worklist semantics

**Decision**: Reuse `dailyWork.ts` destinations and existing shared readers. Add explicit overdue filtering to the shared finance read path and expose it through API/routing/visible filters. Use the canonical fulfillment-blockers projection reader for blocked outbound work, opened through the existing calculated-view reader with its scope and freshness visible; do not redefine blocked as only an active hold.

**Evidence**: Open incoming/outgoing commitments and pending decisions already have routes/readers. Finance status currently does not offer overdue. `services/core.py:invoice_days_overdue`, `aging_register` and `with_invoice_aging` own due-date interpretation. `services/projections.py:FULFILLMENT_BLOCKERS` and `tools/application.py:_fulfillment_blockers` own blocker observations. `delivery_reads.py:delivery_case` lists holds but is not the whole blocker definition.

**Boundary**: Overdue invoice list = the existing outstanding invoice population filtered by canonical non-null `days_overdue > 0`, on the requested financial side. Resolve date and aging before pagination, using one read-time instant. Opening balances remain governed by existing list inclusion semantics, not silently presented as invoices. Canonical blocker entries are explicitly labeled as commitments/blockers, not orders or a newly inferred shipping permission.

## 6. Identity resolution, access and partial failure

**Decision**: One request per independently failing search provider, at most three in flight; static metadata remains immediately usable. A bounded read-only resolution request reauthorizes targets and refreshes labels for favorites/recents. Ordinary membership, private-report ownership and lesson restrictions apply in service calls, not only in the browser.

**Evidence**: `services/memberships.py:Principal`, delivery principal checks, `services/analytics/reports.py:require_author/owned`, and `web/api.py:require_tenant_surface_access` provide existing access semantics. A new search endpoint must not bypass playground/lesson restrictions through its broader route.

**Alternatives rejected**: One failing query aborting every category, using a cached catalog as execution authorization, and broadening the lesson read allowlist to all searchable models.

## 7. Preferences and contextual actions

**Decision**: Versioned browser-local references only, keyed by user and tenant, max twenty recents and twenty favorites. Persist no labels, amounts, payloads or query history. Resolve before rendering. Clear feature keys on logout and react to logout/storage events in other tabs; inaccessible references are removed after an explicit denied/not-found resolution, not on a transient network error.

**Evidence**: Existing `actionTarget` in UnifiedApp supports specific typed targets, but `ActionDiscoveryProvider.open` currently clears them. Extend that contract using an allowlisted target union. Reuse receipt, reservation release, movement correction, credit/refund and reversal flows only when the exact existing context is available and the shared service permits it.

**Alternatives rejected**: New profile table, cross-device synchronization, arbitrary form-value blobs and rendering stale protected labels from local storage.

## 8. Catalog, reports and chat

**Decision**: Build search entries from the unified ToolCatalog capability identities, resource synonyms and existing navigation/analysis metadata. Deduplicate report/capability representations. Expand the existing application-reference metadata only as necessary to expose canonical synonyms and launch eligibility. Private report search remains owner-scoped; templates open their existing date-selection interaction.

The chat handoff uses the existing company-bound `reality:open-chat` event and draft behavior. Extend the existing visible/removable context mechanism for a selected record; no raw payload or bulk result rows are attached. Never send or execute on selection.

**Alternatives rejected**: Parallel hand-maintained action list, invented direct Web actions for tool-only capabilities, silently inserting a snapshot date and a second chat agent.

## Resolved research status

No unresolved technical clarification remains. The workload, migration compatibility, exact-target hydration and permission-negative scenarios remain required executable checks during implementation. No claim is made that those checks have passed.

## Primary documentation checks

PostgreSQL 17 supports Unicode normalization with UTF8 encoding; lowercasing follows database locale, so the planned indexed normalization must use explicit versioned folding rather than assume locale-independent `lower`. [PostgreSQL string functions](https://www.postgresql.org/docs/17/functions-string.html).

Expression indexes store access expressions and impose maintenance cost on writes; benchmark both read benefit and migration/write impact before retaining each index. [PostgreSQL expression indexes](https://www.postgresql.org/docs/17/indexes-expressional.html).
