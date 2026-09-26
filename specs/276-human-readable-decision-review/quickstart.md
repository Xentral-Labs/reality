# Verification: Human-readable decision review

## Test-first evidence

`node --test scripts/decision-review-ux-contract.test.mjs` initially failed all three contracts
before implementation: Chat had no decision card, the common dialog had no stable labelled frame,
and order review had no decision-specific hierarchy.

## Verification

| Check | Result |
|---|---|
| Shared decision review contract | PASS — 4/4 |
| All Web source contracts | PASS — 398/398 |
| Production TypeScript/Vite build | PASS; existing bundle-size advisory only |
| Localization audit | PASS — 2279/2279 in en, de, nl and es |
| Spec policy | PASS |
| `git diff --check` | PASS |
| Existing order-entry browser fixture | Updated for the new action labels; not executed because this checkout has no configured Playwright module/browser or running Web/API |

## Review

- The implementation changes frontend presentation only. Existing proposal IDs, tenant-scoped
  reads, review tokens, authorization, confirmation, rejection and recovery calls are unchanged.
- Chat routes the exact proposal ID and server review kind to the existing canonical destination.
- The order review continues to display received quantities and amounts without recomputation.
- Technical trace content remains available in the collapsed System details disclosure.
- Common, order and master-data reviews share header, structured-value and action components.
  Nine additional action-specific review surfaces share the same pending action footer.
- Nested master-data values such as email contacts render as labelled rows and links, never as
  serialized JSON in the primary review.
- The unrelated untracked `reality-pre-reset-2026-09-21.dump` was not modified.
