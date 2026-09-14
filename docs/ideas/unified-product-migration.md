# Unified Business Reality product migration

**Date:** 2026-09-07
**Status:** Proposed migration roadmap for product review; not an approved implementation plan.
**Spec impact of this document:** None. This records a proposed product migration without changing runtime behavior. Each implementation increment must pass the repository's Spec Kit workflow.
**Design reference:** `output/visualizations/reality-unified-ui.html` and its standalone preview. These local, currently untracked mockups communicate interaction intent; their fixtures, scripted chat, arithmetic, CSS and in-memory state are not production contracts.

## Owner direction: build from the new design

For the post-Spec-115 implementation status and proposed remaining scope, see the
[capability inventory](unified-capability-inventory.md). The roadmap below records
the original direction; its milestone descriptions are not current completion flags.

The owner clarified that the new HTML is the preferred product starting point.
Build its coherent interface first, then review legacy functionality for actual
product value. Much of the old UI was experimental; feature-for-feature parity is
not a requirement. The old application is a source of proven services and useful
capabilities, not the target information architecture or a mandatory backlog.

Build a fresh presentation layer within the existing Product Web application and
its design primitives. Reuse the domain, services, tools and security contracts.
Do not transplant whole old screens merely to preserve their existence, and do not
copy the mockup's scripted behavior into production.

Review old capabilities in bounded batches as the relevant new workspace is built:
keep when a concrete user task requires them; redesign when useful but awkward;
defer when the use case is unproven; retire experimental UI with no target use case.
Record decisions and affected contracts. Existing data, authorizations, confirmed
effects, recoverable pending actions and required safety/correction paths remain
protected even when their old entry points disappear. An exhaustive old-screen
inventory must not delay the first new-design implementation slice.

## Outcome

Deliver one product application with one navigation system, one case workspace, one action experience and one explainability path. Replace both the current Product App presentation and the separate Playground presentation. Users must not finish the migration with an Old app/New app/Playground choice.

One application does not mean one enormous page. Home, Analytics, Chat, operational registers, master data and configuration answer different jobs inside the same shell. The shared case workspace connects them.

Working assumption pending owner feedback: retain isolated practice companies inside this application, and remove the standalone Playground interface. Retiring an interface does not delete saved runs, source payloads, records or execution history. If the owner instead wants learning removed entirely, retain an authorized read/history path and specify the retirement policy before implementation.

## Product decisions captured from the conversation

- Preserve the App's dashboard strength and the Playground's understandable business flows.
- Home answers what needs attention now. Analytics explains company position and change over time. Home contains a compact Analytics preview.
- The case workspace keeps a selected business case and its contextual assistant together; its worklist is immediately reachable.
- Business language leads. Important quantities open their derivation and shortest true links to Reality, Evidence and Source.
- The global Chat can connect multiple business cases within the active company. The case assistant starts with explicit selected context.
- One action card is reachable from a case, Chat and a global action launcher. These are entry points, not three implementations.
- Action cards support typed fields and reference choices: edit intent, prepare/review the exact change, explicitly confirm, inspect the verified result.
- Show tool name, arguments and execution evidence in optional technical detail.
- Master data is a visible company navigation destination, separate from imports, source payloads and technical exploration.
- Retire the separate legacy and Playground shells after the approved new-product scope, data continuity and security are verified. Full legacy feature parity is not required.

## Evidence from the current repository

This is a focused structural inspection, not a completed capability audit or a verified release assessment. Runtime code and executable tests must settle discrepancies with older feature descriptions.

