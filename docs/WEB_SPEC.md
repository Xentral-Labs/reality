# Web UI Specification

## Product principle

**Simple on the surface. Fully explainable underneath.**

## Accounts and access

- The public site links to a self-hosted email/password signup. Passwords use Argon2id; verification codes and browser sessions are stored only as hashes.
- By default, verified accounts become active immediately without personal review (spec 189). Missing/blank `REALITY_AUTO_APPROVE_LIMIT` means unlimited automatic admission; `0` requires manual approval; a positive integer sets cumulative capacity. Explicit negative/invalid values require manual approval. Automatic admissions atomically increment the existing counter in unlimited and finite modes, so a later finite limit includes prior admissions. Administrators/invitations retain their existing exceptions. Existing pending/rejected accounts are not retrospectively approved. Account verification, tenant membership and company eligibility remain enforced.
- Approved users create companies through the normal application service. Access is granted by explicit tenant membership and checked at the API boundary.
- Active company owners can manage Members in company settings. Invitation links keep
  their secret in the URL fragment, scrub it immediately into session-scoped browser
  storage, and require explicit acceptance after sign-in or invite-bound signup and
  email verification. Ordinary members can use non-secret company functionality but
  cannot invite, resend, revoke, remove members, or see owner-only controls.
- Browser authentication uses an HttpOnly, SameSite session cookie. Production enables `Secure`; session tokens are never stored in browser storage.
- A new account adopts the presentation the browser already states (spec 194). Signup and invitation signup accept an optional IANA time zone and UI language; the server pairs the accepted language with its display locale and never takes a locale from a client. An absent, unsupported or unresolvable hint keeps `UTC`, `en` and `en-GB` and never fails a registration. The hint is unverified presentation, never identity or authorization, and stays changeable in Settings. Existing accounts are unaffected.
- Business timestamps remain UTC. Each user stores three independent presentation preferences: UI language (`en`, `de`, `nl`, `es`), locale/number format (`en-GB`, `de-DE`, `nl-NL`, `es-ES`) and an IANA display timezone. The React client formats every date, time, quantity and amount through one shared localization module. Inspector reads retain optional numeric presentation parts for composite quantities, money and unit prices; every Inspector surface uses the shared formatter, while original values, payloads and identifiers remain exact. English is the default and fallback; technical model identifiers remain stable. Model category labels use canonical English terms in every UI language (spec 208); general business objects and controls remain localized.
- The initial platform administrator comes from deployment secrets and reviews applications at `/admin/access`.
- Transactional account mail uses a provider boundary. Deployments may select
  Resend with `REALITY_EMAIL_PROVIDER=resend`, `RESEND_API_KEY`, and a verified
  `REALITY_EMAIL_FROM`; local development without a provider logs mail instead.

## Historical Learning Playground contract (retired browser UI)

Spec 143 retires the browser presentation described in this section. Its protected backend contracts and saved records remain; this section records their historical behavior. See the current retirement contract below.

Sandbox creation distinguishes Quick experiment (default) from a named Practice
company. Each owns a separate private playground tenant. Practice companies remain
active when other sandboxes start and show their name in saved entries and cockpit.
Quick replacement archives only the prior quick experiment with explicit confirmation.
Neither mode expires or deletes automatically; neither links production data.
Creation review uses one New sandbox heading and a primary Create sandbox plus
outlined Cancel in a shared action row; library refresh is hidden during review.
Unavailable customer returns explain the missing shipment after selection and offer
a return to operations. Guided editors offer an exit before preparing the next step;
after recorded steps, a notice explains that leaving does not undo goods or money
records and may require a return, reversal or compensating operation. Unknown
executions remain guarded; existing proposed-action rejection is unchanged.
Needs attention exposes an information dialog over the current authenticated
exception-class catalog. All classes, not just active findings, are searchable;
expanded entries show canonical descriptions, ownership and resolution guidance.
Each opening reloads metadata. Loading and retry states are explicit; descriptions
remain in the catalog's original language. The UI maintains no parallel class list
and does not claim every class can be triggered with the available sandbox actions.

The account-scoped `/api/playground` entry and run start/detail APIs require a real verified
session even with local business authentication disabled. Verified pending-production users
may access their own sandbox only; this does not approve them for production companies.
Run lists are bounded, owner-scoped and require current owner membership. A confirmed start
creates only synthetic references through shared services. Unready runs expose setup status,
not partially usable references. The entry flag defaults off; saved history remains readable.
The internal `/playground` browser entry now supports confirmed setup, saved-run selection,
failure/retry and actual reference lists in all four product languages. It bypasses the
production shell entirely and preserves only allowlisted local Playground account-return paths.
The original request key survives a lost response/reload; another confirmation retries it.
Mobile presents the selected experiment before its saved history. Business reference labels
remain original data; setup/reference views do not claim to be live inventory measurements.
The cockpit supports the trading lesson through invoice and allocated payment,
plus a four-step partial-delivery exercise. Full Inspector integration and chat
remain incomplete. See
`docs/features/learning-playground.md` for implemented boundaries and remaining release gates.

## Primary user

The primary user is a **Head of Operations at a modern, high-volume ecommerce
company who is also financially literate**. They understand inventory,
commitments, open items, settlement, debit/credit, and reconciliation. Do not
dumb the product down into generic KPI cards, but do not expose raw technical
records without an operational hierarchy either.

Every page must answer, in this order:

1. What requires attention or control?
2. What is the operational or financial position?
3. What changed, and why?
4. Which action is available?
5. How can the answer be traced to Reality, Evidence, and Source?

The interface should feel appropriate for fast-moving brands such as modern
D2C and ecommerce companies: precise, quick, visually current, and comfortable
for all-day use. Accounting-capable users should see useful control totals,
balanced postings, settlement state, and evidence links without having to open
the technical Explorer.

### UI acceptance criteria for this persona

Before an operational page is considered complete, verify it from the primary
user's perspective:

- The page has one obvious operational purpose and a clear primary action.
- Exceptions and material risks appear before neutral activity or raw history.
- Amounts, quantities, currencies, dates, counterparties, and business status
  can be scanned without opening a detail view.
- Finance views expose the relevant control total, debit/credit direction,
  settlement state, and reconciliation context where those concepts apply.
- Business language leads; opaque IDs and implementation details remain
  available for traceability but do not dominate the page.
- Tables support operational comparison with aligned numbers, useful column
  labels, restrained status badges, and clear empty states.
- A user can move from an operational answer to its Reality record, Evidence,
  and original Source without encountering a second interpretation of the data.
- Desktop and mobile layouts preserve navigation, hierarchy, actions, and
  readable business data; horizontal scrolling is acceptable only for genuinely
  tabular detail.
- Loading, empty, error, confirmation, and destructive-action states use the
  same shared component and interaction language as the rest of the product.
  A read that already has an answer never loses it while the next one loads: the
  previous content stays in place, dims, and reports itself busy. A placeholder is
  reserved for a request no answer is held for, draws the shape of the answer rather
  than stating that something is loading, carries no border of its own inside a
  surface that already has one, and appears only once a read is slow enough to notice.
  A failed read keeps its own card with the reason and a retry action, and discards the
  previous answer so a stale view never stands in for a read that did not happen.
- The result looks and behaves like a finished daily operations product, not a
  database administration screen or a component-library demonstration.

The web application combines two modes without creating two products:

1. **Operations Cockpit** — the default experience for a Head of Operations.
2. **Reality Inspector** — a deeper technical view for implementation, support, and special cases.

The web UI must never create its own business logic. CLI, chat, demo and web all call the same application services/tools.

Sales and Purchasing distinguish Delivery Commitments from physical Shipments. Commitments are
promises; Shipments are real consignments with Package tracking observations and linked Movement
contents. Sales defaults to outbound customer shipments and Purchasing to inbound supplier ones.

The page-by-page product job and preferred interaction pattern are defined in
`docs/WEB_UX_MATRIX.md`. Review that matrix before implementing or accepting a
web surface.

The current migration gaps and removal order for legacy UI styles are tracked in
`docs/TAILADMIN_UI_AUDIT.md`.

## Start

Run the independently deployed surfaces with:

```bash
docker compose up web docs api mcp
```

The public Site, Product Web, and product Docs are independent browser deployments.
Site owns the tenant-independent landing page at `https://runreality.ai`. Product Web
owns authentication, onboarding, `/`, and every `/app` route at
`https://app.runreality.ai`. Web/API is an API-only service on port 8000 and
owns `/api/*`, `/healthz`, `/docs` and `/openapi.json`. The independently deployed MCP
runtime owns authenticated Streamable HTTP at the exact configured `MCP_URL` and uses
port 8001 in the local Compose profile. Web/API neither mounts nor proxies MCP. It
contains no Jinja templates, browser JavaScript or CSS. Direct browser requests to retired
backend UI routes receive a permanent redirect to the React deployment.

Product Docs owns public, tenant-independent guidance at the exact configured `DOCS_URL`
(typically `https://docs.runreality.ai`). It is a static container with local full-text
search and no API, authentication, tenant, database, hosted-search, analytics, or CMS
dependency. The required information architecture is Getting Started, Core Concepts,
Product Guides, Integrations, API & Tools, Deployment & Operations, Development, and
Reference. Public guidance summarizes the product; the Constitution, durable `docs/`
contracts, feature specifications, and runtime OpenAPI remain authoritative.

`DOCS_URL` is additive. Existing `SITE_URL`, `APP_URL`, `API_URL`, and `MCP_URL`
retain their names and meanings. Site and Product Web use `DOCS_URL` for documentation
links and normalize trailing slashes; local builds use the documented Compose fallback.

The visible product wordmark is `Reality` across Site, Product Web, authentication and
Docs. Lowercase `reality` is reserved for technical identifiers such as commands,
packages, paths and storage keys.

## Public product page

`/` on the public Site is the tenant-independent product landing page. English is the default;
`/?lang=de`, `/?lang=nl` and `/?lang=es` render the complete German, Dutch and Spanish
versions, and the public header provides a visible language selector for all four. Public
Site components hold English source text only; German, Dutch and Spanish live in the
site's own catalog, monetary amounts are formatted for the selected locale, and its
`i18n:audit` gate fails when an advertised language is incomplete. The
Operations Cockpit and all account routes belong to Product Web. Public account actions
use the configured Product Web origin and preserve language selection.
It addresses managing directors and Heads of Operations at modern, digital-first
D2C and ecommerce companies and
positions Reality as the trusted operational foundation for autonomous
companies. Its primary call to action opens the existing self-hosted account signup;
returning users can open the existing sign-in flow. Early-access positioning may remain
in the product copy, but the landing page must not present a separate waitlist form.

The page must distinguish demonstrated product behavior from scale goals. It
positions the product through growing operational complexity rather than numeric
revenue or order-volume claims unless a repeatable benchmark exists. The page uses
the Site presentation stack and must not proxy or depend on API, tenant,
authentication, or database state.

### Public clarity contract

The Context Graph/agent-core section precedes Observe (04, then 05), retaining both
anchors. Its diagram uses appearance-aware surface/text tokens and readable labels
inside the dark section frame. A prominent explanation identifies the five linked
Reality record types as the agents' shared context. The redundant current-context
label is removed to avoid overlapping the final time marker (spec022 FR-028).

The landing page adds an ERP Lite section after Connections and before the agent
context comparison (spec022 FR-028). Six concise business areas explain inventory,
orders, purchasing, operational finance, journal and exceptions. It distinguishes
lossless versioned source payloads, selective operational mapping and derived state;
describes shared tools and confirmed actions; and presents custom views, MIT open
source and self-hosting. The owner removed the dashboard publishing teaser; the
section makes no dashboard availability or roadmap claim. All four
site languages and responsive layouts retain this message without fixed table counts
or unverified performance/setup claims.

The ERP Lite introduction explicitly makes an existing ERP optional: Reality can
use the Context Graph itself as the shared operational foundation: Facts,
Commitments, Reservations, Movements and Ledger Entries linked to evidence. It can
operate alongside existing systems or serve as the core for custom business
applications. The Build on Reality block explains extension with AI coding tools
while business rules, permissions and traceability remain in shared services.

The public landing and explanatory pages retain the original technology-led positioning: Reality
is the operational core beneath agents, not just an operations dashboard. Preserve the hero,
core diagram, brands, context graphics and capability progression. Refine explanations in place,
including an illustrative order (ten lamps promised, four shipped, six open, two actively reserved).
Unreserved demand does not itself prove a shortage; lateness needs a promised date.
Public entry distinguishes sample learning, an own-data pilot and live integration. A registered
source or connector shell is not a running vendor connection. Agent guidance distinguishes
read, propose, approve and verify, and internal Reality changes from external execution.
Facts are observations/classifications, not a replacement for typed operational/financial records.
History claims must not imply all tables are immutable or arbitrary past-state reconstruction.
The documentation provides separate business, operator and integration entry paths while retaining
the complete technical guide. See specs/083-clear-operational-story/spec.md.

## Global shell

Global actions MUST occupy reserved space in existing shell chrome and MUST NOT use
fixed or absolute positioning over the content canvas. Desktop actions belong in the
persistent sidebar header; mobile actions belong in the existing mobile header. A
global control MUST NOT introduce an additional page-wide bar merely to avoid content
collisions.

The product uses a modern commerce-operations design system: cool neutral
surfaces, white navigation, deep graphite, and precise indigo as the product and
agent accent. Green, amber, and red are reserved for semantic business states.
Interfaces favor precise hierarchy, compact controls, excellent operational
tables, and minimal decoration. Marketing and product UI must feel like one
system.

The implementation uses the open-source TailAdmin Community Edition as its UI
foundation. Prefer TailAdmin/Tailwind layout, navigation, card, table, badge,
form, modal, drawer, empty-state, and responsive patterns over custom UI. Add
custom CSS only for domain-specific visualizations such as commitment control,
posting control, or the Source → Evidence → Reality chain. Never combine an old
global component stylesheet with a new TailAdmin component on the same surface.

All newly built or changed product UI must use the frontend Tailwind component
primitives (`br-*`) for page headers, sections, cards, tables, buttons, dialogs,
and forms. Raw browser-default `input`, `select`, `textarea`, checkbox, or button
controls are not accepted. Every form field uses the shared field, label,
control, help, focus, disabled, and validation states; its appearance must not
depend on incidental nesting inside a particular card or dialog. Changes to
component markup or styles require rebuilding the frontend bundle and a
desktop/mobile visual check of the affected state.

Every product page uses the same page-header primitive. The left column owns
eyebrow, title, and description; the right column owns a single action row.
Buttons, selects, status labels, and compact counters in that row use the same
44 px control height, radius, border, spacing, and bottom alignment. Counters
remain compact inline summaries rather than dashboard cards. On narrow screens
the action row moves below the title and fills the available width. Feature
pages must not create their own competing top-right header layout.

Read-only detail for a record in a daily-work list or operational register opens as an
inline preview immediately below its originating row where practical. A disclosure
chevron points right when collapsed and down when expanded. Navigation, related-record
filtering, editing and operational work use distinct icons plus outcome-oriented labels;
they do not reuse the disclosure chevron. In dense registers the disclosure occupies a
fixed trailing action slot, so its horizontal position does not move when secondary
actions differ between rows. Dense register rows do not add a generic eye or unlabeled
forward arrow beside the disclosure: the trailing chevron alone means inline preview.
Any icon to its left represents a distinct outcome-named navigation, filter, edit,
source, or operational action. In Sales, Purchasing, Warehouse, Finance, and Master Data,
these secondary actions live as visibly labelled buttons inside the expanded preview;
the dense row itself contains only its trailing disclosure. Desktop previews use a compact two-column hierarchy when
multiple meaningful information groups exist and reflow in the same order on mobile.
All preview actions, including the route to the full explanation, share one wrapping
footer row when space permits. Their visible outcome labels carry the meaning; these
buttons do not add decorative or category-only icons. The footer aligns to the trailing
edge near the disclosure control on wide layouts. The disclosure itself remains
background- and border-free in normal, hover, and focus states.
Their header is left-aligned and keeps the record title plus short counterparty or
context label on one wrapping line. A generated description is omitted when it merely
repeats both header values.
Business-facing Inspector dates and instants use the operator's selected locale and
display timezone. Their exact API values remain unchanged; raw ISO timestamps belong
only in explicitly technical or original-source views.
Inline content is read-only and keeps an
explicit route to deeper explanation. Editors, confirmation flows, focused operational
work and the full technical Inspector remain separate surfaces. The repeated interaction
is **operational answer → Reality → Evidence → Source**.

Persistent elements:

- Active tenant switcher at the top of persistent desktop navigation and in the mobile header
- Create tenant
- Main navigation
- Search / inspect by ID when practical
- Clear indication when a tenant is empty or is a demo tenant

### Progressive operational entry

The authenticated landing surface continues the public product story through
one explicit sequence: **What is true → What needs attention → What can be
decided**. Facts are a first-class product surface, while Evidence, projections,
movements and ledger details remain available through explanation and enabled
workspaces rather than competing for attention on first use.

New companies start with Home, Facts, Exceptions and Settings, and reach
Sources & imports from the Get started panel on Home. Operational, warehouse and finance workspaces become prominent only
when their required records exist. The UI may recommend enabling a ready
workspace, but capability discovery never changes domain state or invents a
second business rule.

The empty-company example preview may illustrate order intake and shipping with
clearly labelled synthetic data. Its selectable time window uses calendar dates,
shows weekend and warehouse cut-off effects, and never presents the illustration
as live tenant Reality. An open-backlog series is the non-negative running balance
of prior backlog plus order intake minus shipped orders.

The example preview ends with a bounded horizontal Reality Flow that demonstrates
one concrete Source → Evidence → Reality path. Record-type nodes, timestamps and
elapsed waits preserve the shortest true links and illustrate how an operational
answer can be traced back to immutable source evidence without inventing a second
process model.

### Workspace views

The application presents one domain and one set of services through five
task-oriented workspace views. The selected view is a UI preference, never a
permission boundary and never an alternative implementation of business rules.

- **Company Overview** — tenant-wide status, cross-functional exceptions, and
  the shortest entry points into operations, warehouse, finance, and traceability.
- **Order Operations** — orders, commitments, holds, allocation readiness, and
  execution control.
- **Warehouse Operations** — inventory, reservations, movements, handling
  identities, locations, and operational activity.
- **Finance Control** — open items, payments, reconciliation, journal, parties,
  and financial evidence.
- **Data Management** — compact registers for maintaining the minimal typed
  operational references, normalized evidence, commercial terms, and source
  definitions Reality actually uses. It is not a replacement ERP or source
  system.
  Switching views changes navigation, landing surface, labels, and default task
  context only. It does not change the active tenant, stored records, calculations,
  or the Source → Evidence → Reality trace.

The Companies settings end with a **Danger zone** (spec 186): the selected business
company can be archived by an owner after an explicit confirmation, archived companies are
listed with restore and permanent deletion, and deletion requires the exact company name and
the literal word `DELETE`. A selected sandbox or demo company is archived and restored through
its playground run instead (`archive_run` / `restore_run`); its records stay and deleting
sandbox data is not offered yet. The browser only explains disabled controls; the lifecycle
endpoints remain the authority.

Setup is not a workspace. The company switcher has one **Companies** entry;
there is no separate distinction between "manage companies" and "company
settings". Companies opens the active company's settings directly. A compact
company switcher and **New company** action live in that settings header; there
is no intermediate company-management dashboard. General, Data and Agents live
in one detail surface. Company lifecycle, imports,
AI/MCP, Payment
Terms, Price Lists, Pricing Groups and the minimal typed reference data live
there. This keeps occasional configuration out of daily operations without
hiding it inside a technical persona.

Traceability is not a daily-work navigation item. Explorer and its supporting
technical views live under Company → Data. Operational records link directly
to their shortest true trace where explanation is required.

Register tables use one shared visual frame. The outer section owns border,
corner radius, background, clipping, and shadow. Search/filter toolbars are the
first child and use only a bottom border; the horizontal table wrapper and table
must not introduce a second card border or a second set of rounded corners.
Toolbar, headers, cells, and empty states remain inside that one frame. A register
that returns no rows says so in one body row of its own table, keeping the column
header, selection controls and pagination in place; pages do not draw an empty-state
card above, below or instead of the table. The shared wording is "No matching records"
with "Try another filter or inspect the original records."; a register may replace either
for its subject, and the explanation stays at the visible left edge while wide registers
scroll horizontally. See spec 154 FR-001–003.

Navigation:

- Persistent daily work: Ask Reality, Home, Facts, Exceptions
- Data Management includes **Open questions**, a shared queue for unanswered
  business questions, source-backed investigation, human classification, safe Fact-rule
  simulation, activation, replay, and developer handoff. Its rule editor uses structured
  business controls for bounded, visibly nested ALL/ANY condition groups, extracted or fixed output, order versus line
  scope, and time source. Simulation and replay distinguish applicable sources, normal
  skips, invalid inputs, ambiguous subjects, and conflicts; replay continuation and
  durable outcome totals remain visible without native browser dialogs or raw JSON.
- Workspace-specific work: only the registers and tasks used by that persona
- Company menu: switch company, Companies, Help
- Company detail uses one standard grouped settings navigation: General; Data
  (Sources & Intake, Processing, Reference Data, Explorer); Agents (Copilot,
  MCP Server). The settings shell uses a persistent left navigation. Each
  destination has one page title only; configuration uses standard forms,
  registers use tables, and destinations use compact link lists. Settings must
  not be presented as a dashboard made from equally weighted cards.

Visible navigation labels and page titles use one canonical noun. The
canonical product names are Home, Facts, Exceptions, Commitments, Inventory,
Reservations, Movements, Open items, Payments, Documents, Activity, Parties,
Items, Locations, Commercial terms, and Sources & imports. Descriptive phrases
such as decision queue, promise control, document register, stock control, or
immutable intake belong in the eyebrow or description and do not replace the
page title.

Within a selected workspace, contextual navigation is divided into **Views** and
**Actions**. A View is a business read surface and may be backed by an authoritative
Reality register or a rebuildable Projection; the primary interface does not call every
View a Projection. An Action is a governed entry into an explicitly Web-enabled shared
application command. Workspace Actions never use a generic command executor, never
change workspace permissions, and never bypass service validation. Every mutation has
a distinct human confirmation; snapshot-sensitive corrections confirm the exact
server-produced preview or revision. Successful actions return to the affected canonical
register and retain the existing Inspect path. The validated application reference owns
workspace membership and ordering so the Web shell, documentation, and agents do not
maintain competing classifications.

