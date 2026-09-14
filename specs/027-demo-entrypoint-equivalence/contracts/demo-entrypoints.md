# Contract: Guided Demo Entrypoints

## Canonical operation

All supported entrypoints invoke the existing tenant-scoped guided-demo application
operation. Adapters may differ in confirmation and presentation but must not reproduce
its business steps.

## Entrypoint matrix

| Entrypoint | Starting state | Confirmation | Application operation | Outcome |
|---|---|---|---|---|
| Interactive CLI | selected empty tenant | terminal confirmation | guided-demo service | canonical demo state |
| CLI auto | selected empty tenant | explicit `--auto` intent | guided-demo service | canonical demo state |
| Product Web | authenticated company onboarding | preview plus confirmation | company adapter → guided-demo service | owned tenant with canonical state |

## Product Web company creation

The existing authenticated company-create request accepts a required company name and
an optional guided-demo choice defaulting to false. Omitted/false means empty company.
True is sent only after explicit confirmation. The response retains the new tenant's
opaque ID and name so the client can select it.

## Web interaction contract

Product Web must expose separate empty/demo actions, explain their consequences, issue
no demo request before confirmation, permit cancellation, send the demo choice through
the normal API client, open the returned tenant after success, and render API-owned
errors without local fallback data.

## Canonical comparison contract

Before the manifest is fixed, one real execution inventories every produced record
family, including indirect Facts and BusinessEvents. Each real entrypoint then runs in an
equivalent isolated tenant. Fresh authoritative reads produce the six versioned sections
from `data-model.md`. Comparison asserts exact sections, inventoried record types and
multiplicities, values, provenance, topology, lifecycle, derived results, and an explicit
financial zero state. It aliases generated IDs consistently and normalizes only
timestamps, ordering, decimal representation, and explicitly run-relative dates. A
mismatch reports the entrypoint and section.

## Safety contract

- Cancellation and empty-company creation: zero demo mutation.
- Populated tenant: zero reset, overwrite, or sample-data mixing.
- Completed rerun: zero duplicate canonical records.
- Another user inspecting the created demo tenant: not found without disclosure.
- Confirmed population failure: truthful error, no safe-retry claim, and no implicit
  tenant deletion; the possibly partial tenant remains for explicit operator handling.

## Baseline closure

`015/FR-010` remains `Documented gap` until complete executable evidence, full gates,
and final product-owner review pass. Closure removes only that coverage row.
