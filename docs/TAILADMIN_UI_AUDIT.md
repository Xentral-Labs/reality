# TailAdmin UI Audit

Audit date: 2026-08-29

Migration status: the former global `design-system.css`, `app.css`, and
`navigation.css` have been removed. The remaining legacy files listed below are
page-local migration work and no longer define the global application shell.

Scope: all product application routes captured by `scripts/visual_audit.py`, reviewed
at desktop and representative mobile sizes. The independently deployed public Site
in `provider-site` is outside this admin-shell migration.

## Executive finding

The application is not yet a single TailAdmin UI. After removal of the old
global design system it still combines these styling layers:

1. vendored `tailadmin.css`;
2. legacy page styles such as `erp.css`, `chat.css`, `explorer.css`, and
   `documentation.css`;
3. `tailadmin-adapter.css`, which currently contains the shell, new shared
   application components, and compatibility rules for unmigrated pages.

The thick black create buttons came from the removed global legacy rule
`button { background: var(--br-ink) }`. Remaining buttons must now use explicit
TailAdmin semantic classes rather than a default element skin.

## Priority 0 — remove the mixed foundation

| Problem | Current evidence | Target |
| --- | --- | --- |
| Global legacy button styling | New Party, New Item, New Location, Pricing actions and many integration actions render as heavy black blocks | Explicit TailAdmin primary, secondary, danger, ghost, and icon-button components; no global `button` skin |
| Competing global typography/table rules | `design-system.css` defines tiny `th`, `td`, status, card, and heading sizes; the adapter enlarges them again | TailAdmin tokens and utilities are the only global rules |
| Legacy ERP component layer | Most operational and master-data templates load `erp.css` | Replace `erp-*`, `detail-*`, `record-*`, and `master-*` presentation classes with shared TailAdmin template components |
| Growing override layer | `tailadmin-adapter.css` fixes rules from both old systems | Shrink it to shell behavior and genuinely domain-specific patterns |
| Utility availability is accidental | Some Tailwind utility classes used in templates are absent from the vendored compiled CSS | Build Tailwind from this repository's templates or use a small, explicit component stylesheet; do not rely on classes compiled for TailAdmin's demo pages |

## Global shell

### Not yet matching TailAdmin

- The header is mostly empty and shows only the agent square. TailAdmin provides
  a prominent command search, menu control, and right-side utility area.
- Breadcrumb/page context is not reliably visible.
- The sidebar accordion now follows the correct hierarchy, but tenant switching
  and company creation still use bespoke controls.
- Buttons have no shared semantic component API; their appearance depends on
  element type and surrounding legacy class.
- Page headers alternate between direct Tailwind utilities and `erp-head`.
- Empty states are usually a sentence inside an otherwise empty table.

### Target

- One shared page-header component with eyebrow/breadcrumb, title, description,
  optional KPI summary, and a TailAdmin primary action.
- One shared command/search header.
- One button system: `primary`, `secondary`, `danger`, `ghost`, `icon`.
- One table system: toolbar, search, filter chips, result count, table, empty
  state, pagination area, and row action menu.
- One drawer/dialog system with consistent header, body, confirmation copy, and
  footer actions.

## Page-by-page findings

### Home

- Direct utility markup, but several proportions still depend on utilities that
  may not exist in the vendored build.
- Content hierarchy is visually left-heavy; the exception list and agent card
  do not form a balanced operations workspace.
- The inventory snapshot is visually smaller than its operational importance.
- Target: TailAdmin ecommerce/operations dashboard grid with exception queue as
  the primary panel, control cards, and a full-width current-position table.

### Operational Exceptions

- The review-queue model is appropriate and should remain.
- Search lacks severity/type filters and a visible result count.
- The detail interaction still uses the legacy `record-dialog` drawer.
- Target: TailAdmin task-list proportions, filter chips, a review drawer, and
  actions that clearly distinguish inspect, control, and trace.

### Copilot Chat

- Still loads `chat.css` and is restyled through adapter overrides.
- Messages are plain text blocks; evidence, source links, proposals, and
  confirmation states do not have first-class visual components.
- Target: TailAdmin chat/text-generator shell with conversation search, business
  context header, evidence cards, and explicit proposal/confirmation cards.

### Commitments

- The domain-specific promise control is useful and may remain custom.
- The register is legacy `erp-table`; there are no risk/direction/due-date filter
  controls or sorting affordances.
