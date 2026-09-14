# Logical Data Model: Complete Operational Exception Coverage

This feature adds no persisted business entity. Taxonomy entries are source-controlled
metadata; operational exceptions are disposable derived values.

## ExceptionClassDefinition

| Attribute | Meaning | Validation |
|---|---|---|
| id | Stable visible class identity | Unique; one of five approved IDs |
| label | Operator-facing class name | Non-empty and stable |
| severity | Default priority | Approved severity value |
| derivation | Shared derivator registry key | Maps exactly once |
| record_type | Authoritative record kind | Existing opaque-ID entity |
| authority | Governing requirement | Exact spec reference |
| evidence | Focused executable proof | Non-empty and resolvable |
| causes | Approved nested cause definitions | Optional; outgoing risk has exactly insufficient_reservation |

## ExceptionCauseDefinition

| Attribute | Meaning | Validation |
|---|---|---|
| id | Stable causal classification | Unique across taxonomy |
| label | Operator-facing cause | Non-empty |
| parent_class_id | Owning visible classification | References exactly one ExceptionClassDefinition |
| authority | Governing requirement | Exact spec reference |
| evidence | Focused cause proof | Required even without a separate queue row |

A cause inherits its parent class's default severity, derivation authority, and
authoritative record type. It does not define an independent queue identity or duplicate
those class attributes.

## OperationalException

| Attribute | Meaning | Validation |
|---|---|---|
| id | Derived queue identity | `exc__{class_id}__{record_id}` |
| class_id | Visible class | References one ExceptionClassDefinition |
| cause_ids | Exact current causes | Approved by the class; no duplicate queue row |
| severity/title/impact | Compatible operator summary | Non-empty and deterministic |
| record_type/record_id | Shortest authoritative identity | Opaque, tenant-owned record |
| causal_values | Reproducible quantities, amounts, dates, or error | Class-specific typed values |
| trace | Existing Source/Evidence/Reality links | Tenant-scoped; absence explicit |

## Explanation

An explanation is the current OperationalException plus hydrated authoritative values,
events where available, and optional raw Source payload. It is returned only after the
exception is re-derived for the selected tenant.

## Class Relationships

```text
outgoing_commitment_at_risk
  └─ cause: insufficient_reservation
  └─ Commitment → DocumentLine/Document → SourceRecord (optional)

overdue_incoming_supplier_commitment
  └─ Commitment → receipt Movements

source_interpretation_failure
  └─ ImportJob → SourceRecord

unexplained_movement
  └─ Movement → Commitment or SourceRecord (both absent for current exception)

unmatched_financial_event
  └─ payment control LedgerEntry → SettlementAllocation → invoice LedgerEntry/Document
```

## Derived State and Transitions

- Cause absent → cause appears → exception is derived.
- Owning remediation corrects authority → refresh → exception disappears.
- No exception state transition is stored.
- Unexplained Movement has no retroactive clearing transition in this feature because
  Movement history remains append-only.
- Projection rows may be created, replaced, or deleted without changing authority.

## Invariants

- Exactly five visible classes and one nested cause exist in the initial taxonomy.
- One insufficient Reservation creates one outgoing-risk row, never two rows.
- All record and trace links are opaque and tenant-scoped.
- Missing optional Evidence/Source is explicit, not fabricated.
- Decimal remainders/quantities and UTC instants retain exact semantics.
- Taxonomy metadata grants no runtime authorization.
