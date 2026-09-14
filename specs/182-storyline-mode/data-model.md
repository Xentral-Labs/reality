# Data Model: Storyline Mode

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | Migration: `0058_storyline`

Every addition below is justified by a read that filters or joins on it (Constitution III).
Nothing here stores a derivation as authority: the delta, raised and cleared findings and the
graph excerpt are computed at read time.

## Changed tables

### `fact`

| Column | Type | Why |
| --- | --- | --- |
| `recorded_at` | `timestamptz NOT NULL DEFAULT now()` | The delta read selects Facts recorded after a marker; `observed_at` is business time and can be backdated. Backfilled from `observed_at`. Index `(tenant_id, recorded_at)`. |

`observe_fact` sets `recorded_at = now()` explicitly so tests do not depend on the server
default. No other Fact column changes; `action_id` stays out (the delta does not need it).

### `playground_run`

| Column | Type | Why |
| --- | --- | --- |
| `storyline_key` | `varchar(80) NULL` | The library lists runs per storyline; resume finds the run; the recorder decides per tenant whether to record. |
| `storyline_version` | `integer NULL` | FR-020: a run keeps the version it started with. Check: both null or both set, `storyline_version > 0`. |
| `storyline_state` | `jsonb NOT NULL DEFAULT '{}'` | Chosen branches only (`{"branches": {"<chapter>": "<branch>"}}`); the current chapter is derived from the steps (plan §2). Check: object, `octet_length ≤ 8192`. |

Partial unique index `uq_playground_run_active_storyline` on `(owner_user_id, storyline_key)`
where `status = 'active'`: one active run per storyline per person, so "open Storyline"
resumes instead of creating.

### `playground_step`

| Column | Type | Why |
| --- | --- | --- |
| `proposal_id` | becomes `NULL`-able | Read chapters are steps without a proposal. Check: `proposal_id IS NOT NULL OR lesson_step_key IS NOT NULL`. The unique constraint on `proposal_id` already ignores nulls. A unique `(tenant_id, id)` is added so the trace can reference a step with a composite FK. |
| `marker_sequence` | `bigint NULL` | FR-005: the delta filters events after this. Set before the chapter's first mutating call. |
| `marker_at` | `timestamptz NULL` | FR-005: the delta filters Facts after this. Captured in the same transaction as `marker_sequence`. |

`before_observation["exceptions"]` (existing JSONB) holds the sorted list of exception
identities at marker time; it is a comparison snapshot, bounded by the existing 64 KiB check.

## New tables

### `storyline_trace_entry`

| Column | Type | Note |
| --- | --- | --- |
| `id` | `varchar PK` | `uid("trc")` |
| `tenant_id` | `varchar FK tenant.id, indexed` | tenant scope |
| `run_id` | `varchar` | composite FK `(tenant_id, run_id) → playground_run(tenant_id, id)` |
| `step_id` | `varchar NULL` | composite FK `(tenant_id, step_id) → playground_step(tenant_id, id)`; null in free play |
| `ordinal` | `bigint` | per-run order; unique `(run_id, ordinal)` |
| `kind` | `varchar(16)` | `view`, `read`, `propose`, `confirm`, `reject`, `error` |
| `name` | `varchar(120)` | tool name or `view:<key>` or route template |
| `access` | `varchar(8)` | `read`, `propose`, `confirm` |
| `actor` | `varchar(16)` | `person`, `copilot`, `mcp`, `storyline` |
| `proposal_id` | `varchar NULL` | for propose, confirm, reject |
| `marker_sequence` | `bigint NULL` | free-play confirms: marker for their delta |
| `marker_at` | `timestamptz NULL` | as above |
| `before_exceptions` | `jsonb NULL` | free-play confirms: the finding ids open before the call, bounded like `input`, so raised and cleared can be computed for a marker without a step |
| `input` | `jsonb NULL` | bounded: `octet_length ≤ 16384`, truncated with `{"truncated": true}` |
| `result` | `jsonb NULL` | bounded as above; error text for `kind = error` |
| `duration_ms` | `integer NULL` | |
| `recorded_at` | `timestamptz NOT NULL DEFAULT now()` | |

Indexes: `(tenant_id, run_id, ordinal)`, `(tenant_id, step_id)`. Bound: the service deletes
the oldest entries beyond 2 000 per run inside the same transaction that inserts. The table
is never joined by business reads and is dropped on downgrade.

### `storyline_package`

| Column | Type | Note |
| --- | --- | --- |
| `id` | `varchar PK` | `uid("stp")` |
| `owner_user_id` | `varchar FK app_user.id, indexed` | account scope (FR-018) |
| `key` | `varchar(80)` | from the package |
| `version` | `integer` | from the package; `> 0` |
| `title` | `varchar(200)` | English title, for lists |
| `author` | `varchar(200) NULL` | free text from the package |
| `checksum` | `varchar(64)` | sha256 of the stored document |
| `document` | `jsonb NOT NULL` | the package as received (YAML parsed to JSON); `octet_length ≤ 200000` |
| `validation` | `jsonb NOT NULL` | `{"catalog_version": …, "warnings": [...]}` at import time |
| `imported_at` | `timestamptz NOT NULL DEFAULT now()` | |
| `replaced_at` | `timestamptz NULL` | set when a same key and version import replaces this row |

Unique `(owner_user_id, key, version)` where `replaced_at IS NULL`. Built-in packages are not
rows; the library read merges them from the repository files.

## Entities that are not tables

- **Storyline package** (built-in): a file in `packages/reality-core/storylines/`, validated
  by `reality.storyline.package` at test time and at load time.
- **Chapter**: an element of the package; at run time a `playground_step` with
  `lesson_step_key = <chapter key>`.
- **Delta**: the read-time answer for a marker; see plan §4.
- **Draft**: the export of a run; a package document with `missing` text markers, never stored
  by the server.

## Rollback

`0058_storyline` downgrade drops `storyline_trace_entry` and `storyline_package`, drops the
three run columns and index, drops the two step columns and restores `proposal_id NOT NULL`
after refusing if any step has a null `proposal_id`, and drops `fact.recorded_at` with its
index. It refuses while any run has a `storyline_key`, so a downgrade is a deliberate act
after archiving storyline runs, not a silent loss.
