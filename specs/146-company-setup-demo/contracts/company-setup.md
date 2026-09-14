# Company Setup Interfaces

Status: implemented and verified locally on 2026-09-09. All adapters call `services/company_setup.py`; payloads reject extra fields. No generic Chat tool is introduced.

## Account-scoped API

| Endpoint | Contract |
|---|---|
| GET `/api/company-setup/options` | Verified session; application-name suggestion, permitted environments/content, practice availability and reason codes; no creation or seed |
| POST `/api/company-setup` | `{request_key, name, environment: business|sandbox, content: empty|international_demo, live_simulation?: boolean, confirmed: true}`; owner/session identity is server-resolved; never supplied by body |
| GET `/api/company-setup/requests/{request_key}` | Account-owned receipt/run state and exact ready destination, or indistinguishable not-found; no retries or seed on read |
| POST `/api/company-setup/requests/{request_key}/retry` | Explicit confirmation of identical stored intent; retry failed or interrupted initializing setup through existing initialization safeguards |
| GET `/api/company-setup/requests/{request_key}/profile` | Ready owner's manifest, version/anchor/windows/case links/capabilities; no operational writes |
| POST `/api/company-setup/requests/{request_key}/execution` | Confirmed fresh execution profile with its own request key; repeat same key reuses result; never confirms a reservation |

Request name is trimmed, nonempty, at most 120 characters. Request key is nonempty, bounded 128 characters. Demo content forces sandbox on client and is validated on server. Server creates no company for options, input editing, preview or cancellation. Same key/different canonical payload returns 409. Return initializing/failed/ready with safe error codes, result identity, actual tenant ID when authorized, and a destination only when ready. Forbidden environment is 403; unknown/foreign request is 404; stale/reused request is 409; invalid fields are 422.

Active ready destinations use the existing explicit App company selector/route. Pending ready destinations use `/playground` with the existing run selection mechanism and open its cockpit directly, not another creation form. Existing memberships and invitation acceptance bypass setup. Options does not change admission or membership.

Legacy `/api/companies` creation must delegate to the shared service and require the request key; legacy `guided_demo=true` maps to the canonical demo Sandbox, never ordinary seeded data. Update its API tests and spec 027 entrypoint documentation accordingly. Preserve the compact demo helper/CLI/lesson fixtures themselves; they are explicit lesson tools rather than the new company-creation profile. No second creation implementation may remain reachable.

## UI contract

One `CompanySetupForm` serves first setup and every later creation entry. Empty is default. Environment has ordinary/Sandbox choices where permitted; demo visibly selects Sandbox. First name uses existing application metadata as an editable initial value only. Later entry starts blank. Access-application copy says company/volume describe the access request and do not create a company; no personal/volume question repeats here.

Retain request key and exact submitted choices in session storage until known success or explicit abandonment of an unsubmitted request. Lost response reloads status before allowing a new request. Show name errors at the field, safe recovery for failed setup, busy semantics during submission and a direct Open action for known ready results. Prevent response races from switching into another company's context. No partial profile is operationally usable.

Four languages (en/de/nl/es), light/dark, mobile/desktop, labelled radio groups, keyboard focus/validation and live status announcement. Stable business names are never translated. Sandbox banner describes the environment without asserting that empty companies contain sample records. The live-simulation checkbox is part of the confirmed company request: it automatically provisions and starts the integration. The ready screen links to Manage live simulation. Static companies retain the optional later-configuration link.

## Live company creation

The shared creation request accepts optional strict `live_simulation` (default false), valid only with `international_demo` in a Sandbox. Selecting it and confirming company creation automatically connects Demo Data and starts 60 orders/hour. The owner does not need to configure or start the integration separately. Static demos and later manual connections remain available. No real external integration is automatically authorized.

The flag is immutable creation intent in the existing PlaygroundRun JSON and part of its request fingerprint. After baseline seeding, shared connection/start services and `live_setup_complete` commit atomically. Failed setup retains the same baseline and exposes a retryable, non-ready result; GET never performs setup. A completed request remains completed even if the owner later pauses/stops the source. No new schema or scheduler mechanism.

Spec 146 FR-023: first and later creation use one goal-based choice: Start your own company, Create an empty Sandbox, or Try demo data. Only the demo choice shows optional Enable live simulation; switching away clears it. Eligibility filters available choices. The existing environment/content/live_simulation API contract is unchanged.

Spec 146 FR-025 supersedes the post-creation ready/profile/action menu: a ready result automatically enters the new company and shows a dismissible creation confirmation there. A recovered ready receipt also opens automatically. Opening failures preserve the request and expose a retry without a new creation/start action. Integration management stays in Integrations.
