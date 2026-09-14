# Inline Preview Interaction Contract

| Meaning | Visual cue | Required wording | Result |
|---|---|---|---|
| Preview | right/down disclosure chevron | `Preview …` or visible row label with expanded state | Toggles read-only content below the row |
| Navigate | external-link icon | destination-oriented verb | Changes route or focused workspace |
| Related filter | filter icon | relationship-oriented label | Changes current register scope |
| Edit | pencil icon | `Edit …` | Opens an editor; does not save |
| Operational action | domain icon plus verb | effect-oriented wording | Opens existing review/confirmation flow |

Dense register rows do not show a generic eye or an unlabeled forward arrow. When no
distinct secondary action exists, the disclosure chevron is the only trailing icon.

## Invariants

- Disclosure owns `aria-expanded` and `aria-controls`.
- Only one preview is open per register.
- Preview activation performs no mutation.
- Nested links and actions do not toggle the row.
- Closing returns focus to the disclosure.
- Full traceability remains an explicit destination.
