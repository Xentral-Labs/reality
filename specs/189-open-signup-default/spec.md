# Feature Specification: Open Signup by Default

**Created**: 2026-09-14
**Status**: Implemented and verified locally; not deployed
**Language**: English
**Input**: Make access open by default until the operator explicitly sets a restriction.

## Context and Intent

### Problem

A prospect follows Try Reality, registers and verifies their email, then encounters
a personal-review waiting page before experiencing the product. The owner requests
immediate access by default, with optional operator-controlled restrictions.

### Scope

- Unlimited automatic admission when no restriction is configured.
- Explicit manual review or a finite automatic-admission capacity.
- Consistent signup, public package and administrator descriptions and installation defaults.

### Non-Goals

- Removing email verification, authentication, tenant isolation or action confirmation.
- Automatically approving existing pending or rejected accounts.
- Automatically creating companies, bypassing company setup, changing prices or demo fixtures.
- Changing live deployment variables or overriding deliberately restricted deployment profiles.

### Existing Contracts

- [Web contract](../../docs/WEB_SPEC.md)
- [Company setup](../../docs/features/company-setup-demo.md)
- [Railway profile](../../docs/RAILWAY_DEMO.md)

## User Scenarios & Testing

### User Story 1 - Start after verification (Priority: P1)

A prospect can enter company setup immediately after verifying their email when
the operator has not configured an admission restriction.

**Independent Test**: Register and verify multiple accounts without a configured limit.

**Acceptance Scenarios**:

1. **Given** no admission restriction, **When** an account verifies its email,
   **Then** the account becomes active and its application is automatically approved.
2. **Given** an unverified account, **When** business access is attempted,
   **Then** existing verification and tenant membership guards still apply.
3. **Given** a previously pending or rejected account, **When** configuration changes,
   **Then** the account is not retrospectively approved.

### User Story 2 - Restrict admission explicitly (Priority: P1)

The operator can require personal approval or impose a finite capacity without code changes.

**Independent Test**: Exercise zero, positive, missing, blank, malformed and negative settings.

**Acceptance Scenarios**:

1. **Given** an explicit zero limit, **When** an account verifies,
   **Then** it waits for personal approval.
2. **Given** a finite positive limit, **When** capacity is reached,
   **Then** subsequent verified accounts wait; concurrent admissions cannot exceed capacity.
3. **Given** prior unlimited admissions, **When** a finite limit is configured,
   **Then** those admissions count toward the existing cumulative capacity.
4. **Given** a malformed or negative configured limit, **When** admission is evaluated,
   **Then** manual approval is required; a blank value means no restriction.

### User Story 3 - Understand access conditions (Priority: P2)

Prospects and operators receive descriptions consistent with open, finite and manual modes.

**Independent Test**: Public package presentation and administrator capacity for all three modes.

**Acceptance Scenarios**:

1. **Given** default open admission, **When** reading signup and packages,
   **Then** no mandatory personal review or finite number of places is advertised.
2. **Given** any admission mode, **When** an administrator inspects capacity,
   **Then** unlimited, manual and finite capacity are distinguishable.
3. **Given** a fresh generic installation, **When** default configuration is used,
   **Then** no finite or manual restriction is silently injected.

### Edge Cases

Verification replay, invitation acceptance, disabled public signup, exhausted capacity,
blank configuration from Compose, malformed values and existing deployment overrides.

## Requirements

### Functional Requirements

- **FR-001**: Missing or blank admission configuration MUST allow unlimited automatic admission after email verification.
- **FR-002**: Zero MUST require manual approval; positive limits MUST retain atomic cumulative capacity; negative or malformed settings MUST require manual approval.
- **FR-003**: Unlimited admissions MUST be counted exactly once through the existing transactional verification flow, so later finite limits retain their meaning.
- **FR-004**: Signup and administrator/public package copy MUST accurately represent unlimited, manual and finite modes. Generic installation defaults MUST be open; explicitly restricted profiles MUST remain explicit.
- **FR-005**: Existing pending/rejected accounts, invitations, disabled signup, verification, company eligibility and tenant boundaries MUST retain their behavior.

### Domain and Traceability Requirements

- **DR-001**: Admission remains platform account metadata; no business record, source payload, relationship or schema is added. One shared admission policy supplies account processing and administrator reporting.

## Success Criteria

- **SC-001**: Every eligible new verified account enters setup without personal review in the default mode.
- **SC-002**: All three admission modes and their transitions have executable proof; no bounded admission overshoots capacity.

## Assumptions and Dependencies

- The owner's request approves the product-scope reversal; email verification remains required as established in this conversation.
- Empty configuration is equivalent to unset to support environment interpolation.
- Existing explicit deployment overrides remain effective after upgrade; changing them is a separate rollout action.
- No new infrastructure, schema, billing entitlement or demo-only access mode is introduced.

## Requirement Traceability

| Requirement | Scenarios | Planned evidence |
|---|---|---|
| FR-001 | US1.1 | Signup/verification HTTP story |
| FR-002 | US2.1–4 | Policy matrix and finite-capacity tests |
| FR-003 | US2.3 | Unlimited-to-finite transition and replay |
| FR-004 | US3.1–3 | Site tests, web build, deployment assertions |
| FR-005 | US1.2–3, edge cases | Access, membership and company suites |
| DR-001 | All | Shared policy tests, schema/diff review |