| Area | Existing foundation | Migration implication |
| --- | --- | --- |
| Application root | `apps/web/src/App.tsx`, `App()` selects `PlaygroundPage` or `ProductApp` by path | There are actually two presentation roots to consolidate. Preserve their different admission rules. |
| Product navigation | `ProductApp`, `Sidebar`, `MobileHeader`, workspace views and launchers in `App.tsx` | Build the common shell from existing components and route contracts. |
| Actions | `WorkspaceActionLauncher`, `WorkspaceActionModal`, `SimpleCreateModal`; catalog-owned command effects | Reuse discovery, metadata and service execution. Consolidate presentation and proposal lifecycle rather than create a command engine. |
| Chat and review | `Copilot`, `ProposalCard`, `DecisionQueue`, `DecisionHistory` | Preserve durable company conversations and existing proposals/history. |
| Traceability | `InspectorDrawer`, `Explorer`, existing projection and inspector APIs | Put a readable case layer in front of the existing authoritative paths. |
| Registers | Commitments, documents, inventory, reservations, movements, open items, payments, journal, master-data and commercial components | Evaluate each capability against the new product's user tasks; reuse services and rebuild only justified UI. |
| Playground UI | `apps/web/src/playground/PlaygroundPage.tsx`, `PlaygroundWorkspace.tsx`, operation editors and history components | Reuse proven interaction patterns while moving them into shared surfaces. |
| Sandbox execution | `services/playground.py`, `web/playground.py`, `playground/actions.py`, `playground/catalog.py` | These enforce capabilities, ownership and recovery. They are not disposable duplicate UI. |
| Sandbox companion | `services/playground_chat.py`; Spec 106 | Currently contracted as read-only and without durable conversation storage. Unified appearance must not silently grant mutation or persistence. |
| Dashboard trends | `previewTrendData`, `PreviewOperationsTrend`, `PreviewRealityFlow` in `App.tsx` | Existing examples are illustrative. They do not prove live historical metric support. |
| Quality | `.github/workflows/quality.yml`, frontend contract tests, PostgreSQL suites | Preserve behavioral coverage when replacing tests tied to old markup or navigation. |

Relevant contracts include Specs 030, 038, 042, 046, 049, 051, 056, 096, 103, 104, 105 and 106, plus `docs/WEB_SPEC.md`, `docs/WEB_UX_MATRIX.md` and the Constitution. The implementation inventory must find additional affected specs rather than assume this list is exhaustive.

## Target information architecture

| Navigation group | Destination | Responsibility |
| --- | --- | --- |
| Daily work | Home | Current position, compact Analytics preview, exceptions, briefing and next decisions |
| Daily work | Analytics | Defined metrics, historical trends, filtered contributors and explanations |
| Daily work | Ask Reality | Company-scoped conversations, answers, evidence and action cards |
| Daily work | Your work | Open business cases with selected case detail and contextual assistance |
| Daily work | Exceptions | Existing derived exception catalog and prioritized investigation |
| Daily work | Decisions | Pending proposals, rejection, execution state and decision history |
| Workspaces | Orders & deliveries | Sales/purchasing, commitments, holds, readiness and execution controls |
| Workspaces | Warehouse | Inventory, reservations, movements and existing warehouse projections |
| Workspaces | Finance | Open items, payments, allocations, journal, reconciliation and corrections |
| Workspaces | Facts | Existing facts and access to related open questions/rule workflows |
| Company | Master data | Parties, items, locations, payment terms and existing commercial/pricing functions |
| Company | Data & sources | Sources, imports, evidence, processing, technical Explorer and relevant troubleshooting |
| Company | Settings | Company membership, preferences, agent/provider access and existing administration |
| Existing shell chrome | Company/context selector | Authorized company or private practice context, visibly distinguished |
| Existing shell chrome | Execute action | Searchable command-backed actions with business labels and prerequisites |
| Existing shell chrome | Activity/help/profile | Preserve existing support destinations without crowding everyday navigation |

Use progressive visibility for a new company. Empty operational modules remain discoverable without implying that sources or records already exist. Practice creation and guided learning belong in onboarding/help and the context selector, not in a second product shell.

## Shared interaction contracts to specify

### Case workspace

A case is a UI selection over authoritative records, not a new workflow/status table. Start with a commitment or open item and follow existing links. Support partial fulfillment, several lines, multiple reservations, returns and related evidence without inventing a linear completion status on documents.

On a wide display, show worklist, selected case and contextual assistance together. Global application navigation remains distinct from the case worklist. On smaller displays, adapt layout while preserving selected case, draft, explanation and return context. A technical inspector can open alongside or within this workspace; it must not replace the user's current tenant or silently lose the case.

### Shared action card

The proposed lifecycle is: editable intent → validated proposal/review → confirmed execution → verified receipt or explicit failure/uncertainty. Map this to existing backend statuses; do not invent a separate client-side authority.