Every page with actions shows exactly one `More actions` control. All page actions,
including the first catalog-ordered action, appear inside it; an empty menu is never shown.
No page action competes as a separate header button. That control keeps its
keyboard-accessible disclosure behavior and catalog order. The separate global Actions
launcher remains searchable over the complete ordered workspace action set. Selecting an
entry starts the same explicit form and confirmation path as a direct entry. Commands that
are not classified and Web-eligible never appear. On desktop the page heading and action
row occupy the same middle column as page content and end at the open chat panel's left
edge; they never extend over the chat. Global activity, Actions, appearance and chat
controls remain right-aligned in the shell's right column, above the chat when open.
Page-specific More actions is right-aligned in the local view-tab row. Pages with actions
but no tabs keep that row without inventing a tab. Exceptions treats its complete finding
catalog as filter-adjacent reference help rather than a page action. Order Operations'
complete set includes document-level commitment holds and party delivery holds.

Decisions places proposal guidance beside its action-type filter. The explanation identifies
human/workspace and connected-agent proposal origins and makes clear that a pending or
rejected proposal has not changed business records.

Every business mutation in the Command catalog has an explicit Web adapter. Manual
sales/purchase order creation uses the canonical atomic order service and produces
immutable Source evidence, Document/Lines, and Commitments. Source-supported Fact
observation is available from Company Overview and Data Management. Customer and
supplier payment posting is available from Finance Control. Each uses the shared
two-step review/confirmation surface and tenant-scoped server validation.

In the legacy product, Activity is a cross-functional Company Overview View. Its single navigation entry opens
the complete Activity page directly. The entry is fixed directly below Exceptions in
primary company navigation and is excluded from the contextual Views list and launcher.
It is not repeated in Operations, Warehouse,
Finance, or Data Management, and there is no competing header control or global drawer.
While the browser tab is visible, a lightweight tenant-scoped cursor may poll durable
BusinessEvents to show a bounded unread count and brief pulse on that entry. The first
response establishes a baseline, opening Activity clears unread presentation state, and
an open Activity page refreshes its existing bounded read when the cursor advances.
Only newly observed attention events produce a polite, temporary notification; polling
creates no business records and does not become a second event authority.
The unified app replaces this legacy navigation with the read-only header drawer specified in Spec 134 below; its presentation has no unread counter, notifications or polling.
Activity groups and steps lead with server-produced business language and the best
available human references, source, party, item, quantity, and outcome. Exact event
types and opaque identifiers remain available under a collapsed Technical details
disclosure so operational readability does not weaken traceability.
For a company with no operational records yet, the Get started entry is not a
navigation group. It is the fourth Home panel, taking the place of Automation:
a company that has imported nothing is not yet asking how far automation may go.
Sidebar navigation therefore stays the Company Overview Views alone.

### AI and MCP boundary

Company settings separate the internal **Copilot** from the external **MCP
Server**. Copilot selects the provider and model used by Ask Reality. MCP Server
shows the HTTPS endpoint, tool catalog, tenant-scoped bearer tokens, and the
explicit tool allowlist for each external agent.

Data Processing explains the complete runtime path rather than showing isolated
counters: configured integration or tenant-scoped intake API → immutable,
lossless SourceRecord → monitored Import Job → Evidence and typed Reality →
rebuildable projections. Its run register exists to diagnose ingestion and
interpretation; it is not an alternative source of operational truth.

The internal Copilot is deployment-managed and uses Anthropic through its native
Messages API. Company owners do not select a provider, model, endpoint, or API key.
The server reads `ANTHROPIC_API_KEY` only from its runtime environment; the clear key
is never rendered, logged, returned through an API, persisted, stored as Evidence,
or passed to a Reality tool. The deterministic local provider remains test-only.

The same vault is the credential boundary for future source connectors. Each
secret uses a random AES-GCM data key; a deployment master key wraps that data
key and remains outside PostgreSQL. Production must provide a valid
`REALITY_MASTER_KEY`; local development may use the permission-restricted key
file. Vault records expose only purpose, provider, label, fingerprint, lifecycle
timestamps and a metadata-only audit trail. Replacing a credential creates a new
secret and revokes the old one. Consumers resolve a secret only for the active
tenant and only at the moment it is needed.

The unified Copilot settings UI offers Reality-managed credentials or a company
Anthropic key, matching the current chat runtime. The old settings adapter can store
OpenAI-compatible provider presets, but Ask Reality currently uses company credentials
only for Anthropic and otherwise falls back to managed Anthropic credentials. The new
UI preserves other saved provider metadata with this limitation explicitly displayed;
it does not present those presets as working chat providers. The company key is
write-only and stored through the tenant vault; selecting managed mode revokes it.
Anthropic model and endpoint remain fixed by the server. See Spec 131 below.

External enterprise-agent access to operational data goes through the Reality MCP
server. MCP tools dispatch to the same application tools and services used by
CLI, Web, and API. Read tools may execute immediately. Mutation tools may only
create an auditable `ChangeProposal(status=proposed)`; the model cannot cross
the human approval boundary by implication. The dedicated MCP runtime exposes only
authenticated Streamable HTTP at the exact configured `MCP_URL`; HTTP is also the only
supported local-development transport. Tenant administrators create named bearer tokens
in AI & MCP settings. Only a SHA-256 digest and short display prefix are stored;
the clear token is shown once immediately after creation. The verified token
subject is the tenant authority, so an MCP request cannot select or override a
tenant. Tokens can be revoked independently and their latest use is recorded.
The settings page renders the complete MCP tool catalog and every token stores
an explicit allowlist. An administrator may grant all current and future tools,
or select individual tools. The server enforces this allowlist for every tool
call; UI visibility is explanatory and never the security boundary.
Because catalog review and credential creation are occasional setup tasks, the
AI & MCP page shows them as compact summary actions. The full catalog and the
per-token permission selector open in shared Tailwind dialogs instead of
occupying permanent dashboard space. Active token scope remains visible in the
main page.

Operational Exceptions are derived Reality, not Jira-style tickets and not
manually closed records. Change Proposals are prepared mutations that have not
run. The user-facing lifecycle is consistently named **Exception → Change
Proposal → Approval → Execution**. MCP exposes tools to list and explain current
exceptions, inspect proposals awaiting approval, and approve and execute one
exact proposal. Approval is separately permissioned and requires an explicit
true approval argument. It executes through the same application boundary as
CLI and Web and remains tenant-scoped and auditable. Permission to read
exceptions never grants proposal approval. Public Web, MCP, CLI, documentation,
and projection names use these terms consistently; `issue` remains reserved for
the warehouse meaning of issuing goods where needed.

Proposal preparation returns a structured next step shared by Web and MCP. It names the stored
proposal, the server-side review read, the required confirming principal, explicit-confirmation
requirements, `proposal_execution_status` for lost-response reconciliation and authoritative
verification reads. This metadata describes the decision boundary; it never grants an agent
approval authority. Owner-governed finance and costing remain owner decisions. Ordinary mutating
actions, including a free supplier invoice, require an authorized human but do not acquire a new
owner-only rule.

Explicit rejection uses the same tenant-scoped proposal lifecycle. The controlled rejection
surface requires a true human decision, is excluded from default model-selected tools, has no
business effect and returns stable rejected state on replay. Executing or executed proposals are
reconciled rather than rewritten.

Progressive disclosure in workspace navigation is the rule, not a reflex. A workspace
lists five Views and two Actions directly and keeps the rest behind its searchable
launcher, except where it declares complete navigation in the catalog, in which case it
lists its whole surface directly. Data Management declares it and is the only workspace
that does. A launcher is offered only when it holds an entry the reader cannot already
see, so a workspace never presents a control that repeats the list above it, and a
workspace that commands nothing shows no Actions section rather than a header over an
empty state. Data Management lists authoritative registers only; source intake is
company configuration and is reached there.

The Exceptions workspace keeps these concepts adjacent but distinct: current derived
Exceptions, tenant-wide Pending approvals, and read-only Decision history are separate
views. Pending approvals remain reachable independently of any Chat session. Home leaves
its onboarding/example state as soon as operational records, derived exceptions, or any
Change Proposal history exists, so pending-decision counts are never hidden by demo data.

A settled Change Proposal records when it was settled and, when a signed-in person
settled it, who. Approval and rejection are attributed through the same path. Where no
person can be named — a decision taken without a signed-in principal, or one settled
before attribution existed — the record leaves the person blank rather than substituting
one, and the register renders that blank as unknown. Only a person who actually decided
for the company being read is resolved to a name.

Decision history is a register, not a stack of cards. It only grows, so it is counted,
filtered and sliced in the database and read one bounded page at a time under a
deterministic order, with a row per decision stating time, action, scope, requester and
outcome, and its full arguments available on request in place. Pending approvals keep a
card each while their number stays small, but their count comes from the same server
total rather than from the cards on screen.

Inside the browser product the thing a person acts on carries one name: an approval.
`ChangeProposal` stays the model, API and documentation term for the same record, but no
Web surface offers a reader both words for one card. Pending approvals holds what waits,
Decision history holds what was already decided, and a card that needs a person says
Approval required. Both queues are counted where they are opened: the Exceptions sidebar
entry carries a single dot while open exceptions or pending approvals exist, and each tab
carries its own exact count, so a zero on one tab never hides work on another.

Ordinary Chat removal is reversible archiving. It hides a conversation from the active
list without deleting messages or changing a proposal, approval, or execution record.
Archived conversations can be viewed and restored. The archive is reached from the
bottom of the conversation list, never from a page-level mode beside the conversation,
and it is offered only when a hidden conversation exists. A tenant whose every
conversation is hidden still keeps the list, so the archive can never be stranded
behind the zero-conversation invitation. An empty Copilot conversation never
renders unrelated tenant-wide proposal cards; decision work remains in Pending approvals.

- Documentation: generated CLI reference and a restricted `reality` command console

Finance pages are operational subledger views, not statutory accounting. Open
amounts and payment state are derived from LedgerEntries and
SettlementAllocations through shared services.

Financial postings should be readable as classic debit/credit T-accounts while
retaining the technical journal register. Goods views use the same visual
grammar but remain explicitly named control accounts: physical receipts/issues
derive from Movements, availability derives from Reservations, and future
inbound/outbound obligations derive from open Commitments. Never mix forecasts
into the financial ledger or persist balances solely for presentation.
Document detail uses one shared debit/credit frame with Soll on the left and
Haben on the right. Date and posting reference remain visible inside each row.
It must not render one separate frame per posting group; account-level T-accounts
belong in Journal.
Every financial account label in document postings and Journal links to a
tenant-scoped account sheet. It shows chronological debit and credit entries,
evidence links, and a derived running balance; balances are not stored separately.
The Journal read is bounded to 50 rows by default and 100 at most. Its account and
effective-date filters execute in tenant-scoped SQL, and its debit, credit, and
balance controls aggregate the complete filtered result rather than the visible page.

Pricing uses the shared application services for sales and purchase price lists,
quantity tiers, direct party assignments, and party-group assignments. Resolution
is deterministic and exposes the selected PriceListEntry for traceability. Document
inspection presents immutable agreed line pricing first, followed by a separately
labeled current resolution. It retains inactive or expired historical entry/list
identity for explanation and never describes a current price as the historical price.

### Operational references

Parties, items, and locations are minimal operational references, not replicated
CRM, PIM, WMS, or ERP master data. Their registers show the concrete source-system
instance, source type, and external reference. The complete upstream record remains
losslessly available through the immutable SourceRecord payload. A field is copied
into a typed reference only when core logic repeatedly calculates, filters, joins,
constrains, predicts, or acts on it. Orders, invoices, and credits remain Evidence;
commitments, reservations, movements, and ledger entries remain derived Reality.

### Shared autocomplete

Reference inputs use one keyboard-accessible Tailwind combobox and the tenant-scoped
`/api/tenants/{tenant_id}/suggestions/{kind}` endpoint. Entity choices such as party,
item, location, price list, and price group submit opaque IDs. Vocabulary choices
such as source type, target type, unit, and currency may allow a custom typed value.
Source-type suggestions are filtered by the selected source-system instance. The
component is an input aid only: submitted values are still validated by the existing
application services, and suggestion queries never bypass tenant scope.

The React product uses this shared combobox for every stored relationship: party,
item, location, commitment, document, payment term, source system, unit, and
currency. The operator sees human labels while forms submit opaque IDs or stable
tenant-scoped codes. Free text is allowed only for suggestion kinds explicitly
marked as extensible by the API.

### Manual evidence entry

Operators may record a document header together with one or more normalized line
items. Party, ship-to party, item, unit, currency, and payment term use the shared
tenant-scoped autocomplete. This command records `Document` and `DocumentLine`
evidence atomically through the application service. It does not infer a delivery,
reservation, movement, or financial posting; those remain explicit Reality
commands and projections.

Integrations is a tenant-scoped registry, not a connector-management facade. It
defines multiple external source systems and their accepted upstream-to-target
type capabilities. It shows whether application code has an interpreter for a
capability and offers manual JSON ingestion through the shared source service.
Credentials, endpoints, schedules, and field mappings appear only when a real
connector use case proves that they are required.

### Sample import data

The central **Import data** page offers a compact sample-data panel for users
who want to evaluate the product before connecting a real source. Samples are
downloadable individually and as one ordered ZIP package. They use the same
explicit file mapping, immutable source storage, proposal, and confirmation
flow as customer files; downloading a sample must never seed or mutate a tenant.

An empty tenant's getting-started page links to this panel as the alternative to
registering a live source. Sample downloads are an onboarding aid, not a main
navigation destination and not a second demo implementation. Download routes
use a fixed allowlist and never accept an arbitrary filesystem path.

### Shared data intake

Orders, Items, Parties, Inventory, Payments, and Documents offer a contextual
**Import** action. Integrations additionally offers **Drop any data**. All links
open one shared intake screen and pass only an expected operational target. The
user chooses a source, streams a file, reviews a bounded preview, and confirms a
`source_ingest` application-tool proposal.

The System workspace exposes the same screen as the central **Import data**
entry. There the user first chooses an explicit mapping profile (Items, Parties,
Orders, Inventory snapshot, or Bank statement) or elects to retain the file as
raw data only. This is navigation into the shared intake, not a second importer.

Large files must be streamed to immutable tenant-scoped artifact storage and
must not be buffered in application memory or embedded as base64 in a Change Proposal
input. The UI shows filename, media type, exact size, SHA-256, expected target,
and interpretation readiness. Confirmation creates SourceRecord evidence and an
ImportJob; it does not imply that unknown input was mapped. Inventory snapshots
and bank statements never mutate balances directly.

## Empty tenant

A newly created tenant opens Home and shows a three-step, tenant-scoped getting
started flow based on real stored state:

1. register an external source system;
2. declare which upstream record types it may provide;
3. ingest the first immutable source record.

Completed steps remain visibly checked so setup can be resumed. The primary
action always points to the first incomplete step. A guided demo is a secondary
alternative and must use the same scenario and services as the CLI demo; do not
maintain a separate web-only demo data path. Once interpreted operational
references exist, Home becomes the normal exception-first control surface.

## Home

Question answered: **Where does the business need attention?**

Show at minimum:

- commitments at risk
- overdue commitments
- stock shortages
- supplier commitments overdue
- unallocated/unreserved customer commitments
- commitments due today / tomorrow / next 7 days
- compact inventory summary
- recent operational exceptions and activity

Do not turn Home into a generic SaaS KPI dashboard.

Every number that can be drilled into should lead to the records that explain it.

## Operational Exceptions

Operational Exceptions are the derived operational work queue.

Initial exception types:

- customer commitment cannot currently be fulfilled
- supplier commitment overdue
- commitment insufficiently reserved
- source record could not be interpreted
- movement without expected/linked commitment where relevant
- payment/ledger event that cannot be matched where relevant

An Operational Exception is not merely a UI alert. If persisted, it must have a clear derivation/provenance and lifecycle.

V0 may derive exceptions dynamically if persistence adds unnecessary complexity.

## Commitments

This is the primary operational table.

Columns should include only useful operational fields, for example:

- risk/status
- due date
- direction (incoming/outgoing)
- counterparty
- item
- promised quantity/amount
- reserved/fulfilled quantity

Useful filters:

- at risk
- overdue
- customer
- supplier
- due today
- unfulfilled

Commitment detail must show:

- promise
- parties
- due time
- reservation state
- fulfillment state
- projected availability when relevant
- source/evidence chain
- `Inspect` entry into the technical view

Do not store document delivery status just to render this screen. Derive operational status from reality primitives.

## Inventory

Primary view:

- item
- location
- physical
- reserved
- available
- incoming
- projected

Item/location detail should explain the calculation using movements, reservations and incoming commitments.

Core invariant:

**Every displayed inventory number must be explainable from underlying records.**

## Documents

Documents are evidence, not the operational center.

Document detail shows:

- normalized document header
- normalized lines
- source system / source ID
- reality created from the evidence (commitments, etc.)
- link to original source record
- raw source JSON

The UI should make the distinction between "what the source sent" and "what Reality interpreted" visually obvious.

All typed document and line fields are visible on document detail. Manual/internal
evidence can be corrected through the shared application service. Type, party,
currency and gross amount become read-only after commitments or ledger entries have
been derived. Externally sourced evidence is never overwritten: a correction appends
a new immutable SourceRecord version to the same source stream for interpretation.

Manual DocumentLine correction uses one complete intended line snapshot plus a
canonical revision. Existing opaque line IDs retain rows, omitted IDs remove rows, and
lines without IDs receive server-assigned identities. Stale divergent snapshots are
rejected; a snapshot already equal to current Evidence is a no-op. Item, quantity,
unit, price, amount, requested/promised time, line type, addition, and removal are
economic changes and are rejected after linked Commitment or Ledger Reality exists.
Reference-only SKU, description, and source-line corrections remain eligible. The
operation never rewrites Reality, and external Evidence remains source-version owned.

## Timeline

Timeline is an exception-first Business Activity Monitor, not an unbounded
decorative feed. Its default view groups related events into understandable
business processes; a raw event view remains available for support and audit.
The first viewport shows today's event and order throughput, exceptions, source
freshness, and processing latency together with a 24-hour activity distribution.

Events include at minimum:

- source received
- document interpreted
- commitment created/changed/fulfilled
- reservation created/released/consumed
- movement recorded
- ledger entry
- agent/user action when available

Filters should support party, item, commitment, document/source and date.
Filtering and cursor pagination are server-side. Search accepts business
references and opaque IDs. Selecting an activity reveals its causal trace from
Source through Evidence to Reality without losing the current filter context.

## Chat

Chat sessions are tenant-scoped and persistent.

Minimum entities:

```text
chat_session
- id
- tenant_id
- title
- created_at
- updated_at

chat_message
- id
- tenant_id
- session_id
- role
- content
- created_at
```

The chat uses a compact two-pane application layout. The left side shows multiple saved
sessions for the active tenant, highlights the current session and supports creating a new
session. The right side keeps the conversation header, scrollable message history and message
composer visually separate. On narrow screens the session list moves above the conversation.

Chat must use the same tool layer as CLI and web actions. The model must not mutate database records directly.

For mutating actions, prefer preview/confirmation:

> Buy 50 Bike Lights from Parts GmbH for Friday.

The assistant prepares a structured action; the user executes/approves it. Tests may use a deterministic dummy provider.

Changing tenants changes the visible session set.

## Explorer / Inspector

The Explorer is intentionally technical. It exists for implementers, operations specialists and support.

Expose the core collections:

- source records
- documents
- document lines
- commitments
- reservations
- movements
- ledger entries
- facts
- actions (when implemented)
- tenant scope and master data (`party`, `item`, `location`)
- chat sessions and messages for agent/support traceability

Group stored collections as Scope, Master Data, Source, Evidence, Reality, and
Change Proposals/Audit. Also expose Inventory, Operational Exceptions, Open Items, and Timeline as clearly
labelled **Derived Views**. Derived views must call shared services and must never
be presented as stored tables.

A record inspector uses the conventional three-pane object-browser pattern:
collections on the left, a bounded searchable record list in the middle, and
the selected record on the right. It must not render every collection as a
stack of expanded cards on one long page.

The selected record inspector should show:

- typed fields
- IDs and foreign keys
- relations/provenance
- raw JSON/payload
- timestamps/history when available

Support staff should be able to answer both:

- "Why does the system believe this?"
- "What did the original source actually send?"

without requiring direct SQL access for normal investigations.

Operational drill-downs use the same Inspector surface but lead with business meaning:

1. what the record means and its current state;
2. the best authoritative business reference and supported review guidance;
3. the current quantitative position;
4. why Reality knows it, in Source → Evidence → Reality order;
5. related business context; and
6. a collapsed Technical details section containing opaque IDs, exact predicates,
   event types, timestamps, and the losslessly stored source payload.

The server supplies meaning, references, and guidance through tenant-scoped shortest
links. The browser only renders that read model. When authoritative context or guidance
does not exist, the Inspector omits it or says so honestly instead of inventing it.
Human references remain display context and never replace opaque identity.

### Record origin (spec 211)

Every operational register, detail and card states where its record came from, through one
`origin` contract the server supplies with the row: the source system's configured name,
the external reference it arrived under, its version and receipt time. A record with no
source states that it was created in the application and names the deciding user where one
is recorded; an empty origin is never rendered. Registers whose records are predominantly
imported show origin as a column; derived registers keep it available but hidden.

Activating an origin opens the source record: its identity, import state, the terminal
interpretation outcome or the honest `not_recorded` label, the retained payload behind its
existing disclosure and bounded with an explicit truncation notice, and every record
produced from the same source. Where the tenant has configured a base address on the source
system and the connector declares a template for that source type, the origin also offers a
link to the record in the system that owns it: `https` only, opened without an opener
relationship, with the target host visible before activation. Where either is missing, the
origin is still stated and the link is simply absent. Where a record's Facts reference more
than one source system, the detail discloses all of them while the register row continues to
name the creating source only.

## Documentation, data model and CLI console

