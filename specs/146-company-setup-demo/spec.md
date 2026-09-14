# Feature Specification: Clear Company Setup with Empty or Demo Data

**Feature Branch**: `149-demo-company-live-activity` (combined specs 146, 147 and 149).
**Created**: 2026-09-09
**Status**: Product scope accepted by the owner’s explicit continuation after spec 147 on 2026-09-09; implemented and locally verified; review evidence is recorded in quickstart.md and review.md.
**Language**: English
**Updated**: 2026-09-09 — optional continuous Demo Data integration.
**Input**: Make registration and company setup understandable without asking for the same company twice. Offer empty or demo-filled companies both initially and through Companies → New company. Use coherent international demo data matching the Atlas request; an empty company may also be a sandbox. Offer an optional Demo Data integration that continuously delivers new orders for interactive practice.

## Context and Intent

### Problem

A new user supplies their name, company and order volume, then reaches an older sandbox screen asking them to create a company again. The product does not explain that access-application details and an operational company are different. The user reasonably believes the company already exists.

The current checkout also offers a compact guided demo during first-company onboarding, while later New company forms create empty companies. Different entry points therefore promise different experiences. Demo quality must serve ordinary evaluators as well as Atlas, rather than depend on individually prepared examples.

### Scope

- One understandable account-to-company journey, reusing a previously supplied company name.
- The same company-creation choices at first setup and every later New company entry.
- Three goal-based choices map to the distinct content and environment fields: own company, empty Sandbox, or demo Sandbox.
- A canonical international demo profile, sharing the dataset contract in spec 144.
- Safe creation, interruption recovery, clear progress and direct entry into the created company.
- An optional Demo Data integration in the normal Integrations experience, delivering new synthetic orders continuously into a Sandbox until paused or stopped.

### Non-Goals

- Redesigning authentication, production admission, billing, all Playground lessons or the entire application shell.
- Automatically upgrading a pending account to production access or treating a Sandbox badge as authorization.
- Retrospectively seeding history into existing populated companies, converting demo records into real records, destructive resets or deleting historical sandboxes. Explicitly connected ongoing demo orders in a Sandbox are in scope.
- Full Shopify emulation, simulated payments/shipment/refund lifecycles, fault-injection tooling, accelerated time and load testing in this increment.
- Building CRM, marketing, forecasting, autonomous purchasing, a general analytics platform or new pricing/cost authorities.
- Executing Tobias's reservation, deploying this feature, distributing credentials or claiming the current deploy already meets these requirements.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md), [workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md), [Web product](../../docs/WEB_SPEC.md).
- [Demo entrypoint equivalence](../027-demo-entrypoint-equivalence/spec.md) and [demo contract](../../docs/DEMO_SPEC.md).
- [Atlas demo and reads](../144-atlas-demo-contract/spec.md) and its [capability assessment](../../docs/agreements/atlas_reality_capability_assessment.md).
- [Shared scheduled jobs](../147-scheduled-jobs/spec.md) and [developer contract](../../docs/features/scheduled-jobs.md): separate scheduler/worker apps own timing and queued execution.
- [External-system simulator idea](../../docs/ideas/integration-simulator.md), used as context only: this feature promotes the bounded continuous-order use case, not the full unapproved simulator proposal.
- [Unified application foundation](../107-unified-app-foundation/spec.md) and [Learning Playground](../../docs/features/learning-playground.md).

This feature replaces first/later company-creation presentation and the compact default onboarding dataset. It does not replace the compact guided lesson or its equivalence tests. Spec 144 owns analytical meanings, detailed fixtures and agent-read improvements; this feature owns how users select and receive that shared profile. Existing documents must be reconciled during implementation, not silently treated as already changed.

## User Scenarios & Testing

### User Story 1 - Enter my first company without repeating setup (Priority: P1)

As a new user, I understand which information describes my account/application and which action actually creates my company.

**Why this priority**: The current handoff undermines confidence before users reach business data.

**Independent Test**: Complete account/application, verification and first-company setup with a previously entered company name; verify that one company is created and opened.

**Acceptance Scenarios**:

