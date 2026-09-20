# Feature Specification: Demo Contribution Portfolio

**Feature Branch**: `243-demo-contribution-portfolio`

**Created**: 2026-09-20

**Status**: Draft

**Language**: English

**Input**: User description: "Extend the canonical demo company so business users can inspect a broad, credible set of DB1 and DB2 examples across demo invoices and items, including positive, low, and negative contribution outcomes, varied selling costs, and truthful incomplete cases. Deliver it as a separate pull request."

## Context and Intent

### Problem

The canonical demo company proves the retained-cost and contribution model with one complete case, one missing-cost case, and one late-cost/return case. That is sufficient for a technical proof but too narrow for a business demonstration: most demo invoices do not show a reviewed DB1 or DB2, and a Head of Operations cannot quickly compare different commercial outcomes.

### Scope

Extend the canonical demo profile with a bounded, source-backed contribution portfolio. The portfolio must contain several easy-to-find invoice-line examples with materially different DB1 and DB2 outcomes while preserving deliberately incomplete cases. Every amount must remain traceable through the normal Source → Evidence → Reality path and the shared retained-cost services.

### Non-Goals

- Making every historical or continuously generated demo invoice contribution-ready.
- Inventing costs for existing records whose sources do not state them.
- Adding a second contribution calculation, demo-only read path, schema field, or browser rule.
- Changing ordinary company setup, empty Sandbox behavior, or continuous Demo Data semantics.
- Turning derived DB1 or DB2 values into stored financial authority.

### Existing Contracts

- [Company setup and demo data](../../docs/features/company-setup-demo.md)
- [Spec 146 demo profile contract](../146-company-setup-demo/contracts/demo-profile.md)
- [Spec 242 retained inventory cost and contribution](../242-inventory-cost-contribution/spec.md)
- [Web specification](../../docs/WEB_SPEC.md)

## User Scenarios & Testing

### User Story 1 - Compare Credible Contribution Outcomes (Priority: P1)

As a Head of Operations evaluating Reality, I can open a canonical demo company and inspect multiple reviewed invoice-line contributions that demonstrate healthy, low, and negative commercial outcomes.

**Why this priority**: A varied portfolio shows that Reality explains real commercial differences instead of presenting one hand-crafted happy path.

**Independent Test**: Create a fresh canonical demo company, inspect the named portfolio entries, and verify that at least one entry has healthy positive DB2, one has lower positive DB2, and one has negative DB2, with exact source-backed inputs and complete review state.

**Acceptance Scenarios**:

1. **Given** a freshly initialized canonical demo company, **When** a business user opens the contribution explanations for the named portfolio invoices, **Then** at least three complete reviewed outcomes cover healthy positive, lower positive, and negative DB2.
2. **Given** any complete portfolio outcome, **When** the user opens its explanation, **Then** received net revenue, consumed acquisition cost, reviewed selling costs, DB1, DB2, effective time, knowledge time, and trace links are available through the shared contribution read.
3. **Given** the same profile is initialized again for the same setup request, **When** initialization replays, **Then** it does not duplicate source evidence, reviews, or portfolio identities.

---

### User Story 2 - Understand Different Selling-Cost Drivers (Priority: P2)

As an ERP or finance professional, I can compare complete contributions whose DB2 changes because their reviewed selling-cost composition differs.

**Why this priority**: DB2 is useful only when users can see which selling costs bridge DB1 to DB2 and distinguish direct from allocated costs.

**Independent Test**: Inspect the complete portfolio entries and verify that at least three different reviewed selling-cost compositions are present and reconcile exactly from DB1 to DB2.

**Acceptance Scenarios**:

1. **Given** the complete portfolio, **When** the user compares its explanations, **Then** the portfolio includes distinct direct and allocated selling-cost amounts rather than repeating one cost pattern.
2. **Given** a complete portfolio entry, **When** its DB2 is shown, **Then** every included selling-cost category is evidenced or explicitly reviewed as zero and the displayed arithmetic reconciles exactly.

