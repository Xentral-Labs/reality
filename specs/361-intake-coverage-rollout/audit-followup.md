# Local user audit follow-up — 2026-10-04

Owner authorization: fix the reported payment validation, payment selector,
source review and action accessibility defects, and qualify outstanding intake cases.
The external-only admission boundary remains unchanged.

## Existing requirements and plan

- Spec 359 FR-001/008: malformed payments retain raw and a coded no-effect failure;
  independent valid jobs still prepare. Normalize Pydantic source refusals at the
  shared intake service, without suppressing arbitrary infrastructure exceptions.
- Spec 121 FR-001/006: the open payment selector reloads current server data on its
  own Refresh action. Reproduce before changing its lifecycle.
- Spec 357 FR-002, spec 359 FR-002, spec 360 FR-002/011 and WEB_SPEC explainability:
  present prepared effects once, expose original source/file, and readable
  missing-value notices. Keep exact IDs and technical plan inspectable.
- Spec 121 FR-007 and WEB_SPEC keyboard usability: named native page action buttons.

Use existing preparation errors, read hooks, review and download services. No schema,
new permissions, calculations, provider calls, timers or acceptance authority.
Source remains immutable; exact digests and confirmation remain unchanged. Tenant
scoping/shared application boundary: PASS. Received amounts: PASS. Smallest model:
PASS. Review/test traceability: PASS. No critical inconsistencies.

## Tasks

1. Add HTTP missing/zero payment and valid sibling regression; observe failure.
2. Restore coded refusal; verify raw, durable outcome and zero effects.
3. Exercise initially empty payment dialog, updated projection and Refresh.
4. Reuse source-meaning view for single/batch reviews; preserve full raw downloads,
   effect arguments, unknown issue fallback and technical inspection.
5. Check action names with browser role queries; add explicit localized names.
6. Run financial/source, role, mandate/quota/revocation, MCP and demo proofs.
7. Record results and limits; run required checks and PR CI.

No general writer gate or additional authenticated-human decision cycle.
