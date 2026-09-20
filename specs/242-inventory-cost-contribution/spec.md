# Feature Specification: Evidenced inventory cost and contribution margins

**Feature Branch**: `242-inventory-cost-contribution` (based on `origin/main`)
**Created**: 2026-09-18
**Status**: Production model and staged implementation approved; external usability and reference-host qualifications are deferred non-blocking follow-up gates
**Language**: English
**Input**: Design a system-compatible concept for reliable actual purchase cost, inventory valuation, DB1 and DB2 across business reporting dimensions.

## Restart checkpoint and remaining work (2026-09-19)

**Resume at T194.** T192/T193 are implemented: four captured-report cache tables,
internal build/CAS-publication/fixed-read/disposal services and their PostgreSQL proofs.
The next step connects this captured generation to the existing graph and saved analyses.
Historical selected inventory/contribution graph reporting already exists.

T194 uses one explicit `captured_cost_context` containing a nonempty opaque
`generation_id`. The context is valid only for a standalone inventory or contribution
valuation question and is mutually exclusive with the existing historical inventory and
contribution contexts. Graph execution verifies the sealed generation once, exposes only
its typed cached rows and known-subtotal coverage, and returns the captured basis metadata.
Saving and reopening an analysis preserves the exact generation identity; it never follows
the publication pointer or substitutes a later review. Unknown captured members remain in
the required coverage count without acquiring inferred dimensions or zero amounts.

The exact restart instructions, completed code, approvals, open task mapping, test evidence
and shared-workspace constraints are in [HANDOFF.md](HANDOFF.md). Read it before continuing.

Still open: captured-report public adapters/selector; shared-worker orchestration and
company-scale qualification; complete financial population/historical context; operational
EK/DB explanations; cost exceptions and demo; broader inventory/returns and commercial
matching; evidenced carrying-value assessments; remaining allocation/tax/conversion cases;
and full product verification/release. Existing captured reports retain the ten-subject
bound, explicit gaps, known subtotals only and null final totals/rates. They are not a
completed company valuation. See the handoff for the individual T078–T090/T194 obligations
and the distinction between functional gaps and old unclosed verification markers.

## Context and Intent

### Problem

Reality knows physical quantities, agreed prices and received financial amounts, but
cannot explain the acquisition cost remaining in stock or consumed by a sale. A current
purchase price is not historical acquisition cost. Operational gross postings and
cost-center assignments do not establish contribution margin. Missing costs must not
make a business appear profitable.

### Scope

Propose a coherent target capability and phased delivery for purchased goods, evidenced
direct service costs and external manufacturing cost evidence. Distinguish actual
acquisition cost, provisional cost, commercial contribution and HGB carrying value.
Cover positions, orders, products, customers, channels and company periods through the
same underlying amounts. Show unassigned and unsupported scope explicitly.

The proposed commercial definition is DB1 = net sales revenue minus acquisition cost
of goods sold/direct purchased service cost; DB2 = DB1 minus attributable selling and
fulfilment costs. These names describe this company's proposed management profile,
not a statutory definition. Full formulas and boundaries are in [research.md](research.md).

### Non-Goals

- No automatic company policy activation, deployment or claim of HGB compliance.
  Production receipt-cost implementation and its required migrations/tools are now
  authorized by the approval recorded below; inventory and DB follow in staged slices.
- No general ledger, automatic statutory postings, tax calculation, tax-balance-sheet
  engine, arbitrary formula language or replacement of received amounts.
- No automatic allocation of all overhead to products; DB2 is not company profit.
- No internally generated manufacturing cost, production/WIP costing, payroll or
  consolidation engine. These remain explicit expansion boundaries, not zero costs.
- No universal exact physical purchase identity for fungible goods: actual evidenced
  costs and a disclosed consumption assumption are distinct concepts.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md), especially principles I–VIII.
- [Data model](../../docs/DATA_MODEL.md), [inventory](../../docs/features/inventory.md),
  [web contract](../../docs/WEB_SPEC.md), [workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md).
- [Finance scope](../148-accounting-journal-cost-centers/spec.md): this proposal extends
  its explicit valuation/profitability exclusions only after approval; existing gross
  postings, received components and assignments retain their meaning.
- Specs 025, 118, 122, 124, 132, 173, 179, 224, 229, 230, 232 and 233 provide pricing,
  correction, billing, opening, physical, projection and analysis foundations.
- Specs 033 (benchmark harness and its established 10,000-orders/day read contract),
  146 (canonical demo profile), 178 (Exceptions and Rules register) and 228 (Analysis
  Builder) are used directly by FR-018 and FR-024 to FR-026; this feature extends them
  through their existing contracts and does not fork their conventions.

## User Scenarios & Testing

### User Story 1 - Explain the cost of received goods (Priority: P1)

A purchaser inspects the cost of a receipt including attributable inbound freight,
duty and price reductions, and sees exactly which evidence is still missing.

**Why this priority**: It establishes the basis for both stock value and margins.
**Independent Test**: Fixture A in [verification.md](verification.md).

**Acceptance Scenarios**:

1. Given 100 received units, a stated goods amount of EUR 1,000, inbound freight of
   EUR 100 and an attributable credit of EUR 50, when all are confirmed as assigned to
   that receipt, then acquisition cost is EUR 1,050 and derived unit cost EUR 10.50.
2. Given only the agreed purchase price, when actual cost is requested, then actual
   remains incomplete; a separately labeled estimate may use the agreed evidence.
3. Given a split receipt or shared freight invoice, when amounts are assigned, then
   the assigned parts and unassigned remainder reconcile without duplicating costs.

### User Story 2 - Explain remaining stock and consumed cost (Priority: P1)

An operator sees quantity and value independently, with the method, cost evidence and
cost coverage behind every valuation.

**Why this priority**: Quantity alone cannot answer what stock is worth.
**Independent Test**: Fixtures B–D and G.

**Acceptance Scenarios**:

1. Given complete receipt costs, when goods are sold or transferred, then consumed and
   remaining acquisition values reconcile; a transfer changes no company total.
2. Given a received quantity with no cost, negative stock or unknown opening cost, when
   viewing inventory, then the quantity remains visible and a complete value is refused.
3. Given a late attributable credit, when rereading current knowledge, then the delta
   affects both remaining and consumed portions; an earlier knowledge view is reproducible.
4. Given an HGB valuation review, when a lower supported value is accepted, then carrying
   value changes separately from historical acquisition cost; a later recovery is bounded.

### User Story 3 - Explain DB1 and DB2 across the business (Priority: P2)

A business owner traces order margins to revenue, consumed cost and direct selling
costs, then groups the same amounts by product, customer, channel or period.

**Why this priority**: Reporting requires consistent unit economics, not unrelated KPIs.
**Independent Test**: Fixtures A, E, F and H.

**Acceptance Scenarios**:

1. Given matched billed-and-fulfilled quantities and known costs, when a margin is
   requested, then DB1 and DB2 follow the declared profile with independent coverage.
2. Given a partial invoice/delivery, return, credit or unbilled shipment, when reporting,
   then unmatched revenue/cost remains visible and is not combined into a final margin.
3. Given a shared shipping charge and an explicit allocation, when grouping reports,
   then totals reconcile including unassigned scope and no invoice/receipt fan-out occurs.
4. Given mixed currencies or unsupported production costs, when requesting all-company
   margin, then unconverted or unsupported scope blocks a complete combined amount.

### User Story 4 - Review completeness and historical changes (Priority: P2)

A finance user reviews incomplete cases, accepts a cost scope as complete and later
explains changes without overwriting a previously reviewed result.

**Why this priority**: A figure is only useful when its limitations and history are visible.
**Independent Test**: Fixtures D, G and I.

**Acceptance Scenarios**:

1. Given missing expected freight, when reviewing completeness, then final cost is blocked
   until evidence arrives or an authorized zero/not-applicable declaration is confirmed.
2. Given a reviewed scope and later evidence, when inspecting history, then the original
   basis remains reproducible and current results show the change and require new review.
3. Given another tenant, duplicate request or stale preview, when assigning costs, then
   isolation, idempotency and confirmation rules prevent leakage or duplicate assignments.

### User Story 5 - Keep financial judgments with authorized people (Priority: P1)

Only an active owner confirms a cost attribution, valuation policy, tax or FX treatment,
economic ownership, impairment or completeness declaration; everyone else reads.

**Why this priority**: Authorization ships with the first slice. A cost attribution any
member can confirm is a defect in the first release, not later hardening.
**Independent Test**: Fixture I.

**Acceptance Scenarios**:

1. Given an ordinary member, when reading values, then permitted company data is visible;
   attempts to confirm policies, allocations, tax treatment or completeness are denied.
2. Given an owner demoted between preview and execution, when the confirmation arrives,
   then it is refused with no partial write and the preview is marked stale.
3. Given an agent-prepared financial proposal, when an active owner explicitly confirms
   it, then execution is permitted through the shared service after rechecking owner
   authorization and the previewed input revision. Without that confirmation, an agent,
   projection worker or scheduled job cannot approve a financial judgment; agent identity
   never elevates the initiating actor.

