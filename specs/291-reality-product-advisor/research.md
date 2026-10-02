# Research: Reality Product Advisor

## Governed knowledge artifact

**Decision**: Generate a deterministic public-safe evidence artifact from canonical Journeys, runtime executable catalogs and an explicit allowlist of durable public documentation.

**Rationale**: Runtime repository search is unsafe and deployment-dependent. Generation makes eligibility, freshness and leakage reviewable without duplicating source prose.

**Alternatives considered**: Runtime repository search was rejected for safety and nondeterminism. Copying answers into a second catalog was rejected as parallel truth. Indexing every Markdown file was rejected because drafts and plans are not product commitments.

## Retrieval without a new database

**Decision**: Generate a compact Capability Map from canonical Journey sections, business-resource metadata and governed executable vocabulary. Let the provider select at most six capability identities, then resolve their evidence relationships on the server and combine them with normalized lexical fallback retrieval.

**Rationale**: Journeys and executable catalogs already contain structured identifiers, questions, keywords and process areas. Grouping them once during generation gives the model semantic orientation without placing hundreds of evidence rows in every request. The map remains reproducible and cannot authorize a claim or action by itself.

**Alternatives considered**: Sending the complete evidence-unit index to a planning model was rejected because payload size and a second sequential model call exceeded the public widget timeout. Giving the public model real application tools was rejected because discovery does not require tenant access or execution authority. A separately curated answer/routing file was rejected as parallel truth. PostgreSQL vectors and hosted vector search remain deferred until evaluation demonstrates an actual recall gap.

## Public tool boundary and latency budget

**Decision**: Tool names and modes may be included in generated capability routing metadata, but the public advisor receives no callable business tools. Provider planning and answer stages use explicit bounded timeouts whose total worst case remains below the 40-second browser request timeout; any failure returns the deterministic path. Recognized broad processes use their governed concern decomposition directly; other questions use semantic catalog planning so ordinary ERP paraphrases do not fall through to weaker lexical retrieval merely because the provider needs more than three seconds.

**Rationale**: The model benefits from knowing which governed operations exist, but public product research must not cross tenant or mutation boundaries. An end-to-end request budget prevents a valid safe fallback from arriving after the browser has already displayed an error.

## Claims before prose

**Decision**: Separate evidence selection, structured claims, validation and final composition.

**Rationale**: The current single rewrite pass can cite valid Journey IDs while making a broader unsupported statement. A claim is the smallest unit whose status and limitations can be tested.

**Alternatives considered**: Prompt-only improvement was rejected because observed answers violate explicit prompt rules. Citation-existence validation was rejected because it cannot catch migration inferred from unrelated item-history evidence.

## Safe progress instead of draft-token streaming

**Decision**: Stream server-controlled lifecycle events and release answer text only in the terminal event after deterministic claim validation. Keep the existing buffered JSON response as the compatibility path.

**Rationale**: Immediate progress makes multi-stage research understandable, but provider tokens are not trustworthy until evidence IDs, support ceilings, limitations and tool names have been validated. Lifecycle events improve responsiveness without weakening Source → Evidence → Reality.

**Alternatives considered**: Raw provider-token streaming was rejected because unsupported prose could become visible and later require retraction. A browser-only rotating message was rejected because it could claim work that the server skipped or had not begun. Replacing the JSON route was rejected because existing Website, Docs, tool and test clients depend on it.

## Latency reduction and telemetry

**Decision**: Measure monotonic durations for deterministic retrieval, semantic planning, composition, validation and total request time without retaining public content. Skip semantic planning only when deterministic retrieval meets an explicit sufficiency rule, and skip validation retry when the shared deadline lacks enough budget.

**Rationale**: The present path may serialize a planning call, an answer call and a validation retry. Measurement identifies the actual bottleneck; bounded stage elimination reduces real latency rather than only masking it.

**Alternatives considered**: Adding a distributed cache or new observability dependency was rejected until measurements prove a need. Caching complete generated answers was rejected because conversation context and knowledge-version invalidation make correctness harder than the initial optimization requires.

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
