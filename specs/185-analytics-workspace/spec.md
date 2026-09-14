# Feature Specification: Composable Analytics and Reports Workspace

**Feature Branch**: `185-analytics-workspace`
**Feature Number**: `185` (resolved by `scripts/next_feature_number.py`)
**Created**: 2026-09-13
**Status**: Implemented and verified on 2026-09-13
**Language**: English
**Input**: The owner requests a general analytics tool and a powerful integrated UI under the existing Analytics → Reports navigation, following the assessment of 30 SMB analytics questions.

## Context and Intent

### Problem

The current Reports page shows fixed delivery metrics and a 7/30/90-day activity chart. The agent has focused reads but cannot freely compose supported dimensions, filters, measures and comparisons. Common questions require additional application code even when the evidence exists. Users need one explainable analytical capability operated visually or through the existing agent.

### Scope

- A discoverable, composable analytics capability shared by agent, CLI and Web.
- An integrated Reports workspace with a visual explorer, starter reports, tables, charts, pivot tables, period comparisons, contributors and CSV export.
- Reusable saved report definitions, private to their author within a company, including rename, duplicate and delete. Saved definitions rerun against current retained data; they are not frozen results.
- Bidirectional handoff between analytical definitions in the existing chat and Reports explorer.
- Sales and purchase order evidence, current inventory and fulfillment, invoice open items, and recorded payments. The [question coverage contract](question-coverage.md) defines supported answers for all 30 assessment questions.
- Existing operational delivery overview and Home contributor links retain their current meanings.

### Non-Goals

- Migrating operational storage or adding another business database.
- Arbitrary database administration, unrestricted code execution or customer-authored business calculations.
- Supply allocation optimization, arrival forecasts, causal supplier-to-order assignment, historical state reconstruction, certified sourcing dependence or a new supplier/payment performance methodology.
- New connectors, inferred missing facts, currency conversion or new unit-conversion rules.
- Scheduled reports, email delivery, public links, shared team editing, a multi-tile dashboard builder, or storing result snapshots as new business authority.
- A second chat interface or embedding an external business-intelligence product.

### Existing Contracts

- [Analytics assessment](../../docs/analytics-question-assessment.md).
- [Web specification](../../docs/WEB_SPEC.md), especially specs 108 and 135: Analytics route, Home links, global chat and navigation.
- [MCP read contracts](../../docs/features/mcp_reads.md): retained-data coverage, currencies, units and consistency.
- [Data model](../../docs/DATA_MODEL.md), [order to cash](../../docs/features/order_to_cash.md), [procure to pay](../../docs/features/procure_to_pay.md), [ledger](../../docs/features/ledger.md).
- [Workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md) and [Constitution](../../.specify/memory/constitution.md).

## User Scenarios & Testing

### User Story 1 - Ask a new business question without a new tool (Priority: P1)

An authorized user asks which customers ordered a product in an ISO week, changes the period, groups by customer, and compares quantities or stated values. The same capability works without the browser.

**Why this priority**: It delivers flexibility independently of presentation.

**Independent Test**: Discover supported dimensions and execute filtered/grouped queries on a known order dataset without adding a report implementation.

**Acceptance Scenarios**:

1. **Given** dated orders with repeated product lines and two tenants, **when** product X and ISO week/year are selected, **then** only matching customers in the current tenant appear, without double-counting identities.
2. **Given** the same definition and observation basis, **when** agent, CLI and Web execute it, **then** exact values and business meanings agree.
3. **Given** an unsupported field, incompatible measure or missing date, **when** execution is requested, **then** validation or coverage explains the limitation without silently substituting another measure.
4. **Given** more matches than one page holds, **when** grouping or ranking is requested, **then** calculations cover the complete matching population and displayed subsets are labelled.

### User Story 2 - Explore results visually inside Reports (Priority: P1)

A user opens Reports and starts from an editable template or an empty explorer using business labels rather than database syntax.

**Why this priority**: The owner explicitly requests a powerful integrated UI here.

