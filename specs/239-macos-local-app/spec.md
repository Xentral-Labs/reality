# Feature Specification: Reality Local for macOS

**Feature Branch**: Not created; specification-only work in the current checkout.
**Feature Directory**: `specs/239-macos-local-app`
**Created**: 2026-09-19
**Status**: Disposable development preview implemented; persistent release qualification remains open
**Language**: English
**Input**: Offer Reality locally on macOS through a download, ask only essential setup questions including an LLM API key, and let the user start immediately. Produce a concept and specification.

## Context and Intent

### Problem

Running Reality locally currently requires technical installation and operational
configuration. A business user needs a normal Mac application that owns this setup
and preserves the existing product's operational and explainability capabilities.

### Scope

- Downloadable macOS application with all required local runtimes included.
- One local owner, minimal first-company setup, optional canonical demo and own LLM key.
- Local persistence, secure access, visible process lifecycle, backup, restore and updates.
- Existing Operations Cockpit, Inspector and confirmed application actions.

### Non-Goals

- Cloud account or license activation requirement, cloud synchronization or hosted AI.
- Team/LAN serving, invitations, public MCP, public webhook hosting or remote access.
- Bundled on-device language models, Intel support, other desktop operating systems.
- New domain model, database alternative, duplicate demo engine or automatic business execution.
- Guaranteed work while asleep, after Quit, or before the user launches the app.

### Existing Contracts

- [Constitution](../../.specify/memory/constitution.md), [workflow](../../docs/SPEC_DRIVEN_WORKFLOW.md).
- [Architecture](../../docs/ARCHITECTURE.md), [Web product](../../docs/WEB_SPEC.md).
- [Self-hosted installer](../187-self-hosted-installer/spec.md).
- [Company setup/demo](../../docs/features/company-setup-demo.md), including spec 146.
- [Scheduled jobs](../../docs/features/scheduled-jobs.md), [health](../../docs/features/home-live-status.md).
- [Proposed delivery concept](concept.md); technical proposals there are not approved decisions.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download and reach a usable company (Priority: P1)

As a Mac user, I install Reality, select a company start and reach the normal product
without developer tools, hosting knowledge or an online Reality account.

**Why this priority**: This is the primary product promise.
**Independent Test**: Install on a clean supported Mac with no development runtimes;
complete first run with AI skipped and perform an ordinary non-AI product operation.

**Acceptance Scenarios**:

1. **Given** a supported clean Mac, **when** I install and launch the official download,
   **then** normal macOS launch protections accept it and no terminal, runtime installer,
   server credential, cloud account or email verification is required.
2. **Given** first run, **when** I choose Empty company, review the name and confirm,
   **then** exactly one local owner and company become available; language/time zone
   follow supported system preferences and remain editable.
3. **Given** Demo selected, **when** I confirm with live activity on or off, **then** the
   canonical Sandbox is created and only the explicitly selected live source starts.
4. **Given** interruption during setup, **when** I retry or relaunch, **then** the same
   request resumes without duplicate owner/company or resetting a completed source control.

### User Story 2 - Use my AI provider with an honest data boundary (Priority: P1)

As an owner, I configure AI with my provider key or continue without it, understanding
what leaves the computer and who charges for usage.

**Why this priority**: AI access is central to the requested setup but must not block local work.
**Independent Test**: Exercise valid, invalid, unreachable and omitted credentials;
inspect persisted state, outgoing requests and diagnostic output.

**Acceptance Scenarios**:

1. **Given** a supported provider, **when** I enter a key and explicitly test it, **then**
   a synthetic request checks the selected model without sending business data and
   shows success, invalid credentials, model access failure or temporary unavailability.
2. **Given** provider setup, **when** I review it, **then** destination, selected model,
   potential provider charges and business-context transmission are explained before use.
3. **Given** no key, no internet or provider failure, **when** I skip/retry, **then** local
   non-AI operations remain usable and Chat reports its unavailable state without fallback.
