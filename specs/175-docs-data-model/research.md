# Research

- Decision: use `reality.db.core.Base.metadata`, with an offline PostgreSQL URL only if no environment value exists. Import constructs an engine but does not query it. Rationale: YAML column lists are incomplete and Commitment.quantity wording is stale. Alternative rejected: copy the database schema into hand-maintained docs.
- Decision: separate persistence nullability/default from input contracts. Rationale: UUID/timestamps and application-supplied values are not user-required fields. Action links expose actual tool parameters.
- Decision: one focused Vue component with parent-owned navigation. Rationale: preserves existing Back behavior and keeps model-specific rendering independent from large ToolUsage component. No new dependency.