Every clickable workspace-navigation label must use the exact canonical title of
its destination page. Workspace context belongs in the page eyebrow, subtitle, or
navigation section heading—not in an alternate alias. For example, a link to the
Parties register is always named `Parties`, never `Customers`, `Business
references`, or `Customers & suppliers`.

`Company Overview` is the cross-functional workspace view and the default for a company on
first use. It provides the cross-workspace Home and the complete exception queue.
After a user selects another view, the UI remembers that presentation preference.

Company management is a cross-tenant lifecycle surface. It shows active and
archived companies, bounded Source/Evidence/Reality usage counts, configuration
state, and last activity. Users may create, archive, and restore companies.
Permanent deletion is available only for an archived company and requires both
its exact name and the exact confirmation word `DELETE`. These operations call
the shared tenant lifecycle services; the client never implements lifecycle
rules itself.

`Ask Reality`, `Home`, `Facts` and `Exceptions` are persistent primary links in
every workspace view. They keep one shared order — Ask Reality, Home, Facts,
Exceptions — in the same position above the contextual workspace list and are not
duplicated inside it. `Ask Reality` leads that list because asking is the shortest
path to an operational answer, but it is a navigation destination like its
neighbours and carries an accent rather than a call-to-action shape; the primary
action for asking lives on the Home surface itself. In a functional workspace, Home is
focused to that function and Exceptions initially shows its relevant subset. The
tenant-wide count and an explicit `All issues` path remain available at all times.
Traceability is contextual rather than a permanent primary-navigation item:
records expose `Trace` or `Explain` actions, exceptions expose `Explain issue`,
Copilot can investigate business identifiers, and the complete Explorer remains
available from Settings for technical investigations.

The functional workspace views expose complete, task-oriented registers:

- Order Operations: `Orders`, `Commitments`, `Holds`, `Reservations`,
  `Inventory`, and `Documents`.
- Warehouse Operations: `Inventory`, `Warehouse Queue`, `Reservations`,
  `Movements`, `Handling Units`, `Lots`, `Serial Units`, `Commitments`, `Items`,
  `Locations`, and `Timeline`.
- Finance Control: `Open items`, `Payments`, `Reconciliation`, `Aging`, `Journal`,
  `Documents`, `Parties`, and `Activity`. Pricing remains company configuration,
  not a daily control register.
- Data Management: `Parties`, `Items`, `Locations`, `Documents`, commercial
  terms, and source definitions. Existing references open in a detail-and-edit
  workspace that keeps related evidence and Reality context visible; focused
  dialogs are used for creation.
- System Control: source setup, import jobs, projection health, AI configuration,
  reference registers, source records, documents, timeline, actions/audit,
  Explorer, documentation, and CLI playground.

Reservations show the shortest link to their Commitment plus optional
NVE/handling-unit, lot, and serial identities. Movements are the append-only
physical journal. Warehouse identities derive their current location from net physical
Movement legs; business timestamps alone are not authority. An outbound net position
means that no tenant location remains. Neither register introduces an editable stock or
fulfillment status.

Movement rows expose derived `normal`, `corrected`, `compensation`, and `replacement`
roles. Eligible normal/replacement rows offer **Correct**. The dialog requires a reason,
optionally accepts one replacement, and displays a server-calculated original → exact
compensation → intended net preview before a distinct confirmation. Stale confirmation
returns refresh guidance. Inspector traversal from every chain member exposes reason,
time, actor context, event, net effects, and each member's own direct Source evidence.

Ledger posting groups expose derived `normal`, `reversed_original`, and `reversing`
roles. An eligible normal group offers **Reverse**. The dialog requires a reason and
shows the server-calculated complete inverse plus affected allocations before a
distinct confirmation; stale confirmation returns refresh guidance. Original entries
and allocations remain immutable. Finance views exclude allocations linked to a
reversed original from operational settlement calculations, and Inspector traversal
from either group exposes the relation, reason, time, actor context, event, allocation
history, net-zero effect, and original Evidence/Source provenance.

The Orders and Warehouse Queue pages read the materialized fulfillment projection.
Append-only truth registers such as movements, reservations, payments, and journal
entries read their authoritative tables through shared tenant-scoped application
services. The web UI, CLI, chat, and MCP layer must not implement parallel business
rules.

Register filters use one consistent toolbar pattern. Whenever a register exposes a
small, known business classification such as document type or commitment status,
the toolbar provides a server-side select filter in addition to free-text search.
The Documents register always offers `All document types` plus the document types
that actually exist for the current tenant. Filter choices remain active across
pagination and never reveal values from another tenant.

Every high-volume register uses the same filter contract: a free-text query searches
the documented identity and display columns; typed controls handle classifications,
dates, and numeric ranges. Applying a filter resets to page one. All active values
remain in the query string and pagination links, so filtered views are bookmarkable
and refresh-safe. A clear action returns to the unfiltered tenant register. Derived
columns such as order readiness, available/projected stock, and open invoice amount
are filtered in tenant-scoped SQL or materialized projections before counting and
pagination—not in browser JavaScript or on the visible page.

The core register catalog is:

- Orders: global query, readiness, source system, due-date range.
- Commitments: global query, direction/type, status, due-date range.
- Inventory: global query, stock state, available and projected quantity ranges.
- Reservations and movements: global query, status/type, occurrence-date range.
- Open items: global query, receivable/payable flow, status, document-date and open-amount ranges.
- Payments and journal: global query, direction/account/side and effective-date range.
- Documents: global query, document type, source, status, document-date and gross-amount ranges.

## Large-tenant read contract

The UI must remain useful when a tenant processes at least 10,000 orders per day.
No register route may load an unbounded tenant table and then search, count, group,
or paginate it in Python. Operational registers use tenant-scoped SQL filters,
stable ordering, a total count, and pages of at most 100 rows (50 by default).

Dashboard cards use aggregate SQL or bounded projections. Their numbers never come
from the length or sum of the currently visible page. Timeline KPIs and its hourly
chart aggregate the complete selected time window in SQL while the event stream
returns only the newest bounded result set. Explorer is an inspector, not a data
export: each collection and derived view returns a small bounded sample and users
open exact records through trace links. Bulk extraction belongs in an asynchronous
export, not an HTML response.

Search and filters are executed before `LIMIT` and always include `tenant_id`.
High-volume sort paths are backed by composite indexes beginning with `tenant_id`.
Select controls must not preload entire party, item, location, document, or source
tables; until remote autocomplete is required, they expose a clearly bounded set.

The Documentation page derives its command reference from the installed Typer
command tree so it cannot silently drift from the CLI. It includes every current
command, argument, option, and default.

The embedded console executes only commands beginning with `reality`; it is not a
general-purpose system shell. Starting another web server from the console is
blocked. Read-only commands execute immediately. Mutating commands show a preview
and require an explicit confirmation before execution, following the same rule as
chat mutations.

The page is split into a Technical Concept, Help Center, Developer Reference,
CLI Playground, and Data Model area. The Technical Concept teaches the complete
Source → Evidence → Reality → Business Event → Projection flow before exposing
generated implementation details. It defines Facts, Commitments, Reservations,
Movements, Ledger Entries, and materialized projections with operational examples,
explains when an upstream field should become typed, and shows how the same
application services are reached through Web, CLI, API, Copilot, and MCP.

Ask Reality uses a full-height, conventional chat workspace rather than a
dashboard page: a compact conversation rail sits beside one continuous white
conversation surface, with a restrained context header and a centered composer
anchored at the bottom. A separate page title or enclosing dashboard card must
not compete with the conversation.
Concept cards use a readable business label first, show the exact technical model
name separately, and identify the canonical Web page where that record or derived
answer is visible. Evidence is explicitly presented as the layer represented by
Documents and Document Lines; physical Movements and financial Ledger Entries are
documented separately.

The English data model reference includes every table and column, its database
format, nullability, foreign-key target, default and business meaning.
`packages/reality-core/config/data_model.yaml` is the machine-readable catalog and source for this
reference and future generators. At runtime and in tests, the catalog is validated
against SQLAlchemy metadata so a schema change cannot silently leave the reference
incomplete or stale.

Commands & Change Proposals and Projections are documented as separate areas. The
machine-readable Command, Business Event, Projection, and Fact-predicate catalogs under
`packages/reality-core/config/` name the actual services and executable vocabulary. One validated
application reference composes them for the API and product. Loading it validates
services, tables, emitted Events, and runtime Projection names so the page cannot
describe a nonexistent or omitted implementation.

Business Events are documented from the composed reference with their producer,
subject, and affected projections. Events are immutable tenant-scoped outbox
records written in the same transaction as their business mutation. Fulfillment
queue, fulfillment blockers, and item supply/demand are disposable materialized
read models in `projection_row`; `projection_checkpoint` records the tenant-local
Business Event position and builder version. The shared scheduler and worker refresh affected projections when their
checkpoint trails relevant committed outbox events. Reads return the completed
stored generation and never refresh or enqueue it. Commands and confirmations always read authoritative
Reality and never rely on these eventually consistent results.

## Inspect pattern

Playground Business history leads with translated business actions and structured
party/item/quantity/amount/reference context from the shared timeline. Business-area
filters apply before pagination; sales/purchasing follow exact tenant document/source
links, warehouse and finance use event families. The overview counts order documents,
shipment/receipt movements and invoice documents across the tenant, not loaded events
or inferred unique deliveries. Technical event mode and payload remain disclosed on
demand. History's linked-record pane shows authoritative metrics and business links;
it never claims a complete order lifecycle or infers open state from absent events.

Business history shows a non-interactive Data overview with four equally styled
outlined record totals. An info disclosure explains that totals are sandbox-wide,
independent of filters. Record-type filtering remains in its select. A separate
info disclosure beside Transactions explains correlation/source grouping limitations;
neither explanation occupies a permanent paragraph. Both support keyboard and Escape.

Playground central register searches use a shared 34px search-icon field with an
accessible name and contextual placeholder, without a detached visible label.
Live search and submitted history search preserve their existing behavior. Include
settled items is an outlined pressed toggle with a visible check indicator; history
Search is outlined too. Toolbars wrap within the panel in both themes.

The Playground central area offers a read-only Ask Reality tab alongside registers;
the right column contains Needs attention only. Three findings are visible initially. Contextual
questions use the loaded sandbox Reality; conversation survives central navigation.
The composer stays above the timeline. The authenticated run owner supplies context
through the existing managed AI and shared read tools; schemas and dispatch exclude
mutations. History is bounded browser state and resets on reload or sandbox change.
Provider failure is explicit. Business records are never written by this companion.
Answers render safe Markdown headings, lists and bounded tables. Sender names are
accessible labels only; alignment distinguishes messages visually. Wide tables scroll
within the message; HTML, images and external links are disabled.
The timeline defaults to a 44px count/latest-event strip with explicit expansion;
new events do not open it. The central chat has no redundant heading/introduction or
focus toggle. Submitted questions appear immediately as right-aligned messages, with
an accessible animated pending reply on the left. Failed replies retain the question
and offer explicit retry/edit; only completed turns enter subsequent provider history.
Attention uses compact class-grouped work items with inspector-resolved business
context and localized server quantities. Unknown classes retain canonical wording;
missing context is explicit. Selection opens the linked record in the center, with
evidence and register navigation. Findings are not manually dismissible tasks.

The Playground Business history tab replaces its flat Journal presentation. It uses
the shared tenant timeline with server-side reference search, subject/time filters
(including all history) and sequence-cursor loading. Compact counts are SQL totals
of sandbox records, not event-page counts. Correlation/source groups contain loaded
matching events and are not claimed to be complete order lifecycles. A split pane
shows recorded chronology and traverses existing Inspector links with Back navigation;
unsupported subjects retain raw event evidence. Selected event IDs highlight the
bottom timeline. The browser does not infer relationships or calculate business state.

The learning Playground uses a viewport-contained workspace with consistent
presentation. Permanent practice companies also appear in their active owner's App
company switcher, labeled Sandbox. Both surfaces operate the identical tenant through
shared services; App edits are not read-only. Direct links retain the exact company.
Temporary runs remain isolated. Practice access does not enable live connectors,
sharing, lifecycle changes or escape from a reviewed Playground action.
The Playground uses consistent
presentation. Its Documents tab lists sandbox evidence using the shared paginated
document register and server-side number/party-ID/source search. Selecting an opaque
document ID opens canonical Inspector details inside the cockpit; Back preserves
the register search and page. No document operational status is invented.
The workspace uses consistent
presentation: primary view tabs are underlined, secondary
selectors and row actions have distinct roles. Central registers place Details with
a chevron in the rightmost Actions column; record labels are plain text. Business
actions use compact outlined buttons without underlines. Keyboard focus and existing
disabled/confirmation behavior remain intact. Secondary
selectors use a compact filled selection, and register headers share typography and
spacing. Text columns align left and quantities right. The exception catalog icon
sits adjacent to the Needs attention heading. The workspace keeps actions and explicit
review on the left, current shared Reality views and master-data tabs in the middle,
only Needs attention (exceptions) on the right, and a selectable event recorder below.
Details and saved history open inside the workspace. The cockpit is the sole
presentation; the old layout is retained in Git history, not as a second product UI.
This changes presentation only; commands and operational derivations remain shared.

The action pane offers one list grouped under Guided examples and Individual
operations, without mode tabs. Four guided examples and two individual order-creation
actions are visible initially. A default-collapsed, keyboard-accessible More operations
disclosure contains the fourteen remaining actions grouped by Warehouse, Finance and
Master data. Toggling it never writes; returning to the chooser restores the compact
default. Master data offers single-record
Party, Item and Location creation/editing through the existing application tools.
Basic-field forms preserve unexposed attributes; Back makes no change, nested
record previews remain readable and confirmation checks the shared update revision.
Settled actions refresh reference choices for later operations. Source intake is
not implicitly enabled by these master-data entries.
Active reservation selection offers reviewed
release through the shared tool; the physical stock and commitment do not change.
Selecting an individual action opens its editor
directly; settlement or cancellation returns to the grouped list. Free customer and
supplier orders stop after explicit confirmation. The central Open deliveries tab reads
the existing paginated commitment-control projection and offers reservation/shipment
for a selected customer commitment or receipt for a selected supplier commitment.
Targets use the selected record's opaque identity, item and location, never the last
lesson. Remaining quantities are server-derived. Pending actions block switching
work; refresh resumes review without automatic confirmation. Archived runs remain
read-only. Bulk picking and sample imports are not offered by this first increment
(spec 103).

Guided quantity defaults copy normalized order lines or the actual reservation
receipt. Shipment bounds use shared validation before review and before execution
claim. Rejected steps return to the same sandbox's action list. A legacy executing
overdelivery offers explicit discard only with saved invalid-quantity proof, no
action events or target movements, rechecked under run serialization. Other unknown
outcomes stay blocked and are never automatically replayed. Sandbox selection is
not presented as scenario recovery.

Pending execution checks status automatically through read-only requests. Unverified
outcomes, recorded actions awaiting evidence, and proven non-execution have distinct
messages. Manual status retry appears only after a read error. A proven failed shipment
offers Return to operations through explicit discard, never sandbox selection or replay.

The central Open items register separates customer receivables and supplier payables.
Shared server filters include open and partially settled invoices by default; a
control includes settled items. Search, pagination and evidence inspection stay
inside the cockpit. Neither financial balances nor goods commitments are duplicated
in the attention pane. The optional finance status `outstanding` selects existing
`open` and `partial` states before counting, pagination and totals. Without an explicit
sort the register lists the newest document first (document date descending, record key
as tie-break), like every other document register; a sortable Date column shows the
document date. Deliveries remain a work queue ordered by due date, oldest first (spec 167).

Operational pages remain clean. Technical details are reached through an `Inspect` affordance.

Example chain:

```text
Reservation
  -> Commitment
  -> Document Line
  -> Document
  -> Source Record
  -> Original Shopify JSON
```

Use the shortest true link in storage. Do not duplicate all ancestor IDs onto every table merely to simplify the UI.

## Non-goals for V0

- polished customer-facing ERP UI
- permissions/RBAC
- dashboard customization
- React/Next.js unless a concrete need proves it necessary
- live Shopify API connection
- background jobs/websocket infrastructure
- generic workflow builder

The goal is to prove that a small Reality core can be operated, understood and debugged through both human UI and agents.

MCP and managed Copilot derive read/proposal schemas from one canonical registry. The
underlying command catalog classifies every tenant business command and is checked for
parity drift. Discovery is bounded and tenant scoped. A mutation changes no business
state when proposed; approval reloads the exact proposal and calls the same application
service used by CLI/API/Web. Existing MCP token allowlists do not automatically gain
new tools.

## Unified App foundation (Spec 107)

The unified app renders the sole operational shell at `/app`, `/app/copilot`,
`/app/work` and `/app/decisions`. Authentication stays outside the dispatcher.
Home uses actual dashboard totals, Your work is a bounded customer-delivery list
and selected case, and Chat can stay beside that case. Each quantity leads to
shared operational records or the existing inventory workspace. The Inspector
retains the shortest Evidence and Source links and discloses bounded history.

Reservation and commitment shipment share one action card across case, command
launcher and Chat proposals. Preparation persists an exact review but creates no
stock effect. Confirmation requires that review token and a fresh authorization
and state check. Proposal identity in the URL recovers original reviews, receipts
and unresolved outcomes. Recovery never invokes the mutation again. Recorded
results remain distinct from fresh observations and observation failures.

Spec 143 removes the temporary migration switch and both obsolete browser interfaces. Recognized old routes resolve to current workspaces; unsupported routes show an explicit unavailable page. Saved practice records and protected APIs remain intact.

## Unified Analytics and Master Data (Spec 108)

The shell provides `/app/analytics` and `/app/master-data`. Spec 221 removes the
legacy Analytics Overview, delivery metric cards, activity chart and contributor
list, including their exclusive backend GET reads. Home retains Open analytics as
a direct link to Explore. Default and legacy Overview URLs open Explore; obsolete
days/metric/day parameters are no longer emitted. Explore and My reports, shared
analytical tools, saved reports and underlying business records remain unchanged.

Master data separates customers and suppliers by PartyRole, with item and
location registers alongside them. Search and active/all filtering precede server
pagination. Exact details expose provenance, the editable codes (payment term, source
system, external ID) and the existing Inspector. Forms create and edit every
operational field the shared services accept (spec 161): party type, roles,
accounting code, payment term, default currency, credit limit and tax
identifier; item SKU, name, unit, type, tracking, default location, purchase
unit, conversion factor and lead time; location name, type, parent and stock
flag; and each record's source system and external ID. Lossless source payloads
are never edited in the form. An update proposal carries the current value of
every field the request omits, the register's own role cannot be removed, an
item's default location cannot be cleared, and unknown fields are refused.

Forms and Chat use canonical reference-tool ChangeProposals. Preparation stores
review intent only; confirmation records the change. Repeated preparation with
the same request identity recovers the same proposal. Edits carry the
reviewed revision; canonical execution rechecks it under the tenant mutation
lock before the handler runs. Concurrent stale edits remain proposed without
an effect. The proposal URL restores review or receipt after reload. An uncertain
confirmation offers a read-only outcome check, never an automatic mutation retry.
Stored intent and execution receipt remain distinct from current record details.
Decisions and Chat open the same master-data review; delivery references link to
their exact customer, item and location. Existing practice policies and the
legacy retirement boundary remain unchanged.

## Spec 109: Unified Warehouse and Attention

The opt-in shell adds `/app/warehouse` and `/app/attention`. Warehouse presents
company-wide physical, reserved and available quantities per item in its own
unit. Stock, reservation and movement registers reuse existing read models;
exact item and state filters precede server pagination. Delivery cases and item
master data link to the exact item. Reservations and movements link to customer
delivery cases only when their actual commitment has that type. Recorded
movement history retains corrected originals and compensations, with canonical
correction roles. Inspector selection survives reload through the URL.

Attention presents current canonical operational exceptions, ordered by existing
severity rules. Search and severity filtering precede pagination. Customer or
supplier delivery findings show the linked party and item; customer findings
open the existing delivery case. Explanation and supporting-record links use
the native Inspector. Resolution guidance comes from the canonical catalog.
Refreshing a resolved finding removes it from the current register; findings
are not stored tasks and have no dismissal action.

Both surfaces are read-only and tenant-scoped. Unsupported warehouse operations
remain in supporting workspaces. Attention still derives the full company
exception set before filtering and pagination; bounded responses do not imply
bounded derivation cost. No schema, new mutation tool or retirement is introduced.

## Spec 110: Unified Finance Investigation

The opt-in shell adds `/app/finance` with Open items, Payments and Journal. It
reuses existing authenticated finance reads and the native Inspector. Open items
default to outstanding receivables, with an explicit payable switch. Filtered
gross, settled and open controls cover all matching records, separately by
currency. They are not a net liquidity measure. No due date is inferred.

Payments show recorded direction, amount, allocated/unallocated values and
reversal roles. Search is by reference IDs. Aggregate payment headlines are
omitted because the existing payment row and projection-total searches have
different scopes; recorded cash history is not marketed as a current cash balance.
Journal retains debit/credit direction and posting references, with exact account
filtering and complete per-currency controls. A selected account need not balance
to zero. Selecting an account filters the same journal.

Tab, filters, page and initial Inspector target survive reload. Company changes
clear scoped context. Open items inspect their Document evidence; payments and
journal inspect exact recorded entries. No invoice-to-delivery link is invented.
Existing advanced finance operations remain supporting paths. This increment
introduces no financial mutation, schema, new calculation or retirement.

## Spec 111: Unified Data and Sources

The opt-in shell adds `/app/data-sources`: registered Systems, Received records
and Documents. Systems show configured active state and SQL counts of every held
source version. Counts do not imply distinct external objects or live connections.
Source metadata lists are paginated and searched server-side; the queries do not
select payload, job input or job error fields. Unregistered origins remain visible
in Received records.

Each original version keeps its opaque ID, external reference, version and received
time. Import-job status is displayed literally and neutrally: completed processing
is not proof of successful interpretation. An original opens in the shared
Inspector, or leads to Documents filtered by its exact source-record ID. That
filter composes with existing document filters before count and paging. Document
amounts stay recorded evidence values, with no inferred operational state.

Selected Inspectors and filters survive reload; company switches clear scope.
Full payload is fetched only by opening one selected Inspector, then rendered as
escaped original text under disclosure. This is not a byte-size limit or a lazy
disclosure fetch. Source configuration/imports and technical Explorer remain
supporting paths. No import job, source or business mutation is added.