1. **Given** an access-details form, **When** it asks for company and order volume, **Then** it labels these as application information, explains that saving does not create a company, and explains the purpose of the volume question. Volume is not requested again during company creation.
2. **Given** an eligible user who already supplied a company name, **When** first-company setup opens, **Then** that name is prefilled and editable, with no repeated personal-name or volume questions. The final action explicitly creates the company.
3. **Given** a confirmed creation, **When** setup succeeds, **Then** the user enters that exact company's operational workspace without another sandbox/company-creation step.
4. **Given** existing membership or an invitation, **When** the user signs in or accepts the invitation, **Then** the authorized company opens without forced creation or renaming from application metadata.
5. **Given** a verified account pending production admission, **When** setup opens, **Then** Sandbox creation is available only under the existing enabled practice policy; ordinary-company creation remains unavailable with a clear explanation. If practice entry is disabled, the existing waiting state remains.

### User Story 2 - Choose the starting content consistently (Priority: P1)

As a user creating any company, I can choose an empty starting point or useful demo data and understand whether I am working in a sandbox.

**Why this priority**: Starting content is a recurring company decision, not a special first-login feature.

**Independent Test**: Exercise first setup and every Companies → New company entry with all permitted content/environment combinations.

**Acceptance Scenarios**:

1. **Given** either creation entry, **When** the form opens, **Then** it presents the same company-name input, three goal-based choices with explanations (FR-023). An empty ordinary company is the default when eligible; no company is created by selecting an option.
2. **Given** Empty, **When** an authorized user creates an ordinary company or a Sandbox, **Then** it contains no synthetic business records and opens a truthful empty state. Necessary company identity, membership and configuration are allowed.
3. **Given** With demo data, **When** selected, **Then** the result is explicitly a Sandbox and a short description states the included business cases, synthetic nature and reproducibility. An ordinary company with seeded demo data is not offered.
4. **Given** valid choices, **When** the user submits the clearly labelled creation action, **Then** the name, environment and content being created are unambiguous. Cancel creates nothing; invalid names retain the choices and show a field-specific error.
5. **Given** creation fails or its response is lost, **When** the user reloads or retries the same request, **Then** no duplicate company or seed appears. Incomplete setup is visibly unavailable for operational use, and a known completed company can be reopened without reseeding.
6. **Given** an existing Sandbox or ordinary company, **When** another is created or switched to, **Then** existing data, memberships and saved history remain unchanged and the active company and Sandbox label are visible.
7. **Given** any creation state, **When** used in English, German, Dutch or Spanish, on mobile/desktop or by keyboard, **Then** choices, errors, progress and confirmation remain understandable and operable in both themes.

### User Story 3 - Start with a credible international business (Priority: P1)

As an evaluator, I receive the same coherent demo quality that Atlas needs, with understandable names and inspectable business evidence.

**Why this priority**: A token order and shortage are insufficient for exploring a business.

**Independent Test**: Create demo companies through both entry points using the same fixture version and date anchor, then compare business expectations and trace the declared operational cases.

**Acceptance Scenarios**:

1. **Given** either entry point, **When** a demo becomes ready, **Then** it contains 16 internationally named items in several synthetic catalog categories, four customers, three suppliers and two named stock locations, with readable references and distinct technical identities. Names are the same business data across interface languages.
2. **Given** the demo, **When** its order cases are inspected, **Then** all ten Atlas cases are distinguishable: fully reserved healthy; unreserved with sufficient matching stock; true shortage; overdue partially reserved; overdue fully reserved but unfulfilled; partially fulfilled; held; multiple blockers; fulfilled; cancelled.
3. **Given** stock and procurement cases, **When** inspected, **Then** physical/reserved/available quantities, wrong-location stock, receipts/issues/releases/corrections, partial and late procurement, high/slow demand and different units remain distinguishable. Open supply is not received stock or a predicted arrival.
4. **Given** a ready demo, **When** its profile details are opened, **Then** the actual company identity, fixture version, anchor, covered periods, stable external references and available/missing capabilities are visible. Important quantities link to their supporting Reality records, evidence and synthetic sources.
5. **Given** an in-progress or failed seed, **When** inspected, **Then** no partial fixture is labelled ready; a partial or mismatched seed is reported explicitly and never silently merged with other business data.

### User Story 4 - Compare periods and repeat an execution safely (Priority: P2)

As an evaluator or Atlas integrator, I can use coherent history and repeat a supervised action without losing analysis history.

**Why this priority**: Historical comparison follows operational usefulness; advanced scenarios must not invent missing business meanings.

**Independent Test**: Verify declared two-period financial cases, then provision and exercise a separate execution fixture under the existing confirmation contract.

