# Unified App: remaining capability inventory

**Date:** 2026-09-08
**Status:** Historical inventory through Spec 134. The owner accepted the bounded completion sequence in [the completion plan](unified-completion-plan.md); unimplemented candidates below are not automatically release blockers.
**Spec impact:** None. Documentation-only inventory; no routes, permissions, tools or runtime behavior change. Implementation requires the applicable Spec Kit gates.

## Reading this inventory

The owner wants the new design to become the only application. Legacy feature parity
is not a requirement. The completed implementation increments are Specs 107–134;
their technical completion does not mean that rollout or presentation retirement is
complete. See [release status](../V0_CHECKLIST.md).

“Covered” means the bounded capability exists in the new UI, not that every function
of the old page has migrated. “Move” is a recommendation to rebuild the useful
interaction on shared services. “Defer” is a proposed exclusion from the initial
cutover scope, not permission to delete data or disable a required control.

This audit inspects route families, action dispatch, supporting links and Playground
editors. It is not a fresh runtime acceptance test or an exhaustive backend-tool
audit. A company Chat tool being available does not prove that its deterministic
form, selected-case entry and recovery experience are migrated.

## Already covered

| Capability | New destination / evidence | Boundary |
| --- | --- | --- |
| Common company shell, Home, worklist and customer delivery case | Spec 107; `unified/UnifiedApp.tsx`, `HomePage.tsx`, `DeliveryCase.tsx` | Production-company presentation; practice still has a separate entry. |
| Company conversations, contextual delivery assistant, decisions and receipts | Spec 107; `ChatPage.tsx`, `CaseAssistant.tsx`, `DecisionsPage.tsx` | Do not extend this claim to sandbox Chat or every legacy action form. |
| Reserve stock and record customer shipment | `ActionLauncher.tsx`, `ActionCard.tsx`; Spec 107 | Spec 116 additionally supplies receipt and reservation release. |
| Current-position Analytics and recorded activity | Spec 108; `AnalyticsPage.tsx` | Recorded-history coverage is explicit; prototype readiness, blocked-revenue and automation claims are not automatically live metrics. |
| Customer, supplier, item and location maintenance | Spec 108; `MasterDataPage.tsx`, `MasterDataCard.tsx` | Basic reviewed maintenance; advanced commercial configuration remains separate. |
| Stock, reservations, movements and exception investigation | Spec 109; `WarehousePage.tsx`, `AttentionPage.tsx` | Read/investigation coverage does not provide all warehouse mutations. |
| Open items, payments and journal investigation | Spec 110; `FinancePage.tsx` | Not a migrated finance action suite. |
| Source systems, source versions and document evidence | Spec 111; `DataSourcesPage.tsx` | Configuration/import and technical Explorer still link to legacy. |
| Personal preferences, appearance, access and AI summaries | Spec 112; `SettingsPage.tsx` | Owner summaries are not membership or provider credential editors. |
| Customer/supplier order evidence and outgoing/incoming commitments | Spec 113; `OrdersPage.tsx` | Supplier receipt is covered by Spec 116; multi-line order entry by Spec 119. |
| Recorded Facts with provenance and Inspector | Spec 114; `FactsPage.tsx` | Not a rule authoring or fact creation workspace. |
| Shared ERP table behavior across 16 variants | Spec 115; `RegisterTable.tsx` | Layout, density, sort and pagination; not additional business capabilities. |

All frontend paths above are relative to `apps/web/src/`.

## Completed since this inventory

Spec 116 completes supplier receipt (the incoming-delivery part of A2) and full
reservation release (A3), with record/launcher entries and shared company Chat and
Decisions review. Technical verification is recorded in
[Spec 116](../../specs/116-unified-receipt-release/quickstart.md).

Spec 117 completes delivery-specific hold/release (part of A4), with reason/note,
own versus customer-wide scope, shared case/launcher/Chat/Decisions review and
exact action-event recovery. See [Spec 117](../../specs/117-unified-delivery-holds/quickstart.md).
Party-wide and document-wide hold editors are still outside this completion claim.

