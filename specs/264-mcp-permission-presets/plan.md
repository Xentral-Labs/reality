# Implementation Plan: MCP Permission Presets

## Summary

Extend the existing browser-only MCP token permission selector with a full-access preset. Reuse the catalog already loaded for token creation, submit explicit tool names, and preserve the existing review/confirmation service flow.

## Technical Context

- **Layer**: Web adapter only (`apps/web`)
- **Data/API changes**: None
- **Persistence/migrations**: None
- **Tests**: Existing Playwright-style browser acceptance script plus frontend build and localization audit

## Constitution Check

| Principle | Result | Evidence |
|---|---|---|
| Source → Evidence → Reality | PASS | Permission-selection UI does not alter business evidence or Reality records. |
| Reality operational authority | PASS | No document or business status is introduced. |
| Proven schema | PASS | No schema or typed business field changes. |
| Tenant/service boundaries | PASS | Token creation continues through the existing API/service; the browser only supplies an allowlist. |
| Specification/test evidence | PASS | Spec and browser acceptance tasks precede implementation. |
| Explainable web product | PASS | Explicit presets and selected count make the granted scope visible; review remains mandatory. |
| Simplicity/storage discipline | PASS | One UI control and translations; no dependency, abstraction, or storage change. |
| Received values | PASS | No received or derived business values are changed. |

## Design

The token form keeps three adjacent selection actions: read-only, full access, and clear. Full access replaces the current selection with a de-duplicated list of every current catalog tool name. It does not submit `*`, so later catalog additions are not silently granted. Individual checkboxes remain editable after either preset.

## Test Strategy

1. Extend browser acceptance coverage first and observe failure because the full-access control is absent.
2. Prove one-click selection across read, propose, and confirm tools; replacement by read-only; clearing; warning visibility; and explicit submitted names.
3. Run the focused browser scenario, production frontend build, localization audit, spec check, and relevant lint/type gates.

## Rollback

Revert the UI control, translations, and acceptance assertions. No stored data or migration requires reversal.

## Risks and Review

- **Risk**: Owners may grant broader access than intended. **Mitigation**: explicit “full access” wording, visible selected count, editable checkboxes, change warning, and confirmation.
- **Risk**: A wildcard could grant future tools. **Mitigation**: submit only current catalog names and assert the request body.
- **Review focus**: wording clarity, keyboard accessibility, mobile wrapping, and preservation of confirmation.

## Complexity Tracking

No constitutional exception or additional complexity is required.