**Acceptance Scenarios**:

1. **Given** the demo profile, **When** historical evidence is inspected, **Then** it covers 84 consecutive days in two adjacent 42-day windows, with volume growth, price growth, a declining item, returns/credits, a large-order outlier, a zero baseline and separate EUR/USD activity. Booked gross sales-account amounts are not labelled net revenue, profit or cash.
2. **Given** missing cost, tax, discount, category-query or promotion support, **When** profile capabilities are consulted, **Then** each is classified as available, fillable with test data, interface gap or another source, with its limitation. No invented cost or supported price scenario is claimed.
3. **Given** the separate execution fixture, **When** provisioned, **Then** the one-unit success case is unreserved, physically available and unblocked, and a reproducible refusal case is present. No proposal is automatically confirmed or executed by setup.
4. **Given** separately authorized and confirmed execution, **When** the reservation succeeds, **Then** reserved increases by one, available decreases by one and physical stock is unchanged; correlated receipt/status and verification reads demonstrate the effect without claiming shipment.
5. **Given** a used execution fixture, **When** a repeat is explicitly requested, **Then** a fresh isolated execution fixture preserves the analysis company and previous audit trail. Repeating completed provisioning for the same request verifies/reuses its result rather than duplicating records.

### User Story 5 - Keep receiving demo orders through an integration (Priority: P1)

As a user practicing in a Sandbox, I can add Demo Data through Integrations, choose how frequently new orders arrive, and work on them while the demo business continues to receive demand.

**Why this priority**: A fixed starting dataset becomes exhausted; ongoing incoming work makes repeated hands-on exploration useful.

**Independent Test**: Connect the demo source, start a declared order rate, observe successfully imported orders and their source links, then pause, resume and stop without losing any received data.

**Acceptance Scenarios**:

1. **Given** a ready demo Sandbox, **When** I open Integrations, **Then** Demo Data is offered as a clearly synthetic integration using the same connection/status vocabulary as other integrations, without Shopify credentials or a claim of Shopify compatibility. Company setup offers a live-simulation option that automatically connects and starts Demo Data on confirmed creation (FR-021). Static demo creation alone never starts ongoing arrivals.
2. **Given** an empty Sandbox, **When** I add Demo Data, **Then** the connection preview names the minimal synthetic catalog/location prerequisites and the pool of demo customers it will add and creates them only on confirmation, without importing historical orders. In a populated Sandbox it reuses compatible profile references and adds only pool customers that do not exist yet; missing or conflicting catalog, company or location references cause an explained setup failure rather than guessed mappings. Starting a run adds pool customers that joined the pool after the connection was made. Ordinary companies cannot activate this source.
3. **Given** a configured source, **When** I explicitly start 60 orders per wall-clock hour, **Then** a delivery is scheduled each minute while running, including when the browser is closed. Each delivery carries a small Poisson-distributed number of orders (usually none, one or two) whose expectation follows a fixed hour-of-day demand curve, decided reproducibly from the run seed and the delivery time, so that arrivals vary naturally, with a quiet night and an evening peak, while the daily average stays at the selected rate. I can select 10, 60 or 300 orders/hour; the initial selection is 60 and the source remains stopped until started. The first scheduled order is due after one interval.
4. **Given** incoming orders, **When** normal ingestion succeeds, **Then** they use the profile's international items, a spread of demo customers weighted toward a few large buyers, and explicit units, currencies and current business timestamps, appear in normal order/work views, and expose their synthetic source and intake result. These arrivals do not automatically reserve, ship, pay, replenish stock or confirm a proposal.
5. **Given** a running source, **When** I pause or stop, **Then** no new orders are scheduled after the control takes effect. Already handed-off orders may finish processing and are shown as pending. Resume continues after a fresh interval without backfilling the pause; restarting after Stop creates a new run while retaining all earlier data.
6. **Given** retry, restart, delayed processing or a lost response, **When** deliveries recover, **Then** an order's stable source identity prevents duplicate business effects; new runs use distinct identities. A bounded backlog slows or pauses generation visibly and never causes an uncontrolled catch-up burst.
7. **Given** the integration detail, **When** inspected, **Then** configured rate, running/paused/stopped/error state, generated/imported/failed/pending counts, last successful import and next scheduled arrival are distinguishable, with links to intake results and orders. Source progress is not presented as successful Reality processing.
8. **Given** an active run, **When** the company is archived, source disconnected or its authorization is revoked, **Then** new delivery stops and prior evidence remains. Foreign-tenant controls are refused. Reconnection requires explicit Start and does not replay missed arrivals.
9. **Given** a fixed historical baseline or Atlas execution fixture, **When** ongoing orders run in a selected demo Sandbox, **Then** baseline records and declared comparison windows are unchanged and arrivals are distinguishable by run/source and current business dates. The separate Atlas execution tenant receives no continuous activity.
10. **Given** the integration controls, **When** operated in any supported language, theme or viewport or by keyboard, **Then** setup, start/pause/resume/stop, errors and progress remain accessible and understandable.