### User Story 6 - Use the feature in daily work at scale (Priority: P2)

An operator opens order margins, inventory value, the Exceptions queue and existing saved
analyses promptly, finds actionable cost gaps, and learns the complete flow in the demo.

**Why this priority**: Correct calculations must remain usable on a realistic company.
**Independent Test**: Fixtures J-M, including the planned benchmark protocol.

**Acceptance Scenarios**:

1. Given the scale fixture, when opening order contribution, an inventory or report page,
   the Exceptions queue or a chat/MCP cost answer, then FR-018 response budgets hold;
   missing/stale projections are explicit and no read starts a whole-history rebuild.
   Reconstruction completes within its separate budget.
2. Given the same cost gap in inventory and Exceptions, when underlying evidence resolves
   it, then both surfaces clear consistently through the shared finding derivation.
3. Given a fresh canonical demo company, when inspecting its completed trade example,
   then actual EK, inventory cost, DB1 and DB2 reproduce fixture A and trace to sources.
4. Given a saved analysis, when selecting DB measures, then the existing builder and
   reporting tools return identical supported results, coverage and grouping refusals.
5. Given a new cost record reference, when it is opened from an explanation, the web, the
   CLI or MCP, then all of them resolve the same record under the same name and scope.

### Edge Cases

Free goods, samples, replacements, zero/negative revenue, rebates arriving after sale,
partial receipts/invoices, pooled freight, recoverable/nonrecoverable tax, FX, unit
conversion, unknown chronological order, negative stock, missing opening layers,
damaged returns, write-offs, corrections, reservations, drop shipping, consignment,
goods in transit, supplier substitutions, bundles, services, manufactured goods,
dimension changes, period boundaries, duplicate evidence and stale confirmations.

## Requirements

### Functional Requirements

- **FR-001**: Show separately agreed EK, actual acquisition unit cost, estimated unit
  cost, consumed cost, and carrying value; never silently substitute one for another.
- **FR-002**: Assign received cost components to exact receipt quantities or direct
  cost targets, preserving original amount, currency, unit and evidence identity.
- **FR-003**: Support explicit signed cost categories, shared-cost allocations and
  residuals; prohibit double inclusion, incompatible bases and allocation beyond scope.
- **FR-004**: Require a reviewed valuation policy for each valuation scope; propose
  FIFO for interchangeable trade goods and evidenced specific identification where
  appropriate. Never select/change an accounting method silently.
- **FR-005**: Derive remaining and consumed acquisition costs consistently, preserving
  value through transfers and distinguishing sales, returns, loss and corrections.
  A customer return enters FIFO at its economic return time with the original consumed
  cost, not its original purchase age; it does not alter earlier consumption. Specific
  identification continues to follow the actual evidenced individual item.
- **FR-006**: Require opening quantities and sufficient cost history for the selected
  method; unknown costs and negative stock remain explicit valuation gaps.
- **FR-007**: Propagate late costs and credits to affected remaining and consumed values;
  reproduce effective-time and knowledge-time views with policy/version provenance.
- **FR-008**: Distinguish physical location from economic attribution, including
  consignment and transit; ambiguous attribution prevents finalized valuation.
- **FR-009**: Maintain separate supported HGB write-down/recovery decisions and explain
  acquisition-to-carrying-value reconciliation without changing source prices.
- **FR-010**: Match revenue and consumed costs at evidenced quantity/amount scope;
  order, shipment, invoice and payment dates cannot silently substitute for each other.
- **FR-011**: Derive DB1/DB2 using the versioned commercial profile, separately showing
  attributable costs, allocated costs, residuals and inventory valuation effects.
- **FR-012**: Aggregate by position, order, product, customer, channel and period with
  identical atomic contributions, stable dimension semantics and an unassigned bucket.
- **FR-013**: Separate currencies and incompatible units unless a reviewed conversion
  basis exists; derived conversion never rewrites an original source value.
- **FR-014**: Show independent coverage for revenue, goods cost and DB2 costs; distinguish
  unknown, provisional, evidenced and reviewed-complete-at-cutoff results. Never
  present a known-cost subtotal as total margin or use absent cost as zero.
- **FR-015**: Require confirmed, auditable completeness declarations and revisions;
  later relevant evidence invalidates current completeness without erasing history.
- **FR-016**: Every important number exposes its formula, policy, effective/knowledge
  cutoff, inputs, allocations, missing basis and source trail on all supported surfaces.
- **FR-017**: Handle free goods, returns, rebates, shipping-only/service sales and
  evidenced kit/production costs through explicit supported rules; label unsupported
  internal production/WIP or missing component scope instead of fabricating a cost.

- **FR-018**: Meet p95 service response times of 500 ms for one order (up to 100
  positions), 2 s for the first 100 inventory rows plus filtered totals, and 3 s for
  a supported monthly grouped contribution report on fixture J. The Exceptions/attention
  queue's first page including its counts must hold 2 s p95 with the new cost classes
  active, and a chat/MCP cost or margin answer 3 s p95; neither may derive contribution
  across the whole tenant to answer one question. A full reconstruction
  of that fixture must complete within 120 s; an affected single-receipt update must
  become visible within 30 s under the stated benchmark load. Missing/stale results
  return their state within the same read budget, never an apparently current value.
- **FR-019**: Reuse existing company permissions: active owners alone may confirm or
  revise valuation policies, cost attribution, tax/FX/unit treatment, economic ownership,
  write-down/recovery assessments and completeness/zero/not-applicable declarations.
  Active members may read within existing access boundaries but cannot confirm these
  decisions. Enforce authorization at preview and execution for every adapter; background
  projections may derive results but cannot approve financial judgments. No finance role
  is invented by this feature; delegated finance approval requires separate role design.
  Agents may prepare proposals and execute an explicitly owner-confirmed proposal through
  the same service, with authorization and data revision rechecked at execution; they
  cannot supply their own approval or bypass the confirming owner.
- **FR-020**: Exclude evidenced recoverable input tax from acquisition cost and include
  evidenced attributable nonrecoverable tax exactly once. Unknown recoverability blocks
  complete cost. Use supplied amounts/classification, never compute missing tax or net
  from rates. FR-019 governs classification approval and revisions.
- **FR-021**: Treat evidenced purchase cash discounts (skonto) as acquisition reductions
  attributed to the original purchase scope, affecting remaining and consumed cost.
  A payment shortfall alone is not skonto evidence. Expose unresolved differences;
  prevent repeating a discount already included in the selected received amount.
- **FR-022**: Preserve original monetary and quantity precision in evidence. The initial
  costing contract supports amounts and base quantities to four decimal places, with
  no silent truncation. Conversion ratios retain their evidenced precision; a conversion
  requiring a finer base quantity is unsupported until the quantity contract is
  extended. Allocate signed cost totals in 0.0001 currency-unit increments using
  largest absolute remainders and opaque-target-ID tie breaking, restoring the sign
  afterwards. For sequential consumption of each cost layer, compute cumulative cost
  as half-even rounded original layer cost times cumulative consumed quantity divided
  by original layer quantity, to four decimal places. Each issue takes the difference
  from the previous cumulative amount; remaining cost is original cost minus cumulative
  consumption. Apply this over the complete canonical sequence before report filtering.
  Late cost corrections recalculate that sequence at a new knowledge cutoff, preserving
  prior-cutoff reproducibility. Keep ratios unrounded until these amount boundaries.
  Show unit costs to six
  decimals and monetary UI values to the currency's display precision while exposing
  exact four-decimal totals in inspection/export. Unsupported input precision is an
  explicit gap until supported. Display rounding never feeds valuation or allocations.
- **FR-023**: Use the canonical English/German vocabulary below across catalog measures,
  tools, explanations, exports and operational pages. Localized labels are data; all
  repository prose and identifiers remain English. Other supported locales follow the
  existing translation/fallback contract rather than independently renaming DB terms.
  `DB1` and `DB2` stay untranslated abbreviations in every locale; Dutch and Spanish long
  forms follow the catalog's existing locale coverage, and a locale without a label falls
  back instead of gaining a second name for the same measure.
- **FR-024**: Extend the existing analysis catalog/builder and saved-report pipeline with
  service-backed cost/contribution measures and honest grain, currency, unit and temporal
  contracts. Reuse the same services for operational detail; no separate reporting engine
  or standalone margin builder. Inventory values are point-in-time/non-additive across
  time; DB amounts are additive only over disjoint matched slices; rates are recomputed
  from totals. Unsupported traversal/coverage is refused or explicitly partial, never
  converted into a plain sum over evidence or a zero from missing amounts.
- **FR-025**: Register missing acquisition cost, unassigned cost component, stale cost
  review and negative actual DB1 as shared operational exception classes inside the
  existing catalog and under its existing field contract: an existing severity value,
  an accountable area named the way that catalog names areas, a derivation, an existing
  `record_type`, an authority reference, clearing conditions and test evidence. No new
  severity word, area vocabulary or subject kind is introduced by this feature; a finding
  whose natural subject has no existing record type must attach to one that exists or
  wait for a separately reviewed catalog extension. Each class also takes a contiguous
  rank in the shared class ordering and raises its pinned count. Reuse the existing
  Exceptions and Rules register. Negative-DB1 detection requires complete evidenced
  DB1; incomplete scope yields a cost-gap finding instead. Preserve the existing
  agreed-purchase-price comparison as a different class. Coverage summaries and
  exception findings must use the same cost-gap facts and scope, including explicit
  freshness.