- IDs remain more visually prominent than necessary.
- Target: TailAdmin data table with exception-first filter presets and a shared
  explanation drawer.

### Inventory

- Legacy table and drawer components.
- `available == 0` currently renders the positive label `AVAILABLE`; for an
  operations user this should communicate fully allocated/no free availability,
  not a healthy available state.
- No shortage/fully allocated/available filter or location dimension.
- Target: stock-control data table with semantic states and TailAdmin filters;
  retain the movement/reservation control equation as a domain component.

### Open Items

- Empty state is only “No posted invoice items” inside a table.
- No aging buckets, overdue control total, receivable/payable split, or suggested
  next setup/action.
- Target: finance worklist with control totals and an explanatory empty state.

### Payments

- Same legacy register pattern and weak empty state.
- Allocation/unallocated state is not visually prioritized as the work queue.
- Target: settlement workbench with unmatched payments first.

### Journal and account statement

- Register is visually acceptable but still uses legacy classes.
- Empty view gives no explanation of which evidence creates postings.
- Debit/credit presentation, account drill-down, and control totals should be the
  primary hierarchy, not technical posting IDs.
- Target: TailAdmin data table plus retained domain-specific T-account component.

### Documents

- The register shows the party opaque ID instead of the party name in the primary
  business column.
- The row action is a plain “View” link and not a consistent action/menu pattern.
- Target: evidence data table with human business context first and technical IDs
  secondary.

### Document detail

- Uses a bespoke two-column card layout and legacy drawer/dialog components.
- Raw source payload is expanded as a large dark block instead of progressive
  disclosure.
- Execution control and financial posting sections compete visually.
- Target: TailAdmin detail header and tabs/sections; operational consequence and
  postings first, raw payload collapsed last.

### Timeline

- Clean basic log, but lacks date grouping, event-type filters, search, and
  business-object focus.
- Target: TailAdmin activity/table pattern with sticky date groups and filters.

### Parties, Items, Locations, Payment Terms

- All use `erp.css`, legacy black create buttons, legacy tables and
  `record-dialog` create forms.
- Opaque IDs occupy primary table columns although they are trace data.
- “Edit →” is repeated as an unstructured row action.
- Target: TailAdmin data tables, blue primary create actions, row overflow menus,
  and Form Elements-based create/edit drawers.

### Party, Item, and Location detail

- Edit forms are permanently visible alongside operational information.
- Lifecycle/destructive controls look like ordinary card content.
- Trace IDs and raw relationships are too prominent for the default view.
- Target: read-first detail view with an explicit Edit action opening a drawer;
  separated danger zone and progressive trace disclosure.

### Pricing

- Header actions are heavy black blocks.
- Six configuration tasks are displayed simultaneously, creating a long setup
  form rather than a guided pricing workspace.
- Empty price lists do not guide the correct creation sequence.
- Target: tabs or staged workflow for Lists, Tiers, Party assignments, and Group
  assignments; TailAdmin primary actions and contextual empty states.

### Integrations

- The page is an overwhelming grid of connector forms with repeated black
  “Create selected definition” buttons.
- Source catalog, configured sources, capabilities, test ingestion, and recent
  records compete on one very long page.
- Target: TailAdmin Integrations catalog cards with one configure action per
  connector; configured sources as the default view; capability and test-ingest
  workflows in drawers or dedicated detail pages.

### Explorer

- Custom CSS is justified because this is intentionally a technical inspector.
- It still needs collection search, record filtering, clearer Source → Evidence
  → Reality landmarks, and sticky navigation.
- Keep it visually distinct from operational worklists without creating another
  global design system.

### Documentation

- Custom layout is justified, but the page is extremely long and dense.
- Generated CLI/data-model material overwhelms task-oriented guidance.
- Target: searchable TailAdmin tabs with task entry points first and generated
  reference content behind focused sections.

## Recommended migration order

1. Remove global element styling from `design-system.css` and introduce shared
   TailAdmin button, page-header, form, table, empty-state, and drawer components.
2. Migrate Parties, Items, Locations, and Payment Terms first; they prove the
   shared register and form patterns with low domain risk.
3. Migrate Commitments, Inventory, Documents, Open Items, Payments, and Journal
   to the shared data-table shell while preserving domain controls.
