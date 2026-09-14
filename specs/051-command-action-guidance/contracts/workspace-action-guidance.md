# Contract: Workspace Action Guidance

## Application reference

Each item in every `workspaces[].actions[]` contains the existing Action fields plus:

```json
{
  "description": "Canonical business effect from the referenced Command"
}
```

The value is non-empty and equals the referenced Command's `effect`. The field is additive; no new endpoint is introduced.

## Product Web

- All actions renders label and description for every result.
- A non-empty prerequisite list renders separately as `Requires: A · B`.
- Search indexes label, description, and prerequisites.
- The shared Action form receives and renders the same description.
- Review and confirmation remain unchanged.
