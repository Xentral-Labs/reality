# Web UX Matrix

This matrix translates the primary persona in `WEB_SPEC.md` into the expected
job, hierarchy, and interaction pattern for every product surface. Identify the
user's decision first, then select the TailAdmin/Tailwind pattern that supports it.

The shell groups these surfaces by user job rather than by database object.
Company Overview, Order Operations, Warehouse Operations, Finance Control,
Data Management, and System & Traceability are presentation modes over the same
services and records.

The executable `ux-matrix-v1` inventory is owned by Spec 030 and must remain in
exact parity with Product Web routes. Authentication and profile remain explicit
supporting destinations. The global Activity drawer is separately owned by Spec
029; this matrix records its destination without duplicating that implementation.

| Surface | User job | Primary hierarchy | Preferred UI pattern |
| --- | --- | --- | --- |
| Home | Start the day and decide where attention is needed | Exceptions, position, recent change, next action | Exception queue, control totals, compact operational tables |
| Operational Exceptions | Review derived exceptions and decide what to inspect or control | Severity, impact, cause, next step, trace | Prioritized review queue with inline finding preview; not a generic register |
| Copilot Chat | Ask a business question and review proposed actions | Context, answer, evidence, confirmation state | Task conversation with explicit proposal and confirmation cards |
| Commitments | Control incoming and outgoing promises | Risk, due date, counterparty, promised versus reserved, evidence | Dense exception-first register with inline read-only preview and separate focused work |
| Inventory | Understand present and projected availability | Shortages, physical, reserved, available, inbound, projected | Stock control table plus movement and reservation explanation |
| Orders | Control order readiness and execution blockers | Order, party, due date, readiness, blocking reasons | Bounded fulfillment register with inline document explanation and distinct related filters |
| Warehouse Queue | Prioritize orders for warehouse execution | Priority, readiness, due date, blockers | Bounded execution queue backed by the shared fulfillment projection |
| Fulfillment blockers | Find shortages and holds blocking fulfillment | Blocker, order, item, shortage, reason | Exception-oriented projection table with Commitment explanation |
| Supply & demand | Compare stock and incoming supply with customer demand | Physical, reserved, available, incoming, open and uncovered demand | Item position table with Inventory and Commitment explanation |
| Open Items | Control receivables/payables | Due/overdue, party, open amount, settlement, evidence | Aging-oriented finance worklist with control total, inline explanation and separate financial work |
| Payments | Review cash evidence and allocation | Date, party, amount, direction, allocated/unallocated | Settlement workbench, unmatched payments first |
| Journal | Verify operational postings | Account, date, debit/credit, amount, balance, evidence | Tenant-scoped journal register; selecting an account focuses its sheet and posting/evidence links open Inspect |
| Documents | Find evidence and assess interpretation | Type, date, party, amount, interpretation, linked Reality | Evidence register with document preview and Reality links |
| Document detail | Explain evidence and its consequence | Summary, execution control, lines, Reality, postings, source | Structured inspector; raw payload last |
| Activity | Understand what changed and in which order | Time, event, context, linked record | Filterable event log grouped by time or business object |
| Activity drawer | Check recent activity without leaving the current page | Time, event, attention state, linked subject | Right-side drawer over the shell, opened from reserved sidebar and mobile-header chrome; companion to the Activity page, not a replacement |
| Parties | Find and control a business partner | Name, role, account code, terms, exposure/holds | Register with operational and financial detail |
| Items | Find and inspect a business item | SKU, name, unit, defaults, stock relevance | Compact register and item detail |
| Locations | Review inventory locations | Code, name, state, stock relevance | Compact register and location stock detail |
| Data Management | Maintain Reality's minimal typed operational references | Register, source identity, connected evidence and Reality context | Compact register with inline read-only preview and separate edit workspace; never a shadow ERP |
| Payment Terms | Maintain due-date rules safely | Code, description, due-day logic, usage | Small register with focused create/edit dialog |
| Pricing | Define and verify price resolution | Direction, currency, precedence, tiers, affected parties | Guided workspace separating lists, tiers, and assignments |
| Integrations | Understand source coverage and ingest evidence | Source, capability, interpreter readiness, latest ingestion | Connector registry with readiness and focused ingestion panel |
| Open questions | Turn unanswered business questions into reviewed model improvements | Question, intended use, evidence, recommendation, bounded ALL/ANY condition groups and output, simulation categories, replay progress, implementation | Shared work queue with guided detail, visibly nested order/line rule editor, explainable execution summary, and product-dialog confirmations |
| Explorer | Inspect exact stored and calculated records | Source → Evidence → Reality, relationships, raw fields | Technical inspector with collapsible collections and deep links |
| Documentation | Learn the model and operate the system | Task entry points, CLI reference, data model | Searchable tabbed reference; guidance before generated detail |
| Playground account entry | Start or reopen a private learning run | Sandbox identity, setup state, next confirmed step, prepared references, saved history | Separate account workspace using the shared page header; explicit inline confirmation and responsive run list; no production tenant shell |

