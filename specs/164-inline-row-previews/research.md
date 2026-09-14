# Research: Inline Row Previews

## Shared disclosure shape

**Decision**: Use explicit list and table disclosure primitives with one controlled opaque record ID per register.

**Rationale**: Lists and HTML tables require different valid structures but can share state, icon, focus, loading, and visual semantics.

**Alternatives considered**: A universal wrapper produces invalid table markup. Native `details` does not naturally provide a full-width sibling table row.

## Inspector reuse

**Decision**: Extract the existing Inspector body for modal and inline rendering.

**Rationale**: This preserves tenant-scoped explanation and trace navigation without a second interpretation.

**Alternatives considered**: New endpoints are unnecessary; copied page-specific markup would drift.

## Interaction vocabulary

**Decision**: A right/down chevron means disclosure; an arrow means navigation; a filter icon means related filtering; a pencil means editing; domain action icons plus explicit verbs mean operational work.

**Rationale**: Outcome-oriented semantics address the ambiguity identified by the user.

**Alternatives considered**: Color alone is inaccessible. Universal chevrons preserve ambiguity. Icons without labels are too subtle.

## Daily work and Master Data

**Decision**: Inline content is preview-only. Decisions retain Review, commitments retain focused work, and Master Data editors remain separate.

**Rationale**: Reading stays distinct from mutation and confirmation.

**Alternatives considered**: Embedding full action cards mixes reading with mutation; keeping both side detail and inline detail duplicates selection.