### Edge Cases

- Empty or whitespace-only name; an edited prefill; identical display names with different technical identities.
- Existing users with application details but no company; users with existing companies; pending admission; disabled practice entry; revoked membership during setup.
- Double click, reload, lost response, partial seed, fixture-version mismatch and concurrent company creation.
- Switching companies while setup completes; errors must not switch the user into an unrelated company.
- Different interface languages, UTC window boundaries, unknown due dates, incompatible units and mixed currencies.
- Existing legacy sandboxes remain accessible; no automatic conversion, replacement or archival.
- Browser closure, scheduler restart, duplicate Start, rate change, pause with an in-flight order, backlog saturation and disconnection during import.
- Deleted or incompatible demo references; exhausted stock remains a real demo shortage and is never silently replenished.

## Requirements

### Functional Requirements

- **FR-001**: Distinguish access-application information from company creation, explain volume collection, and reuse the application company name as an editable first-company default without repeating personal/volume questions.
- **FR-002**: Successful creation MUST open the resulting operational company without a second creation flow; existing membership and invitation entry MUST bypass forced company setup.
- **FR-003**: First and subsequent creation entries MUST share Empty / With demo data choices and the same consequence descriptions; Empty MUST be the default.
- **FR-004**: Empty MUST support ordinary company and Sandbox environments where authorized. Demo data MUST create a visibly labelled Sandbox. Starting content MUST NOT grant access or create alternative business rules.
- **FR-005**: Preserve existing verification, admission, practice-entry and membership restrictions, including pending users' inability to create ordinary companies.
- **FR-006**: Creation MUST be explicit and cancellable before submission, report validation/progress/failure, and recover a lost response without duplicate companies or seeds. Partial/mismatched setup MUST not be presented as ready or silently merged; failed setup retains its identity and an explained recovery path.
- **FR-007**: Empty creation MUST add no synthetic business records. New creation MUST preserve existing companies, data and saved history and show the active company/environment clearly.
- **FR-008**: Every demo-company entry MUST use the same versioned international profile, with 16 items, four customers, three suppliers, two stock locations and stable synthetic external references. Use English business names suitable for an international trading example, such as Harbor Supply, Northstar Outdoor, Summit Bottle and Rotterdam Warehouse; these are illustrative vocabulary, not required identities. Catalog categories remain source content where no typed authority exists.
- **FR-009**: The profile MUST meet spec 144's operational, inventory and procurement fixture requirements, including the ten named order cases and explicit currency, unit and business-date semantics.
- **FR-010**: The profile MUST contain the 84-day/two-window history and financial comparison cases in spec 144, preserving gross-booked metric definitions, source-stated values, origin links and currency separation.
- **FR-011**: Profile details MUST identify fixture version, actual tenant, anchor/windows and supported/missing capabilities using the linked Atlas assessment. Costs, promotions and price constraints are exposed only where their authoritative meaning exists; absent values remain missing.
- **FR-012**: A separately provisionable execution fixture MUST follow spec 144's one-unit success, reproducible refusal, separate authorization/confirmation, receipt and verification contracts. Repetition MUST preserve analysis and prior execution evidence, using fresh execution tenants rather than destructive reset.
- **FR-013**: Creation, recovery and environment labels MUST support all four product languages, both themes, mobile/desktop and keyboard operation without translating stable business references.