Spec 118 completes movement reversal and quantity correction through Warehouse, the
global launcher and matching Chat/Decisions reviews, with exact effect/recovery proof.
See [Spec 118](../../specs/118-unified-movement-corrections/quickstart.md).
Opening/general stock movements, broader hold controls and document-line corrections remain outstanding. Release
uses the existing full-reservation semantics; partial release is not a migrated feature.

Spec 119 completes multi-line sales/purchase order entry (A1), preserving explicit
source totals and raw line metadata, with exact review, attributable receipts and
links to each delivery. See [Spec 119](../../specs/119-unified-order-entry/quickstart.md).

Spec 120 completes customer/supplier invoice entry against one selected order line (A6),
with stated amounts, shared review and exact financial receipts. See
[Spec 120](../../specs/120-unified-invoice-entry/quickstart.md).

Spec 121 completes recording a new customer/supplier payment against one selected invoice
(A7), including partial settlement and shared review/recovery. Existing-payment allocation,
multi-invoice splits and refunds remain separate. See
[Spec 121](../../specs/121-unified-payment-entry/quickstart.md).

Spec 122 removes the single-position invoice entry restriction: one invoice may contain
multiple selected positions of the same order, with independent stated line/header values.
Spec 124 adds partial and renewed billing to this flow. See
[Spec 122](../../specs/122-multi-position-invoices/quickstart.md).

Spec 123 completes full posting-group reversal (part of A8) with reason, exact financial
effects, common review and attributable recovery. Credit/refund entry remains separate;
Spec 124 adds renewed billing after full invoice reversal. See [Spec 123](../../specs/123-unified-financial-reversal/quickstart.md).

Spec 124 completes partial invoices and rebilling after complete invoice reversal (A6/A8).
Selection and review show ordered, effectively invoiced and remaining quantities with invoice
evidence links. This replaces the earlier one-invoice restriction; credit/refund and multi-order
consolidation remain separate. See [Spec 124](../../specs/124-partial-invoicing-rebilling/quickstart.md).

Spec 125 completes invoice-linked customer credit entry (A8): multiple positions and partial
quantities, explicit netting, no mandatory physical return, exact shared review/recovery and
credit→invoice→order Inspector links. Existing order-line return credit remains compatible.
Customer refunds are now covered by Spec 126; supplier credit entry remains separate. See [Spec 125](../../specs/125-unified-invoice-credit/quickstart.md).

Spec 126 completes customer refund entry from open credits (A8), including partial amounts,
reference/time, shared review/recovery, the Customer credits register and selected-row actions.
Both netting and refunds consume the same derived capacity. No bank transfer is initiated.
See [Spec 126](../../specs/126-unified-customer-refund/quickstart.md).

Spec 127 validates the complete linked customer journey in a real browser against an
isolated migrated database: order, reservation, partial shipment/invoice, payment, credit,
partial refund and refund reversal. It fixes narrow reversal wording, with no business-rule
change. Company/member administration is subsequently covered by Spec 128. Source/provider
setup and remaining cutover scope still require their own increments. See [Spec 127](../../specs/127-unified-business-journey/quickstart.md).

## Recommended remaining scope

The [source/import assessment](unified-source-import-assessment.md) audits B1 after
Spec 128. It recommends completing a narrow new-item CSV flow before exposing imports;
template registration is not a live connection. This is assessed scope, not implemented work.

