# Feature Specification: Demo and Scenarios Baseline

**Baseline ID**: `015-demo-scenarios`
**Created**: 2026-08-31
**Status**: Reviewed
**Language**: English
**Input**: "Baseline guided demo onboarding and deterministic reusable business-story scenarios."

## Context and Intent

### Problem

New users and contributors need a short, coherent demonstration of the domain model,
while tests need deterministic business stories that prove the same services. This
baseline prevents separate demo-only business logic and protects non-empty tenants.

### Scope

- Guided 1–2 minute Source → Evidence → Reality onboarding story.
- Step presentation with event, proposed command, primitive result, and explanation link.
- Interactive run/edit/quit behavior and automatic execution.
- Shared demo seeding and normal-month services across CLI, Web, and Chat proposals.
- Deterministic, rerunnable domain state with stable explanation identifiers.
- Non-destructive handling of non-empty tenants and optional configured bootstrap.

### Non-Goals

- A second domain implementation, mocked stock/finance results, or web-only demo path.
- Resetting or deleting a non-empty tenant implicitly.
- Production data migration, benchmark/load generation, or arbitrary fixture scripting.
- Guaranteeing terminal/UI formatting equality; domain-state equivalence is authoritative.

### Existing Contracts

- [`docs/features/demo.md`](../../docs/features/demo.md)
- [`docs/DEMO_SPEC.md`](../../docs/DEMO_SPEC.md)
- [`docs/features/chat.md`](../../docs/features/chat.md)
- [`docs/features/order_to_cash.md`](../../docs/features/order_to_cash.md)
- [`docs/features/procure_to_pay.md`](../../docs/features/procure_to_pay.md)
- [Constitution](../../.specify/memory/constitution.md)

## Current Capability Boundary

The guided demo composes normal application services to create references, record
stock, ingest a Shopify order, expose shortage, receive supply, reserve, ship, explain,
and show activity. Auto mode is the golden integration path. Chat demo and normal-month
suggestions create ChangeProposals and call the same services after confirmation.

The September 2026 normal-month scenario is deterministic and safe to rerun, producing
stable counts and derived inventory/receivable outcomes. Individual interface paths
are tested, but one focused test comparing the entire resulting state across
interactive CLI, auto mode, and Web onboarding is absent and remains a coverage gap.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run a Guided Domain Demo (Priority: P1)

As a new user, I can complete a short business story and understand each resulting
Source, Evidence, and Reality primitive.

**Why this priority**: The demo proves the domain model rather than merely populating data.

**Independent Test**: Run the golden demo on an empty tenant and inspect each intended
primitive, quantity, fulfilment result, trace ID, and explanation link.

**Acceptance Scenarios**:

1. **Given** an empty tenant, **When** the demo runs, **Then** it creates references,
   opening stock, lossless order source, Evidence, customer/supplier Commitments,
   Reservations, receipts, shipment, and explanations through shared services.
2. **Given** each step, **When** presented interactively, **Then** the business event,
   proposed command, resulting primitive, and next explanation link are visible.
3. **Given** edit or quit, **When** chosen, **Then** edit changes only the proposal and
   quit preserves already committed history.

### User Story 2 - Protect Existing Tenant Data (Priority: P1)

As an operator, I can try the demo without an existing company's data being reset.

**Why this priority**: Onboarding must never become a destructive shortcut.

**Independent Test**: Attempt the demo in a populated tenant and verify that existing
records remain and a fresh demo tenant is offered/used instead.

**Acceptance Scenarios**:

1. **Given** a non-empty tenant, **When** demo starts, **Then** it does not reset or
   overwrite that tenant and offers a fresh demo tenant.
2. **Given** no tenant, **When** demo starts, **Then** a bounded sample company may be created.
3. **Given** partial committed progress then quit, **When** resumed or inspected, **Then**
   history remains truthful and no rollback is implied.

### User Story 3 - Run the Deterministic Normal Month (Priority: P1)

As a contributor or evaluator, I can run September 2026 repeatedly and receive the
same coherent business state without duplicates.

**Why this priority**: Determinism makes the scenario executable product documentation.

**Independent Test**: Run normal month twice and compare returned values, table counts,
proposal/action identity, physical inventory, Reservation state, and receivable.

**Acceptance Scenarios**:

1. **Given** an empty tenant, **When** normal month runs, **Then** it produces the
   documented complete business story and stable results.
2. **Given** the same tenant and completed scenario, **When** rerun, **Then** results and
   relevant record counts remain unchanged.
3. **Given** execution from Chat, **When** proposed, **Then** no data changes before
   confirmation and the confirmed action calls the canonical scenario service.

### User Story 4 - Use One Scenario Across Interfaces (Priority: P2)

As a reviewer, I can compare CLI, Web, and Chat demo execution by resulting domain state
rather than presentation details.

**Why this priority**: Interface equivalence prevents demo-specific business rules.

**Independent Test**: Run each entry path in isolated empty tenants and compare Source,
Evidence, Reality, inventory, fulfilment, finance, and trace identifiers.

**Acceptance Scenarios**:

1. **Given** equivalent starting tenants, **When** each interface runs the same scenario,
   **Then** canonical domain outcomes are equivalent.
2. **Given** Chat/Web mutation entry, **When** started, **Then** explicit confirmation is
   required before scenario data is created.
3. **Given** presentation differences, **When** compared, **Then** they do not require
   separate domain state or alternate calculations.

### Edge Cases