Playground is an account-level destination outside the company Route union. Spec 097 owns
its executable contract and isolated browser fixture harness. The viewport cockpit covers
stock, order, reservation, shipment, stated invoice and allocated payment, with shared
open items and event inspection. Partial delivery remains four steps. Full Inspector
integration and chat are pending; no second financial calculation runs in the browser.

## Shared review rules

1. A page title states the business job, not only the database object.
2. The first viewport contains the control state and likely next action.
3. IDs remain secondary until the user asks for traceability.
4. Derived states explain their inputs; they are not presented as stored workflow fields.
5. Mutating actions use confirmation and state their business effect.
6. Empty states explain what belongs here and the correct next setup step.
7. TailAdmin/Tailwind supplies shell, cards, tables, badges, forms, dialogs,
   drawers, and responsive behavior. Custom CSS is for domain-specific controls.

## TailAdmin reference patterns

- Operational Exceptions: `https://demo.tailadmin.com/task-list`
- Register pages: `https://demo.tailadmin.com/data-tables` and
  `https://demo.tailadmin.com/basic-tables`
- Copilot Chat: `https://demo.tailadmin.com/chat` and
  `https://demo.tailadmin.com/text-generator`
- Forms and dialogs: `https://demo.tailadmin.com/form-elements`

These are interaction and proportion references, not permission to copy demo
business semantics into the domain model.


## Spec 107 opt-in foundation

The existing matrix above remains the compatibility route inventory. The new
foundation has its own bounded route contract and preserves supporting links.

| Surface | User job | Interaction |
| --- | --- | --- |
| Home | Understand recorded position and find open work | Authoritative totals, delivery entry, attention and decisions |
| Your work | Resolve one delivery | Searchable bounded list, persistent selected case, quantity explanation |
| Ask Reality | Understand or prepare work across the company | Existing conversations, historical case labels, shared action reviews |
| Case assistant | Discuss the selected delivery while keeping it visible | Same conversation component beside or below the case |
| Decisions | Review pending actions or recover their outcomes | Pending/history lists and direct proposal lookup |
| Actions | Discover reservation or shipment | Existing command catalog eligibility, business descriptions, shared card |
| Inspector | Follow the supporting records | Native modal, keyboard focus restoration, linked evidence and escaped source |

Required review sizes are 390 and 1440 px, in en/de/nl/es and light/dark. Sample
screenshots are test evidence, never company data. Owner visual acceptance and
rollout are recorded separately in Spec 107's validation guide.

## Spec 108 Analytics and Master Data

| Surface | Question / action | Explainability | Validation |
| --- | --- | --- | --- |
| Home analytics preview | Which deliveries need reservation or are overdue? | Same current metrics as Analytics | Shared-service totals and browser navigation |
| Analytics | Current coverage and recorded activity over 7/30/90 UTC days | Exact paginated contributors, delivery case and movement Inspector | Corrections, empty history, revised due dates, period and tenant tests |
| Master data | Find customer/supplier/item/location; create or rename | Role-scoped register, exact snapshot, provenance and Inspector | Server search/paging, four-family preservation and foreign-ID tests |
| Master-data review | Confirm an exact reference change or check its result | Durable canonical input, pending field changes, receipt and record links | Reload, lost response, simultaneous stale changes, keyboard focus |

The executable workspace browser harness covers four languages, both themes and
390/1440 px layouts for Analytics, master-data details, forms and reviews. These
are technical verification gates; owner product review and deployment remain
separate. The old workspaces and Playground are not retired by this increment.

## Spec 109 Warehouse and Attention

| Surface | User job | Explainability | Validation |
| --- | --- | --- | --- |
| Warehouse stock | Find available stock for an exact item | Physical/reserved/available quantities and item Inspector | Units, exact IDs, state filtering, company isolation |
| Reservations | Follow reserved stock to its commitment | Reservation Inspector and customer delivery case | Active/released states, reload, keyboard focus |
| Movements | Investigate recorded stock history | Original, compensation and replacement roles; movement Inspector | Correction history, customer-only links, paging |
| Exceptions | Investigate a current finding | Party/item context, canonical guidance, exception and subject Inspectors | Severity/search, resolved refresh, tenant boundaries |