- Opening, searching, prefilling or cancelling an unprepared form creates no business records.
- Creating a draft/proposal is not business execution; make this distinction visible.
- Editing a prepared intent invalidates its prior review/confirmation token. Obtain the existing service's fresh proposal/revision contract.
- Same command, actor, environment and intended arguments produce equivalent validation/effects regardless of whether the entry is Chat, a case or the launcher.
- Reference resolution uses opaque identities; ambiguous names require a choice.
- Source-stated money/quantities are entered or preserved, not recomputed from guessed prices/taxes.
- Every confirmed mutation rechecks authorization, current prerequisites and stale state server-side.
- Duplicate clicks/reloads must not execute twice. Lost responses must recover the existing outcome rather than blindly retry.
- Execution success and refresh/observation failure are different. Show the recorded receipt and recover observations without executing again.
- A multi-step request such as reserve then ship gets separate, dependency-aware reviews and confirmations. Do not treat the first confirmation as blanket permission.
- All applicable actions must remain usable without an AI provider.

The global launcher exposes only cataloged, authorized capabilities for the active context. Do not turn it into an arbitrary SQL/code/ORM console. Preserve existing specialized command/CLI support under technical tooling where already authorized.

### Chat and environment policy

Use shared message/proposal presentation for global and contextual conversations, with server-bound tenant and selected-record context. Preserve company conversation persistence; specify whether sandbox history becomes durable before adding it. Navigation must not clear a pending action or hide an uncertain execution.

For the first migration increment, keep existing sandbox Chat read-only. Reaching action cards through deterministic controls is still possible under the existing sandbox service policy. Enabling Chat to prepare sandbox mutations is a separately specified capability change with owner, tool allowlist, exact-intent, quota and recovery tests; never bypass Spec 106 by routing sandbox Chat through the production provider path.

Never carry one company's chat context, cached records, draft selection or confirmation authority into another. Verified accounts awaiting production admission must still be able to enter their authorized practice environment without calling a production bootstrap that exposes data or grants access.

### Analytics

Each live metric needs a documented question, unit, scope, numerator/denominator where relevant, filters, time basis, completeness/freshness condition and contributor drill-down. All aggregations and classifications use shared services, not page-loaded record subsets.

- Begin with positions existing services can prove: stock/reservation quantities, open commitments and open-item balances.
- Reservation coverage is not shipment readiness. Readiness also depends on existing holds, references and execution rules.
- Unreserved demand is not proof of a shortage. An open balance without a due date is not overdue.
- Currencies are not added together without an authorized conversion policy. Mixed item units must remain separable.
- Source-stated order values remain source-stated. Do not infer a prorated blocked value from a line price when the source has not supplied that amount.
- A historical series requires reconstructible dated observations/events and defined time semantics. Present-day rows alone do not prove past stock or readiness.
- Never backfill absent history with the HTML's synthetic curve. Insufficient coverage must produce an honest unavailable/partial-history state.
- Automation potential percentages require a defensible candidate population and eligibility rule. A bounded candidate count is a valid first release if a percentage is not supported.
- Home and Analytics use the same metric contract and drill-down parameters. Analytics filters must survive the path into contributors and a selected case.

## Delivery sequence and review gates

These are proposed milestones, not executable Spec Kit tasks. Each phase needs requirements, an approved scope, a Constitution-passing design, test-first tasks, analysis and verification before its implementation begins.

### M0 — Establish the new-product contract

Produce an umbrella feature specification centered on the HTML and conversation, approved information architecture, initial screenshots and a targeted test baseline. First identify shared service contracts, admission boundaries and continuity-critical paths. Review less visible legacy functionality as its target workspace is developed rather than requiring a complete inventory before building the new shell.

Maintain a rolling capability decision log: user job, old entry, service/tool, actor/policy, keep/redesign/defer/retire decision, rationale, applicable contract changes and data/recovery implications. Existing UI does not automatically become a requirement. Any intentional removal affecting actual business workflows or safety must be reviewed before cutover.

Define unavailable-data, empty, pending-access, archived-run and no-provider behavior. Set representative tenant sizes and performance budgets using current measurements. Freeze the required end-state; follow-up feature ideas must not indefinitely delay retirement.

**Gate:** Owner reviews the complete target scope and any intentional removals. Baseline failures are documented and resolved before affected checks can be considered green.

### M1 — Build the common shell and context boundary

