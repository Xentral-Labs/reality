# Documentation Data Model: Specification Baseline

This describes baseline artifacts, not product tables or fields.

## BaselineCapability

| Field | Meaning | Rule |
|---|---|---|
| `id` | Sequential spec number and slug | Unique under `specs/` |
| `name` | Business-oriented capability | Not a table/page name alone |
| `status` | Draft or Reviewed | Reviewed only after owner gate |
| `primary_contracts` | Durable intent sources | At least one |
| `cross_cutting_contracts` | Governance/architecture links | Link, do not duplicate |
| `requirements` | Requirement records | At least one FR and relevant DRs |

## BaselineRequirement

| Field | Meaning | Rule |
|---|---|---|
| `id` | `FR-NNN` or `DR-NNN` | Unique within spec |
| `statement` | Observable rule | Testable and unambiguous |
| `evidence_status` | Current classification | Exactly one allowed value |
| `scenarios` | Acceptance references | At least one |
| `contract_evidence` | Durable intent link | Required for Verified as-is |
| `implementation_evidence` | Observable implementation | Required for Verified as-is |
| `test_evidence` | Executable proof | Required and green for Verified as-is |
| `decision` | Owner decision link | Required when materially ambiguous |

Allowed evidence statuses:

- `Verified as-is`: all three evidence types agree.
- `Documented gap`: intended/documented behavior lacks delivery or proof.
- `Implemented gap`: observable behavior lacks a clear durable contract.
- `Intended`: explicitly future behavior, not current reality.

## CoverageEntry

| Field | Meaning | Rule |
|---|---|---|
| `source` | Repository path or public capability | Resolves or is explicitly external |
| `source_type` | Contract, catalog, service/tool, adapter/UI, test | Controlled vocabulary |
| `primary_baseline` | Owning spec | Exactly one unless cross-cutting |
| `classification` | Primary evidence or cross-cutting | Exactly one |
| `coverage_notes` | Gap, skip, contradiction, secondary links | Explicit when incomplete |

## OwnerDecision

| Field | Meaning | Rule |
|---|---|---|
| `question` | One material business decision | Changes scope/security/user outcome |
| `options` | Alternatives and implications | Two or three plus custom |
| `answer` | Owner-selected outcome | Required before Reviewed |
| `decided_at` | Review date | ISO date |
| `affected_requirements` | Requirement IDs | At least one |

## Relationships and invariants

```text
BaselineCapability 1 ── * BaselineRequirement
BaselineCapability 1 ── * CoverageEntry
BaselineRequirement * ── 0..1 OwnerDecision
```

Every source has one owner or is cross-cutting. Every baseline has an FR. Verified
requirements have three-source proof. Skipped/red tests are not proof. Reviewed specs
have no unanswered decision. Baseline work changes no product or migration path.
