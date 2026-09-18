# UI and Launch Contract

## One palette, one launcher

Keep `ActionLauncher.tsx` as the shell entry and shared ActionDiscoveryProvider seam; move palette state/results into `CommandPalette.tsx` and pure `commandPaletteEntries.ts` helpers. Continue portaling outside the sidebar. Cmd+K/Ctrl+K, expanded/rail/mobile buttons share one instance. Another open modal takes precedence. Escape closes the current palette surface and restores the actual prior focus. IME composition and key auto-repeat cannot activate results accidentally.

Input label: localized Search or start an action. Show current company, All/Records/Actions/Pages/Reports filters and the active Records-family refinement. In All, company/help entries remain explicitly typed. Group results with short labels; show original business labels, held secondary context and an explicit outcome. Use the eleven fixed visible groups and filter mapping in spec.md §Result Groups and Search Filters. For nonempty previews, merge/deduplicate/rank first, then keep at most four hits per visible group and twelve overall. Keep global relevance order and identify each hit's group without reordering weaker hits above exact references. A labeled Show all link remains available for every group with hidden hits, even if it has zero preview rows. Show all selects one visible group, retains query/company/compatible family refinement and pages at most fifty merged hits; returning restores the preceding filter. Page transitions reset active selection safely. Utility controls do not count as hits; matched company/help entries do. Empty-query suggestions use their separate limits.

Use a combobox/listbox pattern with an active-descendant result, stable result IDs and a live status region. Up/Down move the active result and scroll it into view; Enter activates exactly that identity. Tab reaches filters, favorites, retry, Show all and dismissal controls. Secondary controls must not be nested interactive elements inside an option: render them as accessible siblings or a result-actions region. When results update, preserve a manually chosen identity; if it vanishes clear selection and announce the change. Loading must never redirect Enter to a newly inserted row.

Small-screen layout stays within viewport height, with a stable input/scope area and scrollable results. Touch targets at least 44px; test 200% zoom, rail/mobile entry and all four UI languages. No full raw payload, balance dashboard or long command parameter form is embedded in results.

## Typed launch descriptors

A descriptor is a discriminated union, never an arbitrary URL, command string or form-value map:

| Kind | Payload | Outcome |
|---|---|---|
| `page` | canonical destination/register key and allowlisted filter values | Existing navigation |
| `record` | physical kind/opaque ID plus canonical presentation family | Authorized exact detail |
| `action` | existing DeliveryAction key plus optional allowlisted ActionTarget | Existing form/review; no execution |
| `capability` | unified capability ID | Tools exact disclosure with current query |
| `calculated_report` | existing report target key | Existing ProjectionDataDialog/reader, or details if no reader |
| `saved_report` | report ID | Owner-checked report hydration into existing Analytics editor |
| `template` | template key | Existing template selection/input interaction; never auto-fill historical date |
| `chat` | bounded editable prompt and optional authorized visible record reference | Existing chat draft; no send |
| `company` | accessible company ID | Existing switchCompany flow |
| `help` | allowlisted existing help/documentation key | Existing help link; no arbitrary external target |

Backend-provided descriptors and local-storage descriptors are validated with the same allowlist. A click dismisses the palette before opening another form/dialog; failed resolution leaves a safe retry/unavailable state. Record/form context can only use the current company. Repeated activation is guarded until navigation/form open is acknowledged.

## Exact target routes and readers

Extend `Selection` and `readSelection/selectionUrl` with explicit optional fields:

- `inspectorTargetKind`, `inspectorTargetId` for the existing Inspector target.
- `analyticsReport`, `analyticsTemplate` (mutually exclusive with each other and existing proposal target).
- `toolCapability`, `calculatedReport` (mutually exclusive; Tools query uses existing `q`).
- `financeOverdue` for the named worklist, separately from status.

Retain existing master-data `family/record`, order/finance `entry`, and commitment selection. A centralized target-to-selection mapper constructs a clean destination from known defaults, retaining tenant/presentation preferences and clearing incompatible detail, page and filter fields. `companySelection()` clears every new field. Reject unknown target kinds safely. Serialize shipment direction on shipments as well as deliveries/commitments to preserve inbound navigation on reload.

| Target | Required component adaptation |
|---|---|
| Partner/item/location | MasterDataPage renders the existing detail reader/component independently of whether its record is on the list page; inactive records remain selectable. Partner with both roles chooses customer presentation deterministically while displaying both roles. |
| Order | OrdersPage loads exact Document detail for `entry` and displays existing order detail even when absent from the filtered/page slice. Correct customer/supplier side is retained. |
| Invoice/credit | FinancePage resolves exact document selection independent of outstanding defaults; use existing financial detail where supported, else document Inspector. Do not infer financial status from Document.status. |
| Payment/shipment | Exact existing Inspector target `payment`/`shipment` with cash-entry/shipment ID; selected detail opens without loading the corresponding list row. |
| Reality/source/evidence | InspectorRecordsPage accepts explicit kind/ID and opens existing Inspector directly. No `q=id` workaround. |
| Saved report | AnalyticsPage uses authorized `graphApi.report` and existing `GraphSteps`; preserve unsaved-draft navigation handling and report ownership. |
| Template | AnalyticsPage/GraphTemplates selects the template by key and leaves required date/period inputs visible before adoption. |
| Calculated report | RealityInspectorPage selects existing `buildReports` target and opens existing reader; retains unavailable-reader details/freshness. |
| Capability | ToolCatalog seeds query from route and expands the exact capability; reload/Back preserve intended target. |

A missing/deleted/forbidden record produces the same unavailable message without stale data or fallback to a similarly numbered object. Back restores prior route state. Existing detail operations continue through their original services.

## Contextual actions

Extend `ActionDiscoveryProvider.open` to accept an optional existing typed target, matching `UnifiedApp.actionTarget`. Explicit allowlist examples: receipt -> commitment; reservation release -> reservation; movement correction -> movement; sales credit -> invoice; refund -> credit note; ledger reversal -> posting group. Never derive posting-group identity from a document number. Only include an action when its actual detail/service response exposes the eligible target; a mere readable search hit does not imply mutability. Current record ID appears in the shortcut label. Do not promise unsupported prefills.

## Empty state and preferences

Up to four favorites, four recents and two eligible contextual shortcuts; deduplicate before filling missing slots with permitted common destinations. All favorites/recents remain accessible in an explicit management expansion, with pin/unpin/clear controls. Successful opens across existing page/record/report navigation paths feed recents through the shared opener, including ordinary navigation—not only palette selection. Canceled forms, failed detail reads and typed queries do not.

Resolve stored references before labels render. On logout, expiry or a cross-tab logout event clear rendered data and preference keys; successful company switch uses a fresh scope. Unknown storage versions or malformed entries are discarded. Browser storage failure permits in-memory use with a persistence hint.

## Chat, companies and help

Reuse Shell/ChatPage `reality:open-chat`. Append the editable prompt without deleting an existing draft; selected record context is visible/removable and tenant-bound. General question handoff attaches no implicit current-record context. Existing input limits, usage restrictions and failure behavior remain; sending is a separate explicit action.

Use bootstrap's accessible companies through `useCompanyContext.switchCompany`; choosing a company never resumes an old-company action. Existing help links come from ProfileMenu/navigation metadata. Browse all tools passes `q` into ToolCatalog. All new UI copy belongs in `localization.tsx` for English/German/Dutch/Spanish.
