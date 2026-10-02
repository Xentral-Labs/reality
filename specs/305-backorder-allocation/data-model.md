# Data Model: Serving Backorders on Receipt

No new table, column, index or event.

| Observation | Read from | Stored |
|---|---|---|
| Waiting promise and its need | `commitment` (open customer delivery) less active `reservation` | no |
| Serving order | `supply_assignment` order for the named purchase, then `commitment.due_at`, `commitment.created_at` | no |
| Arrived / still to come per assignment | purchase received (`commitment_terms`) spread over effective assignments in creation order | no |
| Available to promise | movements, reservations, blocks, open purchases and their assignments | no |

Reservations made by `backorders_serve` are ordinary `reservation` rows with their `reservation.created` events, linked to the confirmed change proposal by `action_id`.
