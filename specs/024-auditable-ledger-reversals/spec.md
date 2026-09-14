# Feature Specification: Auditable Ledger Reversals

**Feature Branch**: `024-auditable-ledger-reversals`
**Created**: 2026-09-01
**Status**: Approved
**Language**: English
**Input**: "Close `012/FR-008` with a general, append-only, auditable posting-group reversal workflow."

## Context and Intent

### Problem

Finance operators can post balanced invoices, payments, credits, and manual groups, but
cannot correct an arbitrary erroneous posting group. LedgerEntry is append-only, so
update or deletion is forbidden. Operators need one safe reversal that neutralizes the
complete group, preserves evidence, reconciles settlement, and remains explainable.

### Scope

- Preview and explicitly confirm reversal of one tenant-owned posting group.
- Preserve every original entry and append one exact balanced inverse group.
- Record a direct audit relation with reason, time, actor context, and retry identity.
- Reconcile balances, open items, payments, settlements, registers, exceptions,
  projections, events, and explanations.
- Retain allocations touching a reversed group as history while excluding their
  operational settlement effect.
- Expose the same behavior through shared operational interfaces.

### Non-Goals

- Editing or deleting LedgerEntries or SettlementAllocations.
- Partial group reversal, reversing a reversal, or replacing a group in the same action.
- Period closing, statutory cancellation, tax correction, FX revaluation, or managed
  chart-of-accounts behavior.
- Changing Documents, SourceRecords, fulfilment, or physical inventory.

### Existing Contracts

- [`specs/012-ledger-finance/spec.md`](../012-ledger-finance/spec.md)
- [`docs/features/ledger.md`](../../docs/features/ledger.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`docs/CLI_SPEC.md`](../../docs/CLI_SPEC.md)
- [`docs/WEB_SPEC.md`](../../docs/WEB_SPEC.md)
- [Constitution](../../.specify/memory/constitution.md)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reverse an Erroneous Posting Group (Priority: P1)

As a finance operator, I can reverse one complete erroneous posting group without
rewriting financial history.

**Why this priority**: Exact append-only reversal is the missing domain capability.

**Independent Test**: Reverse every supported group shape and prove the original is
unchanged, one exact inverse group balances, and net account/party effects become zero.

**Acceptance Scenarios**:

1. **Given** a balanced group, **When** reversal is confirmed with a reason, **Then**
   each original debit has an equal reversing credit and vice versa in one new group.
2. **Given** original Evidence provenance, **When** reversed, **Then** it remains unchanged
   and the reversal reaches it through the direct correction relation.
3. **Given** a completed reversal, **When** the identical request is retried, **Then** the
   existing result returns without another effect.
4. **Given** a reversed group, reversal group, partial group, or changed retry, **When**
   requested, **Then** it fails without mutation.
5. **Given** a foreign or missing group, **When** requested, **Then** it behaves as not
   found and discloses no foreign data.

### User Story 2 - Reconcile Settlement and Financial Views (Priority: P1)

As a finance operator, I see the same corrected truth everywhere even when the reversed
group participated in settlement.

**Why this priority**: Reversal is unsafe if finance views disagree.

**Independent Test**: Allocate payment to invoices, reverse either side, and compare all
derived views while proving allocation history remains immutable.

**Acceptance Scenarios**:

1. **Given** an allocated payment group, **When** reversed, **Then** allocations remain
   historical but cease settling invoices, restoring invoice open amounts exactly once.
2. **Given** a settled invoice group, **When** reversed, **Then** linked allocations become
   operationally inactive and unaffected payment amounts become unallocated.
3. **Given** any eligible group, **When** reversed, **Then** account, party, running,
   open-item, payment, control-account, journal, and posting-group views agree.
4. **Given** a ledger reversal, **When** fulfilment and inventory are read, **Then** neither
   changes.
5. **Given** stale projections or exceptions, **When** refreshed, **Then** they agree with
   the corrected ledger and active allocations.

### User Story 3 - Preview, Confirm, and Explain (Priority: P2)

As an authorized operator or agent, I can inspect the exact effect before confirmation
and later explain the chain from either group.

**Why this priority**: Financial mutation requires deliberate confirmation and evidence.

**Independent Test**: Preview and confirm through every boundary, abort and retry once,
then inspect both group roles and reproduce identical results.

**Acceptance Scenarios**:

1. **Given** an eligible group, **When** previewed, **Then** exact inverse entries,
   affected allocations, resulting values, revision, and request identity appear without
   mutation.
2. **Given** a preview, **When** aborted, **Then** no relation, entry, or event is added.
3. **Given** an unchanged preview, **When** confirmed, **Then** one atomic reversal occurs
   and all interfaces report the same result.
4. **Given** changed state, **When** an old preview is confirmed, **Then** it fails with
   safe refresh guidance.
5. **Given** either group, **When** inspected, **Then** the complete chain, reason,
   actor/time, Evidence, allocations, net effect, and event are available.
6. **Given** an unconfirmed agent request, **When** submitted, **Then** only a proposal is
   created and no ledger effect occurs.

### Edge Cases

- An entry identifier is supplied instead of the complete posting-group identity.
- The original group is empty, unbalanced, mixed-currency, or party-inconsistent.
- Several allocations connect one reversed group to several unaffected groups.
- Two requests concurrently attempt the first reversal.
- Event persistence fails after inverse entries are prepared.
- Actor context changes while the business request remains identical.
- Reversal time differs from the original effective time.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Confirmed reversal MUST preserve all originals and append exactly one new
  reversing group; entry update and deletion MUST remain unavailable.
