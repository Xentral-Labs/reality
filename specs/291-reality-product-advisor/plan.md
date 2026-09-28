# Implementation Plan: Reality Product Advisor

**Branch**: `291-reality-product-advisor` | **Date**: 2026-09-28 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Extend the spec 290 Business Journey question service into one research-backed Product Advisor used by Website, Docs and authenticated Chat. Generate a versioned, public-safe knowledge artifact from existing authoritative journeys, executable catalogs and an explicit allowlist of durable public documentation. At question time, classify and decompose the request, retrieve a small evidence set, produce structured claims, validate every claim against source eligibility, status and limitations, then compose readable prose in the detected question language. Keep the existing endpoint and journey citations compatible while adding claim/source detail. Use no new database, vector store or unrestricted runtime repository access.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/Vue only for existing Web/Docs presentation changes
**Primary Dependencies**: Existing Pydantic v2, FastAPI, HTTPX, PyYAML, Anthropic adapter and generated catalog infrastructure; no new runtime dependency
**Storage**: Committed generated JSON knowledge artifact plus existing YAML/Markdown authorities; no PostgreSQL schema change
**Testing**: pytest unit/service/API/chat stories; generated-artifact checks; Docs widget/component tests; existing Web and Docs builds; multilingual buyer-evaluation fixtures
**Project Type**: Shared backend service with API, application-tool, authenticated Chat, Docs and embeddable-widget adapters
**Constraints**: Public-safe source allowlist; strict tenant scope; bounded provider calls and evidence; deterministic fallback; no browser business rules; no public runtime filesystem/code search
**Scale/Scope**: Initial 228 journeys, current executable catalogs, curated durable public contracts and at least 75 evaluation questions; lexical/structured retrieval before considering embeddings

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Advisor claims retain source identity and explain business behavior without changing the underlying Source/Evidence/Reality chain. | PASS |
| Reality owns operational state | The advisor reads product evidence only; it adds no document fulfillment status or operational authority. | PASS |
| Proven schema only | No business or database schema change. Advisor models are immutable in-memory/generated contract objects. | PASS |
| Tenant + shared service boundaries | Website, Docs, API tool and authenticated Chat call one service; only existing tenant-scoped tools may add company context. | PASS |
| Spec/test traceability | FR/DR groups map to service, generator, adapter and buyer-evaluation tests below; tests precede behavior changes. | PASS |
| Explainable web behavior | Public answers expose concise claim sources; authorized diagnostics retain research and validation decisions. | PASS |
| Received values not recomputed | The feature classifies held evidence and derives advisory conclusions at read time; it stores no derived business authority. | PASS |
| Smallest coherent design | Reuses current endpoint, catalogs, provider and generation gates; rejects a vector database and unrestricted agent/code access for the first release. | PASS |

Post-design recheck: all rows remain PASS. The generated artifact and claim structures introduce no operational persistence or alternate business rule.

## Repository Structure and Layer Changes

```text
packages/reality-core/config/
├── product_advisor_sources.yaml
├── product_advisor_knowledge.json
└── business_journey_catalog.yaml
packages/reality-core/src/reality/domain/product_advisor.py
packages/reality-core/src/reality/services/product_advisor.py
packages/reality-core/src/reality/services/business_journeys.py
packages/reality-core/src/reality/tools/business_journeys.py
packages/reality-core/src/reality/web/journey_guide_api.py
packages/reality-core/src/reality/services/core.py
packages/reality-core/tests/
apps/docs/scripts/generate-product-advisor-knowledge.py
apps/docs/.vitepress/theme/components/BusinessJourneyGuide.vue
apps/docs/public/journey-guide-widget/widget.js
docs/features/business-journey-guide.md
```

**Dependency direction**: generated/config evidence → domain rules → advisory service → canonical tool → API/Chat adapters → Website/Docs presentation. Adapters neither retrieve nor reclassify evidence.

## Design

### Reality flow

Product advice is a read-time observation, not a business record:

```text
Authoritative catalog/document
  → generated Evidence Unit
  → bounded question-time Evidence Selection
  → validated Advisory Claims
  → transient Advisory Answer
```

For tenant-specific follow-ups, the existing chain remains SourceRecord → Document/DocumentLine → Reality records → canonical tenant-scoped read tool → company observation. The answer labels company observations separately from general product claims and persists neither as business authority.

### Knowledge generation

`product_advisor_sources.yaml` is an allowlist of source references and source classes, not a parallel prose database. The generator loads public Journeys, public executable vocabulary from the existing runtime catalogs and bounded sections from allowlisted durable Markdown contracts. It emits stable evidence identities, normalized search text, support semantics, visibility, source links and fingerprints. It rejects missing anchors, duplicates, internal content and stale tool/Journey references, then writes a deterministic committed JSON artifact consumed by runtime and checked by `make docs-catalog-check`.

Tests, code and private specs are not copied into the public artifact. They can constrain reviewed source status but do not independently become a public product promise.

### Question and claim pipeline

1. **Classify**: deterministic signals plus an optional provider plan identify intent, detected language, subject and no more than six subquestions. A short ambiguous follow-up inherits language from bounded history, then the surface hint. Tenant-specific requests use normal Chat tools.
2. **Retrieve**: lexical aliases, source class, subject and catalog relationships return a bounded evidence set per subquestion. Broad questions receive representative evidence for each requested concern.
3. **Draft claims**: the provider returns structured claim candidates with exact evidence IDs, requested capability, support level, workflow role, limitation and optional exact tool name.
4. **Validate**: server rules verify source visibility, citation existence, status ceiling, exact tool vocabulary, limitation preservation and prohibited confidence transitions. High-risk wording requires exact qualifying evidence. An optional second provider check may test semantic entailment but cannot raise support or authorize a source.
5. **Compose**: only validated claims are rendered into a direct answer, workflow, tools, limits and references in the detected question language. Canonical IDs and tool names remain unchanged. Composition cannot add uncited capability statements.