- **FR-014**: Demo Data MUST be an optional, visibly synthetic source in Integrations, discoverable from demo-company setup and available for authorized Sandboxes only. At most one continuous Demo Data connection may be active per Sandbox; static company creation and manual connection setup do not start arrivals. Explicit live-company creation includes automatic connection and Start under FR-021.
- **FR-015**: Connection setup MUST reuse compatible synthetic profile references or explicitly preview and create the minimal prerequisites in an empty Sandbox. The demo customer pool (the four profile customers plus additional named buyers) is part of these prerequisites; customers missing from the pool are added on connection and on Start, never during intake. It MUST NOT inject historical records, guess missing mappings or require real-provider credentials.
- **FR-016**: An explicitly started source MUST schedule evenly spaced deliveries whose expected total is 10, 60 or 300 orders per wall-clock hour, default selection 60, independently of an open browser. Rate counts new orders on average, not events or records; a single delivery carries a Poisson-distributed number of orders (at most six) whose expectation is the selected rate scaled by a fixed UTC hour-of-day demand curve between roughly 0.7 and 1.3 with daily mean 1, chosen reproducibly from the run seed and delivery time, and the customer of each order is drawn from the referenced pool with demand skewed toward its first entries. Rate changes apply prospectively after a fresh interval and are recorded with run configuration; no elapsed intervals are replayed.
- **FR-017**: Start, pause, resume, stop and disconnect MUST have the semantics in US5-5/8, retain received records and expose in-flight work. Runs MUST record their profile version, seed, configuration changes and identity so the intended order sequence can be reproduced independently of delivery timing. Retried deliveries retain source identity; a new run uses new identities.
- **FR-018**: Continuous orders MUST pass through the normal source intake, validation and interpretation boundary, with lossless synthetic payloads and public traceable outcomes. The producer MUST NOT write business records directly. Incoming demand MUST NOT automatically execute reservations, fulfillment, stock replenishment or user proposals. Amended by feature 168: under its own bounded settlement authority the synthetic source MAY issue and post the invoice it states for an order and MAY record customer payments, allocating only a reference the payment states unambiguously; reductions, refunds, write-offs and ambiguous allocations remain confirmed human actions.
- **FR-019**: Generation MUST have bounded backlog and delivery concurrency, visible throttling/error recovery and no uncontrolled catch-up. Integration status MUST distinguish generated, pending, imported and failed orders, configured rate, last success and next arrival, with intake and resulting-record links. Exact resource bounds must be selected and tested during planning.
- **FR-020**: Controls and deliveries MUST enforce tenant, actor and source authorization, stop on disconnection/archive/revocation, and exclude the separate Atlas execution fixture. Historical baseline records/windows MUST remain intact; new activity MUST be identifiable by source/run and actual business dates. Integration controls MUST meet FR-013's localization and accessibility scope.

- **FR-021**: First and later canonical demo creation offer an explicit live-simulation choice. Confirming creation with live simulation automatically connects Demo Data and starts its schedule at 60 orders/hour, without another connection or Start step. Static demo creation remains available. Empty/ordinary/execution creation cannot request this shortcut. Creation is not reported ready until the requested integration setup succeeds; explicit retry reuses the same tenant, connection and schedule. Completed creation replay never resumes a subsequently paused/stopped source. Reads never provision or start work.

### Domain and Traceability Requirements

- **DR-001**: Synthetic records MUST use the shared application services and preserve lossless SourceRecord → Document/DocumentLine → Reality links where applicable. Every seed/read/action MUST enforce tenant and actor scope.
- **DR-002**: Operational state MUST derive from Reality using opaque identities and shortest true relationships. Sandbox/content selection MUST NOT introduce document fulfillment statuses or new inventory/finance rules.
- **DR-003**: Source-stated amounts and business dates MUST remain authoritative. Historical ingestion must not backdate audit creation; read-time observations must not become stored source authority.
- **DR-004**: Company creation authorizes only the disclosed setup. Explicit Start authorizes the disclosed continuous synthetic order intake until paused or stopped; it does not authorize later operational actions. Controls invoked through Chat require preview and explicit confirmation. Later business mutations, including the execution example, retain existing preview and explicit confirmation requirements.

### Key Entities

- **Account/application**: Person and access-request context; a supplied company name is not a created tenant.
- **Company**: Isolated operational tenant with authorized membership and an identifiable environment.
- **Starting content**: Creation choice between empty business data and the canonical synthetic profile; not a new business authority.
- **Demo profile and manifest**: Versioned synthetic story, date anchor, actual record references, expected cases and declared limitations.
- **Demo Data connection and run**: Tenant-scoped synthetic source configuration and a reproducible sequence of ongoing order deliveries; not a new operational order authority.
- **Execution fixture**: Separately isolated, repeatable supervised-action starting state linked conceptually to the profile, without duplicating analysis records.