- **FR-026**: Version the canonical demo profile with at least one complete source-backed
  chain reproducing fixture A, one deliberate missing-cost case and one late-cost/return
  case. Initialize through existing company setup and shared intake/services with only
  explicitly reviewed initialization authority; no blanket financial approval, direct
  ORM seeds or second queue. Preserve lesson boundaries, replay completion markers and
  later source controls. Ongoing synthetic cases may remain incomplete but cannot be
  advertised as fully costed without evidence.

- **FR-027**: Expose every new cost record reference - cost attribution, valuation
  policy, economic attribution, valuation assessment and cost scope review - through the
  existing record-reference path: an inspector name and page, web pass-through, CLI, MCP
  record reads and the resource catalog's vocabulary, with generated Tool Usage
  documentation regenerated when catalogs or tools change. A reference that resolves on
  one surface and not on another is an incomplete delivery, not a later addition.

### Canonical terminology

These label pairs are intentional product-localization data, not German repository prose.

| English label | German label | Meaning |
|---|---|---|
| Agreed purchase price | Vereinbarter Einkaufspreis | Received agreement; not actual acquisition cost |
| Actual acquisition unit cost | Tatsächliche Anschaffungskosten je Einheit | Evidenced derived EK including attributable costs |
| Estimated acquisition unit cost | Geschätzte Anschaffungskosten je Einheit | Explicit provisional cost |
| Acquisition cost | Anschaffungskosten | Historical attributable acquisition amount |
| Cost of goods sold | Wareneinsatz | Historical acquisition cost matched to sold goods |
| Consumption method | Verbrauchsfolgeverfahren | Disclosed accounting consumption convention |
| Inventory acquisition value | Bestandswert zu Anschaffungskosten | Historical cost remaining in stock |
| Carrying value | Buchwert | Value after supported assessments |
| Write-down | Abwertung | Supported decrease in carrying value |
| Reversal of write-down | Zuschreibung | Bounded supported recovery |
| Contribution margin 1 (DB1) | Deckungsbeitrag 1 (DB1) | Declared commercial profile, absolute amount |
| Contribution margin 2 (DB2) | Deckungsbeitrag 2 (DB2) | DB1 less attributable selling/fulfilment costs |
| Contribution margin 1 rate | Deckungsbeitragsquote 1 | DB1 / positive net revenue |
| Contribution margin 2 rate | Deckungsbeitragsquote 2 | DB2 / positive net revenue |
| Reviewed complete at cutoff | Zum Datenstand vollständig geprüft | Scoped evidence-completeness review |
| Unvalued quantity | Menge ohne Kostennachweis | Quantity whose actual cost is incomplete |

### Domain and Traceability Requirements

- **DR-001**: Preserve Source → Evidence → Reality. Record received values exactly;
  expose costs and margins as derived observations, without making them new authoritative
  Facts. Bounded live derivation or rebuildable projections may serve reads; no request
  may require unbounded history replay. A projection is never authoritative evidence.
- **DR-002**: Use the shortest real identity links for cost attribution. Do not add
  duplicated source/document references to movements or reservations for reporting.
- **DR-003**: All business relationships and reads are tenant-scoped. All writes use
  shared application services; mutating chat actions retain preview/confirmation.
- **DR-004**: Allocation, policy and review decisions are auditable and versioned;
  derived output is rebuildable and never drives circular valuation input.
- **DR-005**: Existing inventory quantity, operational ledger, source lifecycle and
  cost-center assignment semantics remain intact; no duplicate business rules in UI.

### Key Entities

- Received cost evidence: existing financial amounts on actual evidence granularity.
- Cost attribution: an accountable decision connecting a cost component to its use.
- Valuation policy: scope, method, currency/unit basis and effective version.
- Economic attribution: evidence of whose inventory the quantity represents.
- Valuation adjustment: supported lower-value/recovery assessment at a cutoff.
- Cost completeness review: scoped statement about expected and accounted-for costs.
- Cost and margin observations: derived explanations, never independent authority.

## Success Criteria

Owner decision on 2026-09-20: SC-002 and the dedicated-reference-host portion of
SC-006 remain required before making the corresponding usability or reference-scale
claims, but they do not block the provisional technical closeout of feature 234. The
repository must keep both qualifications visible and unclaimed until they are run.

- **SC-001**: All numeric fixtures in verification.md reconcile exactly at their stated
  precision, including signed corrections and unassigned remainders.
- **SC-002** *(deferred external qualification)*: In a moderated task, at least four of five operations users can identify
  an order's DB1/DB2, explain one included cost and find its source within two minutes,
  without developer assistance; use the task protocol in fixture M.
- **SC-003**: Every missing-basis fixture refuses a complete result and names the missing
  scope; every supported complete fixture has an inspectable source trail.
- **SC-004**: All supported report regroupings conserve totals, and repeated historical
  reads with identical inputs/cutoffs/policy produce identical values.
- **SC-005**: Cross-tenant, replay and stale-confirmation fixtures demonstrate no leakage,
  duplicate amounts or unnoticed replacement of reviewed decisions.

- **SC-006** *(reference-host execution deferred; local orchestration remains in scope)*: FR-018 read, refresh and reconstruction budgets - including the Exceptions
  queue and chat/MCP answers - pass on the reproducible fixture J; publish measured
  percentiles, resource limits and cold/warm results.
- **SC-007**: The complete demo trade scope has 100% of its remaining quantity valued
  and its fulfilled/billed quantity cost-matched; the deliberate missing-cost scope
  remains visibly incomplete. Coverage is quantity-based per compatible item/unit,
  not a fabricated cross-unit or monetary percentage. Fixture M proves both states.

## Assumptions and Dependencies

- The original concept request was followed by explicit Phase 0 experiment authorization.
  Product implementation beyond that experiment remains gated; proposed defaults are not
  activation of an existing company accounting policy.
- The first operational scope is purchased trade goods. "Across everything" means
  consistent business dimensions with explicit coverage, not invented costs for all
  possible industries or unsupported accounting processes.
- FIFO is the proposed first derived method, with specific identification for evidenced
  individual goods. Existing company policies take precedence; a company requiring
  average cost/LIFO must wait for that method or use clearly separated external valuation.
- DB1/DB2 use the commercial profile above. Product-fixed-cost DB2 is a different profile
  and must not reuse the same unlabeled measure.
- HGB policy suitability and final carrying-value assessments require the company's
  accounting review. No constitutional amendment is proposed: received inputs and
  explicit judgments are authoritative; calculated observations are not.

## Carrying-value bridge continuation authorized 2026-09-20

The owner authorized continuation of T086 after the implementation checklist gate was
reported. The first supported scope is purchased current inventory already covered by
one complete retained inventory review. A valuation assessment is an explicit,
source-backed owner decision over exact remaining receipt quantities at a cutoff. It
states a supported lower value or recovery; Reality derives the carrying-value bridge
at read time and never invents a market value, impairment percentage, legal conclusion
or accounting posting.

The design was checked against the official text of HGB sections 252 and 253 on
2026-09-20. It preserves individual assessment, prudence and method continuity as review
constraints, treats acquisition cost as the recovery ceiling, requires a lower-value
assessment for a write-down and prevents a lower value from persisting after an explicit
recovery decision. This is a traceable schedule for accounting review, not compliance
certification. Manufacturing/WIP, fixed assets, automatic ageing rules, general-ledger
posting and external market-data interpretation remain unsupported.

## Phase 0 Execution Authorization

Following the Phase 0 plan, the owner explicitly requested implementation of the
performance experiment. That authorizes the isolated benchmark code, tests and
synthetic PostgreSQL runs described by plan.md. It does not authorize production
cost tables, company policy activation or later delivery slices. A completed exploratory
run is not equivalent to a passed fixture J architecture qualification.

## Planning Progression

After accepting the four review decisions, the owner instructed continuation. This
advances the concept to the bounded Phase 0 architecture qualification plan in plan.md.
The proposed commercial profile, method and sequential slices are its planning baseline.
No product schema, tenant accounting activation or production implementation is approved
by that progression; the following choices must be settled in the production design review.

## Open Questions

The following product choices remain explicitly visible for the production design review.
The proposed answers are the baseline for the authorized Phase 0 qualification; they
are not activation of any company accounting policy.

| Decision | Proposed choice | Consequence / alternative |
|---|---|---|
| Initial valuation method | FIFO plus evidenced specific identification | Existing average/LIFO companies need their method first or clearly separated external valuation |
| DB definition | Commercial contribution v1 in FR-011 | Product-fixed-cost DB2 requires another named profile and cost scope |
| First slice | Actual receipt costs, allocation and coverage, with no complete DB claim | Combining slices 1–3 delays first delivery but yields usable end-to-end margins |
| Financial delegation | Owner confirmation with agent assistance is accepted below | A delegated finance role still requires separately reviewed permission expansion |
| Performance acceptance | FR-018/J budgets are release gates | Benchmark failure requires architecture/scope revision, not silent budget relaxation |
| Exception subjects | Attach the four classes to existing subject records (receipt movement, supplier document, sold document line) | A review-shaped finding with no existing subject record needs a reviewed catalog extension, which is a schema decision of its own |

