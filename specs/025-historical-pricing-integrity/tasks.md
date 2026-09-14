---
description: "Requirement-traceable implementation tasks for historical pricing integrity"
---

# Tasks: Historical Pricing Integrity

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/historical-pricing.md`, and `quickstart.md`
**Gate**: Constitution Check passed, specification and plan approved, and no unresolved
`[NEEDS CLARIFICATION]`

All task descriptions, paths, review notes, and resulting repository artifacts MUST be
written in English. Tests precede the behavior they prove.

## Format

`- [ ] T001 [P?] [US1] [FR-001] Action with exact file path`

## Phase 1: Specification and Design Gates

- [x] T001 Record product-owner specification approval in `specs/025-historical-pricing-integrity/spec.md` and `specs/025-historical-pricing-integrity/checklists/requirements.md`
- [x] T002 Record product-owner plan approval after every Constitution Check row passes in `specs/025-historical-pricing-integrity/plan.md`
- [x] T003 Run `$speckit-analyze` and resolve every CRITICAL cross-artifact finding in `specs/025-historical-pricing-integrity/`

## Phase 2: Foundational Historical-Pricing Boundary

**Goal**: Establish reusable test snapshots and one tenant-safe explanation contract
without changing schema or existing mutation semantics.

- [x] T004 [P] [DR-005] Add a schema/model guard asserting that existing DocumentLine pricing fields are sufficient and no Spec 025 table or column is introduced in `packages/reality-core/tests/test_migrations.py`
- [x] T005 [P] [FR-001] [FR-011] Add reusable Document, DocumentLine, pricing-configuration, and downstream Reality snapshot helpers in `packages/reality-core/tests/test_pricing.py`
- [x] T006 [P] [FR-010] [DR-004] Add two-tenant pricing-entry and DocumentLine fixtures with matching human values in `packages/reality-core/tests/test_pricing.py`
- [x] T007 [FR-007] [FR-012] [FR-013] [DR-001] Add failing contract assertions for optional selected-entry attachment, the agreed-versus-current result shape, read-only behavior, and tenant-not-found boundary in `packages/reality-core/tests/test_pricing.py`

**Checkpoint**: The explanation boundary has one vocabulary and no persistence change.

## Phase 3: User Story 1 — Preserve an Agreed Price (P1)

**Goal**: Prove that all supported pricing maintenance leaves existing Evidence and
downstream Reality unchanged.

**Independent Test**: Capture one linked agreed line and downstream records, change
list lifecycle/default/applicability through supported services, and compare the entire
snapshot before and after.

### Failing proof

- [x] T008 [P] [US1] [FR-001] [FR-002] [FR-013] Add failing atomic selected-entry attachment plus linked-line non-rewrite stories for list rename, lifecycle, default replacement, new entries/lists, and later applicability in `packages/reality-core/tests/test_pricing.py`
- [x] T009 [P] [US1] [FR-002] [FR-003] Add failing historical-reference stories for supported new direct/group assignments, new memberships, priorities, and time-bounded configuration without inventing update/delete operations in `packages/reality-core/tests/test_pricing.py`
- [x] T010 [P] [US1] [FR-005] [FR-011] [DR-003] Add failing Commitment, Reservation, Movement, LedgerEntry, fulfillment, inventory, and finance non-mutation stories in `packages/reality-core/tests/test_pricing.py`
- [x] T011 [P] [US1] [FR-011] Add failing rejected-change and injected-rollback before/after snapshot stories in `packages/reality-core/tests/test_pricing.py`

### Implementation and acceptance

- [x] T012 [US1] [FR-001] [FR-002] [FR-003] [FR-013] Add optional selected-entry input to shared DocumentLine creation, reproduce and validate the exact pricing decision before the atomic write, and preserve the retained relationship in `packages/reality-core/src/reality/services/core.py`
- [x] T013 [US1] [FR-005] [FR-011] [DR-003] Verify that pricing mutations are already isolated from Document, DocumentLine, Commitment, Reservation, Movement, and LedgerEntry state; make the smallest correction only if T010–T011 fail in `packages/reality-core/src/reality/services/core.py`
- [x] T014 [US1] Run the complete User Story 1 PostgreSQL acceptance and record exact results in `specs/025-historical-pricing-integrity/quickstart.md`

**Checkpoint**: Existing commercial Evidence is invariant under supported pricing changes.

## Phase 4: User Story 2 — Apply New Pricing Only to New Work (P1)

**Goal**: Prove that each agreement uses its own effective pricing context while older
Evidence remains fixed.

**Independent Test**: Record price A, introduce later pricing context B, record new work,
and reproduce both results independently across resolution dimensions.

### Failing proof

- [x] T015 [P] [US2] [FR-004] [FR-005] Add failing before/after effective-time, quantity-tier, direct/group/default precedence, lifecycle, and validity stories in `packages/reality-core/tests/test_pricing.py`
- [x] T016 [P] [US2] [FR-006] Add failing manually agreed line story proving no manufactured PriceListEntry provenance in `packages/reality-core/tests/test_pricing.py`
- [x] T017 [P] [US2] [FR-008] [FR-009] Add failing same-amount/different-entry identity plus sales/purchase separation stories in `packages/reality-core/tests/test_pricing.py`
- [x] T018 [P] [US2] [FR-010] [FR-013] [DR-004] Add failing foreign tenant, mismatched entry/value/context, unsupported direction, atomic attachment, resolution, and non-disclosure stories in `packages/reality-core/tests/test_pricing.py`

### Implementation and acceptance

- [x] T019 [US2] [FR-004] [FR-005] Verify `resolve_price` already keeps effective-time, tier, precedence, lifecycle, direction, currency, and unit behavior authoritative for new work; change it only if T015 exposes a requirement gap in `packages/reality-core/src/reality/services/core.py`
- [x] T020 [US2] [FR-006] [FR-008] [FR-009] Verify optional opaque selected-entry semantics and manual-price behavior; change shared services only if T016–T017 expose a requirement gap in `packages/reality-core/src/reality/services/core.py`
- [x] T021 [US2] [FR-010] [FR-013] [DR-004] Enforce tenant ownership and full resolver-context equality on historical pricing traversal and selected-entry attachment in `packages/reality-core/src/reality/services/core.py`
- [x] T022 [US2] Run the complete User Story 2 PostgreSQL acceptance and record exact results in `specs/025-historical-pricing-integrity/quickstart.md`

**Checkpoint**: Old and new agreements reproduce independently without retroactive repricing.

## Phase 5: User Story 3 — Explain Historical Pricing Safely (P2)

**Goal**: Present agreed Evidence and a fresh comparison as two explicit, tenant-safe
concepts through the shared service and Inspector.

**Independent Test**: Inspect linked and manual historical lines after pricing changes
and prove agreed values, retained identity, current comparison, and unavailable reasons.

### Failing proof

- [x] T023 [P] [US3] [FR-003] [FR-007] Add failing shared-service tests for linked, inactive, expired, manual, insufficient-input, and changed-current-price explanations in `packages/reality-core/tests/test_pricing.py`
- [x] T024 [P] [US3] [FR-007] [FR-012] [FR-013] Add failing Document creation/Inspector API tests for optional selected-entry transport, agreed-first wording, retained entry/list identity, current comparison, and manual-price guidance in `packages/reality-core/tests/test_master_data_api.py`
- [x] T025 [P] [US3] [FR-008] [FR-010] [DR-002] [DR-004] Add failing Inspector tests for opaque-link traversal, matching foreign human values, and non-disclosure in `packages/reality-core/tests/test_master_data_api.py`
- [x] T026 [P] [US3] [FR-012] Add failing application-boundary test proving the Inspector calls the shared explanation service and performs no write in `packages/reality-core/tests/test_master_data_api.py`

### Implementation and acceptance

- [x] T027 [US3] [FR-003] [FR-007] [FR-012] Implement the read-only agreed/current historical-pricing explanation in `packages/reality-core/src/reality/services/core.py`
- [x] T028 [US3] [FR-007] [FR-008] [FR-013] [DR-002] Add optional selected-entry DocumentLine input transport plus retained pricing-entry/list and current-comparison fields to the Document Inspector in `packages/reality-core/src/reality/web/api.py`
- [x] T029 [US3] [FR-010] [DR-004] Preserve not-found behavior and tenant scope across the Inspector explanation traversal in `packages/reality-core/src/reality/web/api.py`
- [x] T030 [US3] Run User Story 3 API/Inspector acceptance and record exact results in `specs/025-historical-pricing-integrity/quickstart.md`

**Checkpoint**: Operators can distinguish historical agreement from current pricing without a second interpretation.

## Final Phase: Cross-Cutting Review and Baseline Closure

- [x] T031 [DR-001] [DR-002] [DR-003] Clarify Evidence/configuration/Reality boundaries and agreed-versus-current Inspector behavior in `docs/features/operational_fields.md`, `docs/WEB_SPEC.md`, and `docs/DATA_MODEL.md`
- [x] T032 [DR-005] Prove no model or migration expansion and record the result in `specs/025-historical-pricing-integrity/quickstart.md`
- [x] T033 Run Ruff, focused PostgreSQL pricing/API tests, and the complete parallel PostgreSQL suite; record exact results in `specs/025-historical-pricing-integrity/quickstart.md`
- [x] T034 Run applicable Web build and contract tests if Inspector presentation files change; otherwise record a reviewed N/A reason in `specs/025-historical-pricing-integrity/quickstart.md`
- [x] T035 Review the final diff against Constitution, `spec.md`, `plan.md`, every FR/DR mapping, shortest links, tenant boundaries, and unrelated concurrent work in `specs/025-historical-pricing-integrity/checklists/requirements.md`
- [x] T036 After product-owner final approval, mark only `004/FR-014` verified in `specs/004-master-data/spec.md` and remove only its row from `docs/SPEC_COVERAGE_MATRIX.md`
- [x] T037 Run final Spec policy, traceability, checklist, and `git diff --check` gates; record exact results in `specs/025-historical-pricing-integrity/quickstart.md`

## Dependencies

```text
T001–T003 specification/design gates
  → T004–T007 shared boundary
    → T008–T014 US1 historical invariance (MVP)
      → T015–T022 US2 new-work effective pricing
        → T023–T030 US3 explanation/Inspector
          → T031–T037 final review and baseline closure