The provider sees only bounded history, the research task and retrieved public-safe evidence, never the complete repository.

### Service and adapter flow

- `answer_public_question` remains a compatibility facade delegating to `answer_product_question`.
- `business_journey_guide` remains the canonical read tool name to avoid MCP/Chat compatibility churn.
- `/api/journey-guide/questions` retains existing fields and adds optional `intent`, `claims`, `sources`, `clarification`, `detected_language` and `knowledge_version`.
- `services/core.py` replaces the short hard-coded phrase list with shared product-question classification. Tenant operational requests retain normal tool routing.
- Website and Docs render server-returned structure; they do not infer status, evidence or language.
- Platform-admin evidence remains additive and cannot raise the public claim ceiling without a governed public source update.

### Data and migration impact

No Alembic migration and no PostgreSQL table are required. Research plans, evidence selections, claims and answers are request-scoped immutable objects. The committed knowledge artifact is reproducible and identified by a deterministic fingerprint. Existing Journey Proposal/Vote persistence is unchanged.

### Failure, security, and tenant behavior

- Public source allowlisting happens before deployment; runtime cannot browse arbitrary paths or URLs.
- Every model-returned source ID and tool name is server-validated.
- Catalog/doc content is untrusted evidence, never instruction.
- Provider timeout, invalid plan, malformed claims or failed validation falls back to deterministic selected evidence, one clarification or an explicit unavailable result.
- Existing public rate limits and bounded history remain.
- Authenticated company observations use existing session, membership and tenant-scoped tools.
- The service records bounded decision codes and evidence IDs, not secrets or raw private content.
- No advisory path executes mutations; mentioned proposal tools retain confirmation requirements.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-005–FR-007, FR-021–FR-023 | generator/contract | product-advisor generation and stale/private/duplicate source fixtures | No governed multi-source artifact exists. |
| FR-002–FR-004, FR-008–FR-011 | domain/unit | `test_product_advisor_claims.py` | Current one-pass rewrite has no subquestion or claim validator. |
| FR-012–FR-015, FR-019–FR-020 | service/evaluation | `test_product_advisor_service.py` plus multilingual buyer fixtures | Current prose can overstate manual, partial and adjacent capabilities. |
| FR-001, FR-018, FR-027, DR-004 | API/tool/story | extend Journey API/tool/Chat and Docs contract tests | Current surfaces return Journey-only evidence and phrase-bound routing. |
| FR-016, FR-026, DR-003, DR-007 | security/story | public leakage, adversarial prompt and cross-scope tests | No general product-evidence visibility model exists. |
| FR-017, DR-001–DR-002, DR-006 | Chat story | capability plus tenant follow-up and confirmation regression | Current capability branch short-circuits broader research. |
| FR-024–FR-025, SC-001–SC-009 | acceptance/eval | at least 75 claim-oriented buyer cases | No ERP-buyer release gate exists. |
| Docs/widget presentation | adapter | claim/source safe-rendering, detected-language and responsive tests | Clients render prose and Journey citations only. |

Test order is source policy → domain validation → service/evaluations → tool/API/Chat → presentation → full gates. Initial red proofs reproduce the observed migration, credit-hold, return end-to-end and procure-to-pay overclaims.

## Rollout and Rollback

1. Land generation and validation behind the existing endpoint and compare structured conclusions with current answers in tests.
2. Enable the advisor pipeline after buyer evaluations pass; retain deterministic Journey fallback.
3. Add structured source/claim presentation after the additive API contract deploys.
4. Expand authenticated Chat routing last, after public parity and tenant-boundary tests pass.

Rollback disables the advisor pipeline and returns the endpoint/tool to the spec 290 deterministic Journey answer. Additive fields remain optional to clients. No data or business rollback is necessary.

## Review Risks

- Public content may still be unsuitable as a product commitment; allowlist additions require product review.
- Lexical retrieval may miss synonyms; prove the gap with evaluations before adding search infrastructure.
- An LLM verifier may agree with an incorrect writer; deterministic source/status/tool ceilings remain authoritative.
- Broad answers may become catalog dumps; subquestion and 180-word defaults constrain them.
- Chat may misclassify a tenant operation as general advice; explicit company context and normal tool routing take precedence.
- Automatic language detection can be uncertain for short inputs; bounded history and surface language provide deterministic fallback.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

## Implementation Review — 2026-09-28

- **Constitution**: Advice remains a transient read-time observation. No schema, business status or alternate authority was added. The generated evidence chain remains Source → Evidence → public product claim.
- **Source scope**: Runtime reads only the committed generated artifact. Its document inputs are allowlisted public contracts; repository paths, tests, specifications, provider configuration and tenant data are excluded from the public artifact and provider envelope.
- **Tenant and confirmation boundaries**: Public/API research is read-only. Authenticated general advice uses the same canonical read tool. Platform-admin diagnostics are additive and cannot raise the public conclusion. Proposal and vote tools remain mutating and confirmation-bound.
- **Compatibility**: The existing endpoint and canonical tool name remain. Response additions are optional. Journey browsing, proposals and voting are unchanged. Legacy provider responses are validated and normalized.
- **Rollback**: Reverting the Advisor delegation restores spec 290 deterministic Journey answers without a data migration; clients tolerate the absence of additive fields.
- **Known release dependency**: The final reviewer-owned checklist and deployed origin smoke require their designated human/release owners; implementation does not self-approve them.
