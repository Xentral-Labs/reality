# Implementation Plan: Business Journey Guide

**Branch**: `290-business-journey-guide` | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)

**Language**: English for all repository artifacts and review evidence.

## Summary

Replace the two hand-maintained scenario Markdown tables with one validated YAML journey catalog that preserves all 228 IDs and current coverage assessments. Generate a public, localized Docs guide, static search payload and embeddable public chatbot from it. Add a pure query service that ranks catalog entries and constructs cited deterministic answers; an optional provider may semantically select published journey IDs and formulate the response within a server-validated citation and status envelope. Expose the same service through an anonymous, rate-limited read endpoint, normal authenticated Reality Chat and an authorized internal-evidence endpoint. Add account-scoped proposal/vote services and thin Product Web adapters. The private operations repository embeds the published chatbot artifact on the public marketing site under an explicit cross-repository contract. Generate Docs alongside the existing tool catalog so drift fails CI.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript/Vue for Docs and React/TypeScript for Product Web
**Primary Dependencies**: SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, FastAPI, existing provider adapters, VitePress/Vue, React/Vite
**Storage**: Versioned YAML for immutable deployment catalog; PostgreSQL for account proposals and votes only
**Testing**: pytest unit/service/PostgreSQL/API stories; Node contract tests; Playwright Docs/Product Web journeys; generated-artifact freshness, localization, accessibility and full repository gates
**Project Type**: shared application core plus independent static Docs, embeddable public-site widget, Product Web and Web/API adapters
**Constraints**: 228 baseline IDs; public Docs remain usable without API; public answers are read-only; no tenant/business data in public assets; account auth for mutations; no “Atlas” product copy; no new dependency or separate search infrastructure
**Scale/Scope**: Hundreds of versioned journeys, bounded top matches and citations, account-level proposals/votes; proposal volume is initially modest and indexed for status/similarity listing

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Journey explanations encode the business question and point to public evidence while validators reject document-owned operational claims; catalog metadata is descriptive, not business authority. | PASS |
| Reality owns operational state | No operational state or document status is added; statuses describe capability coverage only. | PASS |
| Proven schema only | Two persistence tables are justified by deduplicated proposals, reversible one-vote-per-account semantics, lifecycle filtering and exact counts; journey content remains versioned configuration. | PASS |
| Tenant + shared service boundaries | Public reads contain deployment data only. Account-scoped proposal/vote repositories require the authenticated account; Docs and Product Web call shared services through thin APIs. | PASS |
| Spec/test traceability | Every FR/DR maps to test-first tasks and named acceptance suites in `tasks.md`. | PASS |
| Explainable web behavior | Every answer cites journey IDs, evidence levels, limitations, tools and demos; public and internal evidence are visibly separated. | PASS |
| Received values not recomputed | The guide repeats stated demo/catalog evidence and labels all support summaries as observations; it creates no new source authority. | PASS |
| Smallest coherent design | Static catalog/search covers anonymous browsing and fallback; existing API/auth/provider/generator boundaries are reused; no vector database, CMS or separate feedback service. | PASS |

Post-design re-check: all rows remain PASS. The data model introduces no business table or alternate authority. No Constitution exception is required.

## Repository Structure and Layer Changes

```text
packages/reality-core/config/business_journey_catalog.yaml
packages/reality-core/src/reality/domain/business_journeys.py
packages/reality-core/src/reality/services/business_journeys.py
packages/reality-core/src/reality/db/models.py
packages/reality-core/src/reality/web/journey_guide_api.py
packages/reality-core/alembic/versions/
packages/reality-core/tests/
apps/docs/scripts/generate-journey-guide.py
apps/docs/.vitepress/theme/components/BusinessJourneyGuide.vue
apps/docs/content/{,de/}getting-started/business-journeys.md
apps/docs/public/generated/business-journeys.json
apps/docs/public/journey-guide-widget/                       # deployable public chatbot asset
apps/docs/content/getting-started/business-journey-chat.md  # standalone iframe/document fallback
apps/web/src/unified/JourneySuggestions.tsx
apps/web/src/unified/ChatPage.tsx                            # normal Chat capability routing/presentation
apps/web/src/api.ts
docs/scenarios/{catalog,coverage}.md
docs/features/business-journey-guide.md
```

Dependency direction remains domain → services → web adapters, with both browser applications consuming contracts rather than implementing capability rules.

## Design

### Reality flow

The guide does not create Reality records. Each entry explains how a business source becomes evidence and, where supported, the shortest link into Commitments, Reservations, Movements, LedgerEntries or Facts. Demo references and executable tests establish the coverage observation. A catalog status is deployment metadata derived during review and validation, never a customer-document field or business authority.

### Service and adapter flow