Approval of this concept does not certify statutory valuation suitability. The review
request is part of this design document; no implementation is authorized yet.

## Accepted Review Decisions

The owner explicitly accepted proposals 1–4 in this conversation. This acceptance
covers the following rules, not implementation authorization or the other open choices:

1. Agent preparation and execution after explicit owner confirmation are permitted;
   authorization and the input revision are checked again at execution (FR-019, US5.3).
2. Customer returns re-enter FIFO at economic return time with their original consumed
   costs; specific identification follows actual identity (FR-005, fixture C).
3. Sequential cost consumption uses cumulative half-even rounding and difference amounts,
   independently of report filters; later costs produce traceable revisions (FR-022, K).
4. The mandatory benchmark includes 10,000 test-day orders plus 90,000 historical orders
   over 24 months and 1,000,000 movements, with fixed supporting cardinalities (fixture J).
   It reuses spec 033's harness and retains the proposed latency budgets; historical
   volume is not a claim of 100,000 orders per day.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-002, FR-003 | US1.1–3 | A, F: evidence, signed allocations and conservation |
| FR-004, FR-005, FR-006 | US2.1–2 | B, C, G: policy, movement and opening coverage |
| FR-007 | US2.3, US4.2 | D: late evidence and two-cutoff replay |
| FR-008, FR-009 | US2.4 | G: economic scope and carrying-value bridge |
| FR-010, FR-011 | US3.1–2 | A, E: matched margins and independent dates |
| FR-012, FR-013 | US3.3–4 | F, H: grouping, currencies and units |
| FR-014, FR-015 | US4.1–2 | D, G, I: coverage and reviewed completeness |
| FR-016 | US1–4 | A–I: explanation trail and surface parity |
| FR-017 | US3.2–4 | C, E, H: returns and special business scope |
| DR-001, DR-002, DR-004 | US1–4 | A–I: provenance, replay and no derived authority |
| DR-003 | US4.3 | I: tenancy, concurrency and confirmation |
| DR-005 | US2.1, US3.3 | B, F, I: existing behavior and shared-service regression |
| FR-018 | US6.1 | J: reproducible scale, latency, freshness and reconstruction |
| FR-019 | US4.3, US5.1–3 | I: owner/member/removed-owner and background authorization |
| FR-020, FR-021 | US1.1–3, US2.3 | K: tax, duty and evidenced cash discount |
| FR-022 | US1.3, US3.3 | F, K: signed precision and rounded display independence |
| FR-023, FR-024 | US6.4 | L: catalog labels, saved reports, service measures and rates |
| FR-025 | US6.2 | L: shared exception catalog, detection and clearing |
| FR-026 | US6.3 | M: canonical demo, initialization and replay |
| FR-027 | US6.5 | I: record references across explanation, web, CLI and MCP |


## Qualification continuation authorized 2026-09-18

The owner approved further load qualification and concrete product integration design.
Extend the isolated experiment with distributed returns, signed purchase reductions,
split and partial revenue matching, concurrent late evidence and explicit current/stale
read semantics. Preserve fixture J family counts: returns are receipt-family subsets.
A stricter locally enforced resource cap is supplemental evidence, not a silent change
to the specified reference host. Product implementation and migrations remain outside
this continuation; integration contracts must identify exact existing seams and tests.


## Live-answer qualification continuation

The owner's continuation authorizes the next isolated live-availability experiment.
An unrelated cost change must not make a requested order unavailable. For affected
orders, use the same kernel on a bounded exact input prefix or return explicit not-ready;
never truncate contributing inputs or write observations from a read. Currentness is
relative to one repeatable-read snapshot and the requested scope, separate from evidence
completeness. Aggregate views retain their compatible whole-scope generation semantics.


## Bounded worker qualification continuation

The owner authorized continuation into bounded background reconstruction. The thin
experiment shall use the existing durable queue, claim fencing, authorization, retries
and child watchdog. A staged generation freezes its input revision, limits each work
unit, remains invisible until complete and publishes by one atomic pointer switch.
Worker failure/retry cannot expose partial rows or advance past retained input evidence.
Normal production registration, application migrations and live company activation remain
outside this architecture experiment. Reporting/tool reads must share its published
relation and metadata; default product adapters are not advertised as implemented.

## Product adapter planning continuation

Following the bounded shared-worker results, the owner authorized continuation with
concrete reporting, tool and exception integration design. The reviewed target behavior
remains FR-010–018 and FR-024–027; this continuation introduces no new accounting policy
or production activation. [Adapter delivery](contracts/adapter-delivery.md) defines
execution context, coverage-aware aggregation, canonical relation grain, shared-surface
responses and coherent exception snapshots against the actual current interfaces.
Production schema and reference/integrated qualification gates remain explicit. A
complete-current-only fixture binding is not accepted as proof of the broader contract.

## Production data-model review proposal

The owner next authorized preparation of the concrete product data model.
[Production data model](contracts/production-data-model.md) specifies the proposed
receipt-cost authority, typed later inventory/contribution relationships, immutable
input admission, retained review manifests, disposable generations and migration rules.
Existing financial components and the transaction-serialized event cursor are reused.
Existing cost-centre assignments are not reinterpreted.

The proposal explicitly requests owner review before product-schema implementation.
It also proposes changing the previous architecture-qualification ordering: build an
approved production integration candidate, then require actual integrated fixture-J and
reference-host qualification before release. That proposed ordering is not yet accepted;
the current no-production-implementation boundary remains in force until review.
Company policy activation and deployment/merge are separate and not requested here.


## Accepted production implementation approval

The owner explicitly answered yes to all four decisions in the concrete product-model
review: reuse received components plus signed receipt attribution/reviews; retain exact
immutable input/manifests with an honest history boundary; deliver actual receipt cost
and coverage first, then inventory and DB; implement the reviewed candidate before full
integrated/reference qualification, which remains mandatory before release. This
supersedes earlier planning-only/no-production and pre-implementation benchmark gates.
Schema and first-slice shared services/tools are authorized. Company accounting policy
activation, deployment and merge are not implied. No repeated approval is required for
ordinary implementation choices within this accepted model.

## Approved continuation: inventory calculation foundation

The owner's continuation authorizes the next inventory implementation stage. Build the
pure production calculation boundary first (US2, FR-004–007/017/018/022), before adding
policy/ownership authority and persisted movement admission in shared services. This
stage does not make inventory or DB available through an application command.

Given an explicitly selected FIFO or specific-identification method and a complete,
frozen, single-item/base-unit/currency/economic-owner pool, calculation must:

- Order movements by UTC economic time, retained sequence and opaque movement identity;
  refuse duplicate identities, missing/invalid quantities and stock shortages.
- Split received acquisition amounts cumulatively at four decimals, half-even, preserving
  exact consumed plus remaining cost regardless of process Decimal precision or filters.
- Distinguish sales issues, losses and supplier returns. Supplier returns require exact
  layer selections. Transfers within the same pool change neither layers nor total cost.
- Restore customer returns only from exact earlier sales-issue portions, bounded across
  all returns. Preserve original receipt provenance through repeated returns/resales;
  returned layers enter at return time. Specific consumption requires exact selections.
- Keep unknown costs distinct from zero, with known subtotals and unvalued quantities
  for both consumption and remaining stock. Negative acquisition amounts are unsupported.
- Refuse oversized input/trace work with a stable reason; never quietly truncate output.
  Replaying changed frozen receipt costs recomputes both consumed and remaining portions
  without mutating an earlier result.

Ownership, admitted movement history, confirmed method policy, cross-pool transfers,
correction normalization and sealed stock manifests remain required service work. The
kernel cannot certify any of those prerequisites or an HGB carrying value. It must not
be called from an application read to replay an unbounded company history.

## Approved continuation: reviewed bounded inventory service

The owner's continuation authorizes the approved policy/ownership/history service stage
(US2/US5, FR-004–008/014–019/022/027). Its first supported application scope is one
item, one evidenced base unit/currency and one explicitly confirmed economic owner,
with at most 100 movements and 20 receipts through a fixed economic cutoff. It supports
FIFO receipts, explicitly confirmed economic shipment issues and within-pool transfers.
Specific identification, returns, adjustments, opening layers, mixed/partial ownership,
FX and corrected pools refuse explicitly until their retained authorities are integrated.
This restriction does not remove their full-feature requirements.

An owner confirms `cost.change` operation `inventory_review`: explicit FIFO policy,
owner Party, base unit/currency, zero-opening/history-complete declaration, exact receipt
review manifests, ownership evidence SourceRecord per receipt and exact shipment IDs
that represent economic consumption. Physical shipment/location alone is insufficient.
The service enumerates the entire item history through cutoff itself and rejects omitted
receipts/issues, prior movements outside the declared zero-opening boundary, corrections,
unsupported kinds, incompatible inputs, negative stock and oversized scopes atomically.