**Independent Test**: Build a weekly product report visually, change its display, and open contributors for one value.

**Acceptance Scenarios**:

1. **Given** the existing shell, **when** Reports opens, **then** Overview, Explore and My reports are available in the same destination; existing Home metric links still open their matching operational contributors.
2. **Given** Explore, **when** dataset, dates, filters, measures and grouping are chosen, **then** Run returns a table and compatible chart choices with units and the applied definition.
3. **Given** a completed query, **when** filters are edited or a rerun fails, **then** the old result retains its executed definition and is never labelled as the draft's result.
4. **Given** a result, **when** table/chart/pivot presentation changes or a value is expanded, **then** values agree and contributors lead through the existing Inspector to evidence/source links.
5. **Given** a small viewport, keyboard-only use or a supported language, **when** the explorer is used, **then** controls, results and explanations remain accessible without relying on hover or color alone.

### User Story 3 - Reuse and export an analysis (Priority: P2)

A user saves a report definition, reopens it next week, adjusts it and exports its current result.

**Why this priority**: Repeated questions should not require rebuilding the same configuration.

**Independent Test**: Save privately, reopen after data changes, duplicate, rename, export and delete.

**Acceptance Scenarios**:

1. **Given** a valid definition, **when** Save is explicitly invoked with a name, **then** it appears in the author's My reports for the company without storing result facts.
2. **Given** a saved relative period, **when** reopened later, **then** the period resolves again and current data is read; absolute dates retain their values.
3. **Given** another user's or company's report, **when** its identity is requested, **then** it is not disclosed. Lost membership removes access.
4. **Given** concurrent changes or an uncertain save response, **when** saving/retrying, **then** no duplicate or silent overwrite occurs.
5. **Given** a completed result, **when** exported, **then** CSV covers all matching result rows within a declared bound, preserves decimals and context, and does not silently truncate or reinterpret source text as spreadsheet formulas.
6. **Given** a report, **when** duplicated, renamed or deleted, **then** only the intended definition changes and business records remain untouched.

### User Story 4 - Move between agent and visual exploration (Priority: P2)

The user asks the existing agent for a report, opens its definition in Explore, and continues visually or in the same chat.

**Why this priority**: Both entry points must operate on one analytical capability.

**Independent Test**: Ask for a product/customer report, open it, change its period, then send the explicit definition back to the existing chat.

**Acceptance Scenarios**:

1. **Given** a supported agent report, **when** Open in Reports is used, **then** the matching company and editable definition open with the same meaning.
2. **Given** Discuss in chat is explicitly selected, **when** handoff occurs, **then** the existing dock receives the definition and observation context without starting a second chat or business mutation.
3. **Given** an agent request to save, rename or delete a definition, **when** proposed, **then** the existing confirmation flow shows the exact change before execution. Reads require no confirmation.
4. **Given** an unsupported analytical meaning, **when** requested, **then** the response identifies missing meaning/data and may offer a separately labelled narrower supported question.

### Edge Cases

- Renamed/inactive products, missing item links, duplicate display names and foreign identities.
- ISO year boundaries, daylight-saving changes, unknown dates and zero comparison baselines.
- Partial shipments, cancellations, returns, corrections, invoice reversals, revised promises and multiple allocations.
- Mixed units/currencies, negatives, nulls, imported defaults and incomplete history.
- Source replay or a new uninterpreted version; correction changes a previously observed result.
- Timeout, cancel, network error, stale response, company change, invalid saved fields or lost access.
- More groups than chart/pivot/export limits; displayed rows cannot establish complete totals.
- Contributor data changes after execution; a new observation cannot claim exact reproduction of the earlier one.

## Requirements

### Functional Requirements

