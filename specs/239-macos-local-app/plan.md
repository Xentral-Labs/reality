# Implementation Plan: Reality Local for macOS

**Feature**: `239-macos-local-app` | **Date**: 2026-09-19 | **Spec**: [spec.md](spec.md)
**Checkout**: `234-inventory-cost-contribution`; no branch switch or unrelated edits.
**Language**: English for repository artifacts and review evidence.
**Status**: Planned; product scope accepted. Identity/schema and native security review
must precede production implementation. No release capability is claimed.

## Summary

Package the existing product in a Tauri 2 macOS shell with pinned Python/PostgreSQL
runtimes. Reuse services, tools, demo and jobs. Add narrowly scoped desktop identity,
OS key custody, supervised lifecycle and maintenance. First prove relocatable signed
packaging; then implement test-first in the sequence in [tasks.md](tasks.md).

## Technical Context

**Languages**: Python 3.12, TypeScript/React, Rust for native lifecycle.
**Dependencies**: Existing SQLAlchemy 2, Alembic, Pydantic v2, FastAPI, cryptography;
Initial qualified AI: existing Anthropic Copilot adapter plus explicit no-AI mode;
other presets hidden until shared adapter qualification. Tauri 2 and macOS Security/WebKit integration. Pin exact dependency versions in lockfiles.
**Storage**: PostgreSQL 17, file artifact backend, Keychain master key; OS-user-private
operational manifests. Decimal/UTC/opaque IDs remain unchanged.
**Testing**: pytest on PostgreSQL, Rust unit/integration tests, frontend scripts/browser
checks, native clean-machine scenarios and notarized-package qualification.
**Target**: Apple Silicon/macOS 14+; 8 GB/5 GB baseline subject to release evidence.
**Scale**: One OS owner; one company initialized, existing multi-company isolation retained.

## Constitution Check *(blocking gate)*

Design checks pass; this table does not certify implementation or substitute for human
review of the proposed schema/security change. Rechecked after contracts/data model.

| Principle | Evidence in this plan | Result |
|---|---|---|
| Source → Evidence → Reality | Existing services plus byte/provenance backup equivalence | PASS |
| Reality owns operational state | No domain/document state additions | PASS |
| Proven schema only | One authentication_method field repeatedly gates account eligibility; data-model.md | PASS |
| Tenant + shared service boundaries | Desktop bootstrap/session service; unchanged membership checks | PASS |
| Spec/test traceability | Every FR/DR has test and implementation task; tests precede code | PASS |
| Explainable web behavior | Same cockpit/Inspector; desktop wrapper has no business logic | PASS |
| Received values not recomputed | Copy original database/artifact values; no new calculations | PASS |
| Smallest coherent design | Research rejects Docker/system runtimes/global auth bypass; one shell | PASS |

## Repository Structure and Layer Changes

Paths below describe the target. The isolated socket spike and runtime preflight now exist;
see verification.md for the exact implemented boundary.

- `apps/desktop/src-tauri/src/`: `lib.rs`, `supervisor.rs`, `ipc.rs`, `keychain.rs`,
  `webview.rs`, `maintenance.rs`; native lifecycle only.
- `apps/desktop/src-tauri/`: `Cargo.toml`, `tauri.conf.json`, `capabilities/maintenance.json`.
- `apps/desktop/scripts/`: `build-runtime.py`, `package.sh`, `qualify.sh`, dependency lock.
- `apps/desktop/tests/`: package, lifecycle, backup and release qualification harnesses.
- `packages/reality-core/src/reality/domain/desktop.py`: pure installation/maintenance
  state and manifest validation, independent of native UI and storage adapters.
- `services/desktop_identity.py`, `services/account_sessions.py`, `services/account_policy.py`:
  owner/bootstrap/session and central identity eligibility. Existing `company_setup.py`,
  `tenant_policy.py`, `jobs/handlers/demo_data.py` consume that policy where needed.
- `security/secrets.py`, new `security/key_provider.py`: custody injection retaining vault.
- `services/desktop_maintenance.py`: backup manifest/validation/quiescence orchestration.
- `desktop/runtime.py`, `desktop/control.py`, `desktop/storage.py`: trusted process/IPC/backup adapters.
- `web/desktop.py`, `web/auth.py`, `web/app.py`: explicit local adapter and shared session
  extraction without changing hosted behavior. New desktop entrypoint bypasses legacy
  bootstrap side effects and exposes the same application routes/static assets.
