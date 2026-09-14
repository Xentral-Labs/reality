# Feature Specification: Learning Playground

**Feature Branch**: `096-learning-playground`
**Created**: 2026-09-06
**Status**: Approved; implementation in progress
**Language**: English
**Input**: Build a friendly, account-based Playground to create and explore business scenarios
through chat, see the actual records and resulting views/exceptions, start with sample master
data, and add references quickly. Preserve the real Reality model and services.

## Context and Intent

### Problem

Readers understand isolated terms but struggle to see which action creates which record,
which effects are automatic, and which figures are calculated. The existing demo seeds a
state; the fixed month runs a whole scenario. Neither provides an incremental learning loop.

### Scope

One personal, isolated learning environment with a prepared trading dataset and one complete
order/reservation/partial-shipment lesson. Existing and new users enter without company or
provider configuration. Chat can read, resolve references, propose supported actions and help
build a bounded sequence. Deterministic buttons provide the same actions without AI.
Every applied step has an inspectable receipt, recorded changes and a fresh current picture.
Public Site/Docs offer a labelled example and an account entry; actual experiments require login.

### Non-Goals

- Anonymous writes, shared team sandboxes, imports of production data, production connectors,
  external agent credentials, real payments, external delivery or email actions.
- Arbitrary generated code/SQL, arbitrary tool access, an alternative inventory/finance engine.
- All industry datasets or all scenario types in V1. Purchasing, finance, correction lessons,
  source-update simulation, Fact-rule authoring and time travel are follow-up features.
- Universal undo, branch-at-any-point, replay from every historical state, global clock changes.
- Automatic production admission, changes to public pricing, or production deployment in planning.

### Existing Contracts

- `.specify/memory/constitution.md`; `docs/WEB_SPEC.md`; `docs/WEB_UX_MATRIX.md`.
- `docs/DATA_MODEL.md`; `docs/TEST_STRATEGY.md`; `docs/SPEC_DRIVEN_WORKFLOW.md`.
- Existing application proposals, reference autocomplete, Fact observation and tenant membership.

## User Scenarios & Testing

### User Story 1 - Start a safe experiment (Priority: P1)

A signed-in, verified person opens Playground and confirms creation of a private sample run.
No company form, ERP credentials or model key is required. One business, two customers,
one supplier, one warehouse and three articles are ready. Initial stock is zero.

**Why this priority**: Safety and zero-setup entry are prerequisites for every lesson.
**Independent Test**: An account without a production company starts a run; another user,
the same user's production company and all outbound business channels remain inaccessible.

**Acceptance Scenarios**:
1. Given a verified account, including pending production admission, start creates only an
   isolated Playground after confirmation. Production access rules remain unchanged.
2. Repeating the same creation request returns the same run; no duplicate company or dataset.
3. Unknown/unverified/disabled accounts cannot start; cross-user and production record IDs fail.
4. A normal company, old guided demo or existing data cannot be converted into a Playground.

### User Story 2 - Learn by doing and inspecting (Priority: P1)

The user follows a lesson: record opening stock, create an order, reserve and partially ship.
They see what was proposed, what actually ran, what changed and what remains unchanged.

**Why this priority**: This is the first independently useful demonstration of the technology.
**Independent Test**: Complete the golden lesson with no AI; every result is explained and linked.

**Acceptance Scenarios**:
1. Opening stock 20 creates a Movement; an order for 12 creates source/evidence/Commitment,
   but no Reservation, shipment or invoice. Order amounts use explicit sample values.
2. Reserving 12 creates a Reservation; physical 20, reserved 12, available 8, open delivery 12.
3. Shipping 5 creates a Movement, consumes matching allocation and leaves active reservation 7:
   physical 15, available 8, fulfilled 5, open 7. Shipping the final 7 leaves physical 8,
   reserved 0, available 8, open 0. Each shipment is explicitly recorded, never inferred.
4. A proposal is rejected or an invalid shipment attempted: no invented success or mutation.
5. The relevant current Exceptions are derived by normal rules, shown with reasons and
   compared by identity. Missing evidence/coverage is not presented as proof of no problem.

### User Story 3 - Describe a case and choose references (Priority: P1)

The user can name existing customers/articles, create additional ones, and request a small
variation through chat. The system resolves actual records and breaks requests into steps.

