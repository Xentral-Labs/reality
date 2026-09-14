# Data Model: Reality Gap Workflow

## RealityGap

Opaque ID, tenant, business question, intended use, origin (`chat|mcp|web`), optional origin reference, lifecycle status, nullable destination, revision, tenant-unique idempotency fingerprint, requester, and UTC timestamps.

Statuses: `open → investigating → awaiting_decision → accepted → implementation_ready → implemented`, with terminal `rejected` and `source_only` branches.

## RealityGapEntry

Tenant and gap, type (`answer|context|evidence|recommendation|decision|implementation_proposal|implementation_result|note`), canonical validated JSON payload, actor, and UTC time. Entries are append-only. Evidence stores opaque references, restricted paths, and bounded examples, never full payloads.

## InterpretationRule

Opaque rule-version ID, tenant, originating gap, logical name/version, `draft|active|disabled` status, exact source system/type, ordered validated conditions, optional bounded iteration path, explicit output mode (`source_path|constant`), optional output path, optional typed constant, tenant-local predicate, subject type and closed resolver, scalar value contract, allowed values/mapping/normalization, observation-time selection, actor, and lifecycle timestamps. At most one active version per logical name; semantic fields are immutable after draft. Legacy rows migrate to `source_path` output using their existing value path.

Conditions are stored as canonical JSON because they are immutable validated rule data rather than independently addressed business entities. A leaf contains `path`, `operator`, and, only where required, a typed `operand`; a group contains `mode` (`all|any`) and ordered child nodes. The tree contains at most 20 leaves and three group levels. Existing flat lists use the persisted top-level `conditions_mode` and therefore retain their original all-of meaning.

V1 resolvers are:

- `source_document_commitments`: exactly one same-tenant Commitment through the SourceRecord's Document.
- `source_document_lines`: one same-tenant DocumentLine corresponding to the current bounded source-array element, resolved through an opaque persisted source-line coordinate rather than a human number.

## InterpretationOutcome

Tenant, exact rule version, SourceRecord, non-null source element key (empty for source-level evaluation; canonical array index plus reviewed source-line identity for line evaluation), status (`not_matched|not_applicable|matched|ambiguous_subject|invalid_value|conflict|fact_created|fact_existing|failed`), optional Fact, bounded diagnostic, and evaluation time. A unique rule/source/element-key identity prevents duplicate receipts under PostgreSQL null semantics. Outcome indexes support rule summaries and deterministic replay continuation.

## Replay page

Replay state is derived from immutable InterpretationOutcomes rather than becoming a second operational authority. The opaque cursor contains and validates the exact rule ID, tenant binding, reviewed source scope fingerprint, and last deterministic SourceRecord position. The response returns page counts, cumulative counts, next cursor, completion state, and bounded representative outcomes. Cursor contents carry no authority: every resumed query independently reapplies tenant, rule, and source-scope checks.

## Fact extension

Nullable `interpretation_rule_id` links the exact producer rule. Legacy and manual Facts remain null.

```text
Tenant 1─* RealityGap 1─* RealityGapEntry
                     └─* InterpretationRule 1─* InterpretationOutcome
SourceRecord 1─* InterpretationOutcome *─0..1 Fact
InterpretationRule 1─* Fact
DocumentLine 1─* Fact (for line-scoped predicates)
```

Every cross-record relationship is revalidated within the tenant.
