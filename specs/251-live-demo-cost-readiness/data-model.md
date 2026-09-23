# Data Model: Live Demo Cost Readiness

No schema change is planned.

## Existing records and roles

### SourceRecord

- Holds each received/authored demo acquisition, invoice and selling-cost payload
  losslessly.
- Immutable and tenant-scoped.
- Is the evidence origin, never a calculated result.

### Movement and retained cost basis records

- `Movement` is the authoritative physical change for an item/location.
- Existing inventory reviews and members bind opaque movement identities, ownership,
  explicit acquisition evidence, method, unit, currency and event cutoff.
- Validation: a positively stocked canonical demo item must have a supported positive
  acquisition basis; zero is valid only when the evidence itself states zero for a
  scope where zero is meaningful, never as a missing-value replacement.

### Contribution review records

- Existing commercial-match, selling-assignment and contribution reviews bind an
  invoice line to received revenue, reviewed consumed acquisition slices and reviewed
  selling categories.
- DB1 and DB2 are derived observations and are not financial authority.

### Cost generation

- Existing inventory/contribution generation records are disposable, tenant-scoped
  observations at an exact admitted event sequence.
- State transitions remain `building` → `sealed` → current/published selection; a newer
  relevant event makes a prior result stale without mutating its historical contents.

### PlaygroundRun initialization progress

- Existing JSON progress retains creation intent, profile manifest and live setup
  marker.
- Add a compact `cost_readiness` member containing version, verified event cutoff,
  inventory/contribution coverage counts and a terminal outcome/diagnostic.
- It is orchestration evidence only and never supplies a financial value.

### Canonical profile manifest

- Declares the immutable bounded list of opaque invoice-line identities included in
  contribution demonstration coverage.
- Positive-stock inventory coverage is derived by census at the admitted cutoff rather
  than copied into a second authority.

### ScheduledJobRun

- Existing tenant-scoped queue record for setup and cost generation work.
- Deterministic request fingerprints make repeated/overlapping requests converge.

## Relationships

`SourceRecord → Movement → CostMovementBasis/CostInventoryMember → Inventory review → generation`

`SourceRecord → DocumentLine → commercial match + consumed inventory member + selling assignment → contribution review → generation`

`PlaygroundRun → setup ScheduledJobRun → verified coverage summary`

## Invariants

- Human item/document numbers never identify a scope.
- Every query includes tenant identity.
- A readiness summary references counts/cutoff, not duplicated monetary values.
- Historical demo companies receive no automatic mutation.
- Replay cannot start a stopped/paused source or duplicate a retained review.