Receipt manifests must be the latest receipt reviews, have complete category decisions,
and match all current attribution inputs. This inventory confirmation explicitly reaffirms
those retained cost scopes at the current event cursor; it does not silently reuse a stale
review. New attributed costs or unresolved receipt review categories require receipt review
first. Every receipt must have explicit full-quantity ownership evidence for the selected
Party. New policy/ownership decisions are append-only revisions, bound to the confirmed
action and event. No policy is activated by application startup or a read.

Retain exact movement inputs and typed review membership without storing calculated
stock/cost amounts as authority. `cost.inventory.get` returns the reviewed acquisition
value and consumption, policy/ownership/receipt provenance, fixed cutoff and event cursor.
A later tenant event conservatively makes the latest answer stale; complete current
values become unavailable while the retained basis remains explainable. An explicit
review ID reproduces its frozen historical result even after later correction or unit
changes. Earlier arbitrary wall-clock knowledge is unsupported. Reads never write or
schedule work and never enumerate current full movement history. HGB carrying value,
DB1/DB2 and reporting-graph integration remain unavailable in this bounded service stage.

## Contribution calculation foundation (approved continuation)

The owner's continuation authorizes the next domain stage of US3, under the already
approved commercial_v1 definition (FR-010–014/016/022). Calculate over explicitly
matched, disjoint, frozen slices supplied by a future application service. This stage
does not establish evidence matching, completeness authorization, historical document
context, production reporting adapters or DB availability for existing company data.

Require a single explicit tenant/generation/policy/profile/cutoff context per call.
Partition currency and base unit; group stable opaque dimension IDs and economic month,
keeping missing dimensions as an unassigned group. Refuse duplicate slice identities
and oversized input. Each slice retains independent revenue, goods/direct-service,
direct selling and allocated selling inputs and their evidence/review references.
Reviewed inputs support final actual amounts; evidenced inputs support known actual
subtotals only. Provisional and unknown inputs never enter actual subtotals. DB subtotals
use only jointly evidenced slices; final DB1/DB2 require independently complete scope.
Explicit reviewed zero is valid; an empty scope is no_activity, not completed zero cost.
Rates are 100 times aggregate final DB / positive final revenue, rounded half-even to
four places. Source amounts and signed matched credit/return shares are never rewritten.
Unmatched revenue/cost, inventory valuation effects and unassigned allocation residuals
remain outside this matched-slice kernel for later service reconciliation.

A matched economic date beyond the explicit UTC effective cutoff date refuses. Exact
intraday event admission remains the matching service's responsibility.

## Current contribution preview (approved continuation)

Implement the first read-only application connection for FR-010/011/014/016/019. A
sales invoice line may form a candidate only through its billed order-line FK, one
customer-delivery commitment and one shipment. Require whole-line equal quantities,
matching item/unit/currency/customer/owner, unique billing and a current complete
inventory review containing the exact shipment. Use received line net revenue only;
never derive net from gross or price times quantity. Missing links, partial/ambiguous
billing, returns/corrections, stale inventory and unsupported types yield explicit gaps.

This is a current preview, not a confirmed revenue match or historical DB report.
Return known DB1 where supported; finalized DB1/DB2 and rates remain unavailable until
commercial matching/profile/completeness decisions exist. Selling costs remain unknown.
Expose the trace and separate invoice date, proposed shipment economic date and inventory
cutoff. No source net amount is allocated or prorated. Do not infer historical dimensions.

Use a typed cost.contribution.preview read tool/MCP adapter through the shared service,
with no business/projection writes. Reject foreign identities as not found; recheck the
tenant event cursor to refuse a concurrently changed read. Preview contexts have no
fabricated generation/profile revision identity and cannot produce finalized totals.

## Confirmed single-line contribution (approved continuation)

The owner's continuation authorizes confirmed commercial matching for the existing
whole-line candidate under FR-007/010–016/019/022 and DR-001–005. Follow
contracts/contribution-service.md: preserve received revenue and exact line/shipment
identity, require explicit owner approval of commercial_v1, revenue completeness and
shipment-time recognition, and retain immutable basis and review versions. Current DB1
becomes final for this scope; DB2 remains unknown pending selling-cost decisions.

Reject full-quantity reuse, silent rematching and mutations of admitted invoice/order
evidence. Fresh inventory review plus renewed confirmation may update consumed cost;
historical review IDs reproduce prior DB1 from retained inputs. Later tenant events
invalidate current completeness. This does not introduce partial matching, corrections/
replacement, independent global profile activation, arbitrary historical contexts or
company-wide contribution reporting. Existing confirmed model approval and staged
continuation cover this bounded revenue/history implementation.

## Source-backed selling costs (approved continuation)

The owner's continuation authorizes the next commercial_v1 stage: source-backed
selling attribution and independent reviewed DB2 under FR-003/007/011–016/019/020/022.
Use contracts/selling-service.md for exact scope and refusal cases. Preserve prior
DB1-only reviews unchanged. Fixture A must produce DB1 570 and DB2 456/38% from
explicit direct90 and allocated24 costs. Missing completeness leaves DB2 unknown;
explicit zero can finalize DB2=DB1. Revisions/withdrawals and later events must not
rewrite history, double-count a received amount or reuse acquisition costs as selling.

## Retained costing record inspection (approved continuation)

Implement T078 under FR-016/023/027: all existing cost references resolve through one
read-only service to the existing Inspector, CLI and MCP with tenant-safe source links.
Use contracts/record-inspection.md for the fixed kind/bridge boundary, historical meaning,
exact precision, bilingual names and bounded membership pages. No financial decisions or
new authority. A member can trace a contribution review through selling/inventory inputs
to its source; foreign records and invalid kinds refuse identically on all transports.


### Shared retained cost-query context (T079)

The owner-authorized continuation exposes one consistent query envelope for admitted
inventory and contribution scopes, per FR-004/007/011/012/014/015/016. The exact contract
is contracts/query-context.md. Requested cutoffs are explicit constraints, distinct from
resolved retained cutoffs; unsupported history refuses. A scope review is never renamed
a canonical generation or a company-wide profile. Existing monetary reads stay intact.


### Generation publication guard (T080, first implementation stage)

Under FR-007/012/014/018, publication must reject unfinished input capture, incomplete
work, inconsistent row counts, foreign contexts and replacement of a publication that
changed since work began. A completed generation at an older event cursor remains an
explicit previous basis; it never becomes current merely because calculation finished.
The pure domain guard is the first stage, specified in contracts/generation-publication.md.
It introduces no storage, job, profile approval or operational report by itself.


### Stored inventory review generations (T080 continuation)

Owner continuation authorizes the bounded production storage/worker step in
contracts/inventory-publication.md, refining the already approved disposable generation
model. FR-007/014/016/018/019 require retained-basis reconstruction, atomic publication,
tenant-safe constant-size reads and independent freshness/coverage. This stage builds
one supported confirmed item review, preserving the 100-movement/20-receipt bounds.
No cross-item common profile or grouped DB acceptance is claimed.

### Bounded historical inventory selection (T080 continuation)

Under FR-007/014/016/018/019, a shared read service accepts 1–100 distinct exact
stored inventory generation IDs and returns their historical observations in stable
identity order. Each row preserves its own review, policy, item, owner, currency, unit,
effective/knowledge cutoffs and event cursor. Individually approved reviews do not
become one common financial basis. No combined quantity, value, global generation or
current freshness is inferred. Any absent/foreign member refuses the entire request
without disclosing which member is unavailable. Corrupt cache content also refuses.

Acceptance: two separately reviewed items retain exactly their existing single-read
responses even after new events or pointer changes; input order does not affect output.
Duplicate/empty/oversized/invalid selections refuse. Reads use at most two SQL statements
independent of selection size, never replay inventory, load retained movement members,
flush pending objects, enqueue work or write state. This is an internal shared service
foundation, not a grouped report, company-wide generation or paginated tenant listing.

### Joint inventory confirmation (T080 continuation)

FR-007/014/015/016/018/019 require a common retained knowledge basis before selected
item values can support a joint report. Extend existing owner-confirmed cost.change
with inventory_batch_review for 2–10 distinct whole-item scopes. Each scope follows
the existing FIFO/empty-opening/ownership/receipt-evidence rules; all scopes must have
the same effective cutoff, economic owner and currency. Units remain item-specific.
The batch admits at most 100 movements and 20 receipts in total.

Preview explains every item and the exact requested membership, without a write or
aggregate. Execution rechecks all members under the existing tenant business lock
and expected event cursor, then creates their reviews in one transaction with one
confirmed action, one cost.reviewed event/cursor and one knowledge time. Any validation
or execution failure leaves no partial financial decisions or event. Replaying the
confirmed action returns its original membership/result. An intervening event or
revoked owner refuses. Different owners/currencies/cutoffs, duplicate items or
unsupported/missing/foreign inputs refuse; no partial admission or automatic approval.

