# Implementation Plan: Explain MCP Use

**Branch**: `101-explain-mcp-use` | **Date**: 2026-09-07 | **Spec**: [spec.md](./spec.md)

## Summary

Replace the landing agent section's large MCP capability panel with a compact connection bridge and link it to the existing bilingual setup guide. Update source-based content contracts before markup and style changes. Reuse current public-site components, styles, localization, VitePress navigation, and MCP documentation.

## Technical Context

**Language/Version**: TypeScript with React 19; Markdown
**Primary Dependencies**: Existing public Site and VitePress Docs
**Storage**: None
**Testing**: Node test contracts, Site build, Docs contract/build, localization audits
**Target Platform**: Responsive public web and documentation browsers
**Project Type**: Existing public website and static documentation
**Performance Goals**: No new runtime requests or interactive dependencies
**Constraints**: English repository content; complete supported localization; claims must reflect bearer-token authentication
**Scale/Scope**: One compact landing bridge, its existing bilingual guide, localization, and contract tests

## Constitution Check

| Principle | Evidence | Status |
| --- | --- | --- |
| Source → Evidence → Reality | Examples describe traceable reads and do not redefine records. | PASS |
| Reality is operational authority | Copy preserves proposal, approval, execution, and verification boundaries. | PASS |
| Proven schema only | No schema or persistence change. | PASS |
| Tenant and service boundaries | Copy states tenant-scoped tokens and least-privilege tools. | PASS |
| Specification and tests | FRs map to failing content contracts before implementation. | PASS |
| Explainable Web Product | Business jobs lead; protocol and credential details remain secondary. | PASS |
| Simplicity and storage discipline | Reuses existing pages, styles, and generated catalogs. | PASS |

Post-design re-evaluation: all rows remain PASS.

## Project Structure

```text
specs/101-explain-mcp-use/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/content.md
├── checklists/requirements.md
└── tasks.md

provider-site/src/
├── LandingPage.tsx
├── landing.css
└── localization.tsx

provider-site/scripts/
└── site-contract.test.mjs

apps/docs/content/
├── api-tools/connect-mcp.md
└── de/api-tools/connect-mcp.md

apps/docs/.vitepress/config.mts
apps/docs/scripts/docs-contract.test.mjs
```

**Structure Decision**: Keep the product narrative and one short connection bridge in the existing landing section; keep concrete MCP jobs and durable setup instructions in the existing API & Tools documentation area.

## Complexity Tracking

No constitutional exceptions.
