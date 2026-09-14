# Feature Specification: Silent Source Detection

**Feature Branch**: `072-silent-source`
**Created**: 2026-09-04
**Status**: Draft
**Language**: English
**Input**: "A connector that simply stops delivering is invisible. Only failed imports are reported, never silence."

## Context and Intent

### Problem

A connected system that stops delivering is invisible to Reality.
`source_interpretation_failure` reports a record that arrived and could not be
interpreted; nothing reports a record that never arrived. An integration can break at the
other end — an expired credential, a disabled webhook, a paused job, a renamed endpoint —
and every screen keeps showing the same figures, quietly older by the day. There is no
error to find, because nothing failed. Nothing happened at all.

For a trading business this is the most dangerous of the blind spots, because it degrades
everything else at once. Orders stop arriving, so the promise queue looks calm. Stock
changes stop arriving, so inventory looks stable. Payments stop arriving, so receivables
look healthy. Every derived condition Reality reports stays technically correct and
practically worthless, and the queue that exists to say what needs attention says nothing.

The difficulty is knowing what silence means. A source that delivers every few minutes and
one that delivers once a month are both perfectly healthy, so silence can only be judged
against the behaviour of that particular source. Asking an operator to configure an
expected interval would work, and would introduce the first tenant-tunable parameter in
the product — the same answer that was rejected for grace periods in Spec 068 and for
thresholds since. Reality derives; it does not ask to be configured.

### Scope

- Report a declared, active source capability that has stopped delivering, judged against
  the delivery rhythm that capability itself has shown.
- Derive the expectation from observed history alone, with no tenant configuration.
- Say nothing where there is not enough history to know a rhythm.
- Give the class the same identity, severity, impact, causal values, trace, explanation,
  ordering, tenant isolation and operator guidance as every existing class.
- Extend the closed catalog and its drift gate.

### Non-Goals

- A capability that has never delivered anything. That is "never started", not "stopped",
  and it would light up every tenant immediately after onboarding. It needs its own
  condition and its own decision.
- Watching source systems, streams or record types that nobody declared. A source no one
  registered promised nothing, so its silence is not a finding.
- Any expectation the operator types in: intervals, schedules, calendars, business hours,
  maintenance windows, or per-capability thresholds.
- Monitoring the connector itself — credentials, endpoints, health checks, retries. This
  reports the observable consequence, not the cause.
- Alerting, notification, escalation, or paging.
- Automatic remediation: no re-authentication, no job restart, no backfill.
- Schema changes or migrations. Capabilities and record timestamps already exist.

### Existing Contracts

- [`docs/features/operational_exceptions.md`](../../docs/features/operational_exceptions.md)
- [`specs/005-source-ingestion/spec.md`](../005-source-ingestion/spec.md)
- [`specs/020-exception-class-coverage/spec.md`](../020-exception-class-coverage/spec.md)
- [`specs/068-promise-coverage-exceptions/spec.md`](../068-promise-coverage-exceptions/spec.md)
- [`specs/071-catalog-operator-guidance/spec.md`](../071-catalog-operator-guidance/spec.md)
- [`docs/DATA_MODEL.md`](../../docs/DATA_MODEL.md)
- [Constitution](../../.specify/memory/constitution.md)

## Clarifications

### Session 2026-09-04

- Q: Where does the expectation come from? → A: From the capability's own observed history.
  A configured interval was rejected: it would be the product's first tenant-tunable
  parameter, and it would be less accurate than the behaviour it replaces, because a source
  that really delivers every four hours is late long before a daily setting would say so.
- Q: Which record carries the exception? → A: The declared source capability. A stream
  belongs to one external object and falls silent whenever that object stops changing, so
  silence there is normal rather than notable.
- Q: What counts as too long? → A: Longer than twice the longest pause that capability has
  shown recently, and never less than a day. Using the longest observed pause rather than
  an average is what makes a source with nights and weekends behave: its normal weekend
  pause is part of its rhythm, not a finding.
- Q: What about a capability with almost no history? → A: It says nothing. A rhythm cannot
  be claimed from two or three arrivals, and guessing would be worse than silence.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Notice That a Source Went Quiet (Priority: P1)

