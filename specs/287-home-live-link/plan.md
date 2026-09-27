# Implementation Plan: Home Live Link Placement

**Branch**: `spec/287-home-live-link` | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)

## Summary

Move the existing Home live-monitor entry point out of the period-control group and pass it to `ActivityGraph` as a distinct header action. Render it inline beside the existing Live status with restrained link styling. No service, API, domain or data behavior changes.

## Technical Context

**Language/Version**: TypeScript 5.8, React 19

**Primary Dependencies**: Existing React components, Tailwind utility classes, lucide-react

**Storage**: N/A

**Testing**: Node contract tests, TypeScript build, Prettier, localization audit; existing Playwright Home scenario where available

**Target Platform**: Product Web, desktop and mobile browsers

**Project Type**: Web presentation refinement

**Performance Goals**: No additional requests, polling or runtime work

**Constraints**: Preserve existing authorization and navigation callback; no new translation key or CSS system

**Scale/Scope**: Two React components, one focused contract test, one durable Web contract update

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Presentation only; no records or links change. |
| Reality is operational authority | PASS | No business state or derivation changes. |
| Proven schema only | PASS | No schema or typed fields. |
| Tenant and service boundaries | PASS | Existing callback and access boundary are unchanged. |
| Specification and test evidence | PASS | Approved spec and failing-first focused contract precede implementation. |
| Explainable Web product | PASS | The action is placed beside the status that explains its purpose. |
| Simplicity and storage discipline | PASS | One explicit presentation prop; no dependency or abstraction. |
| Received values are never recomputed | PASS | No values change. |

Post-design check: PASS. The UI contract introduces no data model, API, service or business-rule change.

## Project Structure

```text
specs/287-home-live-link/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/ui.md
├── quickstart.md
├── checklists/requirements.md
└── tasks.md

apps/web/
├── scripts/home-live-link-contract.test.mjs
└── src/unified/
    ├── ActivityGraph.tsx
    └── HomePulse.tsx

docs/features/home-live-status.md
```

**Structure Decision**: Keep navigation ownership in `HomePulse`; pass only the rendered action into the graph header so `ActivityGraph` remains unaware of routes and permissions.

## Complexity Tracking

No Constitution violations or exceptions.