## Spec 112: Unified Settings

`/app/settings` groups personal preferences, company access and AI configuration
inside the unified shell. `settings_view` bookmarks the section. Personal profile
save uses the existing authenticated account API and updates localization from the
returned user. Language, number/date locale and IANA timezone are independent;
appearance belongs to the current browser and synchronizes header and OS settings.

A network/5xx save failure is an unknown outcome, not a rejection. The form disables
another write until a read-only current-profile check confirms the attempt or shows
a difference. A differing saved profile preserves the draft for an explicit new save.
Client validation failure retains editable values; no write is automatically replayed.

Company owners can read access and AI summaries through existing scoped APIs. Other
members see an access explanation without owner-only requests. Membership lists are
bounded at500 members and500 invitations, with invitation and delivery state separate.
AI availability means credential configuration presence, not live provider health.
The summary omits keys, fingerprints, token prefixes and provider endpoint URLs.
Spec 128 brings invitation controls into the unified access section. Credential and
lifecycle controls remain in supporting company administration. No business rule,
source/evidence relationship or schema changes.

## Spec 113: Unified Orders and Deliveries

`/app/orders-deliveries` adds a dedicated workspace for delivery commitments and
customer/supplier order evidence. The default delivery view uses canonical
`delivery_work` observations with effective quantities/dates, correction-adjusted
fulfillment and per-row units. Supplier rows identify the sending supplier.
The remaining quantity column describes unfulfilled quantity, including unfulfilled
quantity on a cancelled commitment. Open means recorded open status plus positive
remaining quantity; all history also
includes fulfilled/cancelled commitments. Counts describe commitments, not orders.

Customer and supplier order tabs reuse the evidence register with fixed sales_order
or purchase_order type filters before paging. They show recorded amounts, never
order-level fulfillment/readiness or cross-currency totals. This is distinct from
the supporting legacy projection-based Orders dashboard. Search follows each API's
supported identifiers/display fields. Document dates remain recorded calendar values.

View deliveries follows the exact opaque document ID through a document-line link
first and direct document link as fallback, selects the corresponding direction
and includes all history. No client-side association or aggregation. Customer rows
open existing Your work cases and reviewed reservation/shipment actions. Supplier
rows open the canonical commitment Inspector; no new receipt action is introduced.
All register/Inspector navigation is read-only. Scope, search, page and inspection
survive reload, and switching companies clears selected order/record IDs. Advanced
order operations retain the supporting `/app/orders` route; Facts remains separate.

## Spec 114: Unified Facts

`/app/facts` is a read-only observation register. Since 2026-09-10 it is not a separate
Workspaces sidebar entry: the Reality Inspector Facts group embeds the same register and
Data & sources links to exact-source observations. The route stays valid for deep links.
Search covers stored predicates, values, subject identifiers and source
references. Exact subject and source-record filters apply before counts and stable
paging; actual tenant subject types provide a bounded choice list.

A Fact records a value at an observation time. It is not a guarantee of current
truth: repeated or differing observations coexist, without an inferred winner,
validity window or replacement status. Stored values and predicates remain original
content in every UI language. Missing source links are stated explicitly.

Related observations opens the exact subject across sources. Data & sources opens
observations for the selected source version. Explain observation uses the shared
Inspector with supported subject and original-source links. No schema, predicate,
write tool, financial derivation or document fulfillment status is introduced.

## Spec 115: Unified ERP table standard

Operational registers in the unified App share one desktop-first table: Orders and
Deliveries, Warehouse, Finance, master data, Facts and received source/evidence
records. Tables fill available content width without a1400/1500px page cap. Home,
Analytics, Chat and registered-source system cards retain their contextual layouts.

Default rows are44px, compact rows36px, headers44px. Body type is14px/20px with12px
horizontal cell padding (4px in the narrow action cell). Cells are single-line with ellipsis and full-text tooltips;
original values remain escaped and untranslated. Headers and first key columns stick
inside an independently scrollable table region. Numbers align right; text/dates left;
actions right. Width profiles distinguish identifiers/status/quantity70–100px,
dates110–130px, amounts100–130px, document numbers120–150px, parties180–240px,
descriptions220–320px and actions80px. Extra width remains blank before actions rather
than stretching text columns. Seven to ten columns is a usefulness target, not a quota.

Row click/Enter opens the existing detail/case. Explicit labeled action icons retain
tooltips and keyboard access; nested controls do not trigger row navigation twice.
Density, optional-column visibility and bounded resized widths persist per signed-in
user and register variant in browser-local storage. Key/actions cannot be hidden.
Reset restores defaults; unavailable or corrupt storage falls back safely.

Page size choices are25/50/100 (default50), applied server-side. Supported column
headers toggle allowlisted SQL sorting over the full filtered company dataset before
paging, with deterministic opaque-ID ties and nulls-last. Monetary projection fields
sort numerically; unsortable hydrated fields do not advertise a sort. Existing API
size1–100 compatibility remains. Header filter entry focuses the existing server
filter toolbar. URL state preserves sort/page size; incompatible register/company
context resets sorting. Existing complete-result totals and action confirmations remain.

## Spec 116: Unified receipt and reservation release

Incoming delivery rows in Orders & deliveries offer Receive goods. Active Warehouse
reservations offer Release reservation. Both also appear in the global action
launcher and matching company Chat/Decisions reviews. Receipt binds the selected
supplier commitment, item and destination, supports partial quantities and existing
tracking references, and uses the shared movement tool. Release identifies one
active reservation and releases its full remaining reserved quantity; there is no
partial-release quantity editor. Physical stock and the commitment remain unchanged
by release. The review shows the exact reservation identity and quantity.

Both use the existing proposal card and state-bound confirmation. Preparation has no
stock effect, stale review fails before execution, editing requires a new review,
and URL recovery opens the stored proposal. Receipt verification checks destination
and movement identity; release verification checks its reservation and action event.
Unknown executions block conflicting stock-pool actions until evidence reconciliation;
recovery never calls the mutation again. Recorded effects remain distinct from current
observations. Register selection is searchable and paginated; settlement refreshes the
views. Existing customer reservation/shipment and practice policies remain intact.

Supplier commitment case reads are now supported for receipt review, extending the
read-only boundary described in Spec 113. No new schema, partial-release service,
opening-stock workflow, rollout or legacy retirement is included.

## Spec 117: Unified delivery holds

Customer delivery cases distinguish the delivery's own holds from customer-wide
holds, showing translated reasons and original notes. Case controls and the global
launcher prepare delivery hold or release through the shared proposal card. Placing
requires a canonical service-provided reason and permits an optional note. Release
binds the complete active own-hold set shown in the review, including original
reasons and notes. A customer-wide hold remains separately visible and effective.
Matching Chat proposals and Decisions open the same stored review.

Preparation has no operational effect. Confirmation rechecks tenant access and the
exact reviewed state; replacement holds, even with identical reasons, invalidate
an old review. Already-held placement and empty release do not create a misleading
review. Existing hold services emit events attributed to the action, without new
schema. Receipt verification and reconciliation prove exact hold identities; an
unknown execution never retries the mutation. Creation proof survives a later
release. Current observation is shown separately from recorded effect.

Neither operation changes inventory, reservations, money or document fulfillment.
Party-wide and document-wide hold editing, rollout and legacy retirement remain
outside this increment. Forms retain shared spacing, useful pagination and localized
light/dark responsive presentation.

## Spec 118: Unified movement corrections

Warehouse movement rows, the global launcher and matching Chat/Decisions proposals
open the same correction review. The deterministic form reverses a movement or
replaces its quantity while preserving supported references. A reason is required.
Richer canonical tool replacements remain reviewable and retain their intent when
editing quantity. Newer return-resolution references are disclosed and prevent the
quantity shortcut where the correction service cannot preserve them.

Shared services validate the inverse and replacement against projected stock,
tracking identity and commitment fulfillment without writing temporary movements.
The review shows original, inverse, replacement and per-item/location stock effects.
Explicit confirmation rechecks current authorization and reviewed state under the
shared mutation lock. Unresolved overlapping operations block in both directions.

Action-attributed events and exact correction/movement relationships prove the
receipt; read-only recovery never repeats execution. Historical proof survives a
later correction. Current observations and their failures remain separate. Originals
are retained and consumed reservations are not restored. No schema, document
fulfillment fields, financial correction workflow or legacy retirement is included.

## Spec 119: Unified order entry

Orders & deliveries and the global launcher offer New order for customer sales and
supplier purchase agreements. The shared order card accepts company/counterparty,
warehouse, human reference, currency and one or more item lines. Quantities, unit
prices, stated line amounts and the stated document total are explicit; the browser
never calculates source authority. Optional fields stay behind line/order details.
Matching Chat and Decisions proposals open the same stored review and preserve richer
supported intent when editing.

Pure shared core validation prepares no business records. Confirmation rechecks current
references and authorization under the common mutation lock, then atomically records
manual source, document/lines and directed delivery commitments. Source includes the
stated total. Entry creates no reservations, movements, invoices or ledger postings.
The unique source/type constraint is explained by rejecting already-recorded identical
payloads before writes; different agreements may retain the same human reference.

Immutable attributed creation snapshots and exact linked IDs prove receipts. Unknown
identical-intent actions block duplicate execution; reconciliation only reads evidence.
Current fulfillment is separate from historical proof. Recorded-order, per-line delivery
and Inspector links continue the flow in the unified shell. No order editing, finance
mutation suite, schema change, deployment or legacy retirement is included.

### Unified invoice entry (Spec 120)

Finance and the global Actions menu expose customer/supplier invoice entry. Select an order
and one line, enter the stated invoice number, quantity, gross amount and optional effective
UTC time, then review and explicitly confirm. Matching Chat/Decisions proposals use the same
card and services. Search is tenant-scoped; paging is shown only when there is another page.

The existing canonical tools create invoice source/evidence and balanced receivable/revenue
or inventory/payable postings atomically. They do not move goods or record payment, and do
not require prior fulfillment. One invoice per order line is the current boundary, including
partial quantities; further partial or consolidated invoices are outside this increment.

Current-reference review prevents stale execution. Exact attributed invoice/line/posting
receipts support response-loss recovery without repeating the mutation. Historical creation
proof remains separate from later financial activity; verified invoice/Inspector links expose
the source and current financial context. The form works in all four languages and themes.

### Unified payment entry (Spec 121)

Finance and the global Actions menu expose customer/supplier payment entry. Choose a searchable
open invoice and enter the actual payment amount, optional reference and effective UTC time.
Matching Chat/Decisions proposals use the same review, edit, confirmation and recovery card.
This records a payment already made; it does not initiate a bank transfer.

Shared canonical services validate the current invoice, amount, source and allocation state,
then atomically record payment evidence, two balanced postings and one settlement allocation.
Partial payments leave a derived remainder. Amounts must fit the existing four-place storage
precision without rounding; the payment review displays every supported decimal place.
Optional original payment source is preserved; its absence is explicit and the invoice source
is never substituted. Preparation creates no business records.

Explicit confirmation checks current authorization and review state under the common mutation
lock. Immutable attributed document/posting/allocation events prove the exact ledger receipt;
response-loss recovery reads evidence without repeating the payment. Verified links open the
invoice, payment and Inspector in the same shell. Historical proof remains available after a
later reversal, separately from current open amount and allocation activity. Existing-payment
allocation, multi-invoice splits, refunds, bank execution and legacy retirement are separate.

### Multi-position invoices (Spec 122)

The unified invoice card supersedes Spec 120's single-position entry limit. Select one or more
distinct positions of the same customer/supplier order, add or remove rows, and state each
quantity and line amount. The invoice total is entered independently and posted exactly as
stated; it is not replaced by a sum of the lines. Supported decimal values are preserved
without storage rounding. Already invoiced positions still cannot be invoiced again, including
further partial billing of the same position; this separate limit is stated in the form.

The existing invoice tools accept either legacy single-position arguments or a lines array.
Shared core validation and ordered row locks protect every selected position. One confirmation
atomically creates one source, one invoice with N linked evidence lines and one balanced posting
group. Invalid, stale, mixed-order or previously billed positions cannot leave a partial invoice.
The source preserves header and line amounts. No stock movement or payment is created.

Finance, Actions, Chat and Decisions share the editor and plural review. Edits/reloads retain
all positions; receipt verification covers every created line in order. Unresolved overlap is
checked across legacy and multi-position proposals; recovery never reruns the booking. Existing
single-position proposals/receipts remain readable. No schema or credit/refund workflow change.

### Unified financial reversal (Spec 123)

Finance and Actions expose a searchable posting selector with original document/party context.
Payment and journal rows can seed the selected group. Enter a reason, review, then explicitly
confirm the same canonical ledger_reverse tool used by other adapters. Chat and Decisions use
the identical stored review, editor and recovery card.

The preview shows exact inverse entries, newly inactive versus already inactive allocations,
and affected invoice open/payment unallocated amounts before and after. Reversal occurs at
confirmation time. Original evidence, postings and allocations remain in history; inverse entries
trace through LedgerReversal to originals rather than fabricating source/document links. This
records no bank transfer or stock movement. Spec 124 extends invoice reversal with renewed billing
availability; credit/refund workflows remain separate.

Current allocation, counterpart and balance state bind confirmation. Unresolved overlapping
payments/reversals block execution in both directions. The existing ledger.reversed event is
attributed to the proposal and retains original/inverse snapshots. Exact relation/group/entry
proof reconstructs the canonical receipt after response loss without rerunning mutation. Later
financial observations remain separate from historical verification. Legacy direct reversal
calls retain their contract and no schema/event name is added.

### Partial invoicing and rebilling (Spec 124)

Both invoice directions support successive partial quantities against the same order position.
The canonical selected-order tools admit positive quantities up to the remaining amount, with
exact four-place storage precision. Invoice line and header money remain independent stated values.
This supersedes the one-invoice-per-position restrictions described in Specs 120 and 122.

One tenant-scoped core observation derives ordered, effectively invoiced and remaining quantities.
Matching invoice lines consume quantity even before posting. They release it only when at least
one original posting group exists and every attached group has a complete reversal. Payment
reversals and credit notes do not change this observation. Received overbilling remains evidence;
its actual total is shown while available quantity stays at zero. No billing state is stored.

Order Inspector lines expose this observation. Selection shows remaining quantities and disables
exhausted positions; entry/review display ordered, already invoiced and remaining quantities,
including the quantity left after the proposed invoice. Prior invoices open in the Inspector.
Financial reversal review shows projected availability from the same calculation. Existing
Finance, Actions, Chat and Decisions entry/recovery paths remain shared.

Invoice reviews include billing evidence and reversal snapshots separately from immutable creation
receipts. Billing, manual evidence/correction, posting and reversal writers share the tenant lock
before row locks. New billing or reversal invalidates an older confirmation even if its quantity
still fits. Historical verified receipts stay valid after partial/replacement invoices. Old pending
reviews may require a refreshed review. No migration, new event or command is introduced.

### Invoice-linked customer credits (Spec 125)

Finance exposes credit entry from a customer invoice row and from the action menu. One invoice
can contribute multiple selected positions and partial quantities. The form accepts independently
stated line/header amounts, a credit reason and an explicit amount to offset against that invoice.
Zero offset leaves the credit open, including on a fully paid invoice. Review shows invoice open
before/after and credit remaining to settle. A financial credit needs no physical return, creates
no goods movement and sends no refund. Supplier credit and refund entry remain separate.

The existing sales_credit_record command has a distinct invoice_id/lines shape; legacy order-line
return credits keep their arguments and return rules. CreditLine.billed_document_line_id points
to InvoiceLine, then to OrderLine, without a new schema field. Linked credit evidence consumes
invoice quantity and header amount capacity; unposted credits count, and complete reversal of all
original credit posting groups releases capacity. A reversed/unposted source invoice cannot be
credited through this entry. Old order-linked credit has no invoice attribution, so it blocks new
credit entry for the affected invoice and exposes Inspector links instead of guessing its identity.

Canonical credit posting and settlement share one transaction and tenant lock. Reviews bind to
invoice/credit/reversal/open-balance state, and concurrent excess requests fail without partial
records. The attributed credit.recorded event retains exact reviewed creation, source/document/
line/posting/allocation snapshots and receipt; lost responses reconcile without executing twice.
Later credit reversal does not invalidate the original proof. Chat and Decisions share the same
editor and recovery card. Returned-not-credited observations include invoice-linked credits;
financial credits without return links do not imply missing returned goods.

Return review remains a separate operational decision. The shared Web and MCP action exposes only
`restock`, `quarantine_repair`, `scrap_loss`, and `return_to_supplier`; it requires the arrived
return Movement, its customer-delivery commitment and arrival location. Review inherits any
handling-unit, lot, or serial identity instead of asking the operator to restate it. The Inspector
shows each resolving Movement and remaining quantity, while the invoice-credit context separately
shows the financial positions and capacity.

## Unified customer refunds (Spec 126)

Finance → Open items includes an explicit Customer credits flow with derived gross,
settled and open amounts, separate currency totals, status/search/sort and server
pagination. Existing receivable/payable invoice projections remain unchanged.
Only outstanding customer credits offer a selected-row Record refund action.
The launcher can select another open credit; company Chat and Decisions open the
same refund card and review.

The operator supplies the amount actually refunded, optional reference and UTC
effective time. Review names the credit/customer/currency and shows the credit open
before and after. Confirmation records outgoing cash evidence and its allocation;
it does not initiate a bank transfer or change goods. The shared service checks
current credit capacity against both netting and refunds under the same lock.
The common lifecycle supports edit, rejection, stale review and exact recovery after
a lost response. Historical credit/refund/posting/source links remain inspectable
after a reversal; current open amount is shown separately. Loading, empty and retry
states and all four languages follow the common action design.

## Unified business journey verification (Spec 127)

The linked journey is order → reservation → partial shipment → partial invoice →
customer payment → invoice credit → partial refund → refund reversal. A dedicated
real-browser test uses a migrated disposable PostgreSQL database, ordinary owner
login and separate API/Vite processes; it does not substitute financial responses
or mutate the shared development company. Existing per-feature tests remain in place.
Reversal reviews label settlement balances as Open amount, because the affected
records may be invoices, credits or refunds. The introduction refers to a financial
posting; the reviewed calculations, confirmation and historical proof are unchanged.

## Spec 128: Unified company and member administration

Settings adds a Company section with current identity and role, and reviewed creation
of an empty company. The no-company entry uses the same form. Bootstrap refresh selects
the returned opaque company ID; duplicate display names never identify a company.
Existing details remain read-only because no rename service exists.

Company access supports owner-only invitation creation, resend (pending or expired),
revoke (pending) and ordinary-member removal, using existing membership APIs. Each
write requires an inline review naming company and recipient. Review/cancel makes no
write; submission is single-flight. The service retains cooldowns, limits, duplicate
neutrality, owner protection and tenant authorization. Invitation request acceptance
does not mean email delivery or membership acceptance. Lists remain bounded at 500.

Unknown writes block resubmission until an explicit current-state check succeeds; no
write is automatically replayed. Unknown company creation offers authorized companies
with their IDs, without matching by name. When creation returned an ID but bootstrap
failed, recovery opens that exact ID once authorized. Company changes discard drafts.
Invitation acceptance routes to its returned tenant in the unified app. Existing auth
verification and invitation secret handling remain unchanged.

Four languages, keyboard review focus and responsive light/dark styling follow the
shared shell. No schema, rename, role editing, archive/delete or provider setup change.
The existing company-creation tenant/membership transaction gap is not repaired by this
UI increment; an unknown result remains explicit and requires inspection.

## Spec 129: Reviewed new-item CSV import

Data & sources offers Import items: upload a UTF-8 CSV, map SKU/name and optional
unit, review every row, then explicitly confirm. Files are limited to 2 MiB, 500
rows and 50 unique nonempty columns; comma, semicolon and tab are supported. The
fallback unit is explicit and visible in review. Original bytes, including unused
columns, remain available as a tenant-scoped attachment.

The existing item_create tool and proposal lifecycle create the source, items and
attributable events in one synchronous transaction. Existing tenant SKUs (including
inactive items), duplicate file SKUs and invalid rows reject the whole batch. This
is import policy, not a new global SKU identity rule. No existing item is overwritten.
Reviews bind the file hash, mapping, defaults and complete validated rows. Shared
serialization protects revalidation against simultaneous master-data changes.

Preparation recovery preserves its request identity. A lost confirmation response
requires an explicit status check; recorded-result recovery never creates items
again. Bookmarked proposals, Chat and Decisions open the same import review. Results
link to exact items, source and original file. Company switches discard visible
state. Ordinary authorized members can import; Playground is excluded.

Existing item-target file worker processing also validates before writes, commits
its batch atomically, returns existing items on completed replay and recognizes file
profiles on retry. Other profiles and live vendor connectors remain separate work.
The new synchronous import does not create or claim a background import job.

## Spec 130: Source definitions in the unified app

Data & sources adds Register source and Configure source on existing system cards.
The inline form reviews normalized code, name and description before calling the
existing registration service. Existing selected definitions reopen by opaque entry
ID, show declared source/target types and interpreter availability, and allow reviewed
changes of source/type registry flags. The type detail displays 25 entries per page;
source register search and server pagination remain unchanged.

Copy distinguishes registry state from transport and ingestion control. Changing a
flag does not start or stop imports. Interpreter availability is a registered code/type
implementation, not proof of an authenticated live connection. No connector installation,
new type creation, rename or mapping wizard is included.

Mutations are single-flight and never triggered by review, cancel or reload. Unknown
results persist a tenant-scoped unresolved marker across reload and block changes until
an explicit current-state read succeeds. That read is not an attributable mutation
receipt; matching code only locates present registry state. A failed check keeps the
block. Component lifetime guards prevent late responses from navigating another
company. Existing member authorization and practice restrictions remain server-owned.

The selected source management flow no longer links to the legacy integrations screen;
Technical Explorer and other migration candidates remain separately accessible. No
schema, domain service or backend authorization change is introduced. Four languages
and shared light/dark responsive styling apply.

## Spec 131: Unified AI setup and external MCP access

Owner-only AI configuration in unified Settings now replaces the legacy company
administration link. Current credential status is distinct from live provider health.
Managed/company-Anthropic setup reviews its exact mode, fixed model/endpoint and key
retention, replacement or removal effect. Other stored provider settings are explicitly
marked as unused by the current chat runtime, with expandable provider/endpoint details.
No remote provider request is made by configuration save.