## Success Criteria

- **SC-001**: First-time acceptance journeys require zero retyping of an existing company name and exactly one successful company creation, followed directly by that company.
- **SC-002**: Both first and later creation pass all permitted combinations: empty ordinary company, empty Sandbox and demo Sandbox. Forbidden combinations cannot bypass admission.
- **SC-003**: Every ready demo satisfies the declared catalog counts, all ten order cases and both 42-day history windows; identical version/anchor produces equivalent business expectations across entries.
- **SC-004**: Cancelled setup creates zero companies; duplicate submission/recovery creates at most one company per creation request; empty setup creates zero synthetic business records.
- **SC-005**: A repeat execution leaves analysis and previous audit evidence unchanged; confirmed one-unit reservation produces exactly the stated stock deltas.
- **SC-006**: Every FR/DR has an acceptance scenario and planned proof; all creation states pass the language, theme, viewport and keyboard review before release.

- **SC-007**: In a healthy controlled run at 60 orders/hour, ten elapsed schedule intervals produce exactly the distinct imported orders their deliveries planned (ten when each delivery carries one order); replaying deliveries produces no duplicate effects, and the two orders of one delivery keep distinct stable identities. Closing the browser does not stop the run.
- **SC-008**: After acknowledged pause/stop, zero additional orders are scheduled; resumption generates no paused-period backlog. Prior records survive stop/disconnect and cross-tenant controls produce no effects.
- **SC-009**: Every imported continuous order is traceable to its synthetic intake and run; no arrival itself changes physical stock or confirms a reservation or shipment. Since feature 168, synthetic invoices and payments follow the same traceability and are recorded only through the shared payment intake core.

## Assumptions and Dependencies

- The owner explicitly instructed continuation with spec 146 after the completed scheduler/worker foundation. This authorizes product-scope planning and implementation preparation. Concrete new persistence and authority boundaries are documented in plan.md/data-model.md for the repository-required review; no live deployment is authorized.
- Retaining access-application questions with explicit purpose and reusing their name is the smallest first increment. Removing the access-qualification process is outside scope.
- Environment and content remain distinct service fields, represented by one goal-based UI choice (FR-023). Existing practice authorization still applies even where business services are identical. Empty Sandbox support is intentional; it is not a claim that the current practice implementation already permits it.
- Spec 144's broader demo remains draft; its seven accepted read improvements are not proof that the dataset is implemented or deployed. This specification makes that profile the intended shared onboarding standard, without changing spec 144's approval record.
- Continuous mode initially generated incoming orders only; feature 168 added invoices and customer payments through a second schedule. Shipment, returns and fault simulation remain future simulator scope. It reuses profile vocabulary and normal integration intake, not a second domain implementation. Continuous intake is a new requirement, not a claim of a currently running connector.
- Continuous intake MUST register `demo.generate_orders` through spec 147's shared job contract. Its scheduler materializes interval work; its independent worker invokes the handler. No browser/API timer or demo-only scheduling loop is allowed. The handler uses the shared transaction-bound source intake; if ingestion currently commits internally, adapt that shared service rather than bypass the scheduler transaction contract.
- The source can run until explicitly stopped, subject to visible backpressure and existing Sandbox lifecycle/authorization limits. A fixed historical fixture remains available by leaving the optional source stopped.
- Delivery order: clear creation and operational/inventory/execution foundation plus optional continuous incoming orders first; comparable history second; supported price/cost scenarios third. A partial internal milestone must not be advertised as the complete canonical demo.
- The detailed interface inventory, permissions, pagination/completeness, history access, currency/unit/time semantics and cache-write disclosures remain owned by spec 144 and its assessment. Reuse those contracts and record gaps; only its reviewed minimum read improvements are dependencies, not a new analytics stack.
- The new application foundation and legacy practice entry coexist. Planning must select the actual rollout baseline and reconcile routing without forced data migration or unapproved practice-policy expansion.
- No schema expansion is authorized by this specification; any necessary persistence change requires concrete proof and review in planning.

## Open Questions

No unresolved product-scope clarification. Current implementation/schema review status is recorded in review.md; the selected baseline preserves existing admission and Playground access boundaries.

## Requirement Traceability

