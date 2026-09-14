# Screens: Operational Finance and Accounting Handoff

**Status**: Proposed UI contract; no screens implemented by this change.  
**Feature**: [148](spec.md)

## Existing application style

Extend Finance Control in the existing application. Reuse the tenant switcher, PageHeader, compact totals, server-paginated tables and right-side Inspector. Follow docs/WEB_SPEC.md and docs/WEB_UX_MATRIX.md: neutral surfaces, graphite text, indigo actions, semantic state colors, shared TailAdmin/Tailwind `br-*` primitives, 44px header actions and right-aligned amounts.

The original screenshot represents a different product boundary. This feature adds no Balance sheet, Profit & Loss, Trial balance, annual close or full financial chart-of-accounts screen. A compact Subledger accounts editor controls permitted local accounts.

| Destination | User job |
|---|---|
| Finance review | Resolve operational recording and handoff gaps |
| Open Items | Existing receivable/payable and aging control |
| Payments | Actual incoming/outgoing payment evidence, differences and allocation |
| Available credits | Customers/Suppliers tabs with payment/credit-note origins and explicit reuse/refund |
| Journal | Existing operational financial postings and corrections |
| Accounting handoff | Prepare exports and inspect external outcomes |
| Cost assignments | Optional responsibility analysis of received amounts |
| Finance settings | Subledger accounts, targets, reference mappings, optional centers and bounded automation |

These are destination requirements, not final routes. The later plan updates the canonical route/UX inventory. Reuse existing destinations wherever possible; avoid separate duplicate editors under Data Management.

## V01 — Finance review

**Job**: Identify missing operational records and incomplete handoff information.

Two clearly named tabs: Operational recording and Accounting handoff. The first lists supported unrecorded events, failed processing and source changes requiring correction. The second lists missing target-required fields, ambiguous mappings, rejected receipts and unmatched/conflicting outcomes.

Filters: search reference/party, source, financial kind, date range, currency and reason. Columns: document reference, party, date, amount with stated basis/currency, issue, next action, Details. Server totals count the complete selected scope.

An invoice may be correctly recorded locally and still require external handoff information. Display those facts independently. Selecting a row opens evidence, received components and next-step controls. Missing source tax leads to additional evidence, not a calculator or editable source-total field.

Actions use shared preview/confirmation: Record operationally, review existing correction, edit optional assignment, or prepare handoff. No read, tab selection or filter change posts a journal entry.

## V02 — Operational Journal and role detail

**Job**: Explain existing financial movements and their evidence.

Keep current Journal and its debit/credit control totals, adding clear operational wording. Columns: effective date, operational role, side/amount/currency, party, evidence reference, posting group, correction role, Details. Technical IDs appear in Inspect rather than leading the table.

Filters: date, account, role, party, source, correction role and search. Account code/name is shown alongside the operational role; selecting an account scopes the detail while role totals cover all its accounts. Selecting a role opens its operational movement/balance detail, not a financial chart account. Complete matching totals come from the service; a filtered role imbalance is not labelled an invalid group.

Posting detail shows the full balanced group, actual evidence, related payment allocations, original/reversal links and separate handoff history. Existing gross sales-account movements are labelled Gross sales postings; inventory counterpart entries are not presented as inventory valuation. No arbitrary manual financial-journal editor is added.

Reverse retains the existing preview and confirmation. If the original has a handoff, disclose that local reversal does not reverse external accounting and offer correction handoff review after the local action.

## V03 — Open Items and Payments

**Job**: Preserve existing operational cash/claim control.

Retain existing aging, outstanding amounts, allocations and payment evidence workflows. Add a compact link to related handoff evidence where useful, without replacing settlement state with a remote processing badge.

A payment accepted externally is not thereby allocated locally; an allocated payment is not thereby booked externally. The same source-backed local services remain authoritative. No bank matching engine, general-ledger opening-accounting editor or remote payment execution is introduced; the bounded opening-item import below is included.

## V04 — Received details and optional assignment

**Job**: Explain financial evidence and optionally attribute responsibility.

Open within Document Inspector or a shared detail workspace. Show source-stated gross/net/tax components at actual line/document-summary level. State Missing for absent values. Do not show a repeated document total against every line.

Assignment editor fields: selected component, read-only basis/currency/available amount, center selector, explicit assigned amount, internal reason. Add assignment creates another row. Show server-calculated assigned and unassigned amounts. Partial assignment is allowed; over-assignment or mixed bases is refused.

For the 1,190 gross / 1,000 net example, display 600 Warehouse + 400 Administration against the net component while the payable remains 1,190. Tax is separately shown as the source-stated 190. Source-coded versus internally assigned values have distinct labels.

Preview and Confirm assignment preserve author/revision. Existing prepared packages remain unchanged. Retired references can be read but not newly selected. External target reference fields show mappings separately from source statements; the separate small Subledger accounts editor controls local eligibility; no full financial chart or tax-rate administration is offered.