External agents live in a separate expandable MCP section. The endpoint and active
opaque token IDs, prefixes, creation/last-use times and scopes remain inspectable. New
tokens start with no permissions and require explicit tool names; read-only bulk
selection never adds propose/confirm. A separate full-access preset selects every
tool in the current catalog, including change-capable tools, while still submitting
their explicit names rather than a wildcard. Either preset replaces the prior
selection; owners can clear or individually adjust it before review. Review
distinguishes reading, preparation and approval/execution, and names all selected
tools. Existing wildcard grants remain visible and revocable; new UI does not grant
wildcard access. Tool search and display pagination retain the selection; presets
apply to the complete catalog rather than only the visible page, and token/tool
displays are bounded at 25 per page. The underlying settings endpoint still returns
the complete catalog/token list.

The full token appears only from a successful creation response, with copy/manual-copy
fallback and explicit hide. It is never persisted or recovered. Revocation reviews the
exact ID/name/prefix. Tokens have no automatic expiry and are tenant-bound; removing an
issuing owner's membership does not implicitly revoke them.

All writes are single-flight and reviewed. A secret-free session marker (random attempt
ID and operation kind) survives reload on uncertain results. Explicit current-state
reads unblock a fresh review but do not prove previous request attribution or recover
a lost token. No save/create/revoke is automatically replayed. Submitted keys leave
form/review state; errors are generic rather than echoing credentials. Company changes
and unmounts discard visible secrets and ignore late responses. Read operations retain
existing settings initialization/legacy vault migration semantics.

Four languages, keyboard review focus, responsive light/dark layouts and existing
owner/practice authorization apply. No backend, schema, model or provider transport change.

## Spec 132: Reviewed opening stock

Warehouse and Actions offer Record opening stock. Matching movement_create opening
proposals from Chat and Decisions open the same form. Bounded item/location search,
a positive exact quantity and an optional device-local occurrence time prepare a
server-owned review. Blank time means execution time. This first form supports
untracked stocked items and stock-capable destinations; it does not add lot/serial,
source, commitment, reason or return fields.

Opening stock is additive, including when stock already exists: 10 plus 5 becomes 15.
It does not set a target inventory balance. The review displays physical stock before,
quantity added and physical stock after, with reserved stock unchanged. Item/location
attributes and balances are revalidated under the shared tenant lock before the
canonical movement_create tool executes. Changed state requires discarding the old
proposal and preparing a fresh review. Existing inactive-reference semantics remain
unchanged; changes to active flags invalidate an existing review.

The movement and attributed movement.recorded event provide manual provenance through
the confirmed proposal. No external source, document, reservation or financial posting
is fabricated. Exact movement/event/intent/output agreement establishes a receipt;
current stock is a separate observation, and later corrections do not invalidate the
historical receipt. Inspector links expose both records. Existing Warehouse movement
correction remains the correction path.

Preparation persists its tenant-scoped request identity and intent before transport.
A lost response recovers that same request. Confirmation uncertainty blocks further
writes and requires checking status; committed-but-unsettled recovery settles the
recorded receipt without replaying the movement. Overlapping unresolved warehouse
proposals block new same-pool work in either direction. Company changes discard visible
state. Ordinary company authorization and Playground exclusion use existing services.

The stricter review applies to this bounded company flow. General CLI/MCP raw opening
proposals retain their existing approval and broader movement contracts; matching
company proposals can explicitly acquire this review. Existing practice stock entry
is unchanged. No schema or additional movement type is introduced. Four languages,
responsive light/dark layouts and modal focus handling apply.

## Spec 133: Customer-wide delivery holds

Customer delivery cases, selected customer master data, Actions and matching company
Chat/Decisions now share the customer-wide hold card. It reviews one customer's exact
identity and supported reason/original note for placement, or all active customer
hold records for release. Customer-role search is bounded and paginated; selected
customers seed the same card. Prepared master-data actions continue in Decisions.

Copy distinguishes the customer-wide scope from individual delivery holds: linked
shipments for current and future customer deliveries are blocked, while new
reservations remain allowed. Existing reservations, physical stock and money remain
unchanged. Release leaves individual/document-derived commitment holds intact and
does not claim shipment readiness. No affected-delivery count is invented.

Shared review binds customer identity/relevant attributes and the exact full active
hold set. The existing tenant lock protects revalidation and canonical service
execution. No-op reviewed actions reject; release/reapply with the same reason still
invalidates an old review. Same-customer unresolved hold work and linked shipment or
shipment-correction work block overlapping actions; reservation permission remains
unchanged. Customer role checks use existing multi-role reference semantics, including
inactive records when deliberately selected. Raw general party tools retain their
broader compatibility outside this reviewed customer form.

Core party hold/release now accepts an optional tenant-validated proposal action ID.
Placement and release events retain their old fields and add exact hold declaration
snapshots and release time, with action/correlation attribution. Verification requires
exact event, hold set, declaration and canonical output agreement. Current active
holds remain separate from historical proof, which survives later release/rehold.
Inspector opens the customer and attributable event. No source/document or new schema
is fabricated for this manual decision.

Preparation stores its tenant-scoped request identity and intent before transport.
Lost responses recover that same request. Unknown confirmation blocks further writes
until status checking; committed-result reconciliation never repeats the hold action.
Company changes discard visible state. Four languages, shared responsive light/dark
styling, modal keyboard/focus behavior and escaped original notes apply. Playground
and document-wide hold editing remain separate.

### Unified activity drawer — Spec 134

Home exposes View all activity as a modal side panel. The duplicate global shell
entry was removed by spec 225; the Inspector Activities page shares this reader. It
keeps the underlying route and unfinished input, restores focus on dismissal, and
closes on company change. Its sole history authority is the tenant-scoped timeline
service, with explicit search, occurrence-time windows (24 hours, 7 days, 30 days or
all time), historical attention filtering and manual refresh. No writes, notifications,
unread state or polling are introduced.

Individual events appear by descending recording sequence. Recorded time is visible;
occurrence time, identifiers and escaped original payload are available in Technical
details. Known action titles and UI labels are localized; business names, references
and exact quantities/amounts retain their original content. Unknown actions fall back
to server titles or exact event types. Historical attention does not claim a current
exception; ordinary events carry no completed-business status.

Older pages use the last returned sequence and service has_more. Duplicate IDs are
not repeated, failed older reads keep loaded rows, and filter/company changes reject
obsolete responses. No complete-process grouping or company totals are inferred from
a loaded page. Every row opens its event Inspector; explicitly supported subject
families also open their related record directly. Unsupported subjects retain event
inspection and technical identifiers. The nested Inspector returns to the drawer.

This is a bounded C1 history migration. Technical Explorer, retained legacy operations,
practice continuity and final retirement remain separate acceptance work.

### Compact shell and global chat — Spec 135

The unified header is 60px and sticky. Desktop primary navigation uses a 200px sidebar,
36px rows and compact group spacing; it scrolls independently below the header.
Spec 221 places Analytics as the final Workspaces link after Master data, replacing
the separate Analytics navigation group and its Reports link. The visible label,
accessible name and collapsed tooltip stay Analytics in every language; the existing
analytics route, company context, active state and mobile drawer behavior remain. The unified UI no longer exposes migration links to the old app or Playground (Spec 135 FR-008).

Ask Reality is an initially open desktop right column, hidden initially on small screens.
The header toggles it; hiding and workspace navigation preserve the mounted conversation
and draft. Company changes remount chat and clear its transient state. The existing
copilot URL opens this same dock with Home behind it. Delivery discussion also opens
the dock with the selected delivery context. No second inline case chat is created.
Existing chat APIs, confirmations and uncertain-send recovery remain authoritative.
On small screens the panel fills the area beneath the header and has a close control.
This is the owner's explicitly requested early UI increment; functional closure and
legacy/practice retirement remain separate unfinished work.

### Reference-style dock chat — Spec 136

The right chat uses one compact conversation header, history/new-chat icons, flat
messages and readable Markdown table dividers. History selection is hidden until
requested. Messages and proposal review links scroll together above the composer.
There is no extra welcome/message card frame or nested textarea border. A single
rounded composer contains the editable text, paperclip, microphone and send arrow;
Enter sends, Shift+Enter adds a line, and IME composition does not trigger submission.

Attachments are local UTF-8 text/Markdown/CSV/JSON reads, at most 64 KiB, appended with
the filename to the editable draft. The existing 4,000-character message API limit is
preserved: an attachment exceeding that combined limit is refused without truncation;
oversized typed/dictated drafts remain editable and cannot be sent. No binary upload,
PDF/image interpretation or source import is implied.

Dictation uses an available browser speech service after explicit microphone interaction
and browser permission. Final transcripts append to the draft and never send themselves.
Listening is visible; stop, hide, send, conversation/company change and unmount end the
recognition session. Unsupported browsers and errors explain the unavailable function.
The footer states an accuracy reminder without claiming that Reality learns from chats.
Shared chat APIs, tenant scope, unknown-send recovery and proposal confirmations remain.

The unified header company switcher uses a keyboard-accessible popover with company initials, full names, selected state, practice labels and duplicate-name IDs. Native light dismissal and Escape close it. It reuses the existing company switch callback. Company settings remain in sidebar Settings, without a duplicate header button (Spec 135 FR-006). The switcher is mounted once, in the top-left header cell beside the logo mark, as a two-line workspace control: a small context line (Reality, or Sandbox in accent colour for practice companies) above the company name. The logo mark alone remains the Home link; the sidebar carries no company block.

### Register workbench — Spec 137

Orders & deliveries, Warehouse, Finance, Facts and Master data use compact headers and horizontal tabs. Existing page actions are grouped at the register toolbar right; contextual row actions remain in the final column. Shared tables preserve density, sticky headers/key columns, column preferences, server sorting and pagination. The sticky desktop footer groups current-page selection, visible-column CSV export, page size and pagination. Selection resets when company, route, filter or page context changes. CSV is a presentation snapshot of selected loaded rows, with formula-safe quoting; it never changes business records or represents a lossless source export. No bulk mutation is introduced.

The primary Daily work navigation omits Ask Reality: the header toggle opens the global chat. Existing contextual chat entry points and /app/copilot links remain supported (Spec 135 FR-007).

Attention includes a separate “How does a finding arise?” explanation card beneath the finding panel. Its link opens the existing searchable global exception catalog with company-appropriate copy distinguishing possible classes from active findings. It does not create, dismiss or modify findings (Spec 109 FR-009).

### Reality Inspector — Spec 138

The dedicated Reality Inspector group between Analytics and Company exposes scoped Facts/records, a bounded graph of returned Inspector links, documented Fact-rule cases and versions, exception classes, command/action catalogs, projection/view definitions and activity history. Rule creation and lifecycle mutations reuse owner-controlled application APIs with explicit review; ambiguous responses block resubmission. Only explicitly mapped existing Web actions launch shared forms. Rule editing uses validated JSON; graph and result limits are labelled. No schema, alternate domain logic or arbitrary executor is introduced.

### Unified legacy exit removal — Spec 135 FR-008

All twelve audited legacy exit sites are removed. Advanced register/detail links and sidebar migration links are absent. Unsupported proposal review stays in Decisions with an explicit unavailable-review explanation; chat does not redirect to the old exception workspace. Practice companies remain excluded from unified operations and expose a message with non-sandbox company switch buttons. Role-less party receipt links use the scoped Inspector record search. Existing old URLs and practice/business data remain intact; removing navigation does not retire the underlying applications.

### Context-first Inspector — Spec 138 FR-001/007/008

Reality Inspector has four primary destinations: Understand context (overview/graph), Facts & origins (facts/records), Rules & insights (rules/exception classes/projections and views), and Actions & history (commands/history). Existing inspector_view URLs remain valid and select the corresponding group. Company no longer contains Technology & system.

Context overview offers a scoped record search/type filter and a conceptual source → evidence → operational records/Facts → derived insights → reviewed actions guide. This guide is explicitly distinguished from actual graph edges. Selecting a record loads existing Inspector metrics, meaning, relationships and available original payload. Graph node navigation updates the detail perspective; stale responses are not presented as another selected record. Catalog counts belong in the corresponding technical views. Chat remains the global existing dock; no automatic injection of arbitrary selected records is claimed.

### Reference-style register chrome — Spec 137 FR-005

Orders & deliveries, Warehouse, Finance, Facts and Master data render their compact title/tab strip inside the actual sticky global header, between branding and company/utility controls (FR-006). The table surface groups search left and an Actions disclosure right, existing filters and shared density/column controls in a second row, then result count and rows. Existing page action handlers and dialogs are reused; no new commands or mutation rules. Facts retain explicit search submission. Selection/export/pagination remain in the shared footer. Empty master-data guidance is expandable instead of a large card. Desktop and mobile wrapping, Escape/focus and existing table behavior are verified.

Spec 137 FR-006: existing select filters display as compact icon/label/current-value chips, with native keyboard and selection behavior retained. Density uses a Normal/Compact dropdown; Columns uses an icon disclosure. Narrow screens may wrap within the global header, with locally scrollable tabs and no page-level horizontal overflow. No duplicate in-content title strip is rendered.

Spec 137 FR-007 extends global-header titles and group-local tabs to Reality Inspector and Company pages (Master data, Data & sources, Settings), retaining existing navigation URLs and a single header for embedded Facts.

Spec 138 FR-009 aligns rule editing with existing server authorization for company owners and platform administrators. Version cards distinguish active application, inactive drafts and disabled history; technical JSON remains expandable and actions are visible. Copying a version opens and focuses a new draft editor. Single-page question lists omit pagination buttons. No destructive rule deletion or backend authorization change is introduced.

Spec 138 FR-010 adds an All/Active/Draft/Disabled rule-state filter. Questions match existing tenant-scoped version states before server pagination; visible versions use the same filter. List badges show actual version states, including simultaneous Active and Draft, independently of question lifecycle. No derived status is stored.

Spec 138 FR-011 renders the exception class catalog and execution history directly in Inspector tabs. The history table reuses timeline filtering, errors and recorded-sequence cursor paging, with isolated column preferences and no unsupported page-size or sort controls. Event inspection remains available from each row. Existing global activity/catalog dialogs remain supported.

Spec 138 FR-012 presents Fact rules as a register with search, version-state filter,
row density, columns and a direct New rule action. Creating or editing opens a dialog
containing the existing version, simulation and reviewed-write workflows. Closing it
restores focus; in-flight and uncertain-result locks still prevent duplicate writes.
Server pagination defaults to 50 with 25/50/100 options.

Spec 138 FR-013 standardizes fixed Inspector definitions (exception classes,
commands/actions, projections/views) and record collections around the same search/count
surface and compact disclosure rows. Facts, rules and history keep table layouts; context
and graph exploration keep their purposeful visualizations. Unsupported mutations are not
invented for fixed definitions. Application-reference metadata loads only on consuming
tabs. Local catalog evidence validation parses each referenced file once per request and
continues to reject missing or renamed test evidence on subsequent requests.

Spec 138 FR-014 adds a graph Record ID combobox. Suggestions use the existing tenant-scoped
explorer with an explicit allowlisted type, SQL search before a ten-record bound and
250ms input debounce. Labels and opaque IDs are visible; mouse or keyboard selection opens
the graph. Empty/error/retry states, type resets and manual-ID entry remain explicit.
Late responses cannot replace the current query's suggestions. Inspector Facts and Fact
rules omit their former pre-table help/count preambles (FR-013).

Spec 138 FR-015/016 makes Overview a graph-first entry. Shared starting buttons offer
Delivery, Order, Item, Customer and Fact. Without a selected record, the first available
category supplies up to three candidates; actual distinct Inspector links choose the
starting sample. Delivery candidates follow the explorer's recent ordering; other types
retain their existing explorer order. This is not a global most-connected/latest claim.
Graph nodes and context details stay linked. Search follows the graph, and the conceptual
model is expandable below it. The focused graph tab keeps manual ID/autocomplete controls.
Manual input and company/category changes cancel obsolete automatic selection; missing
data and errors stay explicit. Narrow graph containers stack linked nodes below the root;
wide containers retain two columns. Zoom and the existing twenty-link bound remain.

Spec 138 FR-017 opens projection data directly in a modal from either catalog entry point.
It loads the current tenant's existing projection endpoint, renders up to 100 returned rows
in a read-only table and keeps technical JSON expandable. Loading, error/retry and empty
results remain inside the dialog. Escape/Close restore trigger focus; closing unmounts the
read and reopening fetches again. The former distant inline result section is removed.

FR-017 follow-up: All Inspector catalog views open the same read-only data modal, including
authoritative registers with application routes and activity. Catalog buttons never
redirect or open a side drawer. Register previews reuse existing scoped reads and label
the first-response preview bound; commercial references retain their collection identity.

Spec 138 FR-018 originally presented Projections/Views and Actions/Commands as matched two-column
catalogs, stacked on narrow screens. Spec 219 replaces the Projections/Views presentation with the report catalog below. Heading information controls open on hover, focus
or touch and explain each concept with a plain ERP example; Escape dismisses help.
FR-019 adds separate Documentation links using the configured docs origin and explicit
Open in application navigation where an application destination is known. Documentation
opens a new tab; application navigation preserves tenant. Data preview buttons still
open only the shared modal.

Company navigation also provides Documentation below Settings, with an external-link
indicator and a native new-tab link to configured DOCS_URL (spec 138 FR-019).

Spec 138 FR-020 progressively explains catalog entries: business purpose and explicitly
illustrative stock/reservation examples first, then How it works with validated reads,
processing, outputs/writes, relationships and service input contracts. Raw technical
definitions remain collapsed. Contract source metadata contains only repository-relative
Python paths and function names; implementation/catalog links open known repository files
in a new tab, without serving source files or exposing runtime paths. Existing preview
modals, forms and separate application/documentation links remain available.

Spec 138 FR-021 adds Code buttons opening a read-only Python modal for every catalog entry.
Source is requested lazily through the tenant-authorized catalog-code endpoint, resolved
only from validated catalog entries or static register read adapters. Actions show their
command; projection-backed views show projection services; direct views identify their
read adapter explicitly. Each function is bounded to 600 lines/64 KiB with truncation
labelled. File/function names, a function selector, retry and Escape/focus restoration
are provided. The modal never evaluates code or accepts a filesystem path.

Spec 138 FR-022 gives all four catalog entry types a consistent card hierarchy: business
title, entry-specific explanation, wrapping primary action/documentation/application row,
then a separated Details section with code, optional example, How it works and technical
definition. Technical identifiers remain in definitions rather than titles. Generic
introductory copy is shown only when an entry description is absent.

Spec 138 FR-023 aligns all Data & sources tabs with the shared register toolbar, grouped
actions, direct filters, density/columns and tables. Systems retain supported paging
without unsupported server sorting/page size. Source setup and CSV import use native
dialogs with busy dismissal guards and unchanged persisted recovery/review flows.
Task-oriented hints replace the large model banner. Table and footer share a 16px inset
from the outer surface, with bottom spacing in each tab.

Spec 138 FR-024 replaces Overview with a flight recorder band of actual business events.
Newest recorded sequence appears first; localized recording dates divide the band.
Scrolling loads older cursor pages without a time cutoff, with a manual load fallback.
Errors preserve loaded history. Source/event/subject nodes use explicit held references
and open the existing Inspector; causation is shown only when recorded. Occurred and
recorded timestamps remain distinct. This is event history, not historical state replay.
The focused Record graph tab remains available. No additional business writes or schema.

Spec 138 FR-025 names the Company entry and page Integrations, with Source systems,
Received data and Documents tabs. Existing data-sources routes, functions and the
registered-versus-connected explanation remain unchanged.

Spec 138 FR-026 replaces the former event-row flight recorder with a layered temporal
graph titled Understand context. Reference, Source, Evidence, Reality and Events have
fixed lanes; each record identity appears once and each event remains separate. Time
slots follow recording sequence from left to right, with localized timestamps, explicitly
not proportional durations. Only held allowlisted references form edges. Nodes known
only by reference sit at the loaded boundary and are marked as earlier references;
other records use their earliest loaded subject observation, not an assumed creation date.
Selection highlights the connected loaded component and provides an Inspector Details
action. Horizontal left scrolling prepends older cursor pages while retaining the viewed
time anchor; latest navigation, retry, manual older loading and tenant isolation remain.

Spec 162 lays the FR-026 graph out as a recorder: the five lanes stay, records become
12px dots coloured by lane, and the horizontal axis is a fixed raster of recording-time
intervals (15 minutes up to six loaded hours, one hour up to three days, otherwise one day)
with interval labels in the header instead of one column per event. Records recorded in
the same interval and lane stack up to eight rows; a denser interval widens its column so
every record stays rendered and clickable. The paper runs up to the present with a now
mark, spans at least the visible band, refreshes newest events every 30 seconds while
visible, and opens with the newest record in view; each lane draws a baseline trace and
every held reference is a faint stitch between its records, emphasised on selection.
Explicit references, selection, off-screen hints, Details and tenant isolation are
unchanged; older pages are anchored to the instant at the viewed left edge and keep
loading while the view sits at that edge or does not overflow. Hovering or focusing a dot opens its record card as an overlay.
Zoom in and zoom out step the raster
through five minutes to one week while keeping the instant at the middle of the view.
Business time stays in the selection details and does not drive the axis.

Spec 163 names the section Context Graph: the first Reality Inspector navigation entry is
labelled Context Graph in every language, its Timeline and Record graph tabs and routes are
unchanged, and the public site uses the same term wherever it describes facts connected over
time. Context Graph is an invariant product term in both localization audits.

Spec 138 FR-027 adds an all-record register to the Inspector Facts tab. A direct Record
type filter selects the explorer families, Facts and document lines; all records is the
default. Lists use tenant-scoped shared summary reads with search before pagination and
deterministic family/ID ordering. Source payloads remain in Inspector details. Type and
page persist in the URL. Selecting Facts restores the existing observation table and
filters/actions; operational Facts and targeted source/subject observation links keep
their existing semantics. Rows provide exact-kind Inspector and Record graph actions.

Spec 137 FR-008 names the delivery tab Commitments and
explains the commitment → reservation → movement distinction. Orders & deliveries
and its route/filter/action behavior remain unchanged.