Build navigation, chrome, page headers, context selection, responsive behavior and route history from the new design using existing product primitives. Establish fresh coherent page components rather than wrapping the old screens. Connect real services progressively, with explicit loading, empty and unavailable states; extract useful low-level components from `App.tsx` only as needed.

Support company, new-company onboarding and authorized practice contexts using the same visual shell while retaining their backend admission policies. Add a temporary internal migration switch and safe old-link translation where needed; do not market a permanent second app.

**Proof:** Reload/deep link/back-forward preserve context. Cross-tenant and cross-run IDs are refused. Pending accounts do not gain production access. All four languages and light/dark desktop/mobile states are usable.

### M2 — Deliver one complete case and action-card slice

Implement the delivery case through shared read models and the reusable action card, then wire all three entries: case, launcher and company Chat. Bring proposals into Decisions with inspectable results. Keep technical details accessible.

The first business story uses the existing canonical lesson: opening stock 20, customer commitment 12, reserve 12, ship 5, observe physical 15/reserved 7/available 8/open 7, then separately confirm shipment of the remaining 7. No invoice or payment is inferred. This replaces the prototype's simplified lamp state with an executable domain story.

**Proof:** All three entries produce the same command/effects with the same inputs. Test ambiguity, rejection, stale inventory, exact preview binding, double confirmation, refresh during execution and lost-response recovery. Inspect the actual created records through their shortest true links.

### M3 — Build the selected operational and master-data scope

Build the operational jobs selected for the new product: sales and purchasing, receipt/shipment/reservation, financial evidence and allocation, and reference maintenance. Review legacy release, return, correction/reversal, hold and commercial features by demonstrated need. Retain the correction and control capabilities required to operate the selected workflows safely; defer or retire unrelated experiments through the decision log.

Create a visible Master data destination with real create/edit behavior, autocomplete, untouched-field preservation and revision checks. Link item/party/location detail from cases and registers. Build sources, evidence and technical exploration around the agreed navigation. Evaluate open-question/fact-rule and specialized projection interfaces separately; their prior existence does not mandate rebuilding them.

**Proof:** Every moved capability has a business story and adapter/UI proof. Include multi-line/partial delivery, two similar party names, stale reference edits, partial payment, return/reversal and bounded large-register navigation. No operation is accepted as complete while its required regressions fail.

### M4 — Unify global and contextual Chat

Reuse the existing company session/provider services, add shared structured action cards in conversations and case assistance, and retain evidence links, pending proposals, command inspection and explicit error states. A selected record is visible context, not invisible prompt authority.

Where the approved scope calls for sandbox Chat proposals, implement the bounded sandbox-specific capability change here after the unified deterministic actions have proven their safety. Keep the same card UI while retaining environment-specific authorization.

**Proof:** Saved company conversations survive reload, case/context transitions remain explicit, model failure leaves forms usable, unsupported commands produce no mutation, and prompt-supplied foreign IDs cannot alter the bound context. Repeated tool messages cannot duplicate execution.

### M5 — Ship Home and Analytics on authoritative data

Build the dashboard, compact preview and Analytics page from the shared metric definitions. Implement period selection and contributor lists only where coverage is sufficient. Reuse the product's existing example preview as a distinctly labeled onboarding demonstration.

Start with supported current-position metrics and extend trend metrics after verifying dated evidence. A metric-definition table and coverage report are required deliverables. Do not delay all navigation and workflow delivery for speculative analytics infrastructure.

**Proof:** Home/Analytics totals agree for identical filters; contributors explain the total; pagination does not truncate aggregates; dates, timezone boundaries, weekends, currencies, units, missing history and partial coverage are exercised. No synthetic KPI appears as live company truth.

### M6 — Migrate saved practice and learning entry points

If practice is retained, bring saved quick experiments and named practice companies into the common entry/context system. Preserve owner-private access, archived read-only behavior, existing run identity, step history, receipts and pending recovery. Place guidance in the shared case/actions, with no separate cockpit implementation.

Translate existing `/playground` links through authorization into the equivalent shared experience, including signup/account-return routes and users who have no production company. Update Site and Docs entry links. Keep narrowly scoped backend endpoints where their safety contract is still required.

**Proof:** Reopen old and archived runs; resume a pending review and an uncertain action; switch multiple named practice companies without replacement; verify no production import/egress permission leaks. Users can complete the existing lessons entirely in the one application.

### M7 — Cut over and remove obsolete presentation

