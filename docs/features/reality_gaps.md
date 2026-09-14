# Open Questions and Reality Gaps

During investigation, the Web detail view first offers a bounded search across the
active tenant's immutable SourceRecords. A user selects a concrete scalar field from
one result; the evidence entry retains the SourceRecord ID, payload field path, and
displayed value. Manual employee knowledge or external observations remain an explicit
fallback and are labelled as such.

Open questions is the customer-facing workflow for a business question that
Reality cannot answer yet. Its durable technical record is a tenant-scoped
`RealityGap`. It is modeling work, not a Fact, operational Exception, ChangeProposal,
or business Reality record.

## Lifecycle

Members capture a business question and intended use through Chat, MCP, or Web. The
shared queue retains guided answers, bounded SourceRecord examples, recommendations,
human decisions, and implementation results independently of the originating surface.
Only company owners classify a gap or control an interpretation rule in V1.

The allowed destinations are source-only, Fact, typed Evidence, typed Reality,
derived view, and rejected. Only a reviewed source-supported Fact mapping can execute
in user space. Every other accepted destination produces a developer package and
continues through the normal Spec Kit workflow.

## Safe Fact rules

A rule matches one source system/type, reads one restricted path, resolves an existing
Commitment through the SourceRecord's Document, validates a closed scalar contract,
and creates an immutable Fact. Rules contain no code, SQL, templates, network calls,
wildcards, or arbitrary expressions.

Simulation reports considered sources, matches, expected Facts, invalid values, and
ambiguous subjects before activation. Future activation and historical replay are
separate confirmed actions. Rule versions are immutable; disabling stops future
evaluation and never deletes previous Facts.

Every rule-created Fact links to its exact SourceRecord, subject, and rule version.
Ambiguous subjects and invalid values create inspectable outcomes rather than guessed
Facts.

### ERP conditions and output

A rule may contain up to 20 conditions in at most three explicit `ALL`/`ANY` group
levels. The closed operator set covers equality, membership, existence, and ordered
numeric/date comparisons. This supports rules such as `B2B AND (high value OR
overdue)` without scripts, formulas, regex, or free-form expressions. A
normal condition miss is recorded as `not_applicable`: it is neither an error nor an
explicit negative Fact. Missing or wrongly typed required values remain visible as
`invalid_value`.

The Fact value is independently configured. It either comes from one restricted
source path or is a reviewed typed constant. This supports both extraction such as
`order.gift_wrap_requested = false` and conditional classification such as emitting
`order.requires_manual_review = true` only for high-value unpaid orders.

V1 resolves either the one Commitment reached through the source Document or a
DocumentLine reached through one bounded source array and its immutable source-line
identity. Each line has its own outcome and Fact retry identity. Source-path
observation times must be timezone-aware ISO-8601 values and are normalized to UTC.

Competing active rule families do not gain precedence from activation order. If they
would emit incompatible values for the same subject, predicate, and observation
instant, Reality records a conflict and creates no newly conflicting Fact.

Historical replay processes deterministic pages of at most 500 sources. The response
returns an opaque continuation cursor, cumulative outcome counts, and completion
state. Retrying a page or resuming later does not duplicate Facts or outcomes. The
rule detail exposes last evaluation, outcome totals, bounded failures, and exact
source and Fact links for operational support.