- Demo is started in a partially populated tenant.
- User quits after one or several committed steps.
- Scenario reruns after prior completion or partial failure.
- Fixture/source is missing or interpretation fails.
- Chat proposal is rejected, replayed, or confirmed under another tenant.
- Bootstrap is enabled repeatedly or absent in production configuration.
- Different interfaces produce subtly different domain counts or links.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Guided demo MUST compose shared services to demonstrate Source → Evidence
  → Reality and MUST NOT write domain tables directly.
- **FR-002**: Each interactive step MUST show business event, proposed command, resulting
  primitive, and next explanation link before advancing.
- **FR-003**: Run MUST execute the proposal, Edit MUST change the proposal before
  execution, and Quit MUST preserve already committed history.
- **FR-004**: Demo MUST NOT implicitly reset a non-empty tenant and MUST offer/use a
  fresh demo tenant for a clean run.
- **FR-005**: Auto, interactive CLI, Web onboarding, and Chat MUST call the same scenario
  and domain services; interactive mutations MUST require confirmation.
- **FR-006**: Scenario success MUST be compared by domain state and trace IDs, not UI formatting.
- **FR-007**: Normal month MUST be deterministic, idempotent on rerun, tenant-scoped,
  and retain one auditable scenario action/proposal.
- **FR-008**: Normal month MUST expose stable expected inventory, Reservation,
  fulfilment, financial, and reference-data outcomes.
- **FR-009**: Configured bootstrap MUST run at most once per intended tenant/setup and
  MUST remain disabled without explicit configuration.
- **FR-010**: A focused executable proof MUST compare complete domain-state equivalence
  across interactive CLI, auto mode, and Web onboarding.

### Domain and Traceability Requirements

- **DR-001**: Demo/scenario code MUST use the same Source, Evidence, and Reality services
  as normal product flows.
- **DR-002**: Scenario identity/idempotency MUST use opaque IDs or stable scenario keys,
  never human business numbers as record identity.
- **DR-003**: Every important outcome MUST link to its created authoritative records and explanation.
- **DR-004**: Demo convenience MUST NOT weaken tenant scope or mutation confirmation.

### Key Entities

- **Scenario action/proposal**: Auditable request and execution identity for a scenario.
- **Demo tenant**: Isolated company workspace for safe evaluation.
- **Source/Evidence/Reality records**: Normal domain output, not demo-specific models.

## Reality Applicability

- **Source**: Demo Shopify payload is ingested through immutable source services.
- **Evidence**: Documents/lines are normal interpreted or manual Evidence.
- **Reality**: Commitments, Reservations, Movements, LedgerEntries, and allocations are normal records.
- **Shortest links**: Demo output exposes the same canonical links as production stories.
- **Stored/derived**: Scenario audit/domain records stored; inventory, fulfilment, and finance derived.
- **Shared boundary**: CLI, Web, Chat, bootstrap, and tests call canonical services.
- **Web explanation**: Guided steps link directly to Inspect and actual created records.

## Success Criteria *(mandatory)*

- **SC-001**: A first-time user can complete the guided demo in 1–2 minutes with each
  important primitive explained.
- **SC-002**: A non-empty tenant loses or overwrites zero records when demo is requested.
- **SC-003**: Two normal-month runs return identical results and relevant record counts.
- **SC-004**: Normal month yields physical 6, reserved 0, and receivable 870 exactly.
- **SC-005**: Rejected/unconfirmed Chat or Web proposals create zero scenario domain records.
- **SC-006**: Every scenario outcome is traceable through normal Source/Evidence/Reality records.
- **SC-007**: Cross-interface state equivalence has focused proof or remains a visible gap.

## Assumptions and Dependencies

- Demo fixtures are versioned repository assets and are not production customer data.
- Domain baselines remain authoritative for each operation in the story.
- Visual/onboarding polish belongs to the Web product baseline.

## Open Questions

The product owner approved this baseline on 2026-08-31. Spec 027 subsequently proved
focused complete-state equivalence across interactive CLI, CLI auto mode, and confirmed
Product Web onboarding; the product owner approved its final review on 2026-09-02.

## Requirement Evidence

| Requirement | Status | Contract | Implementation | Executable proof | Decision or gap |
|---|---|---|---|---|---|
| FR-001–FR-004 | Verified as-is | Demo and Demo Spec contracts | demo services/CLI | demo, CLI, Chat, and business-story tests | — |
| FR-005–FR-006 | Verified as-is | Demo/Chat/Web contracts | shared demo/scenario services | CLI and Chat confirmation tests | — |
| FR-007–FR-008 | Verified as-is | Chat/Demo contracts | `demo/normal_month.py:run_normal_month` | `tests/scenarios/test_normal_month.py` | — |
| FR-009 | Verified as-is | deployment/bootstrap contract | configured bootstrap service | `tests/test_bootstrap.py` | — |
| FR-010 | Verified as-is | Demo contract; Spec 027 | Shared `ensure_demo` service through CLI and Web adapters | `tests/test_demo_entrypoint_parity.py`; Product Web demo contract | Spec 027 final review approved 2026-09-02 |
| DR-001–DR-004 | Verified as-is | Constitution; Demo contracts | shared services and trace outputs | scenario, Chat, CLI, tenancy tests | — |

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-003 | US1 | Guided demo/CLI story tests |
| FR-004 | US2 | Non-empty tenant safety tests |
| FR-007–FR-009 | US3 | Normal-month and bootstrap tests |
| FR-005–FR-006, FR-010 | US4 | Shared entry-path and complete-state equivalence tests |
| DR-001–DR-004 | All | Cross-domain service/trace review |