4. Rebuild Pricing and Integrations as guided workspaces rather than long pages.
5. Rebuild Copilot Chat on the TailAdmin chat pattern with evidence and
   confirmation components.
6. Refine Home, Timeline, Explorer, Documentation, and detail pages.
7. Delete unused legacy CSS and reduce `tailadmin-adapter.css` to shell and
   domain-only rules.

## Required page arrangement

The following order is the target information architecture, from top to bottom
and, where noted, left to right.

| Page | Required arrangement |
| --- | --- |
| Home | Page context → attention/control totals → two-column area with exception queue left and agent briefing right → full-width inventory position → recent business changes |
| Operational Exceptions | Header and open count → filter/search bar → priority review list → right-side review drawer with impact, derivation, recommendation, proposed change, trace |
| Copilot Chat | Conversation list left → business-context header → messages/evidence/proposals center → fixed composer → confirmation card immediately below the proposal it controls |
| Commitments | Header and risk totals → item-level promise control → filters → promise register → explanation drawer |
| Inventory | Header and shortage/allocated/available totals → filters including location → stock register → explanation drawer with physical movements, reservations, inbound and equation |
| Open Items | Header → receivable/payable, overdue and open totals → aging/status filters → worklist → evidence/settlement drawer |
| Payments | Header → received/paid/unallocated totals → unmatched-first filters → payment register → allocation detail drawer |
| Journal | Header and debit/credit control totals → account/date filters → posting register → account or posting detail drawer |
| Documents | Header and evidence totals → type/source/date filters → document register with party name → document detail |
| Document detail | Back/breadcrumb and summary → execution state → document lines → Reality consequences → financial postings → source metadata → collapsed raw payload |
| Timeline | Header → date/type/object filters → date-grouped activity stream → record explanation drawer |
| Parties | Header with blue primary create action → search/type/status filters → party register → row menu |
| Party detail | Identity and state → operational/financial position → commercial terms → source/trace → explicit Edit drawer → separated danger zone |
| Items | Header with blue primary create action → search/type/status filters → item register → row menu |
| Item detail | Identity and state → inventory position → commitments/movements → pricing/defaults → Edit drawer → danger zone |
| Locations | Header with blue primary create action → search/type/status filters → location register → row menu |
| Location detail | Identity/state → stock at location → movements → configuration → Edit drawer → danger zone |
| Payment Terms | Header with blue primary create action → compact searchable register → create/edit drawer → usage context |
| Pricing | Header → tabs for Price Lists, Tiers, Party Assignments and Groups → selected-tab table → contextual empty state → one focused create/edit drawer |
| Integrations | Header → configured sources first → connector catalog/search → source detail with capabilities → test ingest drawer → recent source records |
| Explorer | Header/search → sticky Source/Evidence/Reality navigation → selected collection → records → field/relationship inspector |
| Documentation | Header/global search → task-oriented entry cards → tabs for concepts, CLI, data model and catalogs → local section index → selected reference content |

## Acceptance gate

A migrated page must not load `erp.css`, must not inherit a global element-level
button/table skin, and must use the shared TailAdmin page header, action, form,
table, empty-state, and drawer patterns where applicable. Visual audit must pass
at desktop and mobile with zero browser errors. Raw browser-default form controls
are a failed migration; fields must use the shared `br-field`, `br-input`,
`br-select`, help-text, checkbox, focus, and validation primitives.

## Migration status — completed 2026-08-29

- Every product template now loads one shared `application.css` layer on top of
  the vendored TailAdmin Community stylesheet. The public Site remains isolated
  in `provider-site/src/landing.css`.
- `erp.css`, `chat.css`, `documentation.css`, `explorer.css`, the previous
  adapter stylesheet, and the older global design-system stylesheets have been
  removed. No template references them.
- Registers, page headers, controls, forms, dialogs, badges, detail cards,
  technical inspectors, chat, and documentation now share the `ta-*`
  component language. Domain-specific T-accounts remain custom by design.
- Inventory availability at zero is labelled `Fully allocated`; it is no longer
  incorrectly shown as available.
- The automated visual audit renders 22 desktop/mobile states with zero browser
  errors. The Python quality gate passes with 83 tests and one skipped test.

The longer-term information-architecture recommendations above remain the
product backlog for deeper workflow refinement; they are no longer blockers for
the removal of the legacy design system.