Acceptance: source-backed two-item confirmation produces individually reconstructable
reviews sharing the same action/event/cutoffs; existing snapshot builders/readers
preserve that common basis. Existing single-review behavior remains compatible.
This establishes selected-scope authority, not a company-wide policy, DB profile,
aggregate report, common cache publication or automatic worker scheduling.

### Complete joint inventory publication and totals

Under FR-007/012/013/014/016/018/019, the exact previously confirmed batch action
defines a bounded historical inventory selection. Maintenance may build all its item
generations atomically through the existing shared worker. A common read exposes rows
and an acquisition total only when every retained member has a valid published cache.
Partial availability returns uninitialized with explicit expected/available item counts,
never a partial or zero total. Missing/foreign/non-batch actions and mismatched retained
membership refuse. Reuse the 2–10 item, 100 movement and 20 receipt approval limits.

A complete result pins all exact member generation IDs from one publication lookup; it
retains the batch action identity and common effective/knowledge/event basis rather
than inventing a new global generation. Sum acquisition value in the confirmed currency;
partition remaining quantity by base unit. Carrying value remains explicitly unsupported.
Historical reads perform no live cursor lookup. Explicit current mode requires READ
COMMITTED and returns pending after a later tenant event, suppressing result/rows unless
allow_previous is explicit. No read recomputation, enqueue, autoflush or writes.

Acceptance: two source-backed members yield 840.0000 acquisition value and separate
40.0000 kg / 40.0000 pcs quantities only after both are available. Failed second builds
leave no new partial caches; concurrent same-action builds converge. Independent readers
cannot see an in-progress batch's rows as a complete value; late intake remains possible
and makes current freshness pending. Replaying rebuild preserves exact IDs. Corruption
or missing members cannot masquerade as zero. Reads use at most eight bounded SQL
statements and no movement-history scan. This is selected inventory scope only, not
DB1/DB2 grouping, a tenant-wide publication, carrying assessment or scale qualification.

### Canonical SQL inventory reporting foundation

FR-007/012/013/016/018/019 require report adapters to reuse canonical, generation-pinned
observations rather than reconstruct acquisition values. Provide a typed SQL relation
for 1–100 exact generation IDs at one snapshot per retained item-review grain. Columns
carry snapshot/generation/review/action/policy/item/owner identities, currency/base unit,
effective/knowledge cutoffs, processed sequence, algorithm and exact numeric quantity/
acquisition value. No mutable publication lookup, live Item metadata join, JSON population
or movement replay. Every joined table is explicitly tenant-constrained.

The existing checksum-validating inventory selection reader must use the same joined
source. The relation itself is internal and does not authorize arbitrary IDs as one
complete report: report execution must first resolve the confirmed batch, validate
completeness/checksums and ensure the pinned rows stay stable during aggregation. No
graph node/measure or current-report claim is added before that boundary is implemented.

Acceptance: source-backed joint inventory produces the same exact numeric rows through
SQL and the existing reader; SQL groups preserve separate units and currencies and
return the expected 840.0000 EUR selected total. Missing/foreign IDs produce no matching
rows, never a tenant fallback; an empty relation is not a supported zero inventory.
Old exact IDs retain values after new publication pointers and business events. Invalid
selection shapes refuse before SQL. No new schema or independent financial formula.

### Historical inventory graph execution

FR-007/012/013/014/016/018/019: graph.ask accepts a typed inventory_cost_context
with one confirmed batch action_id and mode historical. The inventory_valuation node
exposes acquisition value and remaining quantity from that exact complete selection.
Currency/unit grouping remains mandatory; temporal buckets and joined paths are refused.
Missing context, context on unrelated questions, missing/foreign actions, incomplete or
corrupt caches refuse without partial values. No current valuation or carrying-value claim.

Protect exact generation/snapshot rows before integrity validation through final SQL
aggregation, including concurrent cache deletion/update. Reads do not replay movements,
flush pending changes, enqueue jobs or approve financial decisions. Return requested
context and resolved action/generation IDs, common cutoffs, coverage and historical
freshness. Saved graph reports preserve the requested context and revalidate it on read.
Text-path formatting must refuse rather than silently drop this context. Initial delivery
uses the existing JSON graph tool/API and saved reports; the visual context picker remains
open under T081. Ordinary graph questions retain their behavior.

Acceptance: the real two-item fixture reports 840.0000 EUR, or 420.0000 per item, and
40.0000 kg / 40.0000 pcs. Missing caches refuse, filter-empty results remain empty, and
later intake does not change the historical result. Cache deletion cannot race validation
and aggregation. A saved/reopened question preserves its confirmed action. At most ten
SELECT statements per successful traversal, with no movement-history replay.

### Historical inventory selection in the Analysis Builder

FR-012/013/014/016/019: the existing visual Analysis Builder lets the reader explicitly
choose a retained joint inventory confirmation by valuation cutoff, knowledge time,
economic owner, currency and item count. Provide a tenant-scoped, bounded, newest-first
read with continuation; never default to the latest confirmation. Discovery lists retained
confirmations, not cache readiness or permission to activate a policy. Execution retains
the existing complete-basis and integrity checks. No confirmation creates or rebuilds
anything merely by appearing or being selected.

The visual plan preserves inventory_cost_context through grouping/filtering/sorting,
saving, reopening and chat handoff. Starting an unrelated analysis clears the context.
Selecting inventory without a context shows the chooser and no report request or stale
result. Changing or clearing a selection invalidates an in-flight answer. Results display
historical valuation/knowledge cutoffs and complete selected-item coverage, with exact
confirmation/generation references available for inspection. No current-value wording.
Text editing is unavailable for this context rather than silently losing it.

Acceptance: choose between two confirmed scopes, page to an older one, and save/reopen
without changing its action identity. No selection is automatic. Missing/foreign cursor
IDs refuse without disclosure; empty discovery has an explanatory state and retry.
Unavailable/corrupt selected caches still refuse through graph.ask. Pending or failed
reads never display the previous valuation as the newly selected one. Labels are localized
in all four supported languages; ordinary non-cost report behavior remains unchanged.

The remaining-quantity measure declares its actual base_unit property as the mandatory
non-additive axis, so the visual editor automatically preserves unit separation.


### Coverage-preserving contribution SQL arithmetic

FR-011/012/014/022: the internal reporting aggregate must reproduce the existing
commercial_v1 kernel for each admitted compatible slice population. Each of revenue,
goods cost, direct/allocated selling cost, DB1 and DB2 exposes known, final, required,
covered, evidenced and provisional values. Known margins include only slices whose
individual required inputs are actual; final margins require every input reviewed.
Preview and empty populations have no final amounts or rates. Rates divide final
aggregate margin by positive final aggregate revenue and round half-even to four
decimal places, including signed exact ties. Currency/unit/context partitioning,
admission and cache readiness remain prerequisites of a future public report. This
arithmetic building block cannot approve a scope or enable graph measures by itself.


### Joint contribution confirmation

FR-007/011/012/014/015/016/019: an active owner may preview and explicitly confirm
2–10 distinct supported full invoice-line contributions in one cost.change action.
Each position retains its own exact candidate hash, economic recognition time, revenue
completeness, commercial_v1 profile confirmation and optional seven-category selling
review. Positions must use one common confirmed inventory action, valuation cutoff,
knowledge cursor, economic owner and currency. Different base units remain separate.
Duplicate invoice lines or shipment bindings refuse; independently confirmed inventory
scopes cannot be silently combined. The entire selection validates before any decision
is written and all retained reviews share one actual event, knowledge time and action.
Failure rolls back every member; stale previews, revoked owners and foreign references
refuse. Replaying the same confirmed action returns the same member identities.

Acceptance: two supported positions on a jointly confirmed inventory basis retain two
reviews with one event/time/action; reviewed zero selling cost finalizes only that
position's DB2, while another position's missing selling costs remain unknown. Historical
per-position reads reproduce their original values after later intake. The result names
the selected profile scope action without relabeling individual profile revision IDs
or inventing a company-wide generation. This step does not expose aggregate totals,
publish caches or enable DB graph/UI reporting.


### Retained joint contribution observations

FR-007/011/012/014/016/018/019/022: rebuild a disposable historical calculation for
one exact executed contribution_batch_review action. Validate its complete retained
membership, real decision event, common inventory basis and per-position bindings.
The worker cannot approve a decision. All 2–10 positions publish in one transaction;
missing output yields uninitialized, while missing members of a published generation
or inconsistent digests refuse. Retry reuses the same verified generation without FIFO
replay. Compute all positions before cache writes so long calculation does not hold
tenant foreign-key locks that block business intake.

Reads preserve the selected historical context after later intake, perform no FIFO
replay or writes, and expose generation/review/action references, independent DB1/DB2
coverage, exact per-position values and currency/base-unit-partitioned totals using
the common SQL aggregate rules. Protect pinned disposable rows through aggregation.
Missing selling coverage never becomes zero; known selling subtotals remain separate.
An owner-authorized shared worker job refreshes this exact selection without activating
a schedule. Current/company-wide valuation, graph measures and visual selection remain
outside this bounded historical observation stage.

### Historical contribution graph selection