`business_journeys` loads one immutable validated snapshot. `search` ranks stable IDs, localized question terms, title and keywords deterministically. `answer` returns a structured conclusion, matched entries and citations. The configured provider receives only a bounded public catalog projection and the question, may select published IDs and formulate copy in English, German, Dutch or Spanish, and has no tools. The server resolves every selected ID back to the catalog, derives the status, and accepts prose only when status and citations match that authority; otherwise deterministic prose wins. The anonymous endpoint exposes public fields only with bounded query length/results and existing request throttling. Docs and the public-site widget call that endpoint and share deterministic local fallback. Normal Reality Chat detects capability intent and calls the same service through its registered read tool while retaining the ordinary conversation. The internal endpoint authorizes an account role and adds allowlisted internal evidence.

The public chatbot is a small, framework-neutral artifact hosted with Docs: a closed-by-default launcher opens an accessible dialog/panel, keeps questions ephemeral and links citations into the Guide. The private operations-owned marketing site supplies only public API/Docs origins and embeds the versioned artifact. If the asset or API fails, the host page remains unaffected. The operations-repository embed and production smoke evidence are external release dependencies, not silently claimed complete by this repository.

Proposal preparation normalizes the business question, searches journeys and open proposals, and returns a confirmation fingerprint. Confirmed creation, vote and withdrawal call one account-scoped service, are retry-safe and never flow through Docs-owned persistence. Chat may invoke the same prepare/confirm tools; direct Web actions use the same application service.

### Data and migration impact

`JourneyProposal` stores opaque ID, creator account, public text/context, process area, lifecycle, public rationale, optional available journey ID, moderation timestamps and UTC audit timestamps. `JourneyProposalVote` stores opaque ID, proposal/account FKs, active state and timestamps with a unique proposal/account constraint. Counts are derived; no counter column exists. Catalog entries stay in YAML because they are release-reviewed product vocabulary, not mutable business data.

Migration is additive. Downgrade removes only the two new feedback tables and indexes. No business backfill exists. Existing Markdown becomes generated output only after parity is proven.

### Failure, security, and tenant behavior

Anonymous requests are length- and rate-bounded, never persist questions or conversation history and receive only generated public fields. Browser clients may resend a bounded text-only in-memory history with each question so follow-ups remain coherent without server-side identity or storage. Prompt/catalog text is quoted as evidence, never executed as instruction. Provider timeout, invalid citations or unsupported status claims fall back to deterministic results. Internal evidence is selected after authorization and excluded structurally from the public serializer and generated JSON.

Proposal text is length-bounded, rejects secrets/contact-patterns and enters `proposed` only after explicit confirmation. Lifecycle changes require the existing platform-authorized boundary. Cross-account vote reads/writes do not disclose private creator information. Database uniqueness plus idempotency keys resolves concurrent votes and retries.

## Test Strategy and Traceability

| Requirement | Test level | Planned test | Expected initial failure |
|---|---|---|---|
| FR-001–FR-005, FR-019–FR-023 | unit/generator/browser | catalog parity/validation, generated Docs freshness and guide filter journey | no canonical structured catalog or page exists |
| FR-006–FR-010p, DR-001, DR-004–DR-005 | unit/service/API/browser | grounded matching, status ceiling, adversarial content, provider failure, bilingual question stories and full-height desktop widget | no shared query/answer service or full-height desktop panel exists |
| FR-011–FR-012, DR-003 | service/API/artifact | internal authorization and public non-disclosure scan | no scoped evidence serializer exists |
| FR-013–FR-018, FR-024, DR-002–DR-003, DR-006 | domain/PostgreSQL/service/API/Web | prepare/confirm, duplicate suggestions, moderation, lifecycle and concurrent reversible vote stories | proposal/vote model and services do not exist |
| SC-001–SC-010 | acceptance/full gates | 228-ID reconciliation, curated QA matrix, generated/check/build/a11y/localization/full tests | guide artifacts and acceptance matrix do not exist |

Tests are added before each implementation slice. Catalog parity and deterministic answering land before provider rewriting; proposal domain/service tests precede schema/API/UI.

## Rollout and Rollback

Deploy additive migration and API before Product Web links. Static Docs remain fully useful with generated browse/search and deterministic local match even when the API is unavailable; interactive answer enhancement shows a bounded unavailable state. Proposal actions open Product Web authentication and degrade to a read-only suggestion list when unavailable. Rollback serves the previous Docs/Web/API release, then optionally downgrades the additive tables after preserving feedback export. No catalog status changes automatically during rollback.

## Review Risks

- A coverage status can become marketing overclaim; executable-evidence and status-ceiling gates are blocking.
- Public generation could leak paths or internal notes; separate serializers plus artifact scans are blocking.
- Free-text public/provider surfaces invite prompt injection and abuse; bounded retrieval, no tools and deterministic fallback are mandatory.
- Duplicate detection is lexical in v1 and can miss conceptual duplicates; it is advisory and moderation remains authoritative.
- Public Docs and the marketing site are static; their host pages must not depend on the question API or widget availability.
- The marketing site is outside this repository, so repository completion can prove the artifact and contract but production completion also needs operations-repository rollout evidence.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |
