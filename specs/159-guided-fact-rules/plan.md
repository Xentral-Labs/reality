# Implementation Plan: Guided Fact Rules

## Summary and technical context

Restore legacy capabilities as focused React/TypeScript components inside the existing
RulesWorkbench modal. Existing Python/Pydantic/PostgreSQL services remain authoritative.
Use existing CSS tokens and translations. No new dependency or schema.

## Constitution Check

| Principle | Result and evidence |
|---|---|
| Source → Evidence → Reality | PASS: source IDs/paths/values retained in existing entries |
| Reality authority and shortest links | PASS: no new status or duplicated identity |
| Proven schema and lossless payloads | PASS: no schema; preserve source values and advanced draft fields |
| Tenant and service boundaries | PASS: existing api methods, keyed workbench state, owner/admin controls |
| Confirmation and uncertainty | PASS: existing review runner; simulation read only; replay explicit batches |
| Spec and tests | PASS: approved restoration scope, unit/browser proofs before implementation |

Post-design check: PASS. No exceptions.

## Design and implementation order

Domain/services/tools unchanged. Adapter layer:
- `guidedRuleDraft.ts`: draft conversion and typed operand validation; preserve advanced configuration.
- `RuleDraftEditor.tsx`: field sections and recursive condition editor, readable definition summary.
- `RuleEvidence.tsx`: source search/selection/manual evidence/recommendation and destinations.
- `RuleResults.tsx`: simulation, execution and replay rendering with source/fact links.
- `RulesWorkbench.tsx`: compose components with existing confirmation and read states; exact rule result scope.

Existing rule DTO omits normalization/value_mapping. Recover matching draft from the
implementation_proposal entry rather than silently resetting it. The structured editor preserves advanced configuration without exposing raw rule JSON.

## Validation planned before implementation

Unit tests first: nested typed conversion, false/zero/decimal precision, lists, invalid inputs,
legacy draft preservation. Browser: evidence/recommendation, editing existing active version,
review/cancel/confirm, simulation/activation, replay cursor, read-only user, tenant change,
error/uncertainty, German mobile/keyboard and overflow. Existing reality-gap backend tests
and required complete suite; web-build, lint, spec policy. Synthetic browser fixtures only.

## Rollout / rollback

Web-only image rebuild in active local stack using root .env, no migrations. Roll back the
web image if needed; additive UI does not change stored rule semantics. Never replace the
integration frontend with root main or publish unrelated integration changes.

## Review risks

Lossy typed conversions; advanced draft omission; stale response crossing rule/company;
wrong replay cursor; accidental mutation before review; localized form overflow. Each has
unit or browser coverage. Do not broaden service behavior to compensate for UI limits.

## Approved usability refinement

Preserve all services and mutation semantics. Add pure initial-draft selection and localized
sentence generation; recompose the same dialog into a scrollable body with persistent footer,
three numbered areas and secondary history/evidence/advanced details. Test existing-value
initialization, no automatic overwrites, new-rule wording, progressive group mode and footer
bounds before final rollout. Constitution recheck PASS: presentation only, no new authority.

## Example-step refinement

Move RuleEvidence into the test section before saved versions; keep evidence available for questions without a Fact destination. Remove raw rule JSON controls, preserve advanced values through the existing draft helpers, and retain structured confirmation summaries. Source simulation remains the shared read-only API, bounded to 100 sources, not a selected-example execution API. Constitution Check: PASS; adapter-only, no schema or service changes.