**Why this priority**: Enables the owner's own experiments without teaching database identifiers.
**Independent Test**: Resolve an ambiguous customer, create a new article, then separately
record its stock, with verified proposal and receipt links.

**Acceptance Scenarios**:
1. A unique existing reference is selected by ID; ambiguous names show choices and pause.
2. A missing reference is proposed for creation, never silently duplicated. Suggestions and
   forms use the same choices. Optional synthetic defaults are shown before confirmation.
3. "Create a helmet with 20 in stock" becomes article creation then an opening-stock action.
   Dependent steps resolve newly created IDs only after execution and get their own preview.
4. "Reserve and ship" does not authorise both immediately; each mutation needs confirmation.
5. An unavailable provider or quota leaves guided controls operational. Unsupported actions
   explain the boundary, create no proposal and offer a supported alternative.
6. Reading Facts uses actual observations; an empty Fact list is explained, not filled with
   duplicate shipment/payment Facts. V1 can inspect Facts but does not author Fact rules.

### User Story 4 - Resume or start again safely (Priority: P2)

Runs and conversations survive navigation. Start again opens a fresh sample environment while
keeping the old experiment inspectable; it does not erase the flight recorder.

**Independent Test**: Reload during execution, recover without duplication, then start another run.

**Acceptance Scenarios**:
1. Repeated confirmation and simultaneous tabs do not apply a step twice; concurrent changes
   invalidate stale previews. An uncertain result blocks dependent steps until reconciled.
2. Failure after an earlier step preserves its success, marks the later failure/uncertainty
   honestly and never retries a potentially applied action blindly.
3. Starting again archives the prior run only once the new dataset is ready. Archived runs
   are read-only through every interface; their records and explanations remain available.
4. A run quota produces an explanation and links to saved runs, not silent deletion.

### User Story 5 - Discover and understand the Playground (Priority: P2)

Visitors see a short labelled example and an entry link. Users learn in a single screen and can
open the actual Inspector and business views without leaving their sandbox context.

**Independent Test**: Site → account flow → Playground, plus keyboard/mobile navigation.

**Acceptance Scenarios**:
1. A public example is clearly synthetic and makes no live tenant query. Login/signup preserves
   the intended Playground destination; existing public hero/layout is not redesigned.
2. The workspace presents Try, What happened and What is true now, with compact record links,
   readable quantities and an always-visible sandbox indicator. Technical JSON is collapsed.
3. All controls, messages, errors, receipts and statuses work in en/de/nl/es; Docs in en/de.
   At 390 px and 1280 px navigation, confirmation and record inspection remain usable.

### Edge Cases

Identical labels across users; duplicate clicks; stale approvals; provider timeout; replayed
creation keys; unavailable source evidence; partial bootstrap; archived tenants; pending access;
quota exhaustion; network loss after commit; invalid quantities; broken projection freshness;
prompts requesting production data, invitation emails, secrets or instruction bypass.

## Requirements

### Functional Requirements

- **FR-001**: Require verified login for experiments; allow a narrowly scoped Playground
  admission for pending production accounts without granting productive company access.
  Entry and run-status APIs require a real session even in local auth-disabled mode.
  Lists are bounded and owner-scoped; missing and foreign runs have the same not-found response.
- **FR-002**: Create an owner-private, explicitly marked sandbox with a versioned sample dataset
  through one confirmed entry; repeated creation requests must not duplicate it.
  Persist the empty private run before setup; create the entire bounded reference preset
  atomically with its ready transition. A failed setup retains a safe error code and no partial
  dataset. Retrying its original request key resumes that run without consuming another quota slot.
  Not-ready HTTP reads expose setup status, not partial reference maps or an inspectable tenant.
  Disabling new entry preserves authenticated owner access to saved history.
- **FR-003**: Enforce a server-side, fail-closed sandbox action boundary across all interfaces;
  forbid production IDs, real integrations, credentials, member invitations and outbound business effects.
  Generic tenant HTTP inspection requires the verified run owner even in local auth-disabled
  mode, has no platform-admin bypass, and permits only explicitly approved read surfaces.
  Normal company selectors must not disclose private sandbox tenants.