```

- US1 is the MVP and proves the non-rewrite invariant independently.
- US2 depends on the US1 snapshot vocabulary but not on Inspector presentation.
- US3 depends on stable US1/US2 agreed-versus-current semantics.
- Baseline closure cannot precede complete proof and final product-owner approval.

## Parallel Execution Examples

- **Foundation**: T004–T006 may split schema, snapshot, and tenant fixtures.
- **US1**: T008–T011 may split configuration, provenance, downstream, and failure stories.
- **US2**: T015–T018 may split effective-time, manual, identity/direction, and tenant proof.
- **US3**: T023–T026 may split service explanation and API/Inspector contracts.

## Implementation Strategy

1. Prove immutable agreed Evidence as the smallest MVP.
2. Prove later work uses its own existing resolver context.
3. Add one shared read-only explanation only after both meanings are stable.
4. Close `004/FR-014` without schema growth or adapter-equivalence scope.

## Requirement Coverage

| Requirement | Test task(s) | Implementation/documentation task(s) | Status |
|---|---|---|---|
| FR-001–FR-003 | T005, T008–T009, T023 | T012, T027, T031 | Pending |
| FR-004–FR-005 | T010, T015 | T013, T019 | Pending |
| FR-006 | T016, T023–T024 | T020, T027–T028 | Pending |
| FR-007–FR-009 | T017, T023–T025 | T020, T027–T028, T031 | Pending |
| FR-010 | T006, T018, T025 | T021, T029 | Pending |
| FR-011 | T005, T010–T011 | T013 | Pending |
| FR-012 | T007, T024, T026 | T027–T029 | Pending |
| FR-013 | T007–T008, T018, T024 | T012, T021, T028 | Pending |
| DR-001–DR-003 | T007, T010, T024, T026 | T013, T028, T031 | Pending |
| DR-004 | T006, T018, T025 | T021, T029 | Pending |
| DR-005 | T004 | T032, T035 | Pending |
| SC-001–SC-007 | T008–T026, T032–T034 | T031, T035–T037 | Pending |