The operations browser harness covers all four surfaces in four languages, two
themes and 390/1440 px layouts, plus traversal, empty/error recovery, URL recovery
and company switching. Reads must not issue mutation requests. Existing App and
workspace harnesses remain regression gates. Product acceptance and retirement
remain separate from technical verification.

## Spec 110 Finance

| Surface | User job | Explainability | Validation |
| --- | --- | --- | --- |
| Open items | Understand outstanding receivables or payables | Complete filtered currency controls and document Inspector | Partial/settled filters, page totals, reload |
| Payments | Follow recorded money and its allocation | Payment Inspector and explicit reversal history | Direction, reference-ID search, paging, no aggregate cash claim |
| Journal | Follow debits and credits | Exact account filtering and ledger Inspector | Currency controls, selected-entry reload and keyboard return |

The Finance harness covers all three views in en/de/nl/es, light/dark and
390/1440 px, plus retries, empty states, company switching and no mutation requests.
The existing unified browser harnesses remain regression gates.

## Spec 111 Data and Sources

| Surface | User job | Explainability | Validation |
| --- | --- | --- | --- |
| Systems | Find an origin and its held versions | Explicit registry state, scoped counts and received-record link | Metadata-only SQL, count/paging, tenant boundaries |
| Received records | Inspect the exact original version | Source Inspector and exact-version evidence link | No payload in list, versions, nullable job status, safe original text |
| Documents | Find interpreted evidence | Existing document Inspector and recorded amounts | Exact-source filtering before paging, company reset, reload |

The source browser covers these three views in four languages, both themes and
390/1440 px, plus traversal, safe payload rendering, keyboard focus, retry and no
mutation requests. Source setup and technical Explorer retain supporting links.


## Spec 112 Settings

| Surface | User job | Scope and authority | Validation |
| --- | --- | --- | --- |
| Personal | Save language, formats, timezone and name | Existing account profile; explicit save/readback | Validation, ambiguous result, draft preservation, reload/localization |
| Appearance | Choose light, dark or device setting | Browser preference shared with header | Header synchronization and live OS change |
| Company access | Understand membership and invitations | Existing owner-only current-company API; bounded500 lists | Owner/member guard, company reset, retry |
| AI configuration | Understand credential mode and model | Configuration presence, not provider health | Owner guard, no secret metadata rendered |

Three sections use grouped navigation and focused forms/details, with en/de/nl/es,
light/dark and390/1440px coverage. Advanced administration stays a supporting link.


## Spec 113 Orders and Deliveries

| Surface | User job | Authority and continuation | Validation |
| --- | --- | --- | --- |
| Deliveries | Find outgoing/incoming current work or history | Shared effective delivery observations, units and Inspector | Supplier identity, revisions/corrections, open/all, search/page/reset |
| Customer orders | Find received customer order agreements | Exact sales_order evidence; order → customer deliveries → existing case | Type filter before paging, exact document-line scope, confirmed action regression |
| Supplier orders | Find purchasing agreements and expected deliveries | Exact purchase_order evidence; incoming commitment Inspector | Supplier scope, no customer action, foreign/error/empty states |

Three sections use four locales, light/dark,390/1440px and keyboard Inspector focus
return. Tables scroll within their own containers; no cross-unit quantities or
order-level readiness is inferred in the browser.

## Spec 114 Facts

| Surface | User job | Authority and continuation | Validation |
| --- | --- | --- | --- |
| Facts register | Find recorded observations | Stored value, predicate, timestamp and source/rule metadata | Scoped search/count, stable paging, bounded types, raw values |
| Related observations | Compare observations of the same subject | Exact subject type and ID; no winning-value inference | Repeated observations, source scope cleared, company reset |
| Observation Inspector | Explain subject and original evidence | Shared scoped Inspector; exact source version | Keyboard/reload, missing source, unsupported historical subject |

The register uses English, German, Dutch and Spanish; light/dark and390/1440px.
Source payloads load only on explicit inspection, not in register metadata reads.

## Spec 115 Shared operational tables

| Surface | Presentation | Query and continuation | Verification |
| --- | --- | --- | --- |
| Orders/deliveries, stock/reservations/movements |44/36px shared rows and sticky key/header | Existing SQL authorities and exact case/Inspector | Geometry, effective quantities, retained actions |
| Finance, sources/evidence | Numeric alignment and bounded metadata columns | Server sort/page size; complete-result controls | Numeric global order, source scope, currency preservation |
| Master data, Facts | Same table standard replaces list/cards | Existing detail/edit review or observation/source Inspector | Original content, row/keyboard navigation |
| Table controls | Per-user/variant density, visibility, widths and reset | Browser-only layout; URL-backed sort/size | Corrupt storage, reload, user separation,24 visual combinations |
