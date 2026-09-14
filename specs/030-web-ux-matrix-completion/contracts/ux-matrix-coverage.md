# Contract: UX Matrix Coverage

## Authority

`docs/WEB_UX_MATRIX.md` defines jobs/hierarchy. The client defines actual navigation.
`ux-matrix-v1` verifies reconciliation and never drives routing, permissions, or business
behavior.

## Coverage groups

| Group | Destinations |
|---|---|
| Shell/entry | Home, workspace navigation, company/settings entry |
| Daily operations | Facts, Exceptions, Commitments, Inventory, Reservations, Movements |
| Finance/Evidence | Open Items, Payments, Journal, Documents, document explanation |
| Reference/configuration | Parties/detail, Items/detail, Locations/detail, Commercial Terms/Pricing, Sources & Imports, Data/Agents settings |
| Support/trace | Ask Reality, Explorer, Help, shared Inspector |
| Separate integration | Activity (Spec 029) |

## Exactness rules

1. Every actual in-scope route appears.
2. Every matrix row maps to a destination, explicit nested/shared destination, or separate owner.
3. Each destination has exactly one primary owner.
4. Each declares hierarchy, primary action/absence reason, applicable states, explanation,
   and responsive cases.
5. Authentication and Profile are explicitly recorded as baseline-supporting, out-of-scope
   destinations. They retain topology drift coverage but do not invent a UX-matrix job.

## Presentation and explanation

- Business job/state precedes implementation identity.
- Attention precedes neutral activity; finance totals state scope/currency.
- Empty states explain valid data and truthful next steps.
- Mutations preserve confirmation/conflict semantics.
- Mobile keeps critical navigation/action and bounds table scrolling.

```text
visible answer
  → authoritative Reality/read model
  → normalized Evidence when applicable
  → immutable SourceRecord/raw payload when applicable
```

Non-applicable stages remain explicit; no visual relationship may be fabricated.

## Drift categories

`unmapped_route`, `stale_matrix_surface`, `duplicate_owner`, `missing_hierarchy`,
`missing_state_evidence`, `missing_primary_action`, `missing_explanation_entry`,
`missing_desktop_case`, `missing_mobile_case`, `browser_owned_calculation`, and
`separate_owner_not_integrated`.
