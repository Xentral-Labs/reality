# Data Model: Web UX Matrix Completion

## Domain model impact

No domain entity, table, column, relationship, index, migration, or stored presentation
state is introduced. Source, Evidence, Reality, tenant, and correction models are unchanged.

## Verification-only concepts

### UXMatrixManifest

| Field | Meaning | Validation |
|---|---|---|
| `version` | Contract version (`ux-matrix-v1`) | Non-empty; reviewed on topology change |
| `destinations` | Complete mapped destinations | Exactly covers actual routes/nested destinations |
| `separate_owners` | Separately specified integrations | Names spec and integration proof; never a silent waiver |

### DestinationCoverage

| Field | Meaning | Validation |
|---|---|---|
| `id` | Stable semantic key | Unique; not database identity |
| `route` | Actual/containing route | Resolves in client topology |
| `surface` | Canonical matrix surface | Matches one authoritative row |
| `job` | Operator outcome | Non-empty and matrix-consistent |
| `hierarchy` | Ordered required sections | At least one; order asserted where material |
| `primary_action` | Main action or absence reason | Exactly one decision |
| `states` | Applicable UI states | Each has evidence or explicit non-applicability |
| `explanation` | Inspector/trace behavior | Required for important answers |
| `responsive_cases` | Desktop/mobile review cases | Both for affected destinations |
| `owner` | Owning specification | Exactly one |

### VisualReviewCase

References a destination, deterministic state, desktop/mobile viewport, expected job and
first-viewport priority, plus the eventual review result/evidence.

## Read-model impact

Existing reads remain authoritative. Additive response projection is allowed only when the
matrix proves current services calculate but do not expose needed data, such as Journal
rows/control totals, tenant-resolved labels for Reservation/Movement links, or authoritative
location/overdue filters. Values are calculated and filtered before pagination; opaque IDs
remain available for trace.

## State transitions

The manifest has no runtime transition. UI state may move among loading, populated, empty,
error, preview/confirmation, success, and cancelled. Business state changes only through
the owning confirmed service operation.