The acceptance mapping below is implemented. Concrete executable tests are listed in tasks.md and observed verification results in quickstart.md.

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1-1/2 | Access copy, retained-name and no-repeat browser journeys |
| FR-002 | US1-3/4 | Successful routing, existing member and invitation journeys |
| FR-003, FR-004 | US2-1/2/3 | Creation-entry and permitted content/environment matrix |
| FR-005 | US1-5 | Pending/active/disabled-entry authorization tests |
| FR-006 | US2-4/5, US3-5 | Cancel, validation, concurrent retry, lost response and partial seed tests |
| FR-007 | US2-2/6 | Empty-record assertions and existing-company continuity tests |
| FR-008 | US3-1 | Fixture count/name/reference and entry equivalence proofs |
| FR-009 | US3-2/3 | Ten-order and stock/procurement business stories from spec 144 |
| FR-010 | US4-1 | Window, cohort, currency, credit and gross-metric fixture proofs |
| FR-011 | US3-4, US4-2 | Manifest and capability-gap coverage review |
| FR-012 | US4-3/4/5 | Unexecuted seed, supervised success/refusal and repeat isolation |
| FR-013 | US2-7 | Four-language, theme, responsive and keyboard review |
| DR-001, DR-002 | US1-5, US3-2/3/4 | Tenant isolation, shared-service parity and provenance proofs |
| DR-003 | US3-4, US4-1/2 | Source-value preservation and business/audit-time checks |
| DR-004 | US2-4, US4-3/4 | Setup consent and separate business-action confirmation proofs |
| FR-014, FR-015 | US5-1/2 | Discovery, stopped-by-default, prerequisite preview and incompatible-reference tests |
| FR-016 | US5-3/6 | Controlled-clock schedule, browser-independent run, rate change and duplicate Start tests |
| FR-017 | US5-5/6/8 | Pause/resume/stop/restart, retained history and deterministic identity tests |
| FR-018 | US5-4 | Normal intake/interpretation trace and no automatic operational action proof |
| FR-019 | US5-6/7 | Backpressure, retry, counts and partial/error recovery tests |
| FR-020 | US5-8/9/10 | Cross-tenant/revocation/archive boundaries, baseline isolation and accessible controls |
| DR-001, DR-002, DR-003 | US5-4/6/9 | Synthetic payload, shortest links, idempotency and business-time integrity |
| DR-004 | US5-1/3/4/5 | Explicit run authorization, confirmed Chat controls and no automatic downstream execution |

## Live creation clarification — 2026-09-09

The owner clarified that selecting a demo company with live simulation must complete integration provisioning and activation automatically. That creation confirmation authorizes both actions; manually connecting a source remains available for later additions. FR-021 extends FR-014–017; no real external connector credentials or operational execution are implied.

FR-021 acceptance: confirmed live creation yields one running connection at 60/hour for active and pending owners; invalid content/environment is rejected; injected Start failure leaves no partial connection and recovers the same tenant; replay after Pause preserves the paused schedule. T041–044 supply service/API/browser and regression evidence.

Spec 146 supersedes the unified-app blanket refusal of owned practice companies. Authorized practice companies open in the unified app with a compact Sandbox badge beside the company name; existing server-side tenant and mutation policies remain authoritative. Retired /playground browser URLs remain retired, and no old workspace is reinstated.

## Company list clarity — FR-022

Each company list item groups its name, environment/content labels, role, switch action and management buttons within one visible card. Show Company, Sandbox or Demo company from authoritative tenant/profile metadata; show connected live simulation state (running, paused, stopped, disconnected) separately. Do not imply static demo data is live. Management actions remain scoped to the displayed company and hidden from non-owners. Bootstrap metadata is membership-scoped and read-only; no new persistence is needed. The owner requested this clarification during the port-8080 rollout.

## Goal-based creation — FR-023

The owner approved one choice among Start your own company (business/empty, default when eligible), Create an empty Sandbox (sandbox/empty), and Try demo data (sandbox/international_demo). Remove the separate content/environment selectors. Show only eligible choices. Only demo reveals optional Enable live simulation, off by default; leaving demo clears live intent. Explain automatic integration setup and recurring demo orders, with the existing 60/hour rate. Preserve first/later creation, required name, confirmation and request recovery.

## Required name feedback — FR-024

