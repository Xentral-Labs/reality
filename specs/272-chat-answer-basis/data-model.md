# Data Model: Compact Chat Answer Basis

## ChatMessage extension

`ChatMessage.answer_basis` is nullable JSON and exists only on assistant messages produced after this feature.

```text
{"version": 1, "calls": [{"operation": string, "input": bounded object, "result": bounded object or list}], "has_more": boolean}
```

Rules:

- The containing row's composite `(tenant_id, id)` remains the identity and tenant boundary.
- At most the configured chat tool-step limit is retained; excess sets `has_more`.
- Input, result, and total JSON size are bounded before persistence and by a database check.
- The snapshot is explanatory metadata, never business evidence or operational authority.
- Existing rows are null and require no backfill.

## PresentedAnswerBasis

A read-time service value, not a table, with `available`, up to four rows, `additional_count`, call count, and capture-limit status. Each row contains a business label, displayed value, role (`recorded` or `derived`), and optional allowlisted record type/ID. Duplicate record references collapse within the presented result.

## Lifecycle

The snapshot is created after the assistant message is persisted, read with that message, and deleted with the message/session through existing ownership. It is immutable after successful attachment. A failed attachment leaves null and never retries the provider turn.