| ID | Existing capability and evidence | Recommendation / target | Cutover condition |
| --- | --- | --- | --- |
| A1 | Manual sales and purchase orders; legacy `WorkspaceActionModal`, `create_manual_order` | Covered by Spec 119: multi-line sales/purchase entry from Orders, Actions and matching Chat/Decisions reviews. | Source-stated amounts preserved, exact references and partial/multi-line downstream work proven. |
| A2 | Supplier receipt and opening/general stock movement; legacy movement form, Playground `free-intent.ts` and guided opening stock | Move receipt into incoming delivery case; expose opening stock through a bounded Warehouse action. Evaluate additional movement types individually. | Quantity, location, authorization and duplicate-execution checks preserved. |
| A3 | Reservation release; Playground `ReleaseOperation.tsx` | Covered by Spec 116 in Warehouse and the launcher, with shared proposal review. | Whole active reservation released; stale/concurrent changes and event recovery verified. |
| A4 | Commitment, document-linked commitment and party delivery holds; legacy action dispatch | Delivery-specific case/launcher/Chat/Decisions controls are covered by Spec 117. Party-wide and document-wide editors remain open. | Existing blocked work can be understood and legitimately released; document links never become document fulfillment state. |
| A5 | Movement correction and document-line correction; legacy `MovementCorrectionModal`, `DocumentLineCorrectionModal` | Movement reversal and quantity correction are covered by Spec 118. Document-line correction remains open. | Retained operating flows have a safe correction path and traceable original records. |
| A6 | Sales/supplier invoice recording; Playground `FinanceOperation.tsx`, legacy `ManualDocumentModal` | Covered by Specs 120/122 through Finance, Actions and matching Chat/Decisions reviews; one or more selected positions of the same order per invoice. Further billing of an already invoiced position remains separate. | Record received amounts; no invented pricing/tax calculation or automatic invoice on shipment. |
| A7 | Customer/supplier payment posting; legacy dispatcher and Playground finance editor | Covered by Spec 121 through Finance, Actions and shared Chat/Decisions review: one new payment against one invoice, including partial settlement. Existing-payment allocation remains separate. | Partial payment, currency, exact allocation, confirmation and outcome recovery proven. |
| A8 | Posting-group reversal; legacy `LedgerReversalModal`; customer return/credit/refund guided Playground scenario | Complete posting-group reversal is covered by Spec 123 through Finance, Actions and shared Chat/Decisions reviews. Invoice-linked customer credit is covered by Spec 125. Customer refunds are covered by Spec 126. Physical return and supplier credit entry remain separate. | Do not retire safety/correction paths merely because their UI is less prominent. |
| B1 | Source registration, connector shell setup, source/capability activation and source enqueue; legacy `Integrations`, `ConnectorSourceModal`, `SourceDropModal` | Move into Data & sources as clear setup/import steps. | Connected-data onboarding and failure inspection work without an old-screen link. Existing connector support is not proof of arbitrary live integration. |
| B2 | Company creation, identity, members/invitations; legacy `Companies`, `CompanyDetail`, `CompanyMembers`, `CompanyOnboarding` | Covered by Spec 128: empty-company creation, no-company entry, identity and owner membership controls in Settings. Legacy name was read-only; no rename service exists. Lifecycle/deletion remains separate. | Verified contextual invitation acceptance, duplicate-name disambiguation, role restrictions and unknown-write recovery. Source/provider onboarding remains B1/B3. |
| B3 | Provider settings and MCP token creation/revocation; legacy `AgentsAndAI`, `MCPToolDialog` | Move provider setup into Settings; retain technical token controls in an advanced subsection where needed. | No secret disclosure or expanded tool permission; forms work without a model. |
| B4 | Payment terms, price lists, pricing groups; legacy `CommercialSettings` and party editing | Move reference maintenance required by retained workflows; defer a broad pricing workspace until a concrete job requires it. | Existing reference values survive editing; no silent loss of referenced commercial configuration. |
| C1 | Timeline/activity, technical Explorer and traceability hubs; legacy `Timeline`, `Explorer`, `TraceabilityHub` | Retain useful history/technical investigation inside Inspector or Data & sources; omit duplicate top-level hubs. | Important records, receipts and provenance remain reachable, including records outside the new registers. |
| C2 | Missing-information cases, fact-rule recommendation/simulation/activation/replay; legacy `MissingInformation` | Defer rebuilding the large authoring workspace pending a demonstrated operational need. Keep investigation understandable from Facts/Exceptions. | Inventory active rules and unresolved cases before retirement; required review/disable/recovery access cannot silently disappear. |
| C3 | Direct fact observation; legacy `observe_fact` form | Defer a generic everyday form; add a specific action only for a source-backed operational task. | Preserve recorded values/provenance and existing supported tool contracts. |
| C4 | Handling units, lots and serial units; legacy action definitions | Defer separate maintenance screens unless retained operations use tracked inventory. | Inspect actual use before excluding; tracked stock must remain operable and explainable. |
| C5 | Orders, warehouse queue, fulfillment blockers and supply/demand specialized projections | Reuse useful service results contextually; defer parallel dashboards and view launchers. | Compare required information with new Orders/Warehouse/Exceptions; do not equate similar titles with semantic parity. |
| D1 | Private practice runs, guided examples, saved/archived history and pending action recovery | Recommended: practice context inside the same app; remove the standalone Playground presentation. | Explicit environment boundary; no production admission/egress leak; old runs, receipts and uncertain actions remain recoverable. Practice retention is still a proposed scope decision. |
| D2 | Old sidebar, view switchers, duplicate registers and Playground cockpit | Retire presentation once selected capabilities and continuity pass acceptance. | One shell; supported old links translate without executing mutations. |
| D3 | Profile/help/Docs entry points and old onboarding/account-return links | Reuse new personal settings; keep help in shell; update external entry links during cutover. | Signed-out, awaiting-access, no-company and archived-practice entries have tested destinations. |
| D4 | `VITE_UNIFIED_APP` switch, legacy fallback and Playground root in `App.tsx` | Activate the new default after acceptance, then remove obsolete presentation and temporary switch after the rollback window. | Rollout approval, tested redirects, affected CI and rollback proof; no record deletion. |