An operator sees that a connected system has stopped delivering, with how long it has been
silent and how long it normally pauses, without having configured anything and without
waiting for someone to notice that the numbers look stale.

**Why this priority**: It is the condition the feature exists for.

**Independent Test**: Give a capability a regular delivery history, advance the evaluation
instant past twice its longest pause, and verify the entry appears with the silence and the
learned pause; deliver again and verify it clears.

**Acceptance Scenarios**:

1. **Given** an active capability that has been delivering regularly, **When** the time
   since its last record exceeds twice its longest recent pause and at least a day,
   **Then** one entry appears for that capability, stating how long it has been silent and
   what pause it normally shows.
2. **Given** the same capability, **When** a new record arrives, **Then** the entry
   disappears without any manual step.
3. **Given** a capability whose current silence is within its normal rhythm, **When** the
   queue is listed, **Then** no entry appears, however long that rhythm is.
4. **Given** a capability that pauses every weekend, **When** it is read on a Monday,
   **Then** no entry appears, because the weekend pause is part of the rhythm it has shown.
5. **Given** a capability that is not active, **When** the queue is listed, **Then** no
   entry appears, because nothing is expected of it.

### User Story 2 - Stay Quiet When Nothing Can Be Known (Priority: P2)

A capability that has just been connected, or that has delivered only a handful of times,
produces no entry rather than a guess.

**Why this priority**: It decides whether the class is trusted. A condition that fires on
fresh tenants is switched off mentally within a week.

**Independent Test**: Create capabilities with zero, one and a few records and verify none
of them appears, then add records until the history is sufficient and verify the class
begins to apply.

**Acceptance Scenarios**:

1. **Given** a capability with no records at all, **When** the queue is listed, **Then** no
   entry appears, whatever the age of the capability.
2. **Given** a capability with fewer records than the minimum history, **When** the queue is
   listed, **Then** no entry appears, however long the silence.
3. **Given** a capability that reaches the minimum history, **When** it then falls silent
   beyond its rhythm, **Then** the entry appears.

### Edge Cases

- All records of a capability arrived in the same second, so the observed pauses are zero.
- A single very long pause dominates the history, so the learned rhythm is much longer than
  the usual one.
- Records arrive out of order, or a record's received time is later than the evaluation
  instant.
- A capability is declared for a source type that has always been delivered under a
  different system code, so it has no records although data is arriving.
- Two tenants declare the same connector and only one of them goes quiet.
- The identity of an entry is explained after the source has resumed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST report one `silent_source` entry for every active declared
  source capability whose silence exceeds its expected pause.
- **FR-002**: Silence MUST be measured from the most recent record received for that
  capability to the evaluation instant.
- **FR-003**: The expected pause MUST be derived from the capability's own recent history
  as the longest interval observed between consecutive records, and MUST NOT come from any
  configured value.
- **FR-004**: An entry MUST appear only when the silence exceeds both twice the expected
  pause and an absolute minimum, so that a source with a very short rhythm is not reported
  for a brief interruption.
- **FR-005**: The system MUST NOT report a capability that has fewer records than the
  minimum history, that has never delivered, or that is not active.
- **FR-006**: The entry MUST state how long the source has been silent, the pause it
  normally shows, and when it last delivered.
- **FR-007**: The entry MUST carry a stable derived identity, severity, title, impact,
  authoritative record type and identity, causal values, and the shortest available trace,
  in the same shape as every existing class.
- **FR-008**: The entry MUST disappear as soon as a new record is received, without
  acknowledgement or any other manual step.
- **FR-009**: The explanation of an entry MUST re-derive the current condition, and an
  identity that is malformed, unknown, resumed, or owned by another tenant MUST produce the
  same not-found response the queue already returns.
- **FR-010**: The queue MUST remain deterministically ordered for identical data, with the
  longest-silent capability first within the class.
- **FR-011**: The class MUST be declared in the closed product catalog with an authority
  reference, named executable evidence, and the operator guidance every class carries, and
  any drift MUST fail the existing coverage gate.
- **FR-012**: Every surface that consumes the queue MUST receive the class through the
  existing shared list and explanation contract, without surface-specific derivation.