FR-012/014/022 refinement: A contribution graph question selects exactly one retained
joint confirmation through `contribution_cost_context` (action identity, historical
mode). The shared admission validates complete membership and integrity and protects
cache rows through SQL execution. Missing generations refuse rather than calculate.
Filters apply before coverage-preserving aggregation. DB1/DB2 totals remain unknown
when any selected position lacks required confirmed inputs; known subtotals and
covered/required position counts remain separately queryable. Percentages are ratios
of grouped totals, rounded half-even to four decimals, never sums of position rates.
Currency and base unit remain explicit grouping/filter axes. Economic dates may be
bucketed; valuation and knowledge cutoffs may not. This initial node is standalone:
no traversals or existence joins may multiply its position grain. Saved questions
preserve the explicit context; the path editor refuses to discard it.

The existing analysis builder offers bounded tenant-scoped contribution confirmation
metadata through the shared graph service. Discovery asserts neither completeness nor
cache readiness. Selection is explicit, survives save/reopen, and clears stale results
on change/failure. The historical basis shows position scope, cutoff and review links;
DB1/DB2 coverage measures distinguish loaded positions from complete financial inputs.
Default contribution reports show DB1, DB2, rates and covered/required positions.

### Contribution freshness at the selected valuation cutoff

FR-007/014/018 refinement: A selected joint contribution scope supports `historical`
(default) and `current` reads. Current means no newer tenant business event than the
retained contribution confirmation at the final read check; it does not move the
valuation cutoff or establish company-wide coverage. Any newer event conservatively
marks the scope pending. Current service reads expose explicit processed/target cursors
and withhold rows/groups while pending; graph execution refuses with
`cost_basis_pending`. Missing generations remain uninitialized/unavailable. Historical
reads remain reproducible. A cache rebuild cannot approve new inputs or make an old
confirmation current. Current reads require READ COMMITTED and recheck after the final
SQL aggregate without blocking normal intake. Events committed after the final check
belong to the next read, not an indefinite freshness guarantee.

The contribution selector offers an explicit unchanged-since-confirmation requirement.
It preserves this mode on selection, edits and save/reopen. Pending/failure clears old
results and explains how to inspect the historical basis. No automatic confirmation or
refresh follows from this control.

### Exact company-generation population closure

FR-007/012/014/018 refinement: Before publishing a company generation, its builder must
prove exact membership against a frozen expected inventory-item and contribution-line
population. A selected set of confirmed reviews cannot itself define that population.
Every expected subject must have exactly one evaluated result, including an explicit
unknown-cost result. Duplicate, omitted, extra or stale-input results refuse closure.
Membership uses opaque item and document-line identities, never labels or counts alone.
The expected population and evaluated output must share tenant, effective/knowledge
cutoffs, input watermark and algorithm version; individual policy/review revisions
remain in each subject's input fingerprint, without a fabricated company policy ID.

Population completeness and financial completeness are independent. Acquisition value,
carrying value, DB1 and DB2 each report expected/covered counts; missing selling cost
cannot suppress a supported DB1 or create a supported DB2. An empty sealed population
is explicit empty coverage, not proof of a zero financial total. Population closure
does not verify monetary output hashes, trace completeness or grant financial approval.
Those remain separate publication checks.

Within this supported valuation model, a known carrying value requires known acquisition
cost to support the separately specified recovery ceiling; no carrying assessment is
created by population validation.

### Source-backed current company census

FR-007/014/018 refinement: The builder discovers inventory subjects from every tenant
Movement at or before the effective cutoff, independently of costing reviews. It
discovers all sales-invoice and customer-credit-note lines from evidence, including
service/freight/unmatched lines. Invoice dates do not establish contribution economic
dates: these lines remain candidates with economic scope unassessed until the retained
matching resolver proves inclusion/exclusion. Headers without lines remain explicit gaps.

Capture runs against one REPEATABLE READ PostgreSQL snapshot. Return the actual snapshot
identity, observed-at instant and visible tenant event watermark, not a fabricated past
knowledge cutoff. It is current input discovery only, not a historical census or a
publishable valuation. Record fingerprints cover visible evidence and event identities;
they are distinct from the later full financial-input fingerprints. No FIFO replay,
financial confirmation, enqueue, flush or commit occurs during discovery.

Missing/ambiguous movement-recorded events remain gaps and never drop movements.
Document-recorded events establish header evidence only, not historical line membership.
Return latest source versions with current import outcome and expose unresolved sources
separately; unknown source relevance cannot be converted into invented inventory/revenue
subjects. Enforce a combined limit of 1–100,000 returned movement/header/line/source
records, refusing overflow rather than truncating. This is bounded builder admission,
not fixture-J qualification or an ordinary report endpoint.

### Company publication prerequisite (FR-007/012/014/018)

A company generation must bind its sealed retained manifest to the exact expected
inventory and contribution population, including each subject's resolved input fingerprint
and shared historical context. It must not invent one company-wide item policy or use
current census record fingerprints as financial input fingerprints. Publication must
refuse missing, substituted, duplicate, stale or mixed-context subjects even when row
counts agree. Explicit unknown financial observations remain valid completed work and
do not imply complete monetary coverage. Counts must agree with exact population closure.
The existing sealed-input, content, work, trace, cursor and atomic-pointer prerequisites
continue to apply, including retries. This internal domain step does not retain inputs,
write a publication pointer, establish historical census support or expose a company report.

### Retained discovery storage — owner approved

FR-007/014/018/019 require old input observations to remain explainable despite mutable
unadmitted evidence. The concrete proposed storage boundary and acceptance proofs are
in contracts/company-census-retention.md. Five dedicated typed census tables preserve
observed current values and immutable source references without asserting historical
financial knowledge or approved costs. The owner explicitly approved this extension on 2026-09-19. Retention may not reuse
SourceRecord as invented external evidence or treat record hashes as retained values.

A captured manual line remains editable under the existing evidence rules, but its opaque
identity cannot be deleted while retained census history references it. The correction
service must refuse removal before mutation with guidance to correct the existing line
or add replacement evidence. The prior captured values remain unchanged.

### Bounded retained-census review resolution (FR-007/012/014/019)

A trusted internal builder may resolve a verified retained census to existing confirmed
inventory and contribution reviews, retaining every captured item and sales-line candidate.
Only reviews introduced by the census event cursor are candidates; later confirmations
must not change an old resolution. Use the latest applicable retained review per subject,
never silently fall back past a newer incompatible review. Keep each subject's own policy,
review identity, knowledge time and missing inputs; do not invent a common financial cutoff.

A supported result at capture requires matching inventory effective cutoff, unchanged
knowledge through the census cursor and exact inventory movement membership. Contribution
also requires economic activity through the census cutoff and its retained inventory cutoff
to match. Older or incompatible reviews remain separately labelled basis results, with the
capture result withheld. Missing reviews produce explicit unknown entries; service/credit
lines and header/source gaps remain present. Independent DB1/DB2 gaps stay as returned by
the canonical reviewed reader. The resolver performs no financial confirmation, persistence,
publication, current-live valuation or aggregate totals. Bound to at most ten subjects;
oversized captures refuse rather than silently truncate. This is a builder prerequisite,
not a report endpoint or full-company release.

### Confirmed contribution reviews do not invalidate unrelated captured scope

Refinement of FR-007/014/019 for the bounded retained-census resolver: a confirmed
contribution-only review does not change inventory acquisition inputs. It also does not
change the inputs of a different sales line. Intervening contribution_review or
contribution_batch_review events may therefore be treated as non-invalidating only when
same-tenant executed owner decisions and exact persisted review/line membership prove the
closed operation. Same-line reviews, all other event types, incomplete/malformed evidence
and an oversized interval retain conservative pending behavior. No blanket exclusion of
cost.reviewed is allowed. Readers outside retained-census resolution remain unchanged.
This enables supported stock and contribution values to coexist in one captured answer
without inventing approval or ignoring late freight, correction or selling attribution.

### Common captured review basis (FR-007/012/014/019)

The bounded retained-census resolver must return one deterministic basis digest binding
the verified census identity/content hash/context to every expected item and sales-line
candidate, its selected review identity/hash and own knowledge time, result digest,
freshness proof and gaps. This is a read-time captured basis, not a retained financial
manifest or a common historical knowledge cutoff. It must never populate PopulationBasis
by substituting observed_at for knowledge_at. Preserve each subject's policy/profile and
linked inventory review through its canonical result, without a fabricated company policy.

Assembly must refuse duplicate, missing, extra or mixed-context resolved subjects before
returning a common basis. All census candidates remain represented independently of
successful reviews. Report separate expected/covered/unknown counts and empty/partial/
complete state for acquisition value, carrying value, DB1 and DB2. Coverage describes
captured subjects/candidates only; header/source gaps remain separately visible even
when subject coverage is complete. A stale historical basis never counts as covered.
Numeric zero is covered; null is unknown; empty coverage is not a zero monetary total.

The digest is insensitive to enumeration order and changes with context, review, result,
proof or gap changes. Repeating an old capture after later live events yields the same
basis. No totals, new storage, financial approval, publication eligibility, enqueue or
ordinary report endpoint are introduced. Existing strict ten-subject and transaction
bounds continue to apply.

### Durable captured review selection (owner approved)