## Proposed delivery order

1. **Finish warehouse execution:** A2–A5, supplier receipt and full reservation
   release are complete in Spec 116; delivery-specific holds are complete in Spec 117.
   Movement reversal/quantity correction are complete in Spec 118. Opening stock,
   broader hold controls and document-line correction remain candidates.
2. **Finish finance work:** A1, A6 and bounded A7 are complete in Specs 119–122; A8 reversal, invoice credits and customer refunds are covered by Specs 123–126; physical return and supplier credit entry remain candidates. Ship narrow business stories with their
   correction paths rather than one generic command panel. Reuse one reviewed action
   experience across deterministic forms, case controls and supported Chat entries.
3. **Make setup self-contained:** B1–B4 and C1. Include only commercial maintenance
   needed by selected workflows. Close normal onboarding, source, provider and member
   administration dependencies on legacy.
4. **Settle exclusions and practice continuity:** C2–C5, D1 and D3. Record owner scope
   decisions and inspect existing records/rules/runs before removal. Proposed deferral
   is not a verified statement that a feature is unused.
5. **Accept and cut over:** D2/D4. Run retained end-to-end workflows, real connected-data
   and provider checks, role/error/recovery journeys and visual acceptance; then make
   the unified application the sole entry and retire obsolete shells.

This is an ordering proposal, not newly approved feature specifications or completed
implementation tasks. New analytics ideas are a separate backlog and should not keep
retirement open indefinitely. The screenshot's illustrative metrics require their own
data definitions and evidence before becoming live claims.

## Retirement evidence still required

- Owner disposition of proposed moves, deferrals and practice retention.
- For every retained action: working deterministic entry, appropriate case context,
  shared service/tool behavior, exact mutation review, current authorization checks,
  idempotency and failure/unknown-result recovery.
- Dataset-aware check for active rules, tracked stock, commercial references, pending
  proposals and saved practice histories before removing their interfaces.
- Route map covering every legacy route and supported Playground/account-return URL;
  shell fallback must not accidentally revive the old application.
- Representative operational acceptance and required CI/browser evidence; update
  `docs/V0_CHECKLIST.md` only after the rollout gates are satisfied.

## Audit sources