### Domain and Traceability Requirements

- **DR-001**: The class MUST be derived at read time from existing tenant-owned
  SourceCapability, SourceSystem and SourceRecord records. It adds no schema, no persisted
  state, and no status field on any of them.
- **DR-002**: The expectation MUST be a function of observed history only. No tenant may
  hold a different threshold from another, and no value may be stored to make one possible.
- **DR-003**: The constants that turn history into a judgement — the history window, the
  minimum history, the multiple of the observed pause and the absolute minimum silence —
  are product decisions, identical for every tenant, and MUST be recorded in the
  specification rather than tuned in the field.
- **DR-004**: The trace MUST reach the capability, its source system and the most recent
  record by opaque identity, and MUST NOT restate their business fields.
- **DR-005**: Every read, derivation and explanation MUST be tenant-scoped. A capability
  MUST only ever be judged against records of its own tenant.
- **DR-006**: The class introduces no new cause.

### Key Entities *(when data is involved)*

- **SourceCapability**: The declared, active intent to receive one source type from one
  system. It is what promises delivery, and therefore what can fall silent.
- **SourceRecord**: The immutable arrivals whose receipt times are the only evidence of a
  rhythm.
- **Observed pause**: The longest interval between consecutive arrivals in the recent
  history; not a stored value and not a setting.

## Success Criteria *(mandatory)*

- **SC-001**: An operator learns that a connected system stopped delivering without having
  configured an expected interval anywhere.
- **SC-002**: A source with a regular weekly or nightly pause produces no entry while it
  keeps that rhythm.
- **SC-003**: A freshly connected capability produces no entry until it has shown a rhythm.
- **SC-004**: A resumed source leaves the queue on the next read with no manual action, and
  its former identity is no longer explainable.
- **SC-005**: Two identical reads of an unchanged tenant return an identical, identically
  ordered queue.
- **SC-006**: Every FR and DR has an acceptance scenario and named executable proof.

## Assumptions and Dependencies

- The four constants are: a history window of the twenty most recent records, a minimum
  history of five records, a multiple of two applied to the longest observed pause, and an
  absolute minimum silence of twenty-four hours. They are chosen to fail late rather than
  early, because a condition that cries wolf on a healthy source is worse than one that
  notices a day later.
- Ingestion does not validate that arriving records belong to a declared capability, so a
  capability with no records may exist beside records with no capability. Only the declared
  side is watched, and the specification says so rather than treating the mismatch as an
  error.
- Receipt times are recorded when Reality accepts a record, so they measure arrival at
  Reality rather than creation in the source system. That is the right measure for this
  condition: it reports that delivery stopped, not that the other system stopped working.
- A source whose rhythm genuinely changes — a daily feed that becomes monthly — will report
  once and then settle, because the new pause enters its history. This is accepted rather
  than smoothed away.

## Requirement Traceability

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1 scenario 1 | silent source derivation test |
| FR-002 | US1 scenario 1 | silence measurement test |
| FR-003 | US1 scenarios 3, 4 | learned-rhythm test |
| FR-004 | US1 scenario 3; Edge cases | short-rhythm floor test |
| FR-005 | US1 scenario 5; US2 scenarios 1, 2 | insufficient-history and inactive test |
| FR-006 | US1 scenario 1 | causal values and impact test |
| FR-007 | US1 scenario 1 | entry shape and trace test |
| FR-008 | US1 scenario 2 | clearing through delivery test |
| FR-009 | Edge cases | explanation not-found parity test |
| FR-010 | US1 scenario 1 | deterministic ordering test |
| FR-011 | US2 scenario 3 | catalog coverage and guidance gate test |
| FR-012 | US1 scenario 1 | shared list and explanation contract test |
| DR-001 | US1 scenario 2 | read-time derivation and no-persistence test |
| DR-002 | US1 scenarios 3, 4 | history-only expectation test |
| DR-003 | US2 scenario 2 | constants recorded and applied test |
| DR-004 | US1 scenario 1 | opaque trace test |
| DR-005 | Edge cases | tenant isolation test |
| DR-006 | US1 scenario 1 | existing cause-vocabulary drift gate, guarding that no cause was added |
