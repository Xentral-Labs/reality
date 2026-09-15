# Implementation Plan: Chat starter questions

## Summary and Technical Context
Add three localized native buttons to the existing empty state in React/TypeScript ChatPage. Reuse question state and composerId. No dependencies, domain, service, tool, API or database changes.

## Constitution Check

| Principle | Evidence | Result |
|---|---|---|
| Source → Evidence → Reality | Presentation only; existing answer trace remains | PASS |
| Reality owns state | No business state added | PASS |
| Proven schema | No schema change | PASS |
| Tenant and shared services | Ordinary send path preserved | PASS |
| Spec/test traceability | FR-001–004 mapped below | PASS |
| Explainable web | Questions assert no facts | PASS |
| Received values | No calculations | PASS |
| Smallest design | Static localized copy; no suggestion service | PASS |

## Repository Structure and Design
- apps/web/src/unified/ChatPage.tsx: three buttons beneath welcome copy, empty-state visibility; set draft and focus matching composer; disable while draft exists or busy.
- apps/web/src/localization.tsx: en/de/nl/es copy using existing t function.
- apps/web/scripts/unified-chat-composer-browser.mjs: extend current fixture acceptance before ordinary conversation checks.
- docs/WEB_SPEC.md: document starter interaction.

## Test Strategy and Traceability
FR-001: browser verifies three starters and zero message requests on activation.
FR-002: browser verifies focused editable draft, draft protection and existing explicit send flow.
FR-003: browser verifies starters disappear on send and are absent in historical messages.
FR-004: browser checks keyboard activation, 390px and desktop overflow; localization audit checks translations.
Observe missing starter buttons fail before implementation. Run existing composer acceptance, make web-build and make spec-check. Backend/migration gates are not required for presentation-only changes with no backend or schema edits.

## Rollout and Rollback
Deploy normal web bundle. Revert only this addition to roll back. No migrations.

## Review Risks
Preserve other work already present in ChatPage and localization. Avoid overwriting drafts or submitting implicitly. Verify compact/mobile layout.

## Complexity Tracking
No exceptions. Pre-design and post-design Constitution Checks pass.
