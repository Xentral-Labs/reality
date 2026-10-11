# Implementation Plan: Read-and-Prepare Preset for Manual MCP Tokens

**Branch**: `383-read-and-propose-preset` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

## Summary

One button in `apps/web/src/unified/MCPAccess.tsx`, next to the existing presets, sets the
selection to the de-duplicated names of every catalog tool whose `access` is not `confirm`.
Labels in German, Dutch and Spanish. The existing browser proof gains the preset.

## Constitution Check *(blocking gate)*

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Untouched. | PASS |
| Reality owns operational state | No business state involved. | PASS |
| Proven schema only | No schema. | PASS |
| Tenant + shared service boundaries | The form submits to the unchanged token API; the server's shared validation still decides. | PASS |
| Spec/test traceability | Each FR maps to the browser proof. | PASS |
| Explainable web behavior | No business rule in the browser; the preset only fills the existing selection from server-provided access classes. | PASS |
| Received values not recomputed | No business value involved. | PASS |
| Smallest coherent design | One button beside the existing presets. | PASS |

## Test Strategy

`apps/web/scripts/unified-ai-access-browser.mjs`: after full access, the new preset leaves
read and propose tools checked and the confirm tool unchecked, and review shows no approval
warning. Observed failing against `origin/main`'s component (the button does not exist).
Also run `npm run i18n:audit`, `npm run test:contracts` and `npm run build`.

## Rollback

Remove the button and labels.

## Complexity Tracking

No constitutional exception is required.
