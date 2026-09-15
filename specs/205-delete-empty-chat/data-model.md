# Data Model: Delete Empty Chat Sessions

## ChatSession

Existing tenant-owned conversation container. No fields change.

Derived removal state:

- `empty`: zero tenant-owned ChatMessage rows reference the session.
- `non-empty`: one or more ChatMessage rows reference the session.

Transitions:

- active + empty → permanently absent
- active + non-empty → archived
- archived + non-empty → active through the existing restore operation

## ChatMessage

Existing durable message linked directly to one ChatSession and scoped to the same tenant. Any
message role or content makes the session non-empty. No cascade behavior or schema change is added.