- **FR-001**: Users and agents MUST discover datasets, grain, dimensions, measures, relationships, filter operators, date meanings and restrictions through one capability catalog.
- **FR-002**: Requests MUST compose measures/dimensions; equality, inclusion, exclusion, text, range and missing-value filters; AND/OR groups; sorting; and day/week/month/quarter/year grouping where applicable. Only documented compatible combinations are accepted.
- **FR-003**: Measures MUST include record/distinct-identity counts, sums of recorded quantities/stated amounts, minimum/maximum dates and agreed prices, and comparisons of the same measure between two explicit or adjacent equal-duration periods. Missing and zero baselines MUST remain distinct.
- **FR-004**: The feature MUST satisfy every row of `question-coverage.md`, including existence/absence, first/last observed purchase, product co-occurrence and period ranking. Restricted meanings MUST produce an explicit limitation.
- **FR-005**: Execution MUST show resolved dates, timezone, date field, cancellation policy and currency/unit boundaries. Defaults are the user's display timezone and ISO weeks with year. Undated records MUST remain unknown/excluded rather than receiving an import date.
- **FR-006**: Results MUST calculate population aggregates independently of pagination and provide deterministic ordering, observation/consistency information and relevant missing/excluded counts. Timeouts, cancellation and limits MUST never yield an apparently complete partial total.
- **FR-007**: Every value MUST offer its definition and bounded, navigable contributing-record explanation preserving filter/group context. If the earlier observation cannot be reproduced, drill-down MUST identify a new observation.
- **FR-008**: Reports MUST contain Overview, Explore and My reports. Overview retains existing operational metrics/links. Explore offers starter definitions, a blank report, collapsible configuration, explicit Run and a result area focused on the selected analysis.
- **FR-009**: Users MUST modify datasets, dates, filter groups, measures, grouping, ordering and comparisons without a query language. Scoped entity selectors show recognizable labels; invalid combinations explain how to repair them.
- **FR-010**: Compatible results MUST offer a sortable table, categorical bar chart, time-series line chart and pivot with up to two row dimensions, one column dimension and two measures. Currency/unit series remain separate. Distinct-count totals are recalculated at the total grain, never summed from subgroups. Display bounds MUST be visible with a table fallback.
- **FR-011**: Draft and executed definitions MUST remain distinguishable across edits, errors, cancellation, out-of-order responses and company changes. Loading, empty, unavailable and retry states MUST be explicit.
- **FR-012**: Users MUST save, reopen, rename, duplicate and delete private company-scoped definitions including presentation and relative/absolute dates. Incompatible older definitions MUST show a repairable error; they must not silently change meaning.
- **FR-013**: Definition changes MUST enforce ownership/membership, prevent duplicate retries/lost updates and use existing confirmation for agent mutations. Web saves are explicit actions; deletion requires named confirmation.
- **FR-014**: CSV export MUST preserve exact values, units/currencies, applied date/filter context and observation information. It covers all matching result rows within a declared bound; oversized exports are refused with a narrowing instruction. Source text is rendered as data, not spreadsheet formulas. A changed observation is disclosed.
- **FR-015**: Agent reports MUST open as editable Reports definitions; Discuss in chat sends the selected definition/context to the existing dock. Handoffs preserve company scope and refuse unauthorized identities. Opening does not save.
- **FR-016**: The workspace MUST use the existing shell, Inspector and language/locale/timezone preferences. English, German, Dutch and Spanish, keyboard operation and 390px–1440px layouts MUST be verified. Essential values remain available as text/table.
- **FR-017**: Equivalent definitions MUST produce equivalent values/meaning through CLI, agent and Web for the same observation. Technical identifiers belong in optional explanations rather than the ordinary setup flow.
- **FR-018**: Queries, continuation, contributors, exports and definitions MUST enforce tenant/authorization boundaries. A definition cannot select another tenant. Analytical execution MUST be bounded and unable to perform business or definition mutations.
- **FR-019**: Editable starter definitions MUST include customer/product orders, weekly trends, inactive customers, product co-occurrence, current inventory, open deliveries, due invoices and unallocated payments. They MUST use shared execution rather than independent calculations.

### Domain and Traceability Requirements