Mark the company name visibly required and explain that it names this company or Sandbox. Keep Create enabled for a missing name. Submission with empty/whitespace-only name shows a localized inline error, marks the field invalid, focuses and scrolls it into view, and sends no request. Preserve selected startup/live options. Correcting the name clears the error. Busy/eligibility guards remain.

## Automatic entry — FR-025

Successful creation automatically opens the ready company, including a recovered ready request. No profile/management decision is required. Show a dismissible company-created confirmation in the destination. Preserve durable request recovery; if opening fails retain the receipt and offer only Retry opening, without recreating or restarting the company/source. Integration management remains in Integrations.

## Sandbox clarity and live activity refinement

FR-026: compact persistent Sandbox badge beside company name, including mobile; authorized Sandbox Reports and contributor reads work, mutation/admission restrictions unchanged. FR-027: Demo Data has clear status, primary start/pause/resume, changed-rate apply and directly visible secondary stop/disconnect actions without a redundant disclosure; the stopped-state action is unambiguously labelled Start simulation, while Resume is reserved for paused state. Existing confirmation is preserved and visually separates its explanation from Confirm/Cancel. FR-028: live activity shows latest 25 real imports ordered by created_at DESC, id DESC, held timestamps/order numbers and explicit truncation. Read-only polling every five seconds while visible, no overlaps or old-scope responses, preserve edits/confirmations and stale rows with warning. Scheduled arrival is not a guaranteed execution time; import state does not assert shipment.

FR-029: put Demo Data directly below Companies in the Company navigation group for companies with canonical demo data or a connected Demo Data source (including paused/stopped/disconnected state). It opens /app/demo-data with current tenant. Remove the large Demo Data panel from Integrations. The standalone page hosts the existing controls/live activity; direct access still uses service eligibility.

## Sandbox exception investigation correction

**FR-030**: Authorized practice/demo companies can read the Exceptions register,
filters/pagination and finding details through the same canonical exception services
as ordinary companies. These reads must not demand ordinary-workspace mutation
permission. Tenant admission, foreign-record isolation, canonical derivation and
all existing mutation restrictions remain unchanged. The previous ordinary-only
read guard caused the observed Sandbox error instead of showing existing findings.
Regression evidence: `test_company_setup_unified.py`, `test_playground_api.py`,
existing `test_attention_reads.py` and `test_unified_operations_api.py`.

## Setup progress presentation — FR-031

**FR-031**: First-company and dialog setup distinguish loading, creation, opening and recoverable failure visually. Busy states show a visible reduced-motion-aware spinner, one status message and the requested company name when known; no retry action or start-choice instructions appear while busy. Idle interrupted requests retain explicit same-request retry, and ready receipts retain automatic navigation. Use shared theme tokens, responsive spacing and en/de/nl/es translations. No API, consent, request identity or company-creation behavior changes.

## Retrospective simulation entry — FR-032

**FR-032**: Owner cards for existing Sandbox/demo companies expose Live simulation, opening the existing company-scoped Demo Data page without mutation or replaying historical fixtures. Existing preview, explicit connection/start controls, rate, pause and resume remain authoritative. Unsupported practice companies, including Storyline companies, explain the limitation and offer a separate Demo Sandbox through normal confirmed company setup with demo/live choices initially selected when allowed. Existing companies remain unchanged. Ordinary company/member cards do not expose the action; server eligibility and admission remain authoritative. All new copy supports en/de/nl/es and mobile.

FR-032 presentation refinement: the unavailable simulation state uses a padded, width-constrained shared surface with a clear heading, readable supporting copy and one primary creation action. Mobile, theme and existing dialog behavior remain intact.

FR-032 correction: unsupported Sandboxes show an explicit unavailable message and link to Companies, where normal New company can create an empty Sandbox. Do not embed another creation dialog or suggest historical data. Supported existing Sandboxes keep the existing connection controls and receive only new simulated activity after start. This supersedes the separate-demo creation shortcut above.

FR-032 unavailable copy must explain the current compatibility boundary: live simulation supports empty/standard demo Sandbox setups; Storyline Sandboxes use a different data setup. Describe the general boundary without inferring a specific backend denial reason from every 403/404.

FR-032 connection preview presentation: group exactly the server-provided missing references by kind with counts and keyboard-accessible expandable names. Keep the no-stock/no-history notice visible. Use a separated, responsive confirmation/cancel row; opening, inspecting and cancelling never connects or starts simulation.