## Sole application and browser retirement (Spec 143)

The unified app is the default without a feature flag. Legacy product components,
Playground screens and their exclusive styles are removed from source and builds.
The exception catalog is a shared Inspector component. Auth, account approval,
company isolation, invitations and current operational controls remain authoritative.

Old operational bookmarks map to current workspace tabs with tenant and compatible
read filters. Unknown routes show an unavailable page. Compatibility navigation
never prepares, confirms, rejects or retries an action. Playground entry/run bookmarks
show a retirement explanation and an App link; no sandbox workspace remains.

No records or historical migrations are deleted. Protected Playground services and
APIs remain for stored runs, history and compatibility. Sandbox tenants do not become
production tenants. The previous build/commit is the rollback artifact; this change
does not deploy or authorize a production migration.

The bottom sidebar account disclosure (Spec 143 FR-007) shows the signed-in user's
name/email and links to personal preferences, configured Documentation and Website
origins, and Sign out. The native popover supports keyboard/outside dismissal and
small screens. Logout uses the shared authentication endpoint; duplicate submission
is blocked, errors remain visible and only success navigates to login. Company
settings remain in company navigation.

Personal preferences are reached through the profile menu and rendered with a
separate Profile & preferences header. They have no company tabs and do not
highlight company navigation. Account preferences and appearance form the first
card; the working company's AI usage follows in its own Usage card on the same
page, with no extra navigation step. The dedicated Settings → Usage page stays
reachable for the chat links that open it when the allowance runs out.

Company navigation uses **Companies** and always opens the authorized company list
with the active working company marked. Owner/member roles are explicit. Owner rows
offer Manage users, Agents & API tokens and AI configuration as focused modals,
each clearly naming its target company. Opening management does not change the
working company or navigate to another application tab. Only Switch company changes
the working context. Members see ownership guidance; direct management URLs open
guarded dialogs and cannot bypass owner authorization. Busy/uncertain mutations
prevent dismissal. New company is a top-right action opening a modal with review
and confirmation. Existing service authorization and API scope remain authoritative
(Spec 143 FR-009–011).

The standalone Your work navigation/list is retired. Home opens the Commitments
register; row activation opens the operational commitment detail within Orders &
deliveries. The register stays mounted so filters, paging, layout and scroll position
are retained on return. Customer actions and supplier receipt actions use existing
services. Exceptions, chat, warehouse and reports open the same detail. Old /app/work
links redirect without writes to the register or selected detail. This supersedes
the separate work list and its automatic initial selection (Spec 143 FR-013).

### Integration preparation — Spec 144

Integrations opens My integrations with an Add integration catalog for Shopify, Shopware 6, Xentral, Shopify Payments, Stripe, PayPal, HubSpot, Salesforce, Akeneo and Pimcore. Search and categories lead to a native modal for instance name, intended data and review. These are planning choices, not claims of supported connector features. Drafts are personal, scoped to user/company and retained only in browser session storage. They can be reopened, edited or removed; they do not register source systems, collect credentials or synchronize data. Shopify Payments asks for a related shop name as planning context only. Existing registered sources, source configuration, received records, document evidence and CSV import remain available separately. No domain model or service contract changes.

Spec 144 FR-007 restores the shared register footer for non-selectable tables, including Received data and Documents. Page size and pagination appear once below the table, aligned right; only selectable registers expose selection/export tools.

Spec 144 FR-008 simplifies Integrations navigation to My integrations and Received data. Received record details show the unchanged source payload, import status and actual tenant-scoped links to supported parties, items, locations, movements, documents, observations, ledger entries and business events (100 per family, with truncation indicated). Events link onward to their recorded subjects; this is recorded provenance, not a claim that the source created every linked entity. Missing links are explicit. Historical document URLs remain a contextual register with a back action; Documents is no longer a primary integrations tab.

Spec 146 supersedes the unified-app blanket refusal of owned practice companies. Authorized practice companies open in the unified app with a compact Sandbox badge beside the company name; existing server-side tenant and mutation policies remain authoritative. Retired /playground browser URLs remain retired, and no old workspace is reinstated.

Company overview cards group identity, company/demo/Sandbox labels, current connection state, role and company-specific management actions within one visual boundary (spec 146 FR-022). Ordinary-company bootstrap shape remains compatible; extra profile/source labels are optional Sandbox metadata read through the shared service.

Spec 146 FR-023: first and later creation use one goal-based choice: Start your own company, Create an empty Sandbox, or Try demo data. Only the demo choice shows optional Enable live simulation; switching away clears it. Eligibility filters available choices. The existing environment/content/live_simulation API contract is unchanged.

Spec 146 FR-024: name is visibly required with helper text. Create remains actionable when the name is missing; empty/whitespace submissions show a localized inline alert and focus/scroll the invalid name field without a request. Correction clears the message and startup/live choices remain intact.

Spec 146 FR-025 supersedes the post-creation ready/profile/action menu: a ready result automatically enters the new company and shows a dismissible creation confirmation there. A recovered ready receipt also opens automatically. Opening failures preserve the request and expose a retry without a new creation/start action. Integration management stays in Integrations.

FR-026–028: the shell labels Sandbox beside the company name. Reports and contributor reads accept authorized practice tenants without changing mutation or admission policy. Demo Data presents state-aware primary controls and a latest-25 activity widget; five-second visible-page refresh only reads data. Recent snapshots use `imports?recent=true`, ordered by persisted import `created_at DESC, id DESC`; `has_more` labels truncation and no cursor is returned. Default history cursor behavior is preserved. Entries expose actual creation/completion times and held document numbers; next arrival is a scheduled time, not a guaranteed execution. Failed refresh retains existing data with a stale warning, and polling preserves input/confirmation state.

FR-029 moves the controls/live widget to `/app/demo-data?tenant=…`, reached by Demo Data immediately below Companies in the Company group for demo-profile companies or those with a Demo Data connection state. Integrations no longer embeds this panel. The dedicated route preserves service eligibility and tenant scope. This supersedes earlier descriptions placing the widget inside Integrations.

Home activity and nontechnical service availability follow [spec149](../specs/149-home-live-status/spec.md)
and [the durable contract](features/home-live-status.md). Readiness never implies
success of every import/action; stale or missing signals cannot produce all-ready.

Home activity range defaults to 24 hours. Explicit 24-hour/7-day/30-day selection is remembered per authenticated user in the current browser across company changes and reloads. Invalid or unavailable browser storage falls back safely to 24 hours; this display preference does not synchronize between devices. See spec 149 FR-012.

## Home category naming

Daily work lists Home, Commitments, Exceptions and Decisions. Home cards repeat the
last three labels with a localized open qualifier below each existing count. All languages
use Commitments, Exceptions and Decisions (spec 208 supersedes the localized labels of spec 151). Menu and cards share exact
destinations, reset stale filters and preserve company context. Commitments retains
the existing open customer-delivery scope; no new business count is introduced.
See spec 151 FR-001–002.

## Inspector navigation (spec138 FR-029)

The four Inspector destinations are Business Graph, Business Facts, Event history and Available actions (spec 218). Business Graph offers Timeline then Record graph. Business Facts is one paginated register with a type filter; a secondary, lazy Technical record overview retains raw grouped records. Its tabs are All records, Calculated views and Fact rules; calculated views are explicitly derived results, not newly stored facts. Exception rules are a tab of Exceptions beside Open exceptions. Old records links resolve to the unified register with their query and tenant preserved.

Facts is an umbrella navigation term for recorded business information, not a change to the typed Fact model. The technical Fact family is labelled Additional facts in the type filter; sources, evidence and operational records retain their distinct identities and authority. The rules that create those records follow the same label: the Business Facts rule tab is Fact rules (German Fact-Regeln, spec 218), and every UI sentence about such a rule says Additional fact rule, so the register and the rules that fill it use one name (spec 191). The rule type itself, its commands and its tool descriptions keep the technical name Fact rule.

## Consistent page introductions (spec 137 FR-009/010)

The compact global header retains title and tabs. Every application's middle content
area starts with the same white rounded introduction surface: small accent icon,
view title, one translated subtitle and existing page actions aligned right. Mobile
stacks the actions below the text. No duplicate explanations or About this view blocks
appear below it. Contextual errors/restrictions remain. Search submits stay in their
forms; Save preferences retains native form association. Sticky sidebar/chat offsets
follow the measured global header height.

Global-header subviews use transparent, square-edged tab controls with a 2px accent
underline on the active tab, replacing the former rounded selection pill. Existing
navigation, focus behavior and narrow-screen horizontal scrolling remain (FR-011).

## Daily work lists (152)

Daily Commitments opens an open-only task-style list with Customer side and Supplier
side tabs; unfiltered side counts and filtered header counts come from shared delivery
reads. The general Orders & deliveries register remains separate. Exceptions groups
compact current findings by canonical severity. Decisions lists pending proposals
oldest first, with SQL tool/search filtering and existing explicit review/confirmation.
Each list initially requests 50 records and loads more on demand; changing filters
resets the loaded result. Details use an accessible side dialog, preserving list
position and keyboard focus. Underlying reality changes, not checkboxes or dismissals,
remove completed work. No client derives business quantities or merges unrelated findings.
Existing exception evaluation still derives all tenant findings before paging; this
known backend scaling limitation is not solved or hidden by the new presentation.

## Operational accounts (148, active unified integration)

Companies settings includes an Operational accounts section for the selected company. Owners review and confirm account creation, code/name edits, blocking/reactivation and role-default changes; members see configuration without an editable form. Active practice companies admit the same bounded owner operation. The existing finance journal displays concrete account code/name while keeping its operational-role filters and evidence inspection. No financial statements or tax engine is introduced. See [integration proof](../specs/148-accounting-journal-cost-centers/verification-results.md).

## Available customer and supplier credit (spec 148)

Finance → Open items offers Available customer credit and Available supplier credit
alongside the existing invoice and customer-credit-note filters. These registers
show active payment/credit-note origins, party, account, original amount, used
amount and available remainder; each currency has its own totals. Explain opens
the original evidence. Availability derives through the shared finance service
from both endpoints of effective allocations, including refund consumption and
reversal release. This is a read-only extension; accepted-discount and guided
payment-credit refund actions remain separate planned work.

## Confirmed settlement reductions (spec 148)

Company owners can select Accept settlement reduction on an open customer or
supplier invoice. Enter an explicit amount and reason; supplier reductions also
require documented entitlement/agreement. Review shows original open amount,
accepted reduction, remaining claim, concrete accounts and zero cash change.
Confirmation creates separate evidence and noncash postings. Pending review keeps
its proposal identity across dialog reopening/reload; unknown confirmations retry
that identity. Journal reversal remains independent from actual payment.

Account settings can explicitly initialize missing reduction defaults, preserving
existing selections. Absent or blocked counterparts prevent new acceptance.
No combined payment editor, automatic discount calculation or tax recomputation is
implied. The earlier available-credit read-only boundary describes that slice only.

### Categorized capability discovery (spec 158)

The unified application uses the validated `action_discovery.json` metadata returned
by application-reference for category ordering, canonical Command paths, explicit Web
form variants and contextual/global placements. Workspace Actions inherit the category
of their existing Command relationship. The Inspector Action catalog is one searchable
business-area/subgroup/entry directory with Action/Command badges, unique counts,
keyboard disclosures, expand/collapse controls, and preserved details. Search reveals
matching ancestor paths and clearing it restores manual branch expansion.

Adapter support does not imply a registered Web form. A general movement Command
exposes the supported opening-stock, receipt and shipment variants explicitly; other
capabilities keep documentation and actual management destinations where available.
Commands without a registered form are labeled honestly. No generic executor exists.

Global menus group registered forms and management destinations using the same
metadata. Warehouse menus vary by Stock, Reservations and Movements. Finance menus
respect tab and customer/supplier context; supplier contexts never present customer
credit/refund forms. Existing row targets, eligibility, service previews and human
confirmation remain unchanged. Dedicated administration/Rules/Demo Data controls remain
on their existing pages and retain their existing authorization and source controls.

See [spec 158](../specs/158-categorized-action-discovery/spec.md) and its
[coverage inventory](../specs/158-categorized-action-discovery/inventory.md).

## Guided payment and available-credit actions (spec 148)

Company owners can open Record payment and allocation from an open customer or
supplier invoice. The actual stated payment and explicit invoice allocation are
separate inputs; optional accepted reduction requires its stated amount/reason and
supplier agreement. Ordinary payment remains available without reduction accounts.
Available-credit rows open matching invoice allocation or actual refund recording.
A refund records observed money and never initiates a transfer. All operations use
one server preview and owner confirmation; pending proposals survive reload, and
receipts link to separate cash/reduction evidence and the original invoice/credit.
No browser calculation or stored document settlement state is added.

### Guided Fact-rule authoring (spec 159)

Inspector → Business Facts → Fact rules retains the shared register and modal while restoring
structured source/subject mapping, recursive all/any conditions, typed output, allowed
values and observation-time controls. Raw rule JSON is absent from the dialog. Editing an existing
version preserves its logical name, scopes, line ID path and advanced configuration
from its matching implementation proposal; it never silently changes the active rule.

Source search can attach a held field/value as evidence with its opaque source identity.
Manual observations, actual recommendation reasons/limitations and alternative model
destinations use the existing reviewed service calls. Source search and simulation are
read-only. Other operations require explicit review/confirmation and existing role checks.

Version definitions, execution counts and simulation counts/examples are readable.
Simulation previews up to 100 sources, and does not promise all matches create new Facts.
Activation requires successful simulation of the exact version in this UI. Historical
replay is offered for active versions in explicit confirmed batches using the returned
cursor and cumulative counts; there is no browser replay loop. Unknown writes lock
further mutation pending reload/inspection. Tenant, rule and modal state remain isolated.

See `specs/159-guided-fact-rules/spec.md` and its verification evidence.

Spec159 usability refinement: Edit initializes from the latest draft, otherwise the
active/latest version, before the first visible form frame. Initialization happens once
per selected question, preserving subsequent edits. Questions without versions say
Set up rule. A localized sentence describes the current form without inventing missing
source/characteristic/value selections. The editor uses When does the rule apply,
What should be remembered, and Check with examples. Group mode appears only for multiple
conditions; scopes, types and mapping fields remain under Advanced settings. Held source
system names are offered as optional native suggestions, preserving existing/custom codes.
Supporting examples remain in step 3; supplementary context/history are collapsed. The scrollable dialog body
has a persistent cancel/review/confirm footer. Tests explicitly refer to saved versions;
there is no unpersisted simulation or automatic activation.

## Opening residual positions (spec 148)

Company owners can open Import opening positions from Finance. A native dialog accepts
1–100 individual rows or one summary per party/direction/currency, with a previous-system
namespace, snapshot reference, cutover and explanation. Four explicit directions cover
customer and supplier debt/credit. Parties and accounts must already exist. Optional
original totals, dates, due dates and source identities remain visible original evidence.
A missing neutral opening counterpart points to company account settings.

The server review shows exact residuals, totals by direction/currency, neutral counterpart,
source coverage and unknown due dates. Preparing and rejecting creates no balances.
The confirmation proposal survives reload; its receipt links each evidence Document.
Open debt and available-credit registers show opening origin and reuse the shared
payment, reduction, allocation, refund and reversal services. No file upload, automatic
historical reconciliation, actual transfer or general-ledger reporting is implied.

## Managed finance references (spec 148)

Companies settings includes Finance references beside Operational accounts. Members
can search defined cost centers, case codes and coding groups, filter active/blocked
state and inspect paginated history. Owners prepare create/name/status changes with
a reason, review server before/after snapshots, then explicitly confirm or cancel.
Pending review survives a tab reload. Codes/kinds are immutable; blocking preserves
identity and prior decisions. Each history row exposes reason, actor and action.
Lists/history are shared service reads, not client projections. Component assignment,
amount splitting and country/tax mapping are subsequent slices.

## Received financial components and internal attribution (spec 148)

Finance → Open items exposes Financial detail for customer/supplier invoices and
credit notes. The native dialog separates received document totals, selected line
values and internal assignment. Documents with lines use line attribution exclusively.
Original source codes and existing document/line/source Inspector links remain visible.
Owners select defined case/coding references and enter explicit cost-center amounts
against a received net, gross or other stated basis. Shared server previews show
before/after, assigned and unassigned amounts; missing values remain unknown.
Confirmation survives reload. Historical revisions retain labels, reason, actor and
action. Members can inspect without editing. No posting or tax calculation occurs.

## Operational transaction matrix (spec 148)

Company settings → Operational accounts → Transaction matrix shows fourteen fixed
operations with debit/credit roles, stated amount bases and current configured default
accounts. Missing/blocked defaults remain visible. The settings link and refresh use
existing account controls and shared reads; confirmed account changes refresh this
view. It is descriptive configuration, not transaction authorization: actual evidence,
original settlement accounts and confirmation are validated by existing actions.
The responsive view offers no posting-rule or tax-calculation editor.

Mobile registers below 640px retain their in-flow footer. Desktop viewport measurements must not pin it over rows when finance filters and summaries consume the viewport; row actions remain reachable through normal scrolling.

FR-011 refinement: Step 3 combines supporting source examples and saved-version tests. Supplementary context/history remain under Further details. Raw technical rule definitions are absent from authoring and confirmation. Evidence selection does not filter the bounded simulation preview.

## One page action bar (spec 165)

Every page reaches the header action slot through one shared bar. The page's first action
is its primary button; one further action stands beside it as a plain button; two or more
further actions fold into the existing keyboard-accessible More actions disclosure; a page
without actions leaves the slot empty, never an empty menu or a placeholder. Companies (New
company), Integrations (Add integration on Source systems with Register source and Import
items behind More actions; Register source with Import items beside it on Received data and
Documents), Master data (New customer, New supplier, New item, New location), Sales and
Purchasing orders, Warehouse, Finance, Rules (New rule) and Exceptions (View all possible
findings) declare their actions this way; discovery-backed pages keep the catalog order,
placement filtering and Web eligibility of spec 158 and render nothing until the metadata
has loaded. The register toolbar carries no action slot; the explicit Search submit of
Facts and Inspector records stays beside its field. Notes and form buttons are not page
actions: the Decisions sorting note sits in its filter row and Save preferences ends its
form with native form association.

## Consistent register title counts (spec 160)

Main register totals use the shared page-title badge, including Sales/Purchasing,
Warehouse, Finance, master data, sources, Inspector records, rules and catalogs.
The previous above-table count line is removed. Counts retain existing filter and
pagination semantics, localized formatting and explicit zero. Nested technical
overviews, category counts, report details and standalone surfaces retain local counts.
No new count query or alternative business calculation is introduced.

Spec160 FR-005–006: Existing page-specific tabs now sit directly below the page
introduction and above search/content. This covers Sales/Purchasing, Warehouse,
Finance, Master data, Integrations and the Inspector sections. The global header
contains global controls; the introduction supplies the single visible h1.
Compact text tabs use a shared bottom separator, accent underline and horizontal
scrolling at narrow widths. Existing labels, routing, selection and count semantics
remain unchanged. No tab row appears on pages without subviews.

Spec160 FR-007–009 supersedes the large introduction card: page title, list count,
compact always-visible description and page actions share the compact 60px top row. Tabs
stay at the top of main content. At compact widths one menu exposes the same
page actions and global controls; controls are mounted only once, and the company
switcher stays beside the logo at every width.
The superscript count badge remains visually subordinate and separated from the
description; it grows from a circle to a compact capsule as digit count increases.
Long page titles and descriptions truncate visually without losing their full text.

## Source code classification (spec 148)

Company settings exposes Source code mappings for case/group references with exact registered source, namespace and code. Owners review and confirm replacement or blocking; pending review survives reload and history preserves previous decision state, destination labels, author and action. Financial detail shows current source classification separately from internal assignment, including missing/malformed/unmapped/blocked/conflicting cases. No inference from country, tax rate or text; no source, assignment or ledger write from a read.

Finance configuration has one canonical home: the Finance workspace Settings tab
(`finance_view=settings`). It reuses the operational account/matrix, reference and
source-mapping editors. Company settings contains company/access management, without
duplicate finance panels. Settings mounts no operational finance register, search,
counts or posting actions. Shared action discovery links target the Finance tab;
selected company scope and existing owner-confirmed mutations remain unchanged.

Within Finance Settings, a vertical area menu selects Accounts & account mapping,
Cost centers, Case codes & coding groups, or Source code mappings. Mobile uses a
labeled area select. Only the selected editor is mounted, shown without an outer
accordion. `finance_settings` persists the area in URLs. Reference kind choices and
pending-review recovery are scoped to their area; the business commands are unchanged.

Finance settings form actions use content-width buttons in their own footer below all
fields. Account rows expose compact Edit and More actions; the native top-layer popover
contains block/activate and eligible set-default actions, without table clipping.
Default is a status badge. Row/history actions are compact and coarse-pointer targets
retain 44px minimum height. Existing confirmation and owner boundaries remain unchanged.

## External accounting configuration (spec 148)

Finance Settings → Accounts & account mapping distinguishes Operational accounts from
External accounting. The latter owns target selection, external account/tax catalogs
and reviewed mapping rules. Received-component rules and operational-account references
are separate scopes. Compact content-width actions, searchable paged choices and
owner confirmation reuse the existing interaction model. Target-specific pending
reviews survive navigation; members can inspect but cannot maintain configuration.
Financial detail exposes read-only target mapping preview, with explicit missing or
blocked classifications/destinations. Mapping resolution never asserts export readiness
or remote posting. The complete bounded contract is spec 148 target-mappings.md.

Finance settings editors follow the existing Company settings and operational entry
dialog pattern (spec148 FR-059). Each area starts with a list and a named create
action. Editing and immutable history open separately in native dialogs using
existing surface, br-control and br-btn tokens. Fields include contextual help;
create/edit forms are never permanently displayed below lists. Preparation and
confirmation retain the shared commands. Dismissing a pending review keeps it
available through Continue review. Dialog errors are visible, busy operations block
dismissal, and closing unsubmitted input produces no write.

Operational accounts uses a compact Add account action in the list toolbar and explains automatic role defaults. View account usage opens Accounts for business transactions in a native dialog, with the existing operation/role/control-policy data. Owners can choose Change default for a role and select an active eligible account through the existing reviewed command. The dialog explains the shared-role effect and preservation of historical accounts (spec148 FR-060).

