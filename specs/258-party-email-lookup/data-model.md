# Data model

## PartyEmailAddress

| Field | Meaning |
| --- | --- |
| `tenant_id` | Required tenant scope and composite FK component |
| `id` | Opaque email-record identity |
| `party_id` | Direct owning Party |
| `email` | Trimmed display value supplied by the caller |
| `normalized_email` | Lower-case exact-match key |
| `label` | Optional caller-supplied business label, maximum 80 characters |

Unique per `(tenant_id, party_id, normalized_email)`. The same normalized address may occur on more
than one Party. Deleting a Party cascades through the database relationship.