- **FR-004**: Provide the golden lesson in US2 as individually previewed and confirmed actions,
  independent of AI availability. Each step uses the real business behavior.
  Preparing an opening-stock step atomically persists one ordinary ChangeProposal and its
  PlaygroundStep, never a Movement. Validate positive quantities without storage rounding,
  owned active references and timezone-aware explicit timestamps. Show a resolved default
  timestamp before confirmation and retain it on replay. A changed normalized request using
  the same key conflicts; preparation must not use the execution output as immutable intent.
  Opening-stock confirmation binds the displayed preview revision and rechecks its relevant
  reference/stock state. Rejection uses the existing proposal lifecycle without a domain effect.
  Execution status and verified Movement evidence remain separate when the final proposal
  update or explanatory read fails; an uncertain action is never executed again.
- **FR-005**: Each applied action exposes verified record references and distinguishes created,
  changed, automatic and unchanged effects. Do not present a proposal or model prose as execution.
  Supported handlers carry the confirmed proposal ID into their shared services. Shipment
  events identify consumed Reservations, any active remainder and newly fulfilled Commitments;
  these automatic events reference the causal Movement event and commit with the records.
  Order evidence identifies its actual DocumentLine IDs and original SourceRecord. No mirror
  Facts are created merely to explain an action.
- **FR-006**: Present current stock, obligations, Reservations, Facts and Exceptions using normal
  reads; explain unavailable evidence and freshness. Receipts are historical observations, not authority.
- **FR-007**: Resolve references from run-local master data; show ambiguous matches, propose
  missing entries explicitly and distinguish creating an article from creating its stock.
- **FR-008**: Support bounded free-text requests within the V1 action set, with visible defaults,
  staged dependencies and individual confirmation; show capability/provider limits honestly.
- **FR-009**: Persist conversations, proposals and receipts; guarantee no duplicate applied step
  on retry and block new mutations while execution outcome remains uncertain.
  Run mutation serialization survives internal commits and rollbacks. Contending requests
  return busy without waiting or executing. A lost database connection must not reconnect
  and continue without its lock. Acquiring the lock alone grants no business-action permission.
- **FR-010**: Start again creates new data without rewriting old history; archived runs deny writes.
- **FR-011**: Enforce configurable run/step/chat quotas before work starts, including concurrent
  requests; exhaustion never disables read access or demands a user-supplied model key.
- **FR-012**: Provide a public synthetic preview and preserved account destination with no
  anonymous mutation or public disclosure of private runs.
- **FR-013**: Provide the three-part learning surface, existing record drill-down, responsive
  keyboard access and advertised translations defined in US5.
  The initial account entry must not mount the production company shell or read its stored
  tenant selection. It uses the shared page header, explicit setup review/confirmation,
  bounded saved-run navigation, visible setup/error/archive states and actual reference reads.
  Retain the original request key across lost responses/reloads; retrying setup still requires
  confirmation. Never render initial stock constants as a live balance. The unfinished lesson/
  chat surface must be labelled unavailable until implemented. Only local Playground paths may
  survive sign-in/signup/verification; they do not grant production access to pending accounts.

### Domain and Traceability Requirements

- **DR-001**: All writes use common services/tools and Source → Evidence → Reality where
  applicable. Manual master data need not manufacture source evidence. Sample inputs retain
  their declared provenance; simulated source intake is not silently replaced by a manual action.
- **DR-002**: Reservations link directly to Commitments; record IDs drive links and action
  attribution. Facts never mirror typed state; documents never own operational status.
- **DR-003**: Every business table/query remains tenant-scoped, including Playground audit data,
  suggestions, search, archives, receipts, proposals and underlying Inspector endpoints.
- **DR-004**: Record explicit input amounts unchanged, use exact quantities and UTC timestamps.
  Views/Exceptions remain derived; receipt snapshots cannot authorise mutations or claim universal
  historical reconstruction. Test fixtures fix evaluation time without changing the runtime clock.

### Key Entities

- Playground run: one private learning experiment, dataset version and lifecycle.
- Playground step: an intended operation linked to its normal proposal and auditable receipt.
- Sample dataset/lesson: versioned instructions and explicit example values, not business state.
- Existing tenant, membership, reference data, source/evidence, Reality, proposal and event records.

## Success Criteria

- **SC-001**: In a moderated test, at least four of five first-time users complete the guided
  order/reservation/partial-shipment loop within five minutes of verified login without help,
  and explain correctly why reservation is not shipment.