4. **Given** saved credentials, **when** I reopen, replace or remove them, **then** secrets
   remain protected, are absent from logs/diagnostics and future requests use the new state.

### User Story 3 - Trust local access and daily lifecycle (Priority: P1)

As an owner, I can reopen my data and understand whether background work is running.

**Why this priority**: A desktop download must be secure and reliable after first run.
**Independent Test**: Use a prepared installation to exercise local access, second
launch, child failure, close, Quit, sleep/wake and tenant-boundary probes.

**Acceptance Scenarios**:

1. **Given** an initialized installation, **when** I launch twice, **then** one runtime
   owns its data and the second launch focuses the existing application.
2. **Given** a running app, **when** I close its window, **then** a visible menu-bar
   presence remains and jobs continue; **when** I Quit, **then** its owned processes stop.
3. **Given** sleep, crash or child failure, **when** execution resumes, **then** queued
   work follows existing recovery/coalescing semantics and readiness reflects actual health.
4. **Given** another web origin, unauthenticated local client or another OS account,
   **when** it attempts to read or mutate this installation, **then** access is refused;
   ordinary tenant checks and explicit Chat confirmations still apply to the owner.
5. **Given** occupied conventional API/database/health ports, **when** I start or restart,
   **then** Reality obtains its own available endpoints without changing other processes;
   an allocation failure reports recovery and starts no partially usable session.
6. **Given** Keychain refusal or unavailable storage, **when** startup fails, **then**
   the app explains recovery without replacing secrets or claiming successful readiness.

### User Story 4 - Keep my data through maintenance (Priority: P1)

As an owner, I can update, back up and restore without administering a database.

**Why this priority**: A public local-data product must have a recoverable maintenance path.
**Independent Test**: Upgrade and restore a seeded installation with sources, artifacts,
secret-backed settings and pending jobs; inject update and storage failures.

**Acceptance Scenarios**:

1. **Given** an available update, **when** I approve installation, **then** a verified
   recovery checkpoint precedes schema changes and only a compatible whole release starts.
2. **Given** tampered content, low disk, incompatible schema or interrupted migration,
   **when** update cannot complete, **then** unsafe startup is blocked and a compatible
   prior state can be recovered without silently discarding subsequent business work.
3. **Given** a portable encrypted backup and its passphrase, **when** I restore on a clean
   supported Mac, **then** original records, source bytes and usable credentials return
   without the old computer; replacement of existing data requires explicit confirmation.
4. **Given** app removal, **when** I reinstall, **then** business data remains; deleting
   local data instead requires a separate preview/confirmation and preserves exported backups.
5. **Given** failed restore validation or a wrong passphrase, **when** restore stops,
   **then** the current installation remains usable and unchanged.

### Edge Cases

- Unsupported OS/CPU, insufficient disk, read-only data directory and revoked signing identity.
- Occupied local ports, stale instance lock and previously installed newer schema.
- Partial owner/company creation and retry after a completed demo source was paused.
- Provider timeout, rate limit, revoked key, inaccessible model and cancelled credential save.
- Locked Keychain, missing recovery key, wrong backup passphrase and corrupt artifact archive.
- Force Quit, power loss during update, stale worker leases and unresolved external outcomes.
- Malicious web origin, forged Host, cross-tenant request and attempts to replay bootstrap access.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Supply an official signed and notarized download for supported Macs with
  all local runtime dependencies; reject unsupported environments with an actionable explanation.
- **FR-002**: Require only company start/name and optional provider/key in normal first
  run. Infer editable presentation preferences. Never require developer tools, cloud
  signup, email verification, server configuration or a separate app password.
- **FR-003**: Establish one local owner through a desktop-specific trusted bootstrap,
  preserving authenticated sessions and tenant authorization without weakening hosted access.
- **FR-004**: Confirm company/demo/live choices together; keep Empty and live-off as
  defaults, reuse canonical setup, and resume interrupted setup idempotently.
- **FR-005**: Offer release-qualified provider/model choices, masked key entry and an
  explicit synthetic connection test with distinct credential/model/network failure states.
- **FR-006**: Explain provider data flow and billing before AI use, allow skipping AI,
  and preserve offline non-AI work with no silent cloud/provider fallback.
- **FR-007**: Protect credentials through the existing secret authority and OS-protected
  key custody; support replace/remove, prevent plaintext disclosure, and fail recoverably
  when key custody is unavailable rather than generate a substitute key.
- **FR-008**: Restrict access to the local user installation, authenticate local requests,
  reject untrusted origins and replayed bootstrap access, and expose no LAN/public services.
- **FR-009**: Keep durable data outside the application bundle, allow only one runtime
  per installation, and preserve data across Quit, crash, relaunch and app replacement.
- **FR-010**: Explain window-close versus Quit, retain visible running status, stop owned
  roles on Quit, and never enable login startup or hidden persistent services implicitly.
- **FR-011**: Report actual database/API/scheduler/worker health separately from AI;
  recover with bounded retries and existing queue semantics after sleep or process failure.
- **FR-012**: Support user-initiated update checks and approved installation; verify the
  release, create a recoverable checkpoint before migration, prevent mixed releases and
  block incompatible startup. Recovery must pair matching application, schema and data.
- **FR-013**: Provide encrypted portable backup/restore including database, original
  source artifacts, configuration and credential recovery; validate before replacement,
  retain a pre-restore checkpoint and require confirmation for replacing nonempty data.
- **FR-014**: Preserve local data when the app is removed; offer a separately confirmed
  data deletion flow with backup opportunity that never silently deletes exported backups.
- **FR-015**: Provide actionable setup/runtime/recovery errors and a user-initiated
  redacted diagnostic export. Do not upload telemetry, diagnostics or business data implicitly.
- **FR-017**: The app MUST require no fixed TCP ports or user port configuration.
  Local network listeners MUST obtain free ports by atomic OS allocation and remain
  loopback-only. All consumers MUST use the actual runtime endpoints. Restart, concurrent
  launches and occupied conventional ports MUST work without stopping other software.
  Exhausted OS resources MUST produce a bounded actionable failure, never a port-stealing loop.
- **FR-016**: Keep setup and recovery keyboard-accessible in the existing four product
  languages and both themes; preserve normal cockpit and Inspector navigation.

### Domain and Traceability Requirements

- **DR-001**: Preserve Source → Evidence → Reality and lossless source payloads through
  setup, use, backup and restore. Installation metadata is not business evidence.
- **DR-002**: Reuse existing application tools/services, opaque identities and shortest
  relationships. Desktop adds no document fulfillment state or stored derived authority.
- **DR-003**: Keep all business access tenant-scoped, including local owner, AI settings,
  diagnostics and background jobs. Chat mutations retain preview and explicit confirmation.
- **DR-004**: Keep PostgreSQL as the sole business database and the existing job registry
  and queue as scheduling authority. API/scheduler/worker startup never runs migrations.

### Key Entities

- **Local installation**: One OS-user-owned runtime/data boundary; not a business tenant.
- **Local owner and company**: Existing account/membership and tenant concepts; no bypass identity.
- **Setup request**: Recoverable creation intent whose successful replay does not repeat effects.
- **Provider credential**: Existing scoped secret with protected local key custody.
- **Release/checkpoint/backup**: Operational recovery artifacts with compatible versions;
  never independent authorities for business state while the installation is running.

## Success Criteria *(mandatory)*

- **SC-001**: At least 9 of 10 representative nontechnical pilot users reach a usable
  demo company within five minutes of first launch, with download complete and provider
  credentials available or AI skipped, without terminal use or assistance.
- **SC-002**: On the declared minimum supported Mac, at least 19 of 20 warm-data launches
  reach a usable cockpit within 30 seconds with 10,000 source records and matching evidence.
- **SC-003**: All qualified recovery cases retain acknowledged pre-checkpoint business
  data, original source bytes and traceability; failed restore leaves the current data intact.
- **SC-004**: All cross-origin, unauthenticated local, cross-tenant and bootstrap replay
  cases are denied; credential/diagnostic inspections find no plaintext secrets.
- **SC-005**: Empty/demo setup, no-AI operation, provider replacement, backup/restore and
  update recovery pass on every advertised OS version with keyboard-only setup checks
  and all four languages reviewed in both appearances.
- **SC-006**: Every FR/DR receives executable proof or an explicitly reviewed manual
  release procedure before the feature is declared implemented.

## Assumptions and Dependencies

- Proposed first release: Apple Silicon, macOS 14+, 8 GB RAM and 5 GB initially free;
  actual supported versions/capacity must be qualified before advertising them.
- Single OS-user trust boundary; no additional local password. A shared or compromised
  OS login is not treated as a separate security principal.
- User supplies provider credentials; network access is required only for requested
  external services, download/update checks and initial provider testing.
- Apple distribution credentials, clean Mac testing and redistribution/license review
  for bundled dependencies are release dependencies.
- Existing cloud-only entry points are hidden/unavailable locally; this does not alter
  hosted admission or claim public-webhook compatibility for local integrations.
- Product scope was accepted for planning. The proposed account identity schema and
  native security design require architecture review before implementation.

## Review Record

On 2026-09-19 the owner replied “yes, continue” after the concept/spec delivery.
This accepts the proposed scope for technical planning. Architecture/schema approval,
release credentials and implementation verification are separate gates.

## Open Questions

No blocking clarification is required to review this proposal. Dynamic port allocation was explicitly requested by the owner during planning.
Apple Silicon scope,
OS-user trust, optional AI, live-off default and app-running-only background behavior
are explicit proposed defaults for product acceptance. Packaging feasibility and
performance remain verification work, not established facts.

## Requirement Traceability

Planned evidence below is not executed. Plan/tasks must assign exact files and test
identifiers before implementation; this document does not substitute for those phases.

| Requirement | Scenario(s) | Planned test/evidence |
|---|---|---|
| FR-001 | US1.1 | Clean-machine signed-install and unsupported-platform release matrix |
| FR-002 | US1.1–2; US2.3 | First-run UI tests and timed novice pilot |
| FR-003 | US1.2; US3.4 | Bootstrap/session service tests and hosted-policy regression |
| FR-004 | US1.2–4 | Empty/demo/live/replay business-story tests |
| FR-005 | US2.1 | Provider-test contract cases with intercepted synthetic payload |
| FR-006 | US2.2–3 | Consent-copy, offline UI and no-fallback network tests |
| FR-007 | US2.4; US3.6 | Secret lifecycle, Keychain refusal and plaintext leakage tests |
| FR-008 | US3.4 | Origin/Host/session/replay/OS-access negative tests |
| FR-009 | US1.4; US3.1–3 | Persistence, single-instance and forced-exit tests |
| FR-010 | US3.2 | Window-close, menu status, Quit and no-autostart checks |
| FR-011 | US3.3,6 | Child-failure/sleep/lease recovery and health tests |
| FR-012 | US4.1–2 | Signed-update, low-disk, migration interruption and rollback matrix |
| FR-013 | US4.3,5 | Clean-Mac restore, missing original Keychain, corrupt/wrong-key cases |
| FR-014 | US4.4 | Uninstall/reinstall and separately confirmed erase checks |
| FR-015 | US2.1; US3.6; US4.2,5 | Safe-error and diagnostic export content/network assertions |
| FR-017 | US3.1,5 | Pre-bound conventional ports, atomic allocation, restart and exhaustion tests |
| FR-016 | US1–4 | Keyboard, four-language, theme and Inspector navigation review |
| DR-001 | US1.3; US4.3 | Source-byte/hash and provenance equivalence checks |
| DR-002 | US1.2–3; US3.4 | Shared-service parity and architecture review |
| DR-003 | US2.4; US3.4 | Tenant isolation, confirmation and scoped job regressions |
| DR-004 | US3.3; US4.1–2 | PostgreSQL integration, job reuse and migration-role checks |

## Repeatable fresh installation tests (owner request, 2026-09-19)

- **FR-018**: Provide a repeatable developer test cycle that creates a fresh disposable
  app installation, runs it, and removes only that installation after process exit.
  For the current stateless preview, use a unique temporary directory and ephemeral
  WebView storage. Never describe this as a clean macOS-machine test or removal of
  all OS-managed logs/caches. A failed copy must also remove its staging directory.
- Before the persistent product can claim this workflow, scope database, artifacts,
  settings and Keychain items to a unique test installation identity. Cleanup must
  stop its children and remove only that identity's data and credentials. Normal
  uninstall must retain user data as specified by FR-014; explicit disposable-test
  cleanup is a separate authorized operation. No global Keychain or Library deletion.
- Acceptance: two consecutive automated preview runs return successful native proof,
  use distinct installation paths, leave neither installation directory nor child
  process, and preserve the source app. A failed executable must also clean up.

FR-018 clarification: the cycle must also initialize a new PostgreSQL cluster using
that installation's bundled binaries, apply migrations, verify zero tenants, stop it,
and remove its data, artifacts and dump. The current stateless GUI is a separate
step after this check. Full-product uninstall must offer an explicitly confirmed
"Remove app and all local data" action; app-only removal preserves data (FR-014).

### Development onboarding milestone

The first interactive development package may run a disposable empty company with AI
and external connections unavailable. It must clearly state that quitting removes its
local data. This is not the persistent release described by US1–US4. It must use the
real company setup service and product frontend; a static placeholder does not meet
this milestone. Demo/live jobs, credential custody and persistent installation remain
separate implementation tasks and must not be advertised as available prematurely.

### Desktop first-use navigation refinement (owner feedback)

- FR-019: Open the native product window at 1440 × 960 logical pixels, centered
  and constrained by the available display. At desktop widths (at least 1024 pixels),
  the existing sidebar must be visible on first use. Keep resizing and the existing
  compact navigation usable on smaller displays.
- FR-020: Completing company creation opens the company's Home page, with its tenant
  selected and the existing creation notice. Company restoration and explicit
  settings navigation retain their current destinations. This uses shared frontend
  navigation; no desktop-specific business flow is introduced.
- FR-021: Disposable desktop onboarding must expose the same empty company, empty
  Sandbox and international demo choices as the web product. Selecting live demo
  must initialize the canonical profile and start Demo Data through the shared job
  registry, scheduler and worker. All role processes stop before the temporary
  PostgreSQL cluster is removed.
- FR-022: Desktop onboarding may accept an optional Anthropic API key. The explicit
  Create action confirms both company creation and saving that credential for the
  created company. Use the existing tenant AI settings service and encrypted secret
  store; never print, persist in browser storage or put the key in process arguments.
  A disposable test installation removes its database, artifacts and encryption key
  on Quit. Hosted onboarding remains unchanged.
- FR-023: The macOS application must use the canonical web `LogoMark` as its native
  application icon. Package a valid multi-resolution ICNS and declare it in the app
  bundle so Finder, Dock and the app switcher never fall back to a blank placeholder.
- FR-024: Selecting Try demo data in the shared web or desktop setup must select
  Enable live simulation by default. The owner may explicitly turn it off before
  creation; choosing another setup mode clears the live intent.
- FR-025: When no company or deployment Anthropic credential is available, Chat must
  state that AI is not configured instead of producing the legacy V0 placeholder.
  The Chat page must expose a direct AI configuration action, and desktop onboarding
  must present its optional Anthropic credential as a clearly visible input. Existing
  deterministic read and proposal commands remain available without an LLM.
- FR-026: At the standard 1440 by 960 desktop startup size, first-company onboarding
  must show the company name, every eligible start choice, optional Anthropic field
  and Create action without page scrolling. Smaller windows remain scrollable and
  preserve labelled controls, help text and touch targets.
