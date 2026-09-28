# Research: Reality Product Advisor

## Governed knowledge artifact

**Decision**: Generate a deterministic public-safe evidence artifact from canonical Journeys, runtime executable catalogs and an explicit allowlist of durable public documentation.

**Rationale**: Runtime repository search is unsafe and deployment-dependent. Generation makes eligibility, freshness and leakage reviewable without duplicating source prose.

**Alternatives considered**: Runtime repository search was rejected for safety and nondeterminism. Copying answers into a second catalog was rejected as parallel truth. Indexing every Markdown file was rejected because drafts and plans are not product commitments.

## Retrieval without a new database

**Decision**: Start with normalized lexical retrieval, aliases, source metadata and explicit relationships over the bounded generated corpus.

**Rationale**: Journeys and executable catalogs already contain structured identifiers, questions, keywords and process areas. This is deterministic and sufficient to measure before introducing infrastructure.

**Alternatives considered**: PostgreSQL vectors and hosted vector search were rejected until the buyer evaluation demonstrates an actual recall gap.

## Claims before prose

**Decision**: Separate evidence selection, structured claims, validation and final composition.

**Rationale**: The current single rewrite pass can cite valid Journey IDs while making a broader unsupported statement. A claim is the smallest unit whose status and limitations can be tested.

**Alternatives considered**: Prompt-only improvement was rejected because observed answers violate explicit prompt rules. Citation-existence validation was rejected because it cannot catch migration inferred from unrelated item-history evidence.

## Deterministic ceilings and semantic checking

**Decision**: Deterministically enforce visibility, identity, source authority, support ceilings, tool vocabulary and prohibited confidence transitions. An optional semantic verifier may only reject or weaken a claim.

**Rationale**: String rules alone cannot prove entailment, but a second model is not an authority and must never upgrade support.

**Alternatives considered**: Free model self-grading and fully deterministic natural-language entailment were both rejected.

## Existing endpoint and tool

**Decision**: Keep `/api/journey-guide/questions` and `business_journey_guide`, adding optional structured fields while delegating to the Product Advisor.

**Rationale**: All three surfaces already converge there. A second endpoint would temporarily create two answer engines.

## Code and tests as constraints

**Decision**: Do not expose or dynamically search source code and tests publicly. Generated catalogs and reviewed public contracts may state product behavior; executable/internal evidence can lower or flag a claim but cannot independently create a public promise.

**Rationale**: Code proves a path exists, not that it is supported, reachable or stable. Tests contain internal fixtures and vocabulary.

## Language handling

**Decision**: Keep canonical evidence in English, detect the latest substantive question's language and compose in that language. Use bounded history and then the surface language only when detection is ambiguous.

**Rationale**: Maintaining translated evidence copies would create drift. Language changes presentation, never retrieval authority or status.

**Alternatives considered**: A fixed four-language list was rejected as unnecessarily restrictive for a public advisor. Surface-language-only behavior was rejected because visitors may ask in another language.

## Claim-oriented buyer evaluation

**Decision**: Maintain at least 75 cases with required facts, required limitations, forbidden claims and source expectations rather than exact answer snapshots.

**Rationale**: Natural wording should remain flexible while semantic overclaims block release.

**Alternatives considered**: Golden full-text snapshots and manual demo-only testing were rejected as brittle or non-repeatable.