- **SC-002**: Every golden step has exact expected quantities and record links; rejection/retry
  and cross-user/production-boundary tests produce zero unintended writes or business egress.
- **SC-003**: On the documented local test profile with ten concurrent sample runs, 95% of
  starts show prepared references within five seconds and completed local actions show refreshed
  evidence/current position within two seconds. Model latency is measured separately, not hidden.
- **SC-004**: Every FR/DR has test and implementation coverage; all required quality gates and
  desktop/mobile human review pass before public release.

## Sandbox entry simplification (approved 2026-09-06)

- **FR-024**: The entry offers a new private sandbox and directly clickable saved sandboxes, replacing the duplicate scenario catalog. Show six recent runs first and allow expanding remaining loaded runs. Operation selection lives only inside the cockpit. Creation requires separate confirmation; opening, browsing and cancelling create nothing. Existing presets, archived history, quotas and lost-response retry keys remain compatible.
- Acceptance: open an existing sandbox with one click, or review and confirm a new sandbox before choosing an operation inside it. No scenario cards or saved-run select remain at entry.

## Assumptions and Dependencies

### Approved scenario-library increment

- **FR-021**: The left cockpit pane is the same in-sandbox operation chooser both
  before the first command and after completing an operation. Offer explicit opening
  stock, a sale from existing stock, and a supplier order/receipt. Opening stock is
  a standalone operation and returns to the chooser. Selecting/cancelling a card
  does not create or restart a run. Hide lesson progress while choosing; show only
  the selected operation's steps during execution. Unsupported workflows remain
  visibly unavailable. Existing pending proposals resume, never get bypassed.

Acceptance: create a sandbox, see cards instead of an automatic stock form; select
stock, review/confirm, see the same chooser; select sale or purchase, complete it,
and see the chooser again with unchanged run URL and complete shared history.

- **FR-020**: In an active sandbox, offer a simple supplier order followed by a
  confirmed goods receipt using shared order_create(direction=purchase) and
  movement_create(type=receipt). The order creates incoming supplier goods
  obligations but no stock. Receipt increases shared physical stock and fulfils
  the linked supplier commitment. Partial receipts leave a visible remainder and
  permit another receipt against the same commitment. Preserve the run, all earlier
  sales and history; reload restores purchase progress and exact evidence links.
  Invalid quantity, customer commitments, mismatched item/location, foreign records,
  altered reviews and unconfirmed/generic mutations remain denied. No supplier
  invoice, payable, payment, or external order is implied by these two steps.

Acceptance: after a sale, order 10 from the seeded supplier, receive 4 and then 6;
stock increases by 10 and the supplier goods remainder changes 10 → 6 → 0. A
replayed confirmation creates no duplicate Movement. Start another sale in the
same sandbox using the received stock. Receipt amount above the remaining promise
fails before execution. Keep missing financial workflows explicitly labelled.

- **FR-019**: A completed lesson does not end its sandbox. Offer another customer
  order in the same run, optionally preceded by additional opening-stock evidence.
  Keep all prior records, balances, obligations and events. The current learning
  progress and downstream evidence selection belong to the latest operation, not
  the first matching step in history. Reload restores the latest persisted operation.
  Selecting an operation is not a mutation; every command still needs confirmation.
  Fresh sandbox creation remains a separate, explicit scenario/setup flow.
  This first continuation increment reuses sales commands only; purchasing and
  returns remain unavailable until their command adapters are verified. Existing
  safety quotas remain enforced; continuous does not mean unlimited storage.

Acceptance: complete a sale, select another customer order without changing run or
tenant, confirm its order/reservation/shipment/invoice/payment, and verify that each
downstream command references the second operation's records. Reload mid-operation;
the first operation remains inspectable and its remaining receivable remains visible.
Selecting or cancelling another operation creates no records or replacement sandbox.

- **FR-018**: Extend the trading lesson in the existing cockpit with invoice recording
  and payment allocation. Invoice input states the billed quantity and total explicitly;
  Reality never recalculates the supplied total from a price. The shared invoice command
  atomically records Source, invoice Evidence linked to the order line, and balanced
  receivable postings. The shared payment command records and allocates the stated payment.
  Each action requires its own review and confirmation. Existing inventory is unchanged.
  Shared open-item and exception reads show the resulting receivable and its settlement.
  Reload preserves progress; repeated confirmations cannot duplicate financial records.
  Foreign records, archived runs, altered previews and generic sandbox mutations stay denied.
  The partial-delivery lesson remains a four-step exercise; returns/P2P/R2R remain unavailable.