- `db/core.py`, new migration `*_desktop_identity.py`: account provenance only.
- `apps/web/src/desktop/LocalSetup.tsx`, `LocalSettings.tsx`, `desktopCapabilities.ts`:
  capability-driven setup/no-AI/recovery presentation. Existing shared localization and
  component language remain authoritative; no copied operational pages.

Dependency order: pure domain rules -> shared services -> tool surfaces if needed ->
Python/native/web adapters. Desktop lifecycle operations are not agent business tools;
no new Chat mutation bypass. Any change to executable tools/catalogs triggers docs generation.

## Design

### Reality flow

Confirmed company setup -> canonical demo sources -> existing interpretation -> Evidence
and Reality. Empty setup creates no synthetic records. Live source uses shared jobs and
durable completion marker. Backup restores records and original artifact bytes exactly;
projection/readiness data is never new business authority.

### Service and adapter flow

See [research](research.md), [data model](data-model.md) and [contract](contracts/desktop.md).
Native shell supervises packaged roles. Trusted IPC establishes owner session; product
requests flow through ordinary HTTP adapters/services and tenant checks. Existing
web/auth session writes move into account_sessions so desktop and hosted transport share
one issuance/revocation implementation. Native code never writes business rows.

### Data and migration impact

One additive account authentication_method column, default email, constrained enum values.
No business table change. Human review explicitly covers local identity policy and SQL
selection predicates. Release controller applies Alembic before API/job startup. Existing
init_db resource assumptions require packaged migration tests. Downgrade refuses local
accounts; rollback pairs database/data and app versions. See data-model.md for state files.

### Failure, security, and tenant behavior

Exact loopback origin, native-only capability exchange, host-only HttpOnly cookie, no
product-page native capabilities, OS-private files and fail-closed Keychain. Treat same-user
malware as outside the promised trust boundary. Do not weaken hosted auth. Existing owner,
tenant and Chat confirmation checks still apply; local mode does not grant platform admin.
Maintenance blocks writers; random ports, stale locks, bounded restart and stage journals
make crash recovery explicit. Restore does not blindly resume external schedules.

## Test Strategy and Traceability