External accounting starts with an accounting-target list. Open account setup enters the selected target; Back to accounting targets returns to the list. Creation and editing use existing native dialogs. Empty lists explain the next step without unused search or pagination controls (spec148 FR-061).

Finance settings list toolbars share left contextual controls and a right-aligned named create action. Card/help spacing, filter sizing, empty-state treatment and conditional pagination are consistent across operational accounts, references, source mappings and external accounting (spec148 FR-062). Existing shared dialog footers retain their action order.

Finance settings distinguish empty catalogs from filtered no-results: only populated catalogs expose list filters; no-results preserves filters with Reset filters. Area selection remains available; switching reference kind clears query/status/paging. Empty account catalogs omit table headers (spec148 FR-063).

### First-time Fact rule wizard (spec 177)

New rule and never-activated questions use five stages: choose a goal, find a real
example, describe the rule, test with existing data, and review/activate. Editable
starters and contextual explanations establish what to enter before the first write.
The goal is explicitly a documented question, not an active rule. Each subsequent
write retains its own review and action-specific confirmation. Back and stage changes
never save, simulate, activate or replay implicitly.

Evidence comes from held source values with original source links; recommendations
and non-Fact handoffs retain the existing service behavior. Configuration reuses the
structured editor and sentence preview with progressive mapping details. Tests run
only on a saved immutable version, cover up to 100 matching held sources and are not
filtered by the selected supporting example. Editing clears the test; saving and
testing the new version is required before its activation can be reviewed. Zero
matches and problematic outcomes are explained without inventing successful coverage.

Closing preserves only saved milestones. Reopening a draft resumes testing, with no
assumption that it was already tested. Unknown writes lock further mutations pending
inspection/reload. Activation applies to future matching intake; historical replay
remains a separate confirmed action. Active or previously disabled rules keep the
existing version-management workbench. The wizard preserves company/role boundaries,
keyboard focus, reachable mobile actions and en/de/nl/es localization.

## Stored projection freshness (spec 179)

The Calculated views directory reuses validated application-version metadata in
memory and mounts collapsed details on expansion. Uncached catalog validation
remains available to tooling. This global cache contains no tenant data and does
not replace tenant admission.

`/projection-snapshots/{name}` returns up to 100 stored rows and metadata in one SQL
snapshot. Paginated projection views and invoice-side open items likewise return
rows, count, currency totals and metadata from one SQL statement. Metadata names
the completed event target/time and `uninitialized`, `ready`, `pending` or `failed`
state; upstream freshness stays unknown. Missing initial data is awaiting
calculation, not confirmed business emptiness. Older completed data stays visible
with its timestamp and read-only Refresh action. Confirmed actions use the existing
shared read refresh notification. The browser does not run projection jobs.

The directory distinguishes stored results, live views and parameterized pricing.
The Inspector's stored Payments projection is distinct from the existing live
Payments screen, whose row and total derivations use canonical live payment data.
Explicit live MCP read contracts retain their consistency semantics. Price answers
come directly from the canonical parameterized pricing service without a cache
write or unrelated rebuild. Actions still validate authoritative Reality.

## Storyline (spec 182)

`storyline` is a unified destination (`/app/storyline?tenant=…&chapter=…`) with a shell
navigation item. A company without a storyline run shows the library: one card per built-in or imported
storyline with its step count and summary, the position and sandbox name of a running one
as a progress line, one primary action (Start, Continue, Open) and a folded menu with
download, draft export, a fresh start in a new sandbox and removal of imports. Import is a
secondary entrance behind one button (validated first, errors listed in full). The library
speaks of sandboxes, the app's own word for practice companies. Starting a storyline
creates a sandbox and opens it.

A company with a run shows three zones: the narrator (chapter list, situation, preview,
confirm and discard, what happened, expected against observed findings, branch choices,
next chapter), the stage (the live view the chapter names through the shared reads, added
rows marked, a link to the full page) and the protocol (every call of the chapter with
input, result and its catalog explanation linked to Tool Usage; what the chapter added:
events, Facts, records, findings raised and cleared, the Context Graph). Every item opens
its ordinary surface: Inspector, Facts register, Exceptions page. Confirmation goes through
the storyline routes only; the ordinary action card is not used on this page. The chat dock
is closed when the destination opens so the three zones have the width.