- [Migration direction](unified-product-migration.md) and Specs 107–115.
- [Application root](../../apps/web/src/App.tsx) and
  [unified routes](../../apps/web/src/unified/routing.ts).
- [Legacy route union, components and action dispatcher](../../apps/web/src/legacy/LegacyProductApp.tsx).
- [New action launcher](../../apps/web/src/unified/ActionLauncher.tsx).
- [Playground operation chooser](../../apps/web/src/playground/OperationChooser.tsx),
  [fulfillment intents](../../apps/web/src/playground/free-intent.ts) and
  [finance editor](../../apps/web/src/playground/FinanceOperation.tsx).

The earlier roadmap's references to old components in `App.tsx` are historical;
those components now live in `legacy/LegacyProductApp.tsx`. No new runtime or test
results are claimed by this documentation-only audit.

## B1 increment — Spec 129

Data & sources now contains the new-item CSV upload, mapping, whole-file review,
confirmation, exact result recovery and original-file inspection flow. Existing
items are never overwritten; limits are 500 rows and 2 MiB. Item-file worker atomicity,
replay and retry are repaired with regressions. B1 remains partial: other file
profiles, source configuration and actual vendor transport need their own scoped
requirements and evidence before the legacy links can be retired.

## B1 increment — Spec 130

Source registration and inspection of existing source/type definitions now live in
unified Data & sources. Registry flags have explicit reviews and honest metadata
semantics; lost responses use current-state inspection without automatic retry.
The old source-configuration link is removed from this normal flow. B1 is still partial:
connector transport/templates, creation of additional type declarations and further
CSV profiles require their own decisions and evidence. Technical Explorer and overall
legacy/Playground retirement remain open.

## B3 increment — Spec 131

The new Settings AI section now provides reviewed managed/company-Anthropic credentials
and explicit MCP token creation/revocation with one-time secrets and tool scopes. The
old advanced-company link is removed from this flow. Other saved provider definitions
remain readable with an explicit runtime limitation: current Ask Reality uses company
keys only for Anthropic. Supporting additional providers in the actual chat runtime is
a separate backend feature, not accomplished by migrating the old provider dropdown.
No live provider connection was tested or shared credentials changed.

## A2 increment — Spec 132

The retained opening-stock action now has a bounded unified Warehouse form and launcher
entry, shared with matching Chat/Decisions proposals. It adds a reviewed quantity to
existing physical stock through the canonical movement tool, with exact receipt,
request recovery and existing Inspector/correction access. This first form accepts
untracked stocked items only. General adjustments, transfers, physical returns and
tracked opening workflows remain separate candidates; this does not complete A2 or
retire the legacy/practice surfaces. No inventory-count or target-balance semantics
are introduced.

## A4 increment — Spec 133

Customer-wide shipment hold placement/release now has one reviewed card in customer
cases, selected customer master data, Actions and matching Chat/Decisions. This retains
existing shipment-only gating: new reservations remain permitted. Exact customer hold
sets, attributed event/history and uncertain-result recovery are separate from current
state. Individual delivery holds remain when the customer hold is released. A4's
remaining document-wide editor is not covered, and overall legacy/practice retirement
remains open.


## C1 increment — Spec 134

The new header Activity drawer retains read-only cross-business event history with
search, time windows, historical attention filtering, explicit cursor paging and
shared event/subject inspection. It preserves current workspace context. This replaces
the need to leave the unified app for ordinary history review; no complete process,
current status or unread/live notification claim is inferred from event pages.
C1 remains partial: broader Technical Explorer navigation and final legacy/practice
retirement still need separate scope and acceptance. No shared business data changes.


## Completion scope freeze — owner accepted 2026-09-08

See [Unified app completion plan](unified-completion-plan.md) for the accepted finish
line, live local read-only findings, remaining route dependencies and three bounded
functional closure packages. Ordinary-company pending decisions, one active rule and
owned practice history need continuity. Unused local tracked/commercial editors are
deferred; broader deployments require their own inventory. The owner’s UI changes
follow functional acceptance and precede final presentation retirement.