Acceptance: deliver 12, record an invoice for the explicitly supplied EUR 300, observe
EUR 300 open and no shipped-not-billed exception, pay/allocate EUR 125, observe EUR 175
open. Inspect distinct source/document/posting/allocation records and reload each step.
No separate payment-without-allocation control or invoice generation is promised here.

- **FR-017**: Before enabling the O2C finance lesson, the shared customer-payment
  command must commit its payment Evidence, balanced LedgerEntries, settlement
  allocation and BusinessEvents atomically. Failure during allocation leaves none
  of those new records committed. Financial events accept the confirmed action ID;
  the customer-payment tool passes its proposal identity to the shared service.
  Invoice posting and payment events retain source provenance and UTC time.
  This prerequisite alone does not enable Playground finance commands or claim
  the invoice/payment lesson is complete.

Acceptance: a forced allocation failure observed through a second database session
leaves the invoice open and no partial payment; successful payment emits exactly
one payment document event, one balanced posting event and one allocation event
with the same confirmed action ID; legacy callers without action ID keep working.

- **FR-014**: Entering `/playground` and choosing another scenario opens a library,
  without immediately starting or archiving a run. Group simple examples into O2C,
  P2P and R2R. Include full sale, split delivery, customer return, full purchase,
  split receipt, expense/payment and posting correction learning goals.
- **FR-015**: Availability must be honest. This increment enables the delivery portion
  of O2C and a partial-delivery exercise using existing tools. Invoice/payment,
  returns, purchase and journal adapters remain explicitly unavailable until their
  shared-service safety and end-to-end tests exist. No placeholder execution.
- **FR-016**: A selected runnable scenario is versioned in existing run metadata.
  Confirmation creates synthetic references only. Changing scenario archives the
  current active run only on confirmation; cancel preserves it. Legacy trading runs
  remain readable. Partial delivery teaches an outstanding obligation; it does not
  claim payment completion or derive balances in the browser.

Acceptance: a fresh account sees seven learning goals and no automatic creation;
unavailable goals cannot start; selecting and cancelling causes no mutation; confirmed
selection persists the chosen preset across reload; switching presets preserves the
old run; both runnable presets retain preview/confirmation and authoritative reads.

- V1 sample set: Acme, Müller, Huber, LightWorks, Augsburg; BIKE-LIGHT, HELMET, BIKE-BELL;
  EUR and unit quantities. No opening stock until explicitly recorded. All are synthetic.
- Default limits, configurable by deployment: 5 new runs/user/day, 20 retained runs/user,
  50 applied steps/run, 30 model turns/user/day and one model request/user at a time.
  No automatic retention deletion in V1. At capacity users may resume the active run or inspect archives.
- Hosted chat uses the deployment-managed provider, never a production tenant's key/configuration.
  Self-hosted deployments without it retain the full guided flow with an explicit unavailable state.
- Only the active owner operates a run. Account suspension always wins. Account verification
  mail is outside the sandbox business-egress ban; sandbox customer/supplier notifications are forbidden.
- V1 free-text actions: create Party/Item/Location, create sales order, record opening stock,
  reserve, record shipment, release a Reservation; supported reads/inspection. No arbitrary tool access.
- The owner approved implementation and the schema/security design on 2026-09-06;
  quickstart.md records the subsequent checklist-gate confirmation. Deployment is not authorised.

## Open Questions

### Approved cockpit revision

Public discovery: the homepage uses one account-creation hero action (Spec 022
FR-027, owner revision 2026-09-06), not a separate Playground CTA. Retain a Docs home
action and contextual links in the first journey and orders/inventory lesson.
Links use configured APP_URL, preserve locale where supported, open separately,
and describe account-required private sample data rather than live integrations.

The account/company menu provides a Playground link under Resources, opening
same-origin /playground in a new tab with the existing account session. It must
not switch the active company or create a sandbox automatically.