- **FR-002**: The reversing group MUST contain exactly one inverse for every original,
  preserving account, party, amount, and currency while swapping debit and credit.
- **FR-003**: Reversal MUST cover the complete group and reject partial, empty,
  unbalanced, mixed-currency, or internally inconsistent groups.
- **FR-004**: Each original group MUST have at most one relation to one reversing group,
  with required reason, reversal time, actor context, and canonical request identity.
- **FR-005**: Original Document/SourceRecord provenance MUST remain unchanged.
  LedgerReversal MUST be the direct durable Evidence of the correction decision, and
  inverse entries MUST reach original business Evidence through that relation rather
  than duplicate or reinterpret the original claim.
- **FR-006**: Entries, relation, derived-state transition, and one event MUST be atomic.
- **FR-007**: Identical retry MUST return the first result; divergent or concurrent
  requests MUST produce one winner and safe conflict.
- **FR-008**: A reversing group MUST NOT be reversible, and a group in either reversal
  role MUST be rejected except for identical original-request retry.
- **FR-009**: Allocations touching a reversed original group MUST remain immutable but
  cease contributing to allocation, open amount, payment, exception, and projection state.
- **FR-010**: Every finance view MUST derive the same net effect and expose group roles.
- **FR-011**: Reversal MUST NOT alter Evidence, Source, physical, promise, or fulfilment state.
- **FR-012**: Tenant-safe mutation-free snapshot/preview MUST return inverse entries,
  affected allocations, resulting values, current revision, and request identity.
- **FR-013**: Execute MUST require that revision and identity, reject stale state, and
  provide safe refresh guidance without foreign disclosure.
- **FR-014**: Web/CLI MUST explicitly confirm; Chat/MCP MUST use proposal and approval.
- **FR-015**: Journal and Inspector MUST explain the complete chain from either group.
- **FR-016**: Exactly one `ledger.reversed` event MUST be created after reversal rows are
  persisted but within the same transaction before commit, and MUST invalidate all
  affected financial consumers.
- **FR-017**: Every read/write/reference MUST enforce tenant scope and non-disclosure.

### Domain and Traceability Requirements

- **DR-001**: LedgerEntry remains append-only financial Reality; LedgerReversal is direct
  correction Evidence that records the decision without replacing entries as truth.
- **DR-002**: Reversal → original/reversing groups is the shortest relationship and MUST
  NOT duplicate Document, SourceRecord, or settlement provenance.
- **DR-003**: SettlementAllocation remains immutable history; operational activity derives
  from both linked groups' reversal state.
- **DR-004**: Relationships use opaque identity; human document/payment/account labels
  never establish identity.
- **DR-005**: All interfaces MUST share one tenant-scoped behavior and confirmation policy.

### Key Entities

- **LedgerEntry**: Existing append-only financial entry in one balanced posting group.
- **Ledger Reversal**: Direct durable correction Evidence and relation between the
  original group and exact inverse group, carrying intent and retry identity.
- **SettlementAllocation**: Immutable historical matching link whose operational activity
  derives from the reversal state of both linked groups.
- **Document / SourceRecord**: Original Evidence and Source reached through the original.

## Success Criteria *(mandatory)*

- **SC-001**: Every supported original plus reversal nets to zero by tenant, account,
  party, and currency while both groups remain visible.
- **SC-002**: 100% of affected allocations remain stored and 100% stop operationally
  settling when either linked group is reversed.
- **SC-003**: Open and unallocated amounts reconcile exactly before/after reversal in all views.
- **SC-004**: Retries create zero duplicates; concurrent first attempts complete once.
- **SC-005**: Invalid, stale, or foreign requests leave all record counts unchanged.
- **SC-006**: Operators can preview, confirm, and find the full explanation in under two
  minutes on desktop or mobile.
- **SC-007**: API, CLI, Web, Chat/tool, and MCP produce identical semantics.
- **SC-008**: Every FR/DR has an acceptance scenario, task, and executable proof.

## Assumptions and Dependencies

- Complete posting group is the unit of balance and reversal; partial correction is excluded.
- Inverse entries use reversal time; original time remains visible in explanation.
- Intended corrected transactions use existing normal posting afterward.
- Allocation history becomes inactive by derivation; manual unmatch is not introduced.
- Existing authorization and confirmation policy applies without a new finance role.

## Open Questions

No unresolved questions remain. The smallest coherent default is complete reversal,
derived deactivation of affected allocations, and separate normal corrected posting.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001–FR-005 | US1 scenarios 1–4 | Exact inverse, relation, provenance, invalid-group stories |
| FR-006–FR-008 | US1 scenarios 3–4; edge cases | Atomicity, retry, concurrency, role stories |
| FR-009–FR-011 | US2 scenarios 1–5 | Allocation, finance-view, projection, exception, independence stories |
| FR-012–FR-014 | US3 scenarios 1–6 | Preview, stale state, confirmation, adapter/proposal stories |
| FR-015–FR-016 | US3 scenarios 3 and 5 | Inspector/journal and event/catalog stories |
| FR-017 | US1 scenario 5; US3 scenario 4 | Two-tenant non-disclosure stories |
| DR-001–DR-005 | All stories | Constitution, link, history, identity, shared-boundary review |