Complete a reviewed target-scope acceptance report and keep/redesign/defer/retire decision log, the required regression suite and representative browser review. Make the common shell the only product default. Remove obsolete navigation, screens and competing styles when the selected workflows and continuity paths are proven. Experimental screens do not require replacements. Update affected specifications and tests for approved scope changes while preserving domain, security and recovery coverage.

Retain tested compatibility redirects and any backend APIs still used by saved runs or supported clients. Remove the temporary migration switch after the reviewed rollback window. Update durable web contracts, user documentation and V0 checklist only when evidence is green.

**Proof:** No legacy UI or separate Playground shell can be reached; every supported old entry resolves to the common app or an explicit authorized retirement page; no saved record is deleted; pending proposals and receipts remain accessible; deployment can roll back to the tested prior artifact without duplicating actions.

## Suggested specification and PR boundaries

Use one umbrella scope for the single-product outcome, with a small number of independently reviewed implementation features: new shell/context; case workspace and action cards; selected operations/master data; Chat integration; Analytics; practice migration and final retirement. Allocate actual feature numbers with the repository's numbering script when these are created.

Each feature may need several narrow PRs. M2 is the first end-to-end acceptance checkpoint, not a frontend mockup milestone. Cross-cutting action-card or context contracts should have one owner document; dependent features link to it instead of duplicating lifecycle rules.

Do not invoke a formal implementation plan before the feature's product scope is reviewed. This roadmap provides the concrete proposal needed for that review.

## Verification strategy

For each implementation feature, plan tests before changes and add them first where practical:

- Domain/service proofs for quantities, proposals, metric definitions and shortest true links.
- PostgreSQL integration proofs for tenant isolation, concurrency, idempotency, persistence and recovery.
- Tool/adapter parity for case controls, global actions, Chat, CLI and MCP where applicable.
- Browser journeys covering real navigation and controls, not only source-text assertions.
- Desktop and mobile visual checks at representative widths, keyboard/focus, long labels and all four supported UI languages; light and dark appearance.
- Negative states: unavailable provider/API, empty references, ambiguous names, stale review, unknown execution, revoked membership and archived practice context.

Required repository commands, with the documented local PostgreSQL test environment prepared:

```bash
make spec-check
make lint
make test
make web-build
cd apps/web && npm run test:contracts
```

Run the relevant browser journeys plus `make docs-build` when their boundaries change; final retirement must pass all affected CI gates in `.github/workflows/quality.yml`. Database upgrade/regression tests remain required for any separately justified persistence changes. No test run is claimed by this roadmap.

## Migration safeguards and rollback

Keep existing domain identifiers, source payloads and financial/operational authorities intact. Prefer no schema change for shell/navigation/case composition. Any durable action draft, chat history or historical aggregation requirement must justify reuse versus a narrowly scoped schema extension in its own spec and plan.

During transition, both entry paths must refer to the same underlying proposal/execution identity. A route redirect must never replay a mutation. Retain compatibility APIs while supported clients or saved workflows depend on them; an obsolete UI does not prove its service is obsolete.

Use tested deployment artifacts and a temporary internal switch as the initial rollback mechanism. Prefer backward-compatible, additive service contracts. Avoid a data rewrite as part of the visual cutover. Final deletion requires the capability matrix and recovery scenarios, not merely unused frontend imports.

## Definition of the final outcome

- One authenticated product shell and one visible navigation model.
- Home, Analytics, global Chat, case work and specialist registers connect through stable context.
- One action-card implementation serves supported case, Chat and launcher entry points.
- Every capability in the approved new-product scope has a tested destination. Legacy capabilities have reviewed retention/deferral/retirement decisions; full feature parity is not required.
- Master data is visible and supports its existing maintenance operations.
- Important numbers and action receipts are explainable through authoritative records.
- Practice, if retained, is an isolated environment in the same application with its existing safety boundaries and history.
- No separate legacy or Playground interface and no permanent old/new toggle.
- Required CI, browser/security journeys and owner review are complete before retirement is declared finished.

The main uncertainties are which legacy capabilities earn a place in the target product, environment admission/recovery, and which historical Analytics claims the held data can actually support. Refine estimates as these gaps are inspected; phase labels are not day estimates. The first delivery should make the new design tangible without waiting for every legacy experiment to be evaluated.