Free play is a browser-only mode carried in the chapter slot (`chapter=free`): the narrator
gives way to a note and "Back to the story", the protocol lists the calls made outside any
chapter and a picked confirmation shows what it added. A blocked chapter names the missing
record or finding and offers a fresh company. Autoplay for a presentation is one small control at the foot of the step card ("Play
automatically" / "Stop autoplay"); it issues the same prepare, confirm, branch and next calls
a person would click, and any click elsewhere or an error switches it off with a short note. The
language switch of the profile re-renders the texts of a run without touching its trace.

## Declared Analytics workspace (specs 224 and 228)

Analytics offers My reports (default), Analysis and Explore data. Analysis starts with
Create with chat, Use a template and Build it yourself; templates are an inline entry
and open unsaved drafts. Legacy template links open this entry inside Analysis.
Spec228 replaces spec224's result-first browser presentation with colored sentence controls, removable conditions, and Result / Connections / Cypher tabs.
The owner’s design refinement removes the separate heading/status and question/examples
panel and aligns Builder and Explore data with the shared flat application design.
Spec221's Overview and spec185's configured dataset explorer remain retired.

The sentence edits the declared traversal, with branching paths, multiple measures,
required currency/unit axes, periods and filters. Result tables retain filtering,
sorting, limits and derivation. Summary cards identify returned-row scope, selected
measures and last successful read, never fabricated business totals. Connections show
actual branch origins and directions; selecting a node exposes fields and filters.

The shared, metered `graph.interpret` capability remains available to tools. Browser
templates and sentence controls work without a provider. Validated output is executed by `graph.ask`; unavailable or
unsupported questions explain the refusal. Generated Cypher-near text and parameters
are editable; unexecuted drafts survive tab changes and failed reads. Advanced `having`,
`exists`, recursion and ordering remain preserved in expert mode, with explicit reset
required before simplifying. Old responses cannot replace a newer query or company.

Explore data shows real catalog counts, searchable objects/fields, declared relationships
and bounded tenant-scoped previews. Use in analysis, Add field and Open path seed unsaved
questions; browsing the catalog preserves the existing builder draft. Layout wraps on
compact screens, with local scrolling for wide tables and diagrams; all new copy is localized.

Private reports store the checked question and model version, never the answer. Explicit
save retains ownership, revisions and retry keys; reopening re-executes it. Invalid expert
drafts cannot save an earlier query. Reports from the configured generation remain unread
and are never overwritten. See [the shared contract](features/analytics.md),
[spec224](../specs/224-native-reporting-platform/spec.md) and
[spec228](../specs/228-guided-analysis-builder/spec.md).

Spec261 makes that explicit save visible and named. The save controls render on the
analysis rather than in the page header's "More actions" menu, and the naming field
opens where the control that opened it was, focused, with a suggested name selected:
a template's own label, the name the copilot proposed, or one composed from the
analysis in the reader's language (records, measures, axes). New analysis and Use in
analysis are likewise shown flat. The analysis states which report it is and whether it
is saved — saved report, unsaved changes, or draft — and a successful save shows the
analysis as that saved report, records it in the address so a reload reopens it, and
links to My reports. A report proposal's preview resolves the report its change
concerns, through the retry key the report row already records, so a confirmed proposal
offers the saved report instead of an unsaved copy of its question. A template states
that adopting it fixes its window to dates. No stored field, endpoint or business rule
changes. See [spec261](../specs/261-analytics-save-clarity/spec.md).

## Public-site privacy and language handoff

Public-site privacy (static legal pages, navigation-only language) is owned by the
provider's marketing site, which is not part of this repository. It defines
essential-only processing and publication evidence (spec 188). Explicit presentation
language travels through URLs rather than durable anonymous browser storage. Existing
account preferences, authenticated sessions and shared application services remain
authoritative and unchanged. Product/Docs processing is a separate review boundary.

## Free trial prospect entry (190)

[Spec 190](../specs/190-free-playground/spec.md) adds explicit ordinary-signup consent for an owner-private canonical demo. Verified admitted prospects enter Home without a company questionnaire. Retry uses the existing setup receipt; GET never creates. Three read-only tasks lead to existing operational evidence. Optional GitHub support follows a rendered result, and managed AI shows its account-wide 20-question UTC-day allowance. Public copy promises a free trial, no initial expiry, no card and no automatic paid subscription; it does not promise permanent free access. See [company setup](features/company-setup-demo.md) and [chat](features/chat.md).

Spec 190 FR-010: Entry waits (session, workspace and trial preparation) show an immediate localized spinner and explanation. Signup/verification submissions stay busy through navigation; errors restore retry. Email verification performs one navigation and language survives the signup handoff. Operational read skeletons retain their existing behavior.

Spec 190 FR-011 supersedes the paid Cloud presentation: the platform card advertises only the currently available free trial, its daily AI allowance and no initial fixed expiry. Monthly/founding prices, usage purchases and the capacity/waitlist banner are absent. Backend admission configuration remains authoritative.

Spec 190 FR-012: Packages ends after the hosted trial and self-hosted choices; the agent-ecosystem architecture block and compatibility footnote are removed from that page.

Spec 190 FR-015: Public pages share more readable heading spacing, responsive section rhythm and consistent free-trial CTA labels/colors. The platform trial note stays with the introduction; existing light/dark surfaces and route behavior are preserved.

Spec 190 FR-018: How it works presents the core flow and worked delivery example first. Native disclosures retain vocabulary, finance, corrections, background and FAQ; all depth is keyboard-accessible and the existing entry anchor targets the compact process flow.

Spec 190 FR-019: Verification mail links reopen the Product App with the recipient in a scrubbed URL fragment. The code remains mandatory; missing tab state permits email entry and the existing resend action. No verification occurs on navigation.

## Storyline Free Play chat (spec 195)

Free Play embeds the normal company chat and composer, including provider, allowance,
voice input and ordinary proposal review/confirmation. Own words entered in the
scripted narrator arrive as an editable draft; switching modes never sends.
What happened on each assistant reply lazily reads exact recorded calls and later
decisions linked by proposal ID. No timestamp-based attribution. Missing/pruned
evidence is explicit. The existing marker delta is labeled as changes since the
call and may include later Sandbox activity; it is not exclusive causal attribution.
Chapter progress remains unchanged and Back to the storyline remains available.

Spec 195: independent `/app/free-play` is separate from guided Storylines. One library
tile opens chat directly in the company selected in the main navigation. Opening it
is read-only. A real-data notice distinguishes ordinary companies; all changes keep
normal confirmation. Reload preserves the opened company. What happened explicitly
reports unavailable evidence outside eligible recorded Sandboxes. Individual story
cards have no Free Play buttons. Contextual story chat remains Sandbox chat.

The Storyline narrator footer has no Free Play/Sandbox chat shortcut. A full-size
Back to selection button returns to the exploration library, emphasized after
completion. Existing contextual draft handoff remains compatible.

The standalone Chat feature appears directly after Home in Daily Work. It has its
own active navigation state. Storyline contains guided stories only.

Pending chat requests show a prominent accent status panel above the composer with
a rotating indicator and Reality is working label. Reduced motion stops rotation;
role=status announces the label. Success and failure remove the status.

Chat turns use neutral right-aligned user bubbles and left-aligned unboxed assistant
responses with bounded reading width and distinct spacing. Author/time metadata is
accessible without visible labels. Pending echoes share user styling; per-reply
evidence stays underneath the associated answer.

AI allowance lives in the chat header (the outer header for Free Play). Its Usage
popover exposes used/remaining counts, reset time and a link to Settings → Usage.
The settings view uses the existing authorized allowance read; no unreported tariff
or upgrade link is shown. Only exhaustion appears next to the composer, with reset
time and send restrictions preserved.

Free Play uses a viewport-bounded shell and content area. Only the message history
scrolls during chat; app/chat headers, navigation and composer remain in place. The
chooser and navigation retain their own overflow for small screens. Other routes
keep their existing document scrolling.

An opened Free Play chat has an unframed full-width surface and a 48px toolbar
with the Free Play title and usage. Company selection lives only in the main navigation.
New conversation is a labeled button above the saved sessions. Company-scoped conversations appear in a left column in the
surrounding gray area, with the current conversation highlighted. Narrow screens
use a history button and dismissible drawer; selection closes it. The opened chat
has no Storyline link or inline conversation dropdown. It has no second conversation header.
Controls retain accessible labels on narrow screens.
Other chat surfaces retain their existing header.

At zero allowance, Free Play replaces the composer with a compact limit/reset status.
Header Usage retains the detailed disclosure. A refreshed positive allowance restores
the composer. Other chat surfaces retain their existing exhaustion presentation.

## Auditable AI extensions (spec 196)

Settings → Usage shows daily consumption, available questions and the scheduled
reset. When eligible, one Reset usage button and a short invitation let the user
continue chatting. Its explicit click confirms the self grant; no preview, lifetime
counter, recipient lookup, mode selector or history is shown (spec 196 FR-007).
Each managed-AI account has three lifetime self extensions of 20 questions, only
after exhaustion. The server enforces this across companies and days. Admin grants
and attributable history remain available through the authenticated APIs.
Every grant is retry-idempotent and recorded with actor/recipient IDs, amount,
reason, time, expiration and self/admin mode in the existing security audit.
Consumption is never erased. Extra questions expire at the next UTC daily reset.
Open chat allowance refreshes after a grant; failures retain the request identity.

Spec 195 FR-017 supersedes the Free Play chooser and company-picker descriptions
above: Free Play opens directly in the company selected in the main navigation.
There is no separate company switcher or Sandbox creation action inside Free Play.
The global company switch retains the Free Play route and clears the prior chat
session, draft and evidence. The library tile and page introduction explain this
shared context. Existing Sandboxes remain available in the main company switcher;
normal company creation and backend compatibility services remain unchanged.

Spec 195 FR-018: Chat is a main product feature at `/app/chat`, independent of the
Storyline library. Former `/app/free-play` bookmarks redirect to Chat, preserving
company and session while dropping action-like query parameters. The sidebar entry
uses a speech-bubble icon directly after Home. The library no longer offers Free Play
or describes Chat as a Storyline mode. Global company context, chat history, usage,
confirmed application tools and optional recorded evidence remain shared services.

Spec 195 FR-019: Standalone Chat uses the full content area without outer page
gutters or an inter-column gap. There is no inner Chat title or desktop toolbar.
Usage is in the session sidebar; mobile retains its history opener. The empty
conversation greeting is vertically centered in its available message area.

Spec 195 FR-021: All cross-company navigation clears prior company-scoped context
before applying explicit destination values. This includes Storyline sandbox entry.
An invalid selected chat offers Back to chats for read-only recovery.

Spec 195 FR-022 supersedes manual missing-session recovery: a selected ChatSession
404 automatically replaces the session URL and reloads the current-company chat.
Other failure types remain visible; no records are created or deleted.

Spec 197: The main and side chats share a provider policy limited to Reality usage
and supported business workflows. Unrelated requests receive a brief redirect;
mixed requests answer the relevant part. Source/tool/conversation instructions
cannot authorize changes or broaden company access. Server tool permissions remain
authoritative; prompt behavior is not claimed to be immune to injection.

## Chat starter questions (spec 202)

Empty conversations show three localized question buttons beneath the welcome copy:
open customer orders, stock shortages for open orders and overdue customer invoices.
Choosing one fills and focuses the composer for editing and explicit sending.
Buttons are disabled while a draft exists or chat is busy; recorded/pending messages
hide starters. Native buttons wrap at narrow widths and retain keyboard access.

## Collapsible primary navigation (spec 203)

At desktop widths, a sidebar toggle switches the primary navigation between its
200px labeled layout and a 60px icon rail. Existing destinations retain localized
names and application tooltips, active state and keyboard access. Profile remains available;
the header keeps the company switcher beside the logo. Content expands into the
released space and existing page/chat state stays mounted. The browser remembers
the preference, with a safe expanded fallback if storage is unavailable. Below
1024px, the existing labeled mobile drawer remains independent of this preference.

The collapse control shares the Daily work heading row and uses a plain sidebar
icon. Collapsed navigation, profile and toggle hints use dark, rounded application
tooltips with white text, outside the scroll container. Hover and keyboard focus
show the label; Escape, scrolling, blur and activation dismiss it. Native browser
title tooltips are absent from these controls (spec 203 FR-005–006).

## Incremental chat replies (spec 206)

The ordinary Chat send can stream provisional text from the configured provider.
Each tool round resets that provisional text; only complete provider tool calls
reach the existing shared dispatch and proposal boundary. The completed persisted
answer replaces provisional output immediately, before metadata refresh. A failed
or disconnected response is never automatically replayed, and incomplete text is
not a completed message. Work already dispatched may finish and remain recoverable
through the ordinary conversation and proposal reads. Existing JSON clients remain
supported. Security policy, tenant admission, allowance and presentation preferences
are unchanged.

Static Anthropic tool/system prefixes are eligible for provider caching. All allowed
tools remain available, result serialization is lossless, and provider history reads
are limited to the latest twelve turns. Timing logs contain round/tool durations and
provider token/cache counts, never prompts, tool arguments or payloads. Inventory
observations use batched tenant reads with unchanged quantities and evidence links.

Spec 195 FR-023: The persistent desktop Chat history uses 36-pixel session rows
without inter-row gaps. Below 1280 CSS pixels the history drawer retains its
40-pixel session buttons and 44-pixel row spacing. Selection and options stay shared.

Spec 195 FR-024: Desktop Chat history is 288px wide. Archive/delete menu labels
remain on one line. Fine-pointer hover devices reveal options on row hover,
keyboard focus or while open; touch devices keep them visible. Row heights and
the mobile drawer width remain unchanged.

## Live simulation header (spec 207)

An eligible owner's current company shows a top-right Live simulation link only after
a fresh Demo Data read reports running without error/throttling. It opens that company's
existing Demo Data overview. Paused, stopped, disconnected, absent, failed and unauthorized
states show nothing. Five-second visible-page polling has an eight-second timeout and
cancellation on company change; old-company responses cannot populate the header. The
pulse is decorative and disabled under reduced motion. Narrow layouts keep the compact
link beside the overflow trigger. This indicates simulation state, not worker readiness.

## Canonical model vocabulary (spec 208)

The current product serves technical operators learning the Reality model. Non-English
navigation, Home categories, Inspector type selectors and related object links/search
labels retain English model nouns: Facts, Commitments, Reservations, Movements,
Exceptions, Decisions, Source Records, Documents, Document Lines, Ledger Entries
and Business Events, including singular forms. Context Graph remains invariant.
The Inspector Additional facts type is labeled Facts in non-English languages.
General business objects (items, business partners, locations), control verbs and
explanations remain localized. English copy, source payloads, formatting, routes,
filters, permissions and operational semantics are unchanged.

## Operational quick previews (spec 209)

Inline Inspector reads explicitly request business preview sections for documents, delivery commitments, items, reservations, movements, shipments/packages, payments and journal entries. The full explanation retains correction/provenance detail. Documents show labeled parties, received totals and SKU plus historical line descriptions; a current item-name fallback is labeled. Existing services supply effective fulfillment, holds, scoped stock, settlement and allocation. Missing data stays unavailable; original business names remain untranslated. Lists show up to twenty rows per section with an overflow notice. Mobile preview content is bounded to the viewport within horizontally scrollable tables. Named links open the full Inspector; footer actions and keyboard disclosure remain shared. No new persistence or business rules are introduced.

Spec 209 master-data extension: Master data is a Workspace link after Finance, no longer a Company link. Customer/supplier lists prioritize accounting code, payment term and currency; item lists expose item type and named default location; location lists show type, named parent and stock eligibility. Previews group the existing editable business fields and format monetary/quantity values through the shared Inspector presentation. Provenance and opaque identity remain in secondary details. Existing edit/revision confirmation, source inspection and customer-hold actions remain available. Related labels are resolved with tenant-scoped, page-bounded reads.

## ERP wording (spec 212)

German, Dutch and Spanish operational controls use ordinary ERP vocabulary. Detail actions and overflow hints refer consistently to all record details. Master-data headings describe general data, commercial settings, inventory and purchasing. Recording remains distinct from completion; settlement remains distinct from cash payment; customer holds explicitly concern delivery. Document previews use a separate Delivery progress heading, leaving model-oriented Operational Reality and spec208 canonical nouns unchanged. Source values and numeric/date formatting are preserved.

Spec 213: Projection freshness notices directly inside register surfaces have a 16px horizontal outer inset. Nested notices inherit their existing padded context, without a second margin. Preserve internal/vertical spacing, all freshness states and the refresh action on mobile and desktop.

## Localized exception and decision labels (spec 215)

Spec 215 supersedes the spec208 canonical-English rule only for Exception(s) and Decision(s). German uses Ausnahme/Ausnahmen and Entscheidung/Entscheidungen; Dutch uses Uitzondering/Uitzonderingen and Beslissing/Beslissingen; Spanish uses Incidencia/Incidencias and Decisión/Decisiones. Apply these names consistently to navigation, Home, page and Inspector labels, searches, links, catalog/rule headings, queue/history, empty states and helper text. All other model nouns retain the prior policy. English copy, original source values, technical identifiers and routes remain unchanged.

## Visible integration actions (spec 210)

Registered sources visibly offer Settings and Received data; received source versions offer Open details and View observations. The shared table's labeled presentation preserves localized text without hover or external-link icons, with action columns wide enough for both controls in normal and compact density. Narrow screens retain table-local horizontal scrolling and release the sticky first column in these labeled tables so it cannot cover the actions. Existing source configuration, Inspector and exact-source Facts destinations, tenant context and read-only activation remain unchanged. Other registers retain their compact preview controls.

## Business Inspector names (spec 216)

The former Context Graph area is named Business Graph; the Facts navigation area is Business Facts. Both names are invariant product labels in every language. Use the same names in shared section/page titles, tooltips, standalone facts-page headings and Storyline graph headings/captions/accessibility labels. Fact/Facts remain data-type names in selectors, individual records and Storyline fact counts. Existing routes, tabs, filters and technical identifiers remain unchanged. This updates only the area/product naming portion of spec208; spec215 remains applicable.

## Source labels (spec 217)

Data-source columns use Source rather than Origin, in every language. Source/Sources are invariant product labels; direct metadata/settings use localized Source compounds. Source Record continues to name an individual received record; related inspection actions and payload details explicitly use that name. The provenance groups in master-data forms/details are labeled Source. Source-system names, external IDs, technical origin fields, geographical origins and software-source-code terms are not rewritten.

### Inspector navigation by purpose (spec 218)

Business Facts contains All records, Calculated views and Fact rules. Exceptions
contains Open exceptions and Exception rules. Event history and Available actions
are separate Inspector destinations, replacing the ambiguous Rules and Actions
groups. Existing Inspector rule/history/action URLs remain usable; legacy exception
rule links open the Exceptions rule tab. Rule-to-finding links select open exceptions.
These presentation changes reuse existing services, permissions and action confirmation.

### Report catalog experience (spec 219)

Calculated views stays in Business Facts and presents a single list of reports with
visible localized business names, summaries and workspace tags. Search combines with
workspace filters. Entire rows are keyboard-accessible buttons opening the existing
read-only data dialog with a matching title and summary. Entries sharing exactly the
same projection target are combined; live registers remain separate from stored
snapshots. Availability comes from the application-reference catalog; unknown entries
retain the catalog description rather than disappearing. Price resolution offers
input/calculation details only and never requests an unparameterized data snapshot.
Report details contain the original technical definitions, code, documentation and
known application links. Existing tenant scope, freshness/error/empty states, preview
bounds, focus restoration and business logic remain unchanged. Copy is localized in
English, German, Dutch and Spanish; mobile uses the same list without page overflow.

## Compact daily work lists (spec 220)

Commitments, Exceptions and Decisions share compact rows. At 720px available list
width, ordinary rows have a 44px target with aligned title/context columns and
right-aligned metadata. Narrow lists retain stacked title/context and at least
44px targets. Container width accounts for side chat. Group spacing is reduced;
search and filters share one row when space permits. Existing font sizes, native
keyboard buttons, inline previews, grouping, ordering, filters, paging and all
business/confirmation semantics remain unchanged.

Spec 180 FR-009 refinement: stored-result Refresh retains its label and position,
with no dimming. Its permanent refresh-arrows icon stays static when idle and rotates for at least
one second after activation and until the read completes; reduced motion keeps it
static. No empty icon slot appears. Keyboard activation uses the same action. The last-calculated
timestamp sits directly beside the button in a wrapping row. Updated/unchanged and
checking feedback is screen-reader-only; no extra visible feedback row. Pending/failed
calculation state and backlog remain compactly beneath. Read errors stay visible and
never produce success feedback. Duplicate clicks remain disabled during feedback.

Spec 219 FR-006: Opened reports retain a visible title, summary and Close control while data scrolls. The catalog explanation is initially open in a separately scrolling right column on desktop. On narrow screens its disclosure is above the data and initially collapsed to preserve reading space; details-only reports remain open. Explanation access never requires scrolling through the table. Existing catalog definitions, code/docs links, readers and preview limits are preserved.

Spec 219 FR-006 sidebar refinement: show a single canonical calculation/view explanation. Code, documentation, alias-specific explanations and technical definitions are grouped under one initially collapsed Technical details disclosure, preserving all original links without repeating controls in the initial sidebar.

Spec 219 FR-007/008 supersedes the alias-card sidebar composition above. About this
report contains one business explanation, deduplicated workspace text links and one
documentation link. One collapsed technical section exposes canonical calculation,
source metadata, code and lossless catalog definitions. Aliases never render repeated
Details cards. Dispatch data uses business-first columns and localized dates/booleans;
other reports preserve unknown field fallbacks. Nested values open readable row details,
where opaque identities and exact original data remain available. Report tables have a
real final details action, neutral settings controls and no nonfunctional filter icon.
No new filtering, business calculations, source authority or service paths are introduced.

Spec 218 navigation refinement: Tools replaces Available actions in the Inspector sidebar and contains Actions (default) and Calculated views. Tools is invariant across languages. Business Facts contains All records and Fact rules only. Existing inspector_view=commands/views URLs preserve tenant context and now activate Tools; reload/history and report behavior remain unchanged. This supersedes the Business Facts ownership of Calculated views stated above.

Spec 219 directory refinement supersedes the custom report list/cards and workspace filter buttons: Calculated views reuses the Actions folder-tree component, toolbar, expandable groups and compact disclosures. Reports have one home under their first workspace category; all category labels remain in their details and search. Search opens matching groups without overwriting manual expansion. Expand all/Collapse all match Actions and are disabled while searching. A report disclosure exposes its description and Open report/Show details action. Existing dialogs, company context, deduplication and focus restoration remain unchanged.

Spec 195 FR-025: The side-chat header no longer duplicates the Usage badge beside
the conversation title. History and new-chat controls remain. Other usage entry
points, allowance reads and exhausted-allowance sending restrictions are unchanged.

Spec 223 company context supersedes both the Companies entry in the Company navigation
group and spec 146 FR-029's Demo Data navigation entry. Company management
(`/app/settings?settings_view=company`) is reached from the company switcher beside the
wordmark, which lists every company, marks each one's live simulation state, and ends with
Manage companies and New company. `settings_view=new` opens the creation form directly, so
the switcher entry, reload and history all land on the same form. The Company navigation
group keeps Integrations and Storyline only. The simulation keeps its own route
`/app/demo-data?tenant=…`, now reached from the header live indicator and from a Demo data
simulation card at the top of Integrations → My integrations, shown for demo and practice
companies and for any company with a Demo Data connection state; the card reports
connection state, rate and last successful import and links to the route. Integrations
still does not embed the control panel itself. No service eligibility, tenant scope or
write path changes.

## Refined workspace shell (spec 225)

Company identity, switching and the existing live simulation link belong to the
full-height primary sidebar. The page has a 48px header with title, inline count,
keyboard-accessible description disclosure and neutral chat toggle. Desktop side chat
starts at the workspace top with its own 48px header; standalone Chat and Storyline
do not reserve a dock column. The existing action launcher sits above Profile in the
sidebar; Appearance is in Profile. The Inspector history destination is named Activities
(German: Aktivitäten), preserving its history URL. There is no duplicate bottom Activity
entry or shell-owned drawer state. Shared timeline services and Home access remain. Native popovers keep menus outside
scroll clipping. Navigation and tabs use neutral active states and 13px text; page
headers use 14px medium text. Business content typography is unchanged.

The existing 200px sidebar/60px rail, storage preference, company isolation, chat
draft persistence, simulation eligibility/polling and shared services remain. The rail
retains company switching and global utility labels through tooltips. Mobile keeps a
labeled drawer and directly reachable navigation/chat controls. Touch targets remain
at least 44px. This supersedes earlier header placement and visual contracts only.

### Command palette presentation (spec 225)

The global action launcher is a centered command palette, opened with Cmd+K/Ctrl+K
or a quiet Search actions control in the sidebar company area with a shortcut hint.
The lower navigation contains Profile only. Empty search shows the same permitted,
grouped global actions and catalog shortcut; translated search and existing forms,
authorization and confirmation remain unchanged. Opening resets search and focuses
it. Escape restores prior focus. Another open modal takes precedence over the
shortcut. The palette is portaled outside navigation so keyboard access works when
the mobile drawer is closed. Expanded, rail and mobile pointer access remain.
Future command capabilities require a separate specification.

### Quiet shell boundaries (spec 225)

Workspace and docked chat headers have no bottom rule. Sidebar separation relies
on its background rather than a right border. Page tabs retain only their active
indicator, without a full-width baseline. The subtle vertical content/chat divider
remains, as do all existing content-table, list and form boundaries.

### Grouped sidebar head (spec 225)

Logo and company context share the company-switcher button. Desktop collapse sits
beside it; mobile retains Close, and the collapsed rail stacks company and expand
controls. Search appears below as a quiet field with short visible wording and a
platform shortcut; its accessible label still identifies action search. Daily work
remains the navigation landmark name without a redundant visible heading. Secondary
company context uses tighter spacing. Existing palette scope and simulation semantics
remain unchanged. Home remains directly available as the first navigation destination.

### Single-row tabbed headers (spec 225)

Multiple register tabs replace the visible page title in the workspace header.
Title-only pages retain it; tabbed pages retain one visually hidden page heading and
the page-information disclosure. Existing page actions occupy a separate right-hand
slot outside tab scrolling, followed by an icon-only, labeled chat toggle. Counts
appear adjacent to the active tab, or beside the title on pages without tabs. Nested
Documents in Integrations select the Received data parent tab. The tab strip scrolls
horizontally as needed; it never scrolls the page to reveal the selection. Compact
mobile action triggers retain their accessible labels. Existing forms, confirmation,
permissions, filters and data reads are unchanged. No second tab/action row remains
above the page content. This supersedes the earlier spec225 title-and-tab placement.

Commitments uses the same header for Customer side / Supplier side. The active side
shows its filtered list count once; the inactive side keeps its overview count.

### Inbox navigation (spec 225)

Daily work has one Inbox sidebar entry with no aggregate badge. Its primary header
tabs are Commitments, Exceptions and Decisions; existing queue URLs remain valid
and select Inbox. The default destination is Commitments. Direction controls and
exception findings/rules are subordinate local controls. Existing side overview
counts remain local; the main header count belongs only to the active register. Home
and Chat remain independent. No AI behavior, authorization or confirmation changes.
This supersedes the three individual sidebar entries and their former primary tabs.

### Inbox decision badge (spec 253)

The Inbox entry shows the number of pending decisions in the current company (99+
above 99, nothing at zero); on the collapsed rail it sits on the icon. While another
Inbox tab is open, the Decisions tab shows the same count. Both read the Decisions
register's own queue count one row wide, on company change, when the tab is shown
again, once a minute while visible and after any write in this browser. This
supersedes spec 225's "no aggregate badge" and active-register-only header count for
this one queue. Commitments and Exceptions keep the active-register-only rule.

### Work counts on workspace tabs (spec 254)

A tab states the open work behind it while another tab is open; the open tab keeps
its own register count. Work tabs are Inbox Commitments (customer side), Exceptions
and Decisions; Sales and Purchasing Commitments; Warehouse Stock (overallocated items,
warning tone, because Stock itself lists every item); and Finance Open items
(outstanding receivables). Stock tabs (orders, shipments, reservations, movements,
payments, journal, balances, master data, analytics, integrations, Inspector,
settings) state no count while inactive. Each count reads its register's own endpoint
with its default filters, one row wide, in the spec 253 rhythm; zero shows nothing.
Only Inbox carries a sidebar badge. This extends the spec 253 exception to spec 225's
active-register-only header count to these work tabs.

The Inbox orders its queues by who must act: Welcome, Decisions, Exceptions,
Commitments (Welcome tiles alike). While decisions wait, their tab count and Welcome
tile carry the accent of the sidebar badge; Exceptions and Commitments stay neutral.
Welcome leads with those tiles; the activity graph follows with its period control in
its own header and a quiet Live indicator. Readiness shows only as a caution notice
when not everything is ready (spec 254 FR-009, supersedes the spec 225 Welcome order).

### Empty standalone chat history (spec 225)

Standalone Chat hides its conversation column when no active or archived conversations
exist. The first successful history read per company/page visit determines automatic
desktop visibility. Creating the first conversation does not expand the layout; an
explicit history button becomes available instead. Reopening Chat with saved history
restores the desktop column. New chat remains in the conversation toolbar regardless
of column visibility. Mobile retains explicit overlay access. Hidden portal targets
stay mounted to preserve composer state; errors do not establish empty history.

### Continuous register surfaces (spec 225)

Shared registers use an unframed surface with neutral filters, plain table headers,
13px body text and tabular numbers. Paging sits directly below the table at the same
width; selected-row tools appear only when rows are selected. Empty registers keep
search, filters and paging, but hide column headers and use compact existing guidance.
Healthy calculation freshness is a quiet line; delayed, pending and failed results
retain their visible status. Inspector record types have a wider default column and
regular-density details can wrap to two lines; stored user layouts remain authoritative.
Search submission, density, resizing, sorting, source links and confirmations remain.
This supersedes prior framed-register and full-column fixed-footer presentation.

### Sidebar simulation indicator removal (spec 225 FR-016)

The sidebar no longer shows a standalone Live simulation indicator or runs its
dedicated status polling. Company-switcher simulation context, Integrations access
and the existing tenant-scoped simulation control route remain unchanged. This
supersedes earlier sidebar/header indicator placement requirements.

## Unified tool catalog (spec 226)

Tools has one directory for both legacy commands/views URLs, without Actions/Calculated
views tabs. Visible business-topic sections contain capabilities, ordered by Retrieve,
Check and explain, Change, then Page shortcut. Search matches localized display labels
and exact command/MCP identifiers; topic and purpose filters compose independently.
Deployment metadata links commands, discovery forms, workspace actions/views, projections
and public MCP definitions through explicit relationships. Equivalent representations
share a capability; distinct movement intents remain separate. The displayed count is
capabilities, not a sum of overlapping technical catalogs. Underlying read variants retain
their own report readers and freshness semantics in technical details.
Details retain actual command/schema/code and report explanations. Web forms and navigation
reuse existing eligibility. MCP badges mean supported tools, not user/token authorization.
Use in chat appends a tenant-scoped draft without sending or discarding existing text;
confirmation remains in the existing workflow. Company switches remount the directory.
All MCP names, schemas, descriptions, access modes and dispatch paths remain unchanged.
This supersedes the earlier two-tab Tools directory presentation from specs 218/219.

## Email-only account menu (spec 227)

The sidebar account trigger uses one localized My account label with its avatar and
chevron, including its accessible name and collapsed-navigation tooltip. The open
menu shows the full original account email with wrapping and no redundant Profile
heading. Account settings links to the existing personal preferences destination.
Appearance, resource links, dismissal and sign-out retain their existing behavior.
No personal name is inferred or required.

Analytics shared-component refinement (spec228 FR-014): all four views use the common
RegisterWorkbench and single-row tabbed header. Save analysis and Use in analysis
are page actions in the shared More actions menu, scoped to the active view. Local
analysis/catalog tabs use the shared local navigation, tables use ERP register geometry,
and templates/private reports use compact flat lists. No duplicate page titles appear
inside these views. Mounted Builder drafts survive view switches without leaking header actions.

### Analysis and the global chat (spec228 FR-015–017)

Create with chat and the visible Adapt with chat action open the existing global chat
with an editable prompt, without sending. Adaptation attaches only the checked query
snapshot, not result rows, in a visible removable context. Pending, failed or unexecuted
queries cannot be attached. Context is tenant-bound, bounded by the existing chat
message limit, retained on failed sends and cleared on successful sends/session changes.
The plain user-message context is not execution authority. Existing AI usage policy
and confirmation remain. History exposes attached query context in a disclosure.

Private graph create/update proposals offer Open in analysis: the destination reads the
proposal through the existing owner/tenant-checked endpoint and executes its full
definition as an unsaved draft. Opening does not approve or save. Other proposal kinds
and operations cannot silently become an analysis. Empty My reports offers Create your
first analysis; a filtered empty list explains the empty search instead.


### Question hierarchy (spec228 FR-018)

The analysis editor has one locally bordered question section headed “How Reality
understands your question”, with Adapt with chat beside it. Larger editable tokens
form the primary sentence; aggregate queries lead with their measures. A labeled
Conditions row follows. The period appears once in the sentence and can be removed
there as a whole, preserving unrelated filters. Measures and columns, record paths,
and sorting remain editable in an initially collapsed disclosure. This local frame
is intentional; result tabs and tables retain the shared flat register design.
Currency and identity axes remain in the canonical query even when technical identity
is omitted from the readable sentence. No additional page hero or question input is added.

### Expanded analysis discovery (spec 229)

Data explorer groups available analysis objects into collapsible business areas and
searches model-provided synonyms and fields. Searches expand matching groups. Builder
record selection uses the same groups. Sales and supplier invoices/credits, purchasing,
payments/refunds, reservations/holds, traceability/shipping, terms, partner structure,
accounts and evidence details have distinct truthful labels. Legacy combined invoice
nodes remain compatible. Historical event/fact/source entries say they are history;
recorded amounts are not labeled derived balances or inventory. See
[analytics coverage](features/analytics.md#expanded-business-catalog-spec-229).

### Finance and calendar analysis (spec 230)

Data explorer and Analysis expose separate customer/supplier financial positions
with canonical outstanding amounts, due dates and payment statuses. Calendar-date
metadata enables period controls and monthly grouping for document dates; date-only
values display without timezone shifts. The existing shared controls and question
frame remain. See the finance and calendar analysis contract in features/analytics.md.

### Current stock analysis and templates (spec 231)

Explore data includes Current article stock under Warehouse and shipping, using the
shared catalog/preview and question editor. Descriptions say all-location current stock
and distinguish arithmetic availability from shipment permission. Three stock and three
finance templates reuse the existing starting-point list and open unsaved definitions.
There is no new page, chart, business write or independent inventory calculation.

### Explicit snapshot inputs (spec 232)

Customer/supplier balance and stock-detail templates use the shared register styling.
A historical template requires a visible UTC snapshot date before adoption. The
sentence editor shows this date separately from activity periods and replaces its
single equality input when edited. Historical catalog previews link to the analysis
for date selection instead of silently returning today's state. The catalog describes
current master-data labels and the unavailable historical reservation/aging dimensions.

### Compact question sentence (spec 228 FR-019)
The question section uses 14px text, compact neutral bordered controls and a secondary
chat action. Business grouping captions omit auxiliary identities, duplicate article
codes and units while the full grouping remains in the query and advanced controls.
Snapshot inputs sit inside the sentence, with accessible labels and a UTC explanation.
The filter row explicitly shows an unrestricted state when no additional filters apply.

## Order journey timeline (spec 233)

Business Graph's Timeline now uses Facts, Commitments, Reservations, Movements and
Ledger entries lanes. Each point is a recorded change; same-position collisions expose
all members. A compact sales-order search selects an exact service-owned journey
through document/line, commitment, reservation and movement relationships. Shared
customer, item, location, source or correlation never expands order membership.
Directly attached facts and ledger entries are included; invoice/payment traversal
is outside this first scope. Source/evidence history remains readable in the journey
and Inspector rather than being plotted as business reality.

The recording-time axis initially fits loaded business events, with explicit short
periods, user-local Today and Fit history. Loaded counts and partial-history notices
never claim tenant totals or a complete process. Polling uses the existing visible-tab
30-second cadence, preserves selection/range, reports failures and pages forward by
sequence. Old pages load explicitly. Relationships are held record references, not
inferred event causation or historical state. Undated endpoints remain inspectable.

Details sit beside the chart when space permits and below on smaller screens; scrolling
stays within the chart. The existing Record graph and Inspector remain unchanged.
This supersedes spec162's five technical lanes, obligatory time-bucket pulses and
stacked-only trace layout for the active Timeline.

### Inbox Welcome (spec 225 FR-017–018)

Inbox is the first daily-work destination, followed by Chat. Home is no longer a
separate sidebar item. Inbox opens Welcome, the first of four header tabs before
Commitments, Exceptions and Decisions. The existing /app landing URL now displays
Welcome; explicit queue URLs preserve their selections and tenant context.
Welcome leads with Your company, in motion and follows it with three compact queue
count links. Trial questions, the open-work hero, duplicate decision explanation
and analytics shortcut are removed from this surface. Activity/readiness services,
polling, periods, errors, drilldowns and independent dashboard loading are preserved.
This supersedes the separate Home entry and Commitments default above.
The Exceptions count reads the same stored generation as the Exceptions register
(spec255), so both show one number; before the first generation completes it shows
the unknown placeholder, never zero.

Welcome styling (spec225 FR-019) follows the flat register surface: compact heading
and readiness row, neutral local period controls, an unfilled stable graph summary
and three queue links separated by subtle rules. No enclosing dashboard cards remain.
Graph colors, activity semantics and confirmation boundaries are unchanged.
Readiness uses a warning triangle for checked but unconfirmed availability, a
neutral loading indicator while checking, and a checkmark for ready. The explicit
text remains; warning color follows the light/dark caution theme token.

### Compact standalone chat navigation (spec225 FR-020)

Standalone Chat directly exposes History with a disclosure arrow, followed by
New chat with a plus icon, in the upper-right page header. Both retain visible labels
on mobile. The shared action bar uses its inline presentation for Chat only; other
pages keep More actions. There is no additional toolbar. History opens a
bounded scrollable overlay aligned to the right, initially closed
on every visit, including saved/archived history. It closes on selection, New chat,
outside click or Escape; Close/Escape restore focus to History. The conversation never
resizes and drafts survive disclosure changes. Empty history hides the trigger until
available. Session/archive services, tenant isolation and docked chat are unchanged.
This supersedes FR-014 automatic desktop history expansion.

## Global command palette (spec 237)

The shared Command/Ctrl+K entry combines scoped record search, navigation, existing
forms, calculated/private reports, templates and personal shortcuts. Search and
selection do not execute business mutations. See the
[command palette contract](features/command-palette.md) for implemented boundaries
and [spec 237 verification](../specs/237-global-command-palette/verification.md) for
remaining release gates, including the unpassed ten-user performance qualification.
## MCP proposal review parity (spec 249)

Every production MCP mutation uses the same tenant-scoped application proposal and
confirmation boundary as Web. Web derives the review destination from server-owned
proposal metadata. Existing specialized business reviews remain authoritative; every
other production proposal has a common exact-input and persisted-preview review. Demo
companies do not add tools or bypass these services, reviews, permissions, or confirmation
rules.

## Commitment integrity actions (spec 250)

Open customer and supplier commitments expose Revise commitment and Cancel commitment
remainder through the unified action launcher and contextual commitment actions. Both forms
prepare the shared server-owned delivery review before confirmation; neither calls a direct
mutation endpoint. Revision review shows the current promised, fulfilled, open and reserved
quantities plus the exact retained and released reservation effect. When different locations or
tracking identities make automatic retention ambiguous, the form lists the eligible opaque
reservation identities and requires explicit retained quantities before a fresh review can be
confirmed. Cancellation requires a reason and shows the open remainder plus reservations and
holds that will release. Completed results retain proposal verification, current observation and
Inspector links. An executing result uses reconciliation and is never submitted again blindly.