- **DR-001**: Results are read-time observations with shortest true links to Reality, Evidence and Source. They MUST NOT become new Facts or overwrite stated values. Sums of stated amounts do not recreate totals from price times quantity.
- **DR-002**: Fulfillment, reservations, effective promises, corrections, returns, billing, settlement and aging MUST reuse shared definitions. Reservation gaps are not physical shortages, dispatch is not confirmed receipt, and supplier promises are not forecasts.
- **DR-003**: All records and definitions MUST be tenant-scoped through shared application capabilities. Names, human numbers and SKUs do not establish identity/ownership.
- **DR-004**: Joins MUST preserve measure grain. Replay/version policy, multiple invoices/payments, repeated lines and distinct totals MUST not multiply values. Coverage is interpreted retained evidence under an explicit version policy.
- **DR-005**: Unknown history/dates/units/price basis/supplier alternatives MUST remain explicit. Incomplete records cannot establish first-ever purchases, global absence, historical due dates or causal allocation.
- **DR-006**: Saved definitions are user configuration, not operational authority. Their lifecycle MUST leave business data and provenance untouched.

### Key Entities

- **Dataset**: A business perspective with defined grain, measures and relationships.
- **Report definition**: Selected question, filters, grouping, dates, comparison and display, independent of results.
- **Observation**: Values, coverage, executed definition and contributor navigation.
- **Saved report**: Named user-owned definition within a company, with a revision for safe editing.

## Success Criteria

- **SC-001**: All 30 assessment questions have executable cases yielding exact supported results or the explicit restricted answer in the coverage contract.
- **SC-002**: Changing a supported product, customer, period, grouping or ordering requires no additional report-specific behavior.
- **SC-003**: A reviewer can build the customer/product/week example, change display and inspect a contribution within three minutes using business controls.
- **SC-004**: Exact counts/decimals agree across entry points, pagination, compatible displays and exports on the acceptance dataset; no foreign-tenant records are disclosed.
- **SC-005**: For a representative company with 100,000 order lines, 95% of the agreed common order/customer/product runs show results within five seconds in the documented benchmark environment. No query runs beyond a 30-second execution bound. Environment and cold/warm results MUST be reported.
- **SC-006**: Every FR/DR has acceptance evidence before completion; current Home/Analytics links pass regression checks.
- **SC-007**: Definition lifecycle, chat handoff and report building work in all four languages and declared viewports with keyboard-accessible controls.

## Assumptions and Dependencies

- The owner explicitly approved this specification on 2026-09-13 (conversation: “freigave”), after reviewing the tool workflow and browser UI draft. Approval covers the described analytics capability, integrated workspace, private saved reports, pivot, CSV and chat handoff. Technical design review and executable verification remain separate workflow gates.
- PostgreSQL remains authoritative. Technical contracts, indexes and any minimal definition schema require planning and a Constitution Check after product-scope acceptance.
- Only cataloged typed data and existing derivations are included; arbitrary filtering of unknown source payload fields is excluded.
- Descriptive order cancellation options are all recorded orders (default) or exclusion of fully operationally cancelled orders. Partially cancelled orders retain original stated evidence amounts/quantities with a visible explanation. Remaining commitments are a separate measure. Version eligibility must follow each intake's real lifecycle.
- Private report ownership is author plus company. Reads require no confirmation; agent definition mutations do. Team sharing is deferred.
- Natural-language interpretation uses the existing agent. The visual explorer remains usable when the agent is unavailable.
- Complete historical sourcing, historical payment terms and general customer receipt completion are not assumed.
- Concrete report-definition and result/display/export size limits belong in the reviewed plan. Performance targets above are proposed requirements, not measurements.

## Open Questions

