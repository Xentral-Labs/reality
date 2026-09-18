# Current-State Audit: Global Command Palette

**Inspected**: 2026-09-18
**Method**: Repository source and existing contracts, plus the user-provided screenshot. No live runtime or database coverage claim is made.
**Spec impact**: This audit records baseline behavior; the adjacent draft spec proposes future behavior. No application code changed.

## Existing behavior and reusable capabilities

| Area | Evidence | What exists | Gap for this feature |
|---|---|---|---|
| Global palette | `apps/web/src/unified/ActionLauncher.tsx` | Cmd+K/Ctrl+K, sidebar trigger, portaled popover, focused/reset search, Escape/focus return, blocking-modal precedence, category grouping, catalog shortcut | Only global discovery entries; substring matching over translated categories/labels and command name; no business-record search, relevance model, recents, favorites or active-result arrow navigation |
| Shared action discovery | `apps/web/src/unified/actionDiscovery.ts` | Catalog placement, owner/demo filtering, existing form/destination dispatch; 23 declared form keys across orders, holds, reservations, warehouse/shipping and finance | Discovery eligibility is not sufficient evidence of execution permission; retain checks in the actual flow |
| Unified Tools | `apps/web/src/unified/ToolCatalog.tsx`, `toolCatalogEntries.ts` | Unified capabilities with topic/purpose filtering, exact technical-name discovery, linked forms, reports, details and chat draft handoff | Palette uses older action discovery rather than this richer discovery surface; capability presence does not mean direct Web execution |
| Business vocabulary | `packages/reality-core/config/resource_catalog.yaml` | Business-object labels and synonyms, including German ERP terms, with catalog relationships | Palette does not currently search these synonyms; every desired term/language needs explicit coverage proof |
| Route state | `apps/web/src/unified/routing.ts` | Workspace/register destinations; record, order, commitment, source, finance, warehouse, report and query selections | Each result family needs a verified exact destination; blindly clearing selection fields would discard record identity or filter context |
| Existing read surfaces | `apps/web/src/api.ts` | Query-bearing reads for documents, commitments, inventory, financial open items, payments, journal, timeline, order journeys, shipments, master-data choices, source records and private reports | These are separate searches with different fields/defaults/pagination; they are not a complete global search contract |
| Combobox suggestions | `packages/reality-core/src/reality/web/api.py`, `suggestion_list` | Tenant-scoped choices for parties, items, locations and other input kinds | Some branches materialize collections before filtering; commitments initially limit to 100. Do not reuse as proof of complete, scalable search |
| Inspector explorer | Same file, `get_explorer` | Tenant-filtered search over selected model fields; bounded groups; exact record representations | Ten-row per-model slices, technical vocabulary and direct adapter queries do not satisfy the new shared-service, ranking and pagination requirements |
| Reports/chat | `ToolCatalog.tsx`; `apps/web/src/api.ts` report reads; WEB_SPEC specs 226/228–232 | Report discovery, reader availability, private reports, templates, explicit snapshot inputs, company-bound editable chat drafts | Add discovery/access paths; preserve existing semantics rather than implement new report or chat execution |

## Product conclusions

1. Navigation and capability discovery can build on existing vocabulary and execution paths.
2. Business-record search is a material addition: it needs explicit family/field coverage, historical visibility, canonical identities, bounded reads and cross-tenant negative tests.
3. Recents/favorites are navigation preferences, not business records. The proposed browser-local scope avoids assuming a new profile schema.
4. Contextual shortcuts must prove a supported prefill path for the selected record; global form availability alone is insufficient.
5. Existing source and Inspector reads provide explainability destinations. A lightweight search result should not duplicate those details.
6. The new feature is distinct from spec 225's presentation-only palette scope and must receive its own reviewed plan and tests before implementation.

## Planning obligations

- Map each coverage-matrix row to actual shared reader/search support, held fields and an exact detail destination; record gaps explicitly.
- Prove worklist filters against shared canonical reads rather than infer status from document fields.
- Specify pagination/continuation and deterministic relevance across providers without full client-side dataset downloads.
- Define an executable language/synonym ranking corpus and a 100,000-record performance fixture.
- Plan unit, service, business-story and browser tests, plus the required repository gates and documentation updates; do not mark implementation acceptance complete during this draft phase.
