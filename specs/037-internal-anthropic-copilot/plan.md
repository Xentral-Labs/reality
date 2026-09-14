# Implementation Plan: Internal Anthropic Copilot

**Branch**: `037-internal-anthropic-copilot` | **Date**: 2026-09-02 | **Spec**: [spec.md](spec.md)

## Summary

Use server-managed Anthropic by default, with owner-selectable Anthropic or curated OpenAI-compatible providers stored in the existing secret vault. Provider presets supply economical tool-capable defaults; custom gateways remain available.

## Technical Context

**Language/Version**: Python 3.12+, TypeScript/React
**Primary Dependencies**: FastAPI, SQLAlchemy 2, httpx, React
**Storage**: PostgreSQL; no schema change
**Testing**: pytest, Node contract tests, TypeScript build
**Target Platform**: Linux API runtime and browser web application
**Project Type**: Web application with Python backend
**Performance Goals**: At most six model turns per user message
**Constraints**: Deployment or encrypted tenant secret only; tenant-scoped tool dispatch; no confirmation tool exposed
**Scale/Scope**: One Copilot runtime and one settings card; Chat sessions and MCP remain intact

## Constitution Check

| Principle | Evaluation | Result |
|---|---|---|
| Source → Evidence → Reality | Existing application tools remain the exclusive business-data path. | PASS |
| Reality operational authority | No domain state or document status changes. | PASS |
| Proven schema only | Existing AI settings and secret-vault fields fully represent the optional tenant credential. | PASS |
| Tenant and service boundaries | Tool dispatch retains tenant ID and read/propose access only. | PASS |
| Specification and test evidence | Specification, tests-first tasks, analysis, and verification are planned. | PASS |
| Explainable Web Product | The provider changes; traceability and tool results do not. | PASS |
| Simplicity and storage discipline | Native HTTP through existing httpx avoids a new SDK dependency. | PASS |

Post-design re-check: PASS. The design introduces no new persistence or business-rule path.

## Project Structure

```text
packages/reality-core/src/reality/agent/mcp_chat.py
packages/reality-core/src/reality/services/core.py
packages/reality-core/src/reality/web/api.py
packages/reality-core/tests/test_ai_mcp.py
packages/reality-core/tests/test_master_data_api.py
apps/web/src/App.tsx
apps/web/src/api.ts
apps/web/scripts/ux-configuration-contract.test.mjs
compose.yml
.env.example
docs/WEB_SPEC.md
apps/docs/content/reference/environment.md
```

**Structure Decision**: Extend the existing provider adapter and shared Chat service; reuse the existing secret service and settings endpoint; expose only credential ownership in the Copilot settings component.

## Complexity Tracking

No Constitution violations or exceptions.