---

### User Story 3 - See Truthful Missing and Changing Knowledge (Priority: P3)

As a process owner, I can contrast complete examples with deliberately incomplete and later-completed cases so that I understand that missing evidence is not zero and later knowledge does not rewrite history.

**Why this priority**: The demo must teach Reality's trust model, not merely maximize the number of populated figures.

**Independent Test**: Inspect the retained missing-cost and late-cost/return cases and verify that their gaps and time-dependent outcomes remain distinguishable from the complete portfolio.

**Acceptance Scenarios**:

1. **Given** the missing-cost case, **When** its contribution is queried, **Then** unknown DB1 or DB2 remains unknown with an explicit missing basis rather than becoming zero.
2. **Given** the late-cost/return case, **When** it is inspected at its relevant knowledge points, **Then** the earlier incomplete state and later reviewed state remain truthful and separately explainable.
3. **Given** continuous synthetic demo orders, **When** they arrive after setup, **Then** they retain their existing default missing-cost semantics and are not silently presented as part of the reviewed portfolio.

### Edge Cases

- A portfolio invoice has revenue but its acquisition-cost coverage is incomplete: it must remain outside the complete outcome counts and expose the gap.
- A selling-cost category has no applicable cost: it must be explicitly reviewed as zero before DB2 is complete.
- A selling cost would make DB2 negative: the signed result and rate must remain visible without clipping or reclassification.
- A customer return reverses quantity and cost: signed evidence must remain linked to the original economic scope.
- Profile initialization is retried after partial failure: the same stable source and review identities must be reused without duplication.
- Multiple currencies exist in the demo company: contribution examples must remain currency-specific and must never be summed across currencies.

## Requirements

### Functional Requirements

- **FR-001**: The canonical demo profile MUST expose a bounded named contribution portfolio containing at least six complete reviewed invoice-line outcomes.
- **FR-002**: The complete portfolio MUST include at least one healthy positive DB2 outcome, one lower positive DB2 outcome, and one negative DB2 outcome.
- **FR-003**: The complete portfolio MUST include at least three materially distinct reviewed selling-cost compositions, including both direct and allocated selling costs across the portfolio.
- **FR-004**: Every complete portfolio outcome MUST derive received net revenue from recorded financial evidence, acquisition cost from reviewed consumed inventory cost, and selling costs from source-backed assignments or explicit reviewed-zero dispositions.
- **FR-005**: Every complete portfolio outcome MUST be readable through the existing shared contribution explanation and MUST expose exact DB1, DB2, DB2 rate, currency, effective time, knowledge time, freshness, and traceability.
- **FR-006**: The profile MUST retain at least one deliberately missing-cost outcome whose DB1 and DB2 remain unknown with an explicit missing basis.
- **FR-007**: The profile MUST retain at least one late-cost/customer-return story whose earlier incomplete and later reviewed states remain separately explainable.
- **FR-008**: Portfolio examples MUST use stable human-readable demo references for discovery while preserving opaque record identities for relationships.
- **FR-009**: Profile initialization and replay MUST be idempotent and MUST NOT duplicate portfolio sources, evidence, assignments, matches, or reviews.
- **FR-010**: The contribution portfolio MUST remain tenant-scoped and MUST use the same services, confirmation records, calculations, and inspection paths as ordinary business data.
- **FR-011**: Continuous synthetic Demo Data MUST retain its existing missing-cost behavior and MUST NOT be silently auto-reviewed or included in the canonical complete portfolio.
- **FR-012**: The canonical demo profile contract and business documentation MUST explain the portfolio's purpose, named outcomes, exact arithmetic, intentional gaps, and boundary from continuous Demo Data.

### Domain and Traceability Requirements