## V05 — Accounting handoff register and preparation

**Job**: Prepare an exact bounded set for an external accounting workflow.

Register tabs: Ready to prepare, Prepared packages, External feedback. Filters include target/profile, evidence dates, preparation dates, source, currency and outcome. Do not collapse these dates or state axes into one status.

Ready rows show document reference/kind, party, amount/currency, received detail availability, assignment/mapping readiness and prior package references. Primary action Prepare selected opens a preview of exact selected versions, output fields, omissions and target profile. A neutral package is clearly labelled Neutral data package — target compatibility not verified.

Unready selected items are listed with reasons. Users explicitly adjust selection or resolve them; no silent partial export is made. Preview/confirmation fixes the selection, profile, assignments and revisions.

Prepared package detail shows preparation time, actor, item count, separate-currency control amounts and exact item versions. Download returns the same immutable file. No Sent, Received or Posted badge is inferred from download. Re-preparation shows prior attempts and requests explicit retry/correction intent.

V1 offers Download package, not a live Send to accounting button. Any later live connector must satisfy its separately reviewed authorization and delivery contract.

## V06 — External feedback and reconciliation

**Job**: Understand what the receiving software actually confirmed.

Rows: target, local reference/version, external reference, received assertion, external occurrence time, local receipt time, reason, Details. Only display Received, Accepted, Rejected or Externally posted if source evidence actually supports it. No linear progress bar fabricates absent intermediate steps.

A compact side-by-side detail shows Operational recording, Prepared packages and External evidence. An accepted file can coexist with unknown item posting. Mixed package outcomes retain item-level detail. Old-version feedback does not make a newer version posted.

Import feedback uses the existing source intake/interpretation flow with a preview and explicit confirmation. Retain unmatched and conflicting records in Needs review with their raw source accessible. An operator note must not masquerade as an external receipt.

Correction detail links original item, local correction, prepared correction versions and any explicit remote receipt. Do not label remote reversal complete because a local reversal occurred. This view reconciles held item evidence; it does not assert a remote general-ledger balance.

## V07 — Cost assignments

**Job**: Inspect optional operational responsibility without pretending to be cost accounting.

Filters: period based on explicitly labelled evidence date, center, component basis, currency and source. Columns: center, assigned amount with basis/currency, contributing component count, Details. Include Unassigned for known component amounts and a separate Missing amount basis count.

Click through center → received components → evidence and related operational journal. Never sum net and gross or unlike currencies. Assignment totals do not claim recognized expense, margin, a budget result or center profit. Empty state: optional assignment can be enabled through settings; it does not prevent normal sidebook operation.

## V08 — Finance settings and automation

| Area | Fields and behavior |
|---|---|
| Subledger accounts | Code, name, operational role, active/blocked, configured destination, external references and usage; owner-maintained through the editor below |
| Targets/profiles | Name, target namespace, neutral profile/version, explicit required fields; no credentials or live-send capability in V1 |
| Transaction matrix | Read-only eight-operation role/side/amount matrix with resolved local defaults and account-setup links |
| Case codes / Coding groups | Defined code, name/description, active/retired; explicit source-code mappings and component assignments |
| Target case mappings | Target, transaction, case, group mode/group, external account/tax code, revision; test on evidence and owner activation |
| External references | Source/local reference, external account/tax/center reference, target, revision; exact reference mapping only |
| Cost centers | Code, name, active/retired; optional and no mandatory financial chart relationship |
| Automatic operational recording | Source, supported financial types, approved interpreter/service revision, enabled/paused state; owner-only explicit activation |

Subledger accounts uses a compact register and shared create/edit drawer. Filters: role, active/blocked and search. Columns: code, name, role, state, default-for-role, external mapping summary and Details. Details show historical usage and related Journal entries.

Actions: Add account, Set up minimal accounts, Import selected references, Edit, Block/Reactivate and Configure role destination. Previews show changes/collisions and require explicit confirmation. Import presents the supplied code/name and an explicit role selection; it does not select a role based on account number. Referenced accounts expose no Delete or change-established-role action. Unresolved legacy accounts offer Review initial role with an explicit audit reason before normal use. A rename explains that identity/history is retained.

The blocking preview names affected default destinations and states that new normal entries will be refused while exact historical reversals remain possible. Selecting a replacement default is explicit; the UI never swaps defaults silently. Journal/correction previews show the resolved account and revalidate after changes. Missing or blocked accounts lead from Finance review directly to the relevant settings record.

External mappings are per target and optional. Labels distinguish Local subledger account from External account reference and show the gross operational basis where relevant; mapping alone is never labelled accounting-ready net coding.

