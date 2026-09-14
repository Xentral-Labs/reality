# Implementation Plan: Product Documentation Surface

**Branch**: `codex/product-documentation` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/031-product-documentation/spec.md`

## Summary

Add `apps/docs` as a statically generated, independently deployable documentation surface. VitePress supplies Markdown routing, hierarchical navigation, page outlines, previous/next links, accessible defaults, and build-time local search. Nginx serves the generated artifact and `/healthz`. Existing Site and Product Web builds receive the single new `DOCS_URL` value for documentation links, while all existing URL contracts remain unchanged. Compose, Make, CI, README, and `docs/WEB_SPEC.md` treat Docs as a fifth independent runtime.

## Technical Context

**Language/Version**: Node.js 22, TypeScript 5, Markdown

**Primary Dependencies**: VitePress 1.x; existing Nginx static-runtime pattern

**Storage**: Version-controlled Markdown and static assets only; no runtime storage

**Testing**: Node built-in test runner for content/config/deployment contracts; VitePress production build; internal-link checker; Docker health smoke test where Docker is available

**Target Platform**: Modern browsers and Linux container runtime

**Project Type**: Independently deployed static documentation web application

**Performance Goals**: Static content is usable immediately on common broadband; local search returns matching shipped content without a network request; CI build completes within the existing frontend-job class

**Constraints**: Public and tenant-independent; English-only in this increment; no API/auth/database/search-provider dependency; 320px responsive floor; only one new URL variable named `DOCS_URL`; repository contracts remain authoritative

**Scale/Scope**: Eight documentation areas, focused task/reference pages, one container, one local Compose service, and links from existing browser surfaces

## Constitution Check

*GATE: Passed before Phase 0 and re-checked after Phase 1 design.*

| Principle | Result | Evidence |
|---|---|---|
| I. Source → Evidence → Reality | PASS | Core-concepts content uses the canonical chain and links durable domain contracts; no new interpretation or data path is introduced. |
| II. Reality Is the Operational Authority | PASS | Documentation rejects document-owned operational state and teaches shortest true links and opaque identity. |
| III. Proven Schema Only | PASS | No database, schema, typed business field, or migration is added. |
| IV. Tenant and Service Boundaries | PASS | Docs is tenant-independent and performs no business reads/writes; examples point to shared application interfaces. |
| V. Specification and Test Evidence | PASS | Spec, review checklist, plan, tasks, analysis, contract tests, production build, and container smoke evidence are required. |
| VI. Explainable Web Product | PASS | The surface explains the Cockpit/Inspector relationship and the trace from operational answer to source payload. |
| VII. Simplicity and Storage Discipline | PASS | Static Markdown plus an established static server is the smallest solution; hosted search, CMS, auth, and runtime storage are rejected. |
| Repository language | PASS | All new artifacts and documentation are English. |

### Post-design re-check

PASS. The content model, UI contract, and deployment contract add no domain entities or alternative business rules. The generated search index contains only public repository-authored documentation. `DOCS_URL` is additive and existing URL variables retain their exact meanings.

## Project Structure

### Documentation (this feature)

```text
specs/031-product-documentation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/documentation-surface.md
├── checklists/
└── tasks.md
```

### Source Code (repository root)

```text
apps/docs/
├── .vitepress/
│   ├── config.mts
│   └── theme/
├── content/
│   ├── index.md
│   ├── getting-started/
│   ├── concepts/
│   ├── product-guides/
│   ├── integrations/
│   ├── api-tools/
│   ├── operations/
│   ├── development/
│   └── reference/
├── public/
├── scripts/docs-contract.test.mjs
├── Dockerfile
├── nginx.conf
├── package.json
└── package-lock.json

provider-site/{Dockerfile,vite.config.ts,src/vite-env.d.ts,src/components/PublicHeader.tsx}
apps/web/{Dockerfile,vite.config.ts,src/vite-env.d.ts,src/App.tsx}
compose.yml
compose.dev.yml
Makefile
.github/workflows/quality.yml
README.md
docs/WEB_SPEC.md
```

**Structure Decision**: Keep product documentation in a separate browser-app directory because it has an independent public origin, build lifecycle, navigation/search needs, and container runtime. It imports no business package and does not duplicate API or domain logic. Site and Web receive the docs origin at build time only for outbound links.

## Implementation Sequence

1. Add failing documentation contracts for content inventory, navigation, links, URL variables, Compose, and container health.
2. Scaffold the static docs project and shared theme/navigation/search configuration.
3. Author P1 concept and getting-started content, then satisfy its contract slice.
4. Author P2 product/integration/API task content and search/not-found behavior.
5. Add P3 operations/development/reference content, container, orchestration, URL integration, CI, and durable contract updates.
6. Run quickstart, all frontend/doc/spec gates, container smoke test, and final Constitution/diff review.

## Migration and Rollback

- No data or schema migration exists.
- Deployment adds one independent service and DNS mapping. Rollback removes or stops Docs and its DNS mapping; Site/Web fallbacks keep navigation safe if `DOCS_URL` is absent.
- Removing Docs does not affect API, MCP, Web, Site, PostgreSQL, or tenant data.

## Review Risks

- Public docs can drift from authoritative repository contracts. Contract tests assert required topics and canonical links; product claims must be classified.
- Duplicating OpenAPI creates drift. Docs identify the API runtime schema as canonical instead.
- A new app increases dependency maintenance. It uses one documentation framework and existing Node/Nginx conventions.
- Build-time `DOCS_URL` values can be malformed. URL helpers normalize trailing slashes and tests cover unset and trailing-slash values.

## Complexity Tracking

No Constitution violations or approved exceptions.