FR-007/012/014/019 continuation: contracts/captured-basis-retention.md specifies the
three-table proposal for retaining exact captured review selection, including unknown
subjects and gaps, independently of disposable calculation caches. The owner approved this storage proposal on 2026-09-19. It is not a common historical financial manifest. Persist existing
authority references and integrity metadata, not another authoritative EK/DB amount.

Stored identity must pin the selected reviews and verified census through retries and
later evidence. Metadata reads do not calculate costs; explicit replay uses pinned
reviews and verifies canonical result digests. Unsupported history/versions refuse.
Lifecycle metadata is outside the proposed version-2 digest; v1 digests remain explicitly
versioned. Sealed retention alone cannot grant financial approval or company publication.
Implementation of this distinct schema family is authorized by the explicit owner approval.

### Bounded captured known-subtotal summary (FR-007/011/012/014/019)

A trusted internal caller may request a read-only summary by retained captured basis ID.
Replay and verify the exact pinned basis before aggregation. Report known inventory and
contribution subtotals partitioned by currency/base unit; additionally partition inventory
by ownership and valuation method. Never add inventory values across cutoffs. Preserve
per-subject review/policy context and independent acquisition/carrying/DB1/DB2 coverage.

Only available-at-capture rows enter numeric groups. Historical-only and unreviewed
subjects remain in a separate unavailable-subject list with their gaps; they remain in
the captured coverage denominator. Do not infer their currency from current master data.
Header/source gaps stay visible. Missing selling costs cannot become zero or suppress
known DB1. Known DB2 sums only positions with all its own inputs, never full revenue
minus incomplete cost subtotals. Each group lists exact contributing opaque identities.

These are known subtotals of the captured population, not final totals or a jointly
approved company context. Final totals and rates are always null; publication eligibility
is false, including when every captured subject has numeric coverage. Zero known inputs
count as covered; an empty family returns no groups, not an invented zero valuation.
The summary has no current-live claim, arbitrary grouping/filtering or public report UI.
Retain the existing ten-subject/replay/transaction bounds. No writes, flush, staging,
financial confirmation or job enqueue. Grouped company reports and atomic publication
remain separate obligations.

### Approved captured-report publication amendment

FR-007/012/014/018/019: contracts/captured-report-publication.md proposes a fixed report
of an exact retained captured review selection, with explicit gaps and known subtotals.
This amendment preserves null final totals/rates and does not establish a historical
company financial context. The owner approved the four-table generic cache slice and
changed basis relation on 2026-09-19; retained captured-basis semantics stay unchanged.

Owner accepted the captured-report amendment on 2026-09-19. Internal build, guarded
publication, fixed-generation read and unpublished-cache disposal are authorized. Report
reads pin a generation; cursors cannot cross generations or row families. They preserve
unknown members and separate group coverage from captured population coverage. No input
replay, autoflush, enqueue, financial approval or final company totals on reads.

### Cost findings through the shared exception projection

FR-014/015/018/025 continuation: add the four approved cost classes to the existing
operational exception catalog and derive them through one tenant-scoped cost-finding
provider consumed by the existing exception projection refresh. Stable finding identity is
class plus the existing business subject; a disposable generation is basis metadata, never
the subject identity. Missing acquisition cost and stale review attach to an existing item
or movement as supported by their authoritative scope, unassigned component attaches to
the existing financial component's document or line, and negative actual DB1 attaches to
the reviewed sales document line. No new record type or severity is introduced.

The provider must distinguish evaluated current, evaluated stale and unevaluated cost
scope. A pending or failed cost rebuild preserves the previous projected finding with
explicit stale basis metadata; absence of new cache rows cannot clear it. Negative actual
DB1 requires complete evidenced DB1 at a compatible current scope. Missing acquisition
cost produces a gap instead, and incomplete selling cost does not suppress a supported DB1
finding. The existing agreed-purchase-price comparison remains independent.

Projection rows carry the consumed opaque cost generation/basis identity and freshness
metadata. The existing bounded projection-backed register, per-class counts, filtered page
and explanation routes continue to read one compatible exception snapshot and never start
reconstruction. This slice adds no new table, queue, timer or browser rule. Fixture-J p95,
full reconstruction timing and downstream refresh latency remain T089 release gates.

### Proposed financial company generation storage

FR-007/012/014/018/019 continuation: the concrete seven-table manifest, typed population,
generation-result and CAS-publication proposal is recorded in
contracts/company-generation-publication.md. It reuses verified per-review calculation
caches and never promotes the diagnostic captured report. The retained manifest establishes
one committed event cursor and a new actual knowledge timestamp under the tenant lock,
retains every expected census subject and its own approved review/input fingerprint, and
keeps unsupported subjects as explicit unknown completed work. Exact unresolved header and
source gap counts plus a canonical typed gap digest bind the remaining census gaps without
turning them into invented financial subjects.

The owner approved this concrete seven-table boundary on 2026-09-19 for migration and
internal implementation. Approval authorizes only the described storage and internal
services; it does not activate accounting policy, certify financial completeness, expose a
public mutation, qualify fixture J or authorize the later carrying-value schema.

## Allocation and conversion continuation proposed 2026-09-20

T087 completes only explicitly evidenced acquisition- and selling-cost distribution. An
owner may ask the existing `cost.change` proposal path to distribute one selected received
amount bucket across 2–100 exact typed targets by positive Decimal weights. The proposal
derives signed four-decimal shares with largest absolute remainders and opaque target-ID
tie breaking. It displays every weight, exact share and unassigned residual before
confirmation. Confirmation retains the explicit shares in the existing attribution-part
authority and keeps the original weights in the immutable action input; a calculated share
does not become received evidence.

The first allocation scope uses receipt quantity or caller-supplied positive weights whose
business meaning is stated in the request. It never invents price, volume, distance or
overhead drivers. Explicit parts and weighted targets are mutually exclusive. The selected
allocation total must preserve the source bucket sign, cannot exceed its received capacity,
and cannot use positive and negative shares to conceal overassignment. Purchase reductions
use the same signed conservation. Nonrecoverable tax remains an independent received-tax
bucket and may be allocated only after explicit recoverability classification; included tax
cannot be added twice. A payment difference alone never creates skonto evidence.

Identity unit/currency treatment requires no new authority. A non-identity unit or currency
conversion is supported only after an owner confirms an immutable source-backed conversion
basis that states the exact source and target unit or currency and positive numerator and
denominator. Conversion ratios retain their received precision; derived target quantities
and amounts are four-decimal observations, never replacements for original values. Current
market rates, text labels, prices, document dates and payment differences are not conversion
authority. Finer-than-four-decimal target quantity refuses rather than truncates.

The approved retained conversion header links its evidence SourceRecord, introducing event
and confirmed action; it stores kind (`unit` or `currency`), exact from/to codes, positive
`Decimal(28,12)` numerator and denominator, effective time, revision and predecessor.
Acquisition and selling attribution parts each have their own nullable same-tenant FK to
the conversion revision, used only for a non-identity conversion. They continue to store
the exact original source share; services derive the converted observation at read time.
Conversion chains and automatic inverse lookup are unsupported. No generic object target,
exchange-rate feed, automatic policy activation or ledger posting is added.

Every weighted request declares one closed driver kind: `quantity`, `equal` or `manual`.
Quantity uses the exact admitted target quantity, equal assigns weight one, and manual
requires every positive weight explicitly. The driver kind and weights remain in the
confirmed immutable action input; the typed parts retain the resulting exact shares.

Acceptance requires pure allocation/conversion arithmetic tests, source-bucket and residual
conservation, stable ties, negative reductions, tax/skonto refusals, precision boundaries,
revision/history, owner revalidation, tenant non-disclosure, tool/Inspector trace and guarded
migration rollback. The owner approved this exact conversion authority, both typed part
links, precision and closed driver vocabulary on 2026-09-20.

## Operational cost explanation continuation

T088 exposes the existing shared cost-query authority on operational and analysis surfaces;
the browser performs no costing arithmetic and persists no financial conclusion. An expanded
inventory row may request the current inventory cost context for its exact opaque item ID.
The explanation keeps acquisition value and carrying value separate, names missing carrying
evidence instead of substituting acquisition value, shows the retained valuation and knowledge
cutoffs, and distinguishes ready, stale, historical and uninitialized states. A stale current
read may explain its retained basis but must not present that basis as a current result.

The same presentation contract is reusable for a contribution scope. It separates received net
revenue, consumed acquisition cost, DB1, reviewed selling costs and DB2, and it never treats an
unknown DB2 as zero. Exact four-decimal service values remain available in explanation and export;
ordinary money display applies the user's locale and currency rounding only at render time. Unit
costs retain six decimal places where the service supplies them. Every retained review/action in
the explanation links to the existing Inspector rather than creating a second cost-detail route.

Delivery is incremental: inventory detail and Analysis establish the shared component first;
order/finance contribution entry points follow only where an exact document-line scope is already
available. Technical browser tests cover loading, missing, stale, exact-value and trace behavior.
SC-002 remains a separate moderated five-user release qualification using fixture M; automated
tests and backend fixtures cannot satisfy it.
