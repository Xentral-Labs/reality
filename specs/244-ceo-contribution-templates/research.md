# Research: CEO Contribution Analytics Templates

## Decision: Use four reusable Analytics templates

**Rationale**: Position, trend, channel mix, and weak-margin ranking cover recurring executive questions using business-readable dimensions already present.

**Alternatives considered**: A dashboard duplicates Analytics; customer/article rankings expose opaque IDs; forecasts and targets need new authority.

## Decision: Require context after adoption

**Rationale**: A confirmed contribution population is an explicit financial choice. The builder already pauses a contribution question without context and exposes the selector.

**Alternatives considered**: Choosing the latest violates the contract; tenant IDs cannot live in static templates.

## Decision: Validate with a planner-only sentinel

**Rationale**: Model loading must check nodes, measures, axes, and additivity. A sentinel satisfies only the pure planner and is never published or executed.

**Alternatives considered**: Weakening runtime planning is unsafe; duplicating planner validation would drift.

## Decision: Keep incomplete groups visible

**Rationale**: Missing cost is not zero. Leakage ordering uses DB2 rate without a filter that would hide incomplete groups.

**Alternatives considered**: Negative-only filtering conceals incomplete scopes.