Action controls occupy a fixed bottom row of the Simulation pane across input,
review and completion states. The main button retains its vertical position;
only fields and review details scroll independently. No command semantics change.

The owner subsequently approved removal of the legacy presentation after a pushed
backup. The sole UI is now the cockpit; legacy links and duplicate forms are removed.
Recovery is through backup/playground-before-legacy-removal-20260906 at d3a9b29,
not an in-product layout switch. Shared command behavior remains unchanged.

Timeline refinement: label the recorder "Reality timeline" and show a compact
business subtitle for each event using recorded payload values and exact linked
master-data IDs (party, item, location, quantity). Never guess missing relations.
Technical event types and exact payload remain available in the inspector.

The owner requests a genuinely separate full-screen workspace, preserving the previous
layout as a reversible legacy option. At desktop sizes the action/review area, current
Reality, obligations/exceptions and selectable event recorder share one viewport.
Master data and journal details open inside that workspace; navigation must change
visible content rather than scroll to duplicate sections below. History is a compact
selector. Existing shared commands, confirmation and tenant boundaries are unchanged.
After a confirmed action, shared obligation and Reality reads must refresh together.
Acceptance: execute the guided four-step story without leaving the workspace; switch
inventory/master-data/journal tabs; inspect event payloads; reload and retain action
context; return to the legacy layout. No new business calculations or schema.

None requiring a product choice before planning. Numeric defaults are explicit reviewable
planning assumptions. Later scenario packs, time control and retention management are deferred.

## Requirement Traceability

### Approved supplier-finance and return increment

- **FR-022**: Supplier invoice, allocated supplier payment, and customer return
  operations must use shared Reality commands. Supplier payment and customer refund
  must commit evidence, postings and allocation atomically and attribute all events
  to the confirmed action. A failed allocation must leave no durable partial payment,
  including when the caller subsequently commits. Non-EUR currency is preserved.
- **FR-023**: Extend the same-sandbox cockpit with supplier invoice/payment after
  receipt, and customer return selection after a shipment. Physical return, credit
  evidence and refund are distinct reviewed steps; returning goods must not silently
  generate a credit or undo the original shipment. Shared views remain authoritative.
  Reload, replay, excessive quantities/amounts, wrong parties and foreign IDs require
  regression coverage before activating controls.

The owner explicitly requested supplier invoices, supplier payments and returns.
No schema expansion, supplier return, external payment execution or automatic
credit calculation is approved by this increment.

| Requirement | Scenarios | Planned proof |
|---|---|---|
| FR-001 | US1.1, US1.3 | Admission/API boundary |
| FR-002 | US1.1–4 | Bootstrap/idempotency |
| FR-003 | US1.3–4, US3.5 | All-interface security/egress |
| FR-004 | US2.1–4 | Golden service and UI lesson |
| FR-005 | US2.1–4, US4.1–2 | Receipts/failure recovery |
| FR-006 | US2.5, US3.6 | Shared read parity/freshness |
| FR-007 | US3.1–3 | Reference resolution |
| FR-008 | US3.3–5 | Bounded chat/confirmation |
| FR-009 | US4.1–2 | Concurrent/replayed execution |
| FR-010 | US4.3 | Archive/restart isolation |
| FR-011 | US3.5, US4.4 | Atomic quota/provider tests |
| FR-012 | US5.1 | Public/account routing |
| FR-013 | US5.2–3 | UI/locale/browser acceptance |
| FR-017 | Approved O2C finance prerequisite | Durable rollback, caller transaction and confirmed-payment causal events in test_finance_payment_atomicity.py |
| FR-018 | Approved invoice/payment cockpit increment | Shared command, private financial steps, receipt/reload, denial and browser tests |
| FR-022 | Approved outgoing finance prerequisite | Supplier/refund rollback, currency, action attribution and replay in test_finance_payment_atomicity.py |
| FR-023 | Approved supplier and return cockpit increment | Purchase/partial receipts/invoice/payment and return/credit/refund stories in test_playground_steps.py; browser continuation and tenant isolation proofs |
| DR-001 | US2.1–3, US3.3 | Service/tool and source lineage |
| DR-002 | US2.2–3, US3.6 | Shortest links/typed records |
| DR-003 | US1.3, US4.3 | Tenancy across all readers/writers |
| DR-004 | US2.1–5 | Exact values and read-only observations |
