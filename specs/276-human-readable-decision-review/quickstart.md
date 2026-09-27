# Verification: Human-readable decision review

## Test-first evidence

`node --test scripts/decision-review-ux-contract.test.mjs` initially failed all three contracts
before implementation: Chat had no decision card, the common dialog had no stable labelled frame,
and order review had no decision-specific hierarchy.

## Verification

| Check                                | Result                                                                                                                               |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Shared decision review contract      | PASS — 4/4                                                                                                                           |
| All Web source contracts             | PASS — 398/398                                                                                                                       |
| Production TypeScript/Vite build     | PASS; existing bundle-size advisory only                                                                                             |
| Localization audit                   | PASS — 2279/2279 in en, de, nl and es                                                                                                |
| Spec policy                          | PASS                                                                                                                                 |
| `git diff --check`                   | PASS                                                                                                                                 |
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

## Compact Chat decision-card increment

- The new compact-layout contract was observed failing before implementation and now passes 5/5
  with the rest of the focused decision-review contract.
- The card remains a distinct decision surface but no longer uses a large, separately filled
  status header. The main conversation bounds it to 680 px; compact and dock presentations use
  tighter padding and vertical rhythm.
- All 438 Web source contracts pass on the final feature branch.
- The production TypeScript/Vite build passes with the existing bundle-size advisory only.
- The localization audit passes 2344/2344 in English, German, Dutch and Spanish.
- Spec policy and `git diff --check` pass. No proposal data, authorization, mutation or routing
  behavior changed.

## Minimal card-content increment

- The minimal-content contract was observed failing before implementation and now passes 5/5.
- Chat cards now show only the localized business action, `Not yet executed` and `Review`.
  Decision labels, proposal purpose and agent origin remain absent from the compact card; full
  review detail remains available after opening it.
- Item, Location and Payment Term creation use explicit business labels in all four product
  languages instead of technical server labels.
- All 438 Web source contracts, the production build and the localization audit pass. The build
  retains only the existing bundle-size advisory.

## Grouped proposal-list increment

- The grouped-list contract was observed failing before implementation and now passes 5/5.
- Ordinary proposals render in one counted, bounded surface with 64 px minimum rows, dividers,
  subtle hover feedback, left-aligned title/status and a neutral review button at the right.
- Each row retains its exact proposal ID and canonical review-kind route. No batch confirmation
  or changed proposal lifecycle was introduced; specialized report proposals retain their own
  component.
- All 438 Web source contracts, the production build and the four-language localization audit
  pass. The build retains only the existing bundle-size advisory.

## In-place Chat review increment

- The in-place routing contract was observed failing before implementation and now passes with
  the proposal-review parity contract.
- Chat now selects only the exact proposal and leaves the current route unchanged. The global
  review host opens the existing canonical dialog over the current Chat/workspace and restores
  that context when closed.
- Decisions retains its server-owned destination routing; Chat no longer imports or invokes that
  workspace mapper. Existing review reads, confirmation/rejection services, permissions, tokens
  and delivery delegation are unchanged.
- All 438 Web source contracts, production build and four-language localization audit pass. The
  build retains only the existing bundle-size advisory.

## Localized review-dialog increment

- Shared-label and common-review localization contracts were observed failing before
  implementation and now pass.
- Chat, Decisions and the common review dialog now consume one proposal business-label mapping.
  Known Party, Item, Location and Payment Term create/update titles no longer depend on technical
  server label wording.
- Known master-data purpose copy and Payment Term/source/hierarchy field labels are translated in
  German, Dutch and Spanish. Received codes, names, quantities and source values remain exact.
- All 438 Web source contracts, production build and four-language localization audit pass. The
  build retains only the existing bundle-size advisory.

## Proposal Review read-deduplication increment

- The focused async contract was observed failing before implementation and now passes 3/3.
- Concurrent reads for the same tenant and proposal share one in-flight Proposal Review GET. The
  entry is removed after success or failure, so reopening always performs a fresh read and a
  failed request can be retried.
- The mechanism does not cache responses and does not wrap confirmation, rejection or any other
  mutation.
- A live uncached Chrome check on the running localhost application showed one matching review
  request (200 OK, 1.36 s), instead of the two concurrent requests observed before the fix.
- All 438 Web source contracts, the production build and the four-language localization audit
  pass. The build retains only the existing bundle-size advisory.
