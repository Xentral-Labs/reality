# Logical Data Model: Complete Tenant Isolation Coverage

This feature adds no persisted business entity. These objects are source-controlled
evidence metadata and disposable test structures.

## PublicBusinessFamily

| Attribute | Meaning | Validation |
|---|---|---|
| key | Stable family identity | Unique and non-empty |
| description | Business boundary being proved | Specific and non-empty |
| classification | Required isolation behavior | One approved classification |
| operations | Public operations in the family | Every discovered operation mapped exactly once unless explicitly shared |
| evidence | Named executable proof | Required for every tenant-scoped family |
| authority | Governing requirement/contract | Required for every entry |
| reason | Grouping or exemption rationale | Required for exemptions/boundaries |

## IsolationClassification

| Value | Required behavior |
|---|---|
| `record_read` | Foreign ID is indistinguishable from unknown ID |
| `collection` | Foreign records and overlapping values are absent |
| `aggregate` | Foreign values contribute zero to totals/projections |
| `mutation_relationship` | Foreign input fails atomically with zero side effects |
| `boundary` | Tenant context reaches a classified shared boundary |
| `global_admin` | Global/administrative scope has named authority |

## IsolationEvidence

| Attribute | Meaning | Validation |
|---|---|---|
| id | Stable evidence/test identity | Unique and resolvable |
| family | Family being proved | References one catalog family |
| local tenant | Execution authority | Distinct from foreign tenant |
| foreign tenant | Owner of adversarial records | Distinct opaque ID |
| assertion kind | Read, exclusion, aggregate, atomic write, or propagation | Matches classification |
| outcome | Observed result | Satisfies classification contract |

## TwoTenantGraph

| Component | Purpose | Validation |
|---|---|---|
| local/foreign graph | Controlled authorities and records | Both populated |
| shared human values | Prove display values are not identity | Overlap where applicable |
| asymmetric measures | Detect contamination | Values cannot cancel/coincide |
| opaque IDs | Authoritative relationships | Unique across records |
| lineage chains | Prove Source/Evidence/Reality isolation | Each chain remains within one tenant |

## ApprovedExemption

| Attribute | Meaning | Validation |
|---|---|---|
| operation/family | Global or administrative boundary | Still cataloged |
| authority | Contract permitting scope | Exact reference |
| reason | Why business tenant scoping does not apply | Narrow and reviewable |
| evidence | Approved boundary proof | Required when externally reachable |

## Relationships and State

- Every discovered operation maps to one family or reviewed exemption.
- Every tenant-scoped family maps to executable evidence.
- The TwoTenantGraph is disposable and never production state.
- Registry/callable drift invalidates the catalog until remapped.
- Passing evidence permits baseline review but does not itself mutate baseline state.