[Tasks coverage](tasks.md#requirement-coverage) assigns every requirement to exact tests
and implementation files. Initial proofs must fail because native packaging, desktop
identity/custody/lifecycle and recovery adapters do not yet exist. Capture meaningful
red-to-green results; do not add tests that merely mirror file existence.

| Area | Planned proof | Requirement coverage |
|---|---|---|
| Package and baseline UX | apps/desktop/tests/test_package.py; qualify.sh | FR-001,002; SC-001,002 |
| Identity/setup | core tests/test_desktop_identity.py, test_desktop_setup.py | FR-003,004; DR-001,002,003 |
| Provider/custody | core tests/test_desktop_ai.py, test_desktop_secrets.py | FR-005,006,007 |
| Security/lifecycle | core tests/test_desktop_http.py; desktop/tests/test_lifecycle.py | FR-008,009,010,011,015; DR-004 |
| Maintenance | core tests/test_desktop_maintenance.py; desktop/tests/test_recovery.py | FR-012,013,014; DR-001,004 |
| Presentation | apps/web/scripts/desktop-onboarding-browser.mjs | FR-002,006,016; SC-005 |

Full backend PostgreSQL suite, Ruff, frontend build/i18n and spec policy remain required;
add migration upgrade/downgrade checks, native cargo test, clean-Mac signed install,
sleep/wake and crash drills. Record actual hardware/OS and never substitute development
launches for Gatekeeper qualification. SC-001 requires ten pilot users; cannot self-certify.

## Rollout and Rollback

Development spike -> internal unsigned build -> signed internal pilot -> qualified public
release. No public publication in this task. Own desktop CI release workflow only after
native dependency/signing proof. Distribution signing/notarization credentials are external
release prerequisites, not permission to acquire an account or accept Apple agreements.

Routine v1 updates retain PostgreSQL major 17 and reject major changes. Stop writers,
validate checkpoint, stage complete release/data generation, migrate, validate and atomically
switch. Keep prior generation until success. A failed migration never launches old code
against new schema. After business writes resume, checkpoint restore warns about data loss
and requires explicit confirmation. App removal preserves Application Support and Keychain;
confirmed erase removes only this installation and its custody after backup opportunity.

## Review Risks

- Local identity needs consistent Python and SQL authorization; one missed verified-email
  predicate can break demos/jobs or open access. Hosted-regression proof is mandatory.
- WebView cookie insertion and nested native code signing need physical-Mac proof.
- Backup portability requires recovering the vault master key, not only database rows.
- Python process spawning/resources must function outside the source checkout.
- Current Mac cannot invoke make/Xcode tooling until its license is accepted; no acceptance
  is performed by this planning work. Direct Python spec validation remains available.

## Complexity Tracking

| Constitution exception | Why needed | Simpler alternative rejected | Approval |
|---|---|---|---|
| None | — | — | — |

The local account column and native runtime are justified additions, not Constitution
exceptions. Their architecture review is tracked in T001 before product implementation.

## Dynamic endpoint allocation (FR-017)

PostgreSQL uses a private Unix socket directory with mode 0700 and TCP listening
disabled; choose a short per-user runtime path to stay within Unix socket path limits.
The persistent database still lives under Application Support. Authenticate database
roles and never use a shared writable socket directory.

For Product Web/API and each optional role health listener bind 127.0.0.1:0 (and only
explicit loopback IPv6 when needed). The process that serves the socket binds it once,
reads getsockname/server_port and reports the endpoint through the inherited trusted
control pipe before readiness. Keep that bound socket open; either serve it directly
or pass the live descriptor to the serving child. Never probe, close and rebind a port.

Scheduler/worker health endpoints bind first, report their actual addresses, then API
startup receives those URLs. Product Web uses the one actual API/static origin for
requests, exact Origin/Host policy and native cookie setup. Bind before setting these
values, with readiness withheld until configuration completes. Runtime endpoints are
volatile, never persisted as future configuration or included in portable backups.
Supervised role restart allocates fresh endpoints and updates consumers atomically;
API-origin replacement recreates the product session/window before allowing requests.
Late reports from an old runtime generation are discarded.

One installation lock prevents duplicate startup; different OS-user installations
use independent private sockets and OS-selected ports. The dynamic-port mechanism
changes no hosted defaults. Allocation exhaustion fails with a safe error after at most
three attempts, closes partial listeners and preserves data. No scanning thousands of
ports, killing foreign processes or requesting port entry from users.

Proof: occupy ports 5432/54329/8000/8001/8080/8081/5173 with sentinel listeners, start
Reality and assert all sentinels remain usable; test two isolated runtime directories,
restarts, stale endpoint reports and injected EMFILE/EADDRINUSE failures. Native tests
must exercise actual bound sockets, not mocked “free port” lookups.

## Isolated packaging proof harness

Before adding Tauri dependencies, `apps/desktop/spike/Cargo.toml` compiles the intended
supervisor module against the standard library only. Python tests launch separate native
probe processes and verify actual bound listeners. `scripts/runtime_audit.py` checks
core wheel resources, escaping symlinks and absolute non-system Mach-O dependencies.
Neither harness is a second business runtime. Native framework integration remains T003/T004.

## Runtime build refinement (2026-09-19)

Use the pinned arm64 CPython 3.12.14 install-only distribution from Astral's
python-build-standalone release 20260901 instead of maintaining our own CPython
dependency toolchain. Verify the publisher release SHA-256 and preserve bundled
licenses. Build PostgreSQL 17.11 from the official checked source archive with
TCP disabled at runtime; omit optional readline/ICU/zlib build dependencies in
the first spike. Fix bundled Mach-O library references relative to each loader,
then ad-hoc sign modified binaries for local tests. Developer ID signing remains
a separate release gate. This changes build mechanics, not supported product scope.

Reference: https://github.com/astral-sh/python-build-standalone and
https://www.postgresql.org/docs/17/install-make.html (consulted 2026-09-19).
Exact download URLs and SHA-256 values live in scripts/runtime-dependencies.lock
under apps/desktop. PostgreSQL minor release is pinned, never resolved at app launch.

Runtime assembly tools now live in `apps/desktop/scripts/build-runtime.py`,
`assemble-runtime.py`, `runtime-smoke.py` and `smoke-core.py`. The exact source
archives and offline Python packages are hash-pinned in the adjacent lockfiles.
Build PostgreSQL's `contrib/pg_trgm` because the existing core migrations require
it. The smoke owns a disposable cluster and tests real migrations; it does not
change startup migration ownership in the product.

## Fresh preview test cycle extension

Owner requests repeated fresh install/test/uninstall cycles. Implement a developer CLI
`apps/desktop/scripts/test-preview.py`: create a unique private temporary directory,
copy the existing preview .app preserving symlinks, launch its executable directly,
wait for Quit (interactive) or bounded --verify, and remove the temporary copy in
finally. Reject unexpected bundle identity and symlinked input root. Do not change
production runtime or data paths. Tests precede implementation: independent copies,
cleanup on success/failure and source preservation. Actual native verification runs
_twice_ to exercise relocation and session renewal. Constitution check: PASS; no domain,
identity/schema, business service, persistent data or hosted behavior is changed.
Persistent product test profiles remain unimplemented and must gate future reuse.

Owner clarification: PostgreSQL data must also be fresh. Each preview test cycle now
runs the existing migration smoke with the copied runtime and a new cluster inside
that cycle's private directory. The smoke stops PostgreSQL and removes the cluster
before opening the stateless UI. This is a database packaging/reset check, not a
persistent company connected to the preview. Assert no cluster directory remains.

## Onboarding implementation refinement

The owner requested development integration after seeing the proof window. Release
qualification remains open. Bind desktop identity through trusted SQLAlchemy session
`info` (`desktop_installation_id`, `desktop_owner_id`), supplied by the native runtime's
session factory, never by request headers/body or ambient hosted environment. Central
Python and SQL predicates require exact owner matching and active local_os status.
Bootstrap is a service protected by a transaction advisory lock per opaque installation;
it never marks an email verified or creates admission applications. Service tests cover
replay, corrupted owner binding, hosted denial, company replay and hosted regression.

### HTTP adapter integration sequence

Before packaging the interactive flow, test a desktop ASGI wrapper around the existing
product app: exact loopback Host/Origin, authenticated local owner for static and API
requests, public hosted auth/admin endpoints denied, frontend assets from the bundled
build, and unchanged company setup routes. The mounted hosted app's lifespan must not
run legacy bootstrap or migrations. Inject the trusted session factory at process
startup; tests use isolated transactions. No frontend business logic is duplicated.

The first native integration is explicitly disposable: reuse the fresh socket-only
cluster harness, run migrations in a separate preparation process, then launch the
existing product through the authenticated desktop wrapper. Pass database settings
and installation identity on stdin, never command arguments; use a sanitized child
environment. The API serves the real frontend at /app. For this bounded development
milestone restrict setup to an empty business company and disable AI/connection writes
until custody/jobs are implemented. Parent-pipe closure stops API before PostgreSQL.

### First-use navigation refinement

Use the native window builder's initial dimensions and centering; retain OS sizing
constraints and user resizing. Pass the existing Home destination flag from the
creation callback, preserving restoration's settings destination. Extend the real
bundled onboarding browser check to assert Home and visible sidebar at 1440 × 960.
Build the native binary and frontend, then package a new artifact without touching
the user's running disposable installation. Constitution check: presentation only;
no schema, authority, service or confirmation changes.

### Web-parity demo and optional AI setup

Remove the development adapter's artificial company-choice filter. Run the existing
`ProcessLoop` scheduler and worker as separate supervised children with trusted local
identity passed through private stdin, including each bounded handler subprocess.
Neither role runs migrations. Stop scheduler and worker before API and PostgreSQL.
The frontend conditionally shows an optional Anthropic password field only when the
desktop adapter advertises it, then calls the shared tenant AI settings API after the
company is ready. The temporary artifact root contains the encryption key and is
deleted with the disposable database. Validate a real live demo, retained payments,
running Demo Data state, configured-key metadata, Home navigation and full cleanup.

### Native application icon

Render the existing web `LogoMark` geometry and brand color into a reproducible 1024
pixel source asset and a multi-resolution ICNS. Copy the ICNS into Resources, declare
`CFBundleIconFile`, and list both assets in Tauri configuration for future signed
bundling. Verify the bundle declaration, ICNS contents, signature and native launch.
This changes presentation only and introduces no domain, service or schema behavior.

### Demo default and missing-AI guidance

Keep the creation API default unchanged for compatibility. The shared setup form sets
live intent when the user selects demo, so hosted web and desktop receive identical
behavior and the owner can still clear the checkbox. Expose only a boolean AI-ready
state in the existing Copilot read payload. Chat links an unconfigured company to the
existing AI settings view; the service replaces the legacy placeholder only when no
company or managed provider key exists. Deterministic shared-service answers and
confirmed proposals remain unchanged. No schema or secret value crosses the API.
Constitution check: all eight principles PASS.

### No-scroll first use

Use responsive CSS only: reduce decorative spacing and option whitespace at desktop
window widths while keeping the existing controls, descriptions and minimum input
heights. Keep the page scroll fallback for smaller viewports. No application state,
service, schema or confirmation behavior changes. Constitution check: PASS.
