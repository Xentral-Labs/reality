# Research: Business Journey Guide

## Decision: one structured catalog is authoritative

Move the 228 matching scenario and coverage IDs into one YAML catalog and generate contributor Markdown and public assets.

**Rationale**: This follows the existing executable catalog and Docs generation model and permits exact drift validation.

**Alternatives considered**: Parse Markdown at runtime (fragile and unsafe for visibility); PostgreSQL (mutable authority without need); a CMS (new infrastructure).

## Decision: static-first public guide with bounded API enhancement

Docs retains complete generated browse/search. Natural-language answering may call the existing API origin, but deterministic matching and cited results remain available without a provider.

**Rationale**: Docs is contractually static and tenant-independent.

**Alternatives considered**: Embed a provider key (unsafe); proxy all Docs (breaks deployment boundary); Product Web only (excludes evaluators).

## Decision: evidence-constrained answer envelopes

The service chooses matched entries and permissible support conclusions before optional generation. Provider output is rejected if it cites unknown entries or upgrades status.

**Rationale**: A structured envelope makes claims testable and preserves deterministic fallback.

**Alternatives considered**: Unconstrained retrieval-augmented prompts; hand-written FAQ; vector database.

## Decision: account-global product feedback

Suggestions describe Reality capability, not tenant business state. They are owned by an authenticated account; votes are account/proposal unique and reversible.

**Rationale**: Tenant-scoping would fragment a global demand signal. These are not business tables.

**Alternatives considered**: Tenant scope; anonymous votes; external voting SaaS.

## Decision: lexical similarity first

Normalize question terms, IDs, synonyms and process area; compare token and phrase overlap against journeys and open proposals.

**Rationale**: Hundreds of entries do not justify embeddings or a vector store; deterministic matching is explainable and testable.

**Alternatives considered**: Embeddings, database-only full text and manual-only review.

## Decision: explicit moderation and lifecycle

Submissions are confirmed, sanitized and published as `proposed`; authorized reviewers control lifecycle with rationale. Available proposals retain votes and link to their journey.

**Rationale**: This preserves demand history without treating votes as roadmap authority.

**Alternatives considered**: Auto-publish, auto-convert votes to tasks and delete declined proposals.
