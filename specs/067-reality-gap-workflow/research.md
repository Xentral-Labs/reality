# Research: Reality Gap Workflow

## Separate modeling work from operational records

**Decision**: RealityGap has its own lifecycle; each mutation still uses ChangeProposal confirmation where required.
**Rationale**: A missing answer is neither truth, a derived operational problem, nor one pending mutation.
**Alternatives considered**: OperationalException breaks derivation semantics; ChangeProposal cannot hold a multi-stage investigation.

## Limit self-service to declarative Fact rules

**Decision**: Only source-supported Fact extraction can execute in user space.
**Rationale**: Facts already have provenance, validation, idempotency, and event semantics; shared domain changes remain governed development.
**Alternatives considered**: Developer-only misses the self-service goal; generated code/schema violates safety and governance.

## Use a closed path and resolver vocabulary

**Decision**: Exact dot/index traversal, one explicitly configured bounded array iteration, and named `source_document_commitments` or `source_document_lines` resolvers.
**Rationale**: Understandable and testable without executing expressions.
**Alternatives considered**: JSONPath/JMESPath, SQL, templates, and a universal relationship builder are unproven or unsafe.

## Separate applicability from Fact output

**Decision**: Conditions form a bounded tree of explicit `ALL` and `ANY` groups. Output is explicitly either one restricted source path or one reviewed typed constant.
**Rationale**: ERP rules need both extraction and event-like classification while preserving the difference between an explicit `false`, a normal non-match, and unknown input.
**Alternatives considered**: Treating Boolean false as a non-match loses source truth; embedding predicates in paths becomes an expression language; unrestricted depth or free expressions are not required.

## Bound Boolean grouping instead of adding an expression language

**Decision**: Permit at most three group levels and 20 leaf conditions, using only explicit `ALL` and `ANY` nodes.
**Rationale**: This covers common ERP combinations while preserving deterministic validation, review, simulation, and auditability.
**Alternatives considered**: Flat all-of rules cannot represent common alternatives; scripts, formulas, regex, arbitrary AST nodes, and unlimited nesting are unsafe or unnecessarily difficult to review.

## Use a closed comparison vocabulary

**Decision**: Permit equality, membership, existence, and ordered scalar comparisons with strict operand/type validation and no implicit cross-type coercion.
**Rationale**: These operators cover common ERP routing and threshold scenarios while remaining reviewable and deterministic.
**Alternatives considered**: Regex, contains, arithmetic, functions, and user-authored expressions materially expand the language and security surface.

## Preserve three-way evaluation meaning

**Decision**: Record `not_applicable` separately from invalid input or ambiguous subject resolution.
**Rationale**: A normal business condition miss is neither a negative Fact nor an operational failure.
**Alternatives considered**: Omitting skip receipts prevents trustworthy execution totals; treating skips as errors creates false operational noise.

## Make replay resumable and observable

**Decision**: Replay pages use a deterministic opaque cursor bound to tenant, rule version, and requested scope; each source/element outcome is idempotent and aggregate counts are queryable.
**Rationale**: Large histories cannot be safely processed as one transaction or an untracked fixed first page.
**Alternatives considered**: Offset pagination changes under concurrent ingestion; unbounded replay is unsafe; a separate job platform is unnecessary for the first synchronous bounded implementation.

## Surface conflicts without precedence

**Decision**: If active rule families produce incompatible values for the same subject, predicate, and observation instant, record a conflict outcome and create no newly conflicting Fact.
**Rationale**: Hidden rule ordering would turn configuration order into undocumented business truth.
**Alternatives considered**: Latest-rule-wins and numeric priority both introduce unapproved semantic authority.

## Version rules and separate replay

**Decision**: Rules are immutable versions; future activation and historical replay are separate confirmations.
**Rationale**: Facts must remain reconstructable and replay has a larger blast radius.
**Alternatives considered**: Mutable rules destroy provenance; automatic replay is unreviewed effect.

## Reuse owner authorization

**Decision**: Existing owners are V1 rule administrators; members may investigate and simulate.
**Rationale**: The current owner/member model is sufficient and avoids speculative permissions.
**Alternatives considered**: All-member activation is unsafe; a new role is broader unproven access work.