No unresolved clarification markers. Defaults are explicit and ready for product-scope review.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-004 | US1.1–4; US4.4 | Catalog compatibility, full question coverage, grain and unsupported cases |
| FR-005–FR-007 | US1.1,3,4; US2.4 | ISO/timezone/null/history, population totals and contribution consistency |
| FR-008–FR-011 | US2.1–5 | Explorer, old links, chart/pivot totals and stale-response browser checks |
| FR-012–FR-013 | US3.1–4,6; US4.3 | Private lifecycle, membership, revision/retry and confirmation |
| FR-014 | US3.5 | CSV scope, limits, decimals/formula text and observations |
| FR-015 | US4.1–3 | Agent/explorer handoff and tenant-boundary tests |
| FR-016 | US2.5 | Language audit, keyboard and mobile/desktop visual review |
| FR-017–FR-018 | US1.2–4; US3.3; US4.1–3 | Adapter parity, tenant isolation, bounded reads and benchmark |
| FR-019 | US2.1–2 | Starters execute as editable shared definitions |
| DR-001–DR-002 | US1.2–3; US2.4; US4.4 | Canonical-service parity and evidence/reality distinctions |
| DR-003–DR-004 | US1.1,4; US3.3 | Foreign identities, replay/version, fan-out and distinct totals |
| DR-005 | US1.3; US4.4 | Partial history and unsupported meanings |
| DR-006 | US3.1,6 | Definition lifecycle leaves business records unchanged |

Exact test names and sequencing belong to planning/tasks after scope acceptance. Nothing is marked implemented by this draft.

### Chart guidance correction (2026-09-13)

FR-010/FR-016 clarification: an unavailable chart identifies the actual cause:
missing non-partition grouping, multiple currencies, multiple units, or both.
Currency-only results must not ask for a unit. Guidance tells users to select the
relevant filter (or grouping) and run the analysis again. Existing partition
boundaries, executed-result semantics and the table fallback remain unchanged.
Acceptance: EUR/USD order results request only a currency filter; kg/pcs results
request only a unit filter; mixed currencies and units request both; ungrouped
results request grouping; a compatible single-partition result still renders.

### Recognizable Explorer controls (2026-09-13)

FR-009/FR-016: dataset, sorting, dates and filter selectors must look like selectable
form controls rather than indented text. Use the shared bordered form control,
a visible dropdown chevron and at least a 44px control height. Text/date/number
inputs use the same shared control. Filters have a bordered disclosure surface.
Preserve native select keyboard operation, associated labels, focus indication,
light/dark themes and mobile width. This is presentation only: editing still
requires explicit Run and never changes the last executed result automatically.
Acceptance: dataset and sorting are visibly bordered and keyboard-selectable;
date/filter controls share this appearance; Filter opens by click or keyboard;
mobile and dark mode retain visible controls with no page overflow.

### Direct chart partition selection (2026-09-13)

FR-010/FR-016 supersedes the earlier mixed-partition narrowing guidance: a grouped
result with multiple currencies/units immediately shows the first available
partition as a chart and exposes labeled selection buttons above it. Selecting
another partition updates only the chart, without editing filters, running a query,
converting values or adding distinct counts. Labels identify the currency and/or
unit, including unknown values. Combined partitions remain separate. Select from
all loaded rows before applying the 50-row chart bound. Table and totals retain all
partitions. A selected partition absent from a new result falls back to its first
available partition. Missing grouping retains its separate guidance.
Acceptance: EUR/USD shows EUR immediately, USD click displays only USD rows without
another API call; kg/pcs and combined partitions behave equivalently; unknowns are
explicit; a partition after row 50 can be selected; limits remain disclosed.

### Dedicated analysis chat (2026-09-13)

FR-015/FR-016: the explicit action is labeled "Start new chat about analysis". It
creates a conversation through the existing session service, opens it in the dock
and attaches the selected definition. It never posts a message automatically or
modifies the previous conversation. Clear old draft/commitment/retry state only
after successful creation; creation failure preserves the old conversation and
shows an error. Concurrent creation is guarded. While a reply is being sent, ask
the user to wait rather than moving its context. The attachment belongs only to the
new session and tenant; history navigation must not carry it into another session.
Sending waits for the selected session's data, never using retained old-session data.
Acceptance: from an existing chat, the action creates exactly one new session and
shows its attachment without old messages; first send targets that session with the
definition; failed creation changes neither old draft nor attachment; foreign
handoffs are ignored; selecting an older conversation removes the attachment.