- **DR-001**: Every portfolio input MUST preserve the SourceRecord → Document/DocumentLine → Movement/LedgerEntry path wherever that business event requires those stages.
- **DR-002**: Source-stated revenue, quantity, prices, acquisition values, and selling costs MUST be recorded losslessly and MUST NOT be recomputed as alternative authority.
- **DR-003**: DB1, DB2, and DB2 rate MUST remain read-time observations derived by the shared retained-cost services and MUST NOT be stored as new financial authority.
- **DR-004**: Portfolio relationships MUST use opaque identities and the shortest true links; stable human-readable demo references are labels for discovery, never identity.
- **DR-005**: Every portfolio read and write MUST remain tenant-scoped and use the same service and confirmation boundaries as ordinary business data.

### Key Entities

- **Contribution portfolio**: The bounded set of named canonical demo scenarios used to compare reviewed commercial outcomes; it groups references but creates no new financial authority.
- **Complete contribution outcome**: An invoice-line scope with reviewed revenue completeness, complete acquisition-cost matching, and complete selling-cost category dispositions.
- **Selling-cost composition**: The reviewed direct and allocated selling-cost assignments that bridge a complete outcome from DB1 to DB2.
- **Incomplete contribution outcome**: A named invoice-line scope that intentionally lacks required evidence or review and therefore exposes an explicit missing basis.
- **Late-cost/return story**: A named scenario that preserves the sequence between initial incomplete knowledge, later cost evidence, and signed return evidence.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A fresh canonical demo company provides at least six complete, named contribution explanations and at least two named non-happy-path explanations without manual data entry.
- **SC-002**: The complete examples include positive, low-positive, and negative DB2 outcomes and at least three distinct selling-cost compositions.
- **SC-003**: Every complete example reconciles exactly from received net revenue through acquisition and selling costs to DB1 and DB2 with no unexplained amount.
- **SC-004**: A business reviewer can locate the named examples and explain why their DB2 differs using only the demo references and contribution explanations.
- **SC-005**: Replaying initialization produces no additional portfolio sources, evidence, reviews, or assignments.
- **SC-006**: Existing missing-cost, late-cost/return, ordinary setup, and continuous Demo Data behaviors remain unchanged outside the bounded portfolio.

## Assumptions and Dependencies

- The canonical `international_demo` profile is the only company-setup profile extended by this feature.
- Six complete outcomes are sufficient to demonstrate variety without turning every seeded invoice into a reviewed financial assertion.
- Existing inventory-cost, commercial-match, selling-cost assignment, contribution-review, inspection, and source-record capabilities are sufficient; no schema expansion is expected.
- The portfolio may add dedicated source-backed demo transactions rather than retroactively assigning invented costs to unrelated historical invoices.
- Existing language and number-format preferences continue to control presentation; this feature changes business examples, not formatting behavior.
- The existing company setup/demo contract and retained-cost/contribution specifications remain authoritative dependencies.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001, FR-002 | US1 scenarios 1-2 | Fresh-profile portfolio count and outcome-classification business-story test |
| FR-003, FR-004 | US2 scenarios 1-2 | Selling-cost composition and exact reconciliation business-story test |
| FR-005 | US1 scenario 2 | Shared contribution query and explanation contract test |
| FR-006 | US3 scenario 1 | Missing-cost regression test |
| FR-007 | US3 scenario 2 | Late-cost and signed-return regression test |
| FR-008 | US1 scenarios 1-2 | Manifest discovery and opaque-link assertions |
| FR-009 | US1 scenario 3 | Initialization replay count and identity test |
| FR-010 | US1 scenario 2 | Tenant-isolation and shared-service test evidence |
| FR-011 | US3 scenario 3 | Continuous Demo Data boundary regression test |
| FR-012 | US1-US3 | Demo contract and handbook documentation checks |
| DR-001, DR-002 | US1 scenario 2, US2 scenario 2 | Source/evidence/reality lineage and exact received-value assertions |
| DR-003 | US1 scenario 2 | Read-time contribution derivation and persistence-boundary assertions |
| DR-004 | US1 scenario 3 | Stable references, opaque relationship, and replay assertions |
| DR-005 | US1 scenario 2 | Cross-tenant denial and ordinary service-path assertions |