Settings are reachable for an empty tenant. Saving draft references does not activate financial automation. Automation confirmation states which future financial evidence can create operational entries. Source intake, external delivery and ordinary chat confirmation remain separate authorities. Revoking or pausing stops new automatic records but does not undo history.

## Shared acceptance matrix

| State | Required behavior |
|---|---|
| Empty/unconfigured | Explain the exact optional setup or missing evidence; never imply a full chart is required |
| Loading | Shared skeleton; no transient reassuring zero amounts |
| Valid zero | Distinct from absent net/tax evidence or an unavailable remote outcome |
| Failed read | Retry with filters preserved; no stale wrong-tenant rows |
| Preview/stale preview | Full effects; changed evidence/assignment/profile requires fresh review |
| Unknown outcome | Reconcile the same operation identity; do not blindly repeat |
| Success | Show the actual recorded/prepared/received fact with evidence |
| Unauthorized/retired | Explain refusal and retain safe editor context |
| Partial/conflicting remote outcome | Preserve per-item version and source evidence, with actionable review |

Verify keyboard focus/return, mobile 390px, tablet 1024px including Safari, desktop 1440px, both themes and English/German/Dutch/Spanish. Wide tables scroll inside their region; shared header controls wrap. Business source labels remain in their original language. All totals, readiness and business state come from shared services; browser code formats and navigates only.

## Declared-case interaction extension

[posting-matrix.md](posting-matrix.md) is the detailed V01/V04/V05/V08 extension. Evidence shows actual component case/group and source-versus-internal provenance. The settings resolver preview exposes zero/one/multiple matches, exact revisions and omitted required information. Missing/ambiguous cases affect case-coded handoff readiness, not an otherwise valid local gross claim. Country and tax rates are never controls that silently determine a case. All new controls use the same shared state, localization and keyboard matrix above.

## Payment-difference interaction extension

[payment-differences.md](payment-differences.md) defines V01–V06/V08 changes for partial payment, claimed deductions, confirmed non-cash reductions, unallocated excess and evidenced refunds. Default residual handling is Leave open. Separate cash, adjustment and remaining credit amounts are supplied by shared services; the UI neither computes a discount amount nor marks an unexplained residual settled. Finance settings adds the accepted-reduction counterpart account; no full-accounting editor is introduced.

## V09 — Available credits

The full [V09 contract in payment-differences.md](payment-differences.md#v09--available-credits-customers-and-suppliers) is mandatory for this release. One canonical destination has Customers and Suppliers tabs, partner/currency totals, unallocated-payment and credit-note subtotals, origin/evidence detail, and direction-specific Allocate / Record refund paid or received actions. Availability includes credits even without open invoices; no automatic netting, duplicate origin counting or stored credit balance is introduced.

V01/V03/V04/V05/V06/V08 also expose supplier payment/deduction/adjustment/refund equivalents. Our unaccepted withholding leaves the payable open; supplier reductions require documented entitlement/agreement. The shared confirmation, keyboard, language, theme, viewport and full-scope pagination matrix applies to V09 and all symmetric actions. Partner details and existing Payments/Open Items link to this same register rather than computing their own credit totals.

## V10 — Import opening items

[opening-items.md](opening-items.md) defines the guided import under Finance settings, linked from Open Items and Available credits. Select source/cutover and Individual items or Summary balances, enter/upload partner/direction/currency/outstanding amount/identity with optional original dates, review account matches and duplicate/coverage conflicts, then confirm the bounded batch. Totals remain separate across all four directions and currencies. The confirmation explains that this records carried positions, not new sales or money.

V03 adds Opening item origin and truthful unknown-due-date handling. V09 includes Opening credits as a separate origin/subtotal and exposes the same allocation/evidenced-refund actions. Journal and Inspector retain cutover/source references and the neutral counterpart. V10 is included in the same keyboard, localization, responsive, theme, error and lost-response verification as V01–V09.

## V11–V13 — Trade finance control extension

[trade-finance-controls.md](trade-finance-controls.md) specifies Money accounts & settlements (V11), earmarked Advances (V12), and goods/invoice/settlement Trade finance control (V13). Finance Control retains its existing shell and uses shared exact-scope reads/Inspector, not a second accounting product.

V01/V03 show payable holds and actual-payment-during-hold reconciliation. V09 splits free/earmarked amounts without doubling credit; journal/allocation detail explains cross-account reclassification. Evidence relationships show Unknown distinctly from not applicable or linked. Provider views never label restricted/in-transit funds as bank cash. Settings expose the bounded roles and source/match configuration, not tax determination or live bank execution. All V01–V13 surfaces share keyboard, four-language, theme, viewport, failure, stale-confirmation and pagination proof.

Agents and browser views consume [the same structured explanations](agent-finance-contract.md), including full-scope totals, input identities, source/decision provenance and limits on completeness. Browser and agent clients cannot derive eligibility from a partial page.
