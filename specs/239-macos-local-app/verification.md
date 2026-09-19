# Verification: macOS Local App

**Date**: 2026-09-19
**Scope**: Native socket proof plus bundled runtime build, offline core assembly and
real migration smoke. Full desktop application remains in progress.

| Check | Result | Evidence |
|---|---|---|
| Native Rust socket/state tests | 6 passed (unchanged module) | evidence/spike-rust.txt |
| Complete desktop Python suite | 23 passed | evidence/runtime-pytest.txt |
| Ruff on apps/desktop | Passed | ruff check apps/desktop |
| Rust formatting | Passed | cargo fmt --check --manifest-path apps/desktop/spike/Cargo.toml |
| Spec policy | Passed | python3 scripts/check_spec_policy.py |
| Standalone Python/PostgreSQL build | Passed | evidence/runtime-build.txt |
| Offline core/dependency assembly | Passed; 110 native binaries checked | evidence/runtime-assembly.txt |
| Relocated runtime migration smoke | Passed through 0067_selling_costs | evidence/runtime-smoke.json |
| Private database transport | TCP disabled; socket mode 0700; SCRAM | runtime-smoke.json and runtime-smoke.py |
| Required search extension | pg_trgm 1.6 loaded | evidence/runtime-smoke.json |
| Bundled backup tooling | Dump written and archive list read | evidence/runtime-smoke.json |
| Signed app / clean macOS 14 machine | Not run; release gate remains open | T003/T004 |

## Runtime evidence

CPython 3.12.14 / standalone build 20260901 and PostgreSQL 17.11 are pinned by archive
SHA-256. The Python dependency lock resolves 73 packages, downloaded as checked wheels
and installed offline. The core wheel hash is recorded in evidence/runtime-manifest.json.
The manifest records assembly-time qualification; the subsequent smoke result is the
separate runtime-smoke.json evidence, not a release qualification claim.

The built runtime was moved away from its deleted staging prefix into a path containing
spaces. Its bundled interpreter runs in isolated mode from a temporary working directory,
with no inherited Python/application environment. The disposable PostgreSQL cluster
requires a generated SCRAM password and a private Unix socket; migrations run only in
that cluster. Catalog resources load; scheduler and worker entrypoints import without
running jobs. The smoke confirms zero tenants and removes the test cluster after stopping
PostgreSQL. A custom-format uncompressed dump is readable by the bundled pg_restore;
full business-data restore and encrypted backup remain future tasks.

The initial smoke revealed missing pg_trgm at the existing search migration; the builder
now compiles/installs that contrib module and validates its macOS dylib/control paths.
See runtime-smoke-missing-extension.txt. Other packaging fixes normalize native library
install IDs using Mach-O metadata (including .so files), reject external load/search paths,
and check arm64 plus minimum macOS metadata. Physical testing on minimum macOS is still
required; binary metadata alone does not prove OS compatibility.

Development artifact: `apps/desktop/build/relocated runtime core/` (236 MiB allocated
on this machine), ignored by Git. This is a runtime directory, not a downloadable GUI app.
All native signatures are ad-hoc for local execution, not Developer ID/notarized releases.

## Remaining boundary

T003 now includes runtime/locks/assembly and an ad-hoc Tauri preview app. T004 has
local native-cookie evidence; Developer ID signing and clean-machine proof remain pending. No FR/SC is marked
fully delivered. Identity schema, setup, Keychain integration, production lifecycle,
update/restore UI and release authorization remain separate future work.

All source changes remain in apps/desktop and this feature's artifacts. Existing backend
and frontend source were not edited. Full backend/frontend release suites were not run
for this isolated packaging work and remain required before product integration.


## Native preview (2026-09-19)

Tauri 2.11.5 / tauri-build 2.6.3 compile with an isolated Rust 1.98.1 toolchain.
`package-preview.py` assembles a macOS .app with the relocated Python/PostgreSQL
runtime, a private-pipe endpoint handshake and an ephemeral product WebView.
The HTTP server binds port zero directly. No production identity, schema, company
setup, Keychain storage or business endpoints are introduced by this preview.

Actual WKWebView execution reports `cookie_hidden=true` and
`native_command_denied=true`: native cookie insertion precedes successful authenticated
page loading, JavaScript cannot see the HttpOnly cookie, and attempting the harmless
Tauri app-version command is denied by policy. This is a bounded negative probe,
not a complete authorization/security audit. The initial stricter assertion that no
Tauri internals exist was false: Tauri injects its internal object even without
capabilities. The final test checks effective permission denial instead of object absence.

The CUA inventory recognized the running app, but selecting it repeatedly returned
`Invalid app`; visual layout has therefore not been verified. Browser-executed proof
results were collected through the private control pipe with only boolean outcomes
logged. Automated HTTP tests cover missing cookies, foreign Host/Origin, malformed
proof payloads and response-secret leakage. All 27 desktop tests pass; Ruff and spec
policy pass. App signatures are ad-hoc and local deep/strict validation passes.
The full hosted backend/frontend suites remain outside this isolated spike.

Final packaged executable `apps/desktop/dist/Reality Local.app/Contents/MacOS/reality-local
--verify` returned 0 with both proof booleans true. A subsequent process check found no
remaining preview/probe process. See evidence/native-webview-proof.txt and packaging.md.
The bundle is approximately 266 MiB on this developer Mac.

## Fresh installation and PostgreSQL cycles (FR-018 preview scope)

`test-preview.py --verify --runs 2` passed. Each unique temporary app copy supplied
its own PostgreSQL binary; each initialized a new private cluster, migrated through
0067_selling_costs, reported zero tenants, validated dump readability, stopped the
server and removed cluster/artifact/dump files before the native UI proof. Both UI
proofs passed. Subsequent checks confirmed both installation directories absent,
no process command referring to either directory, and source app/runtime preserved.
See evidence/preview-cycle-postgres.txt. All 30 then-existing desktop tests passed;
the additional partial-copy failure regression also passes (4 cycle-specific tests).
Ruff and spec policy pass. T033's bounded preview work is complete; persistent
product uninstall, Keychain erasure and crash recovery remain unimplemented.

## Local identity foundation (2026-09-19; not packaged or integrated)

New service tests failed at collection before account_policy/desktop_identity existed.
After implementation, 31 identity/company-setup tests passed (106.92 seconds). Expanded
identity/migration/hosted-access/admission/practice/job-registry selection: 57 passed
(26.10 seconds). Tests used disposable PostgreSQL databases; no existing database was
migrated. Migration 0068 backfills email identity and refuses downgrade with local users.
The native app remains the prior proof build. Full backend suite and end-to-end setup
are pending; this foundation is not a completed onboarding feature.

Automatic approval review rejected the proposed shared session extraction before
execution, citing wider hosted-authentication effects not explicitly authorized.
No extraction retry or alternative bypass was attempted. See session-integration-review.md
for the concrete change requiring owner approval. Custom security review checkboxes
remain unchanged and no release qualification is implied by passing targeted tests.

## Approved shared sessions and interactive development app

The owner explicitly approved the shared-session change after the automatic review
request. `account_sessions.issue_session/revoke_session` now serves hosted auth and
the native entrypoint. All 46 focused local/hosted session and admission tests pass.
Five HTTP adapter tests pass, including exact Host/Origin, cookie requirement, denied
hosted auth/admin routes and actual confirmed company creation/replay. All 31 desktop
packaging/port/fresh-copy tests pass. The product frontend builds successfully.

The updated `Reality Local Setup.app` contains the current core and migration 0068,
real frontend, bundled PostgreSQL and a disposable development runtime. It starts a
fresh private cluster, applies migrations in a separate preparation process, issues
an actual hashed UserSession through the approved service and opens /app. This reuses
the real company setup and workspace; it is no longer just a diagnostic screen.
Native WKWebView --verify exits 0 with both cookie secrecy and command-denial proofs.

The actual browser acceptance test uses the packaged backend without mocked company
responses: company name -> confirmed creation -> one company in /api/v1/bootstrap ->
workspace visible. Both screenshots were inspected. After the test exits, the private
cluster directory is absent. See onboarding-browser.txt, onboarding-native-proof.txt,
local-company-setup.png and local-company-open.png.

This milestone supports a disposable empty company only. AI credential entry, demo/live
jobs, persistent installation, Keychain custody and release qualification remain open.
The screen explicitly warns that quitting removes test data. Full-suite verification
is tracked separately; no full-product acceptance criterion is marked complete here.

Two consecutive fresh installations of the interactive build also pass native
verification and remove their app copies (onboarding-fresh-cycles.txt). The final
interactive bundle is approximately 277 MiB. Backend full-suite attempts under high
parallel load exposed two demo-seeding handler timeouts; both passed when rerun alone
(2 passed in 42.93 seconds). The complete suite is being repeated with two workers.
These timeouts were not suppressed and their production deadlines were not changed.

Project-wide Ruff currently reports 13 import-order findings in Global Search
benchmark/migration/test files outside this desktop change. The desktop and modified
identity/authentication files pass Ruff when run from the backend project directory.
Those unrelated files were not reformatted. See evidence/onboarding-lint.txt.

### Full backend sweep (2026-09-19)

`backend-session-final.txt`: 3272 passed, 9 skipped, 13 failed. This is not a green
release gate. Seven failures report tenant-isolation catalog drift in concurrently
changing costing services; one reports an inventory-generation import failure.
Four fail on shared handler timeouts; one demo settlement batch has unexpected
counts. These results require isolated follow-up before marking the full backend
verification complete. Focused identity/session and desktop HTTP checks recorded
above passed; the complete-suite result must not be presented as passing.

### Web-parity live demo and optional Anthropic setup

The packaged `Reality Local Demo Live.app` passed the real bundled browser flow:
all web setup choices were present; international demo initialization completed in
the shared worker; the shared scheduler materialized live jobs; Demo Data reported
`running`; retained Payments were non-empty; and the optional Anthropic key was saved
through tenant AI settings with only configured metadata returned. The key never
appeared in process arguments or test output. The browser reached Home with the
desktop sidebar visible, then closed stdin; the runtime stopped scheduler and worker,
stopped the API, stopped PostgreSQL and removed the private test root.

Native verification also passed (`cookie_hidden=true`,
`native_command_denied=true`) and removed its disposable app copy. Focused backend
verification passed: 29 tests passed and 2 skipped across desktop HTTP, the separate
scheduler/worker process contract and AI secret custody. Ruff passed for every changed
Python file; the frontend production build, 29 navigation contracts, four install-copy
tests and spec policy passed. The earlier complete-backend sweep remains non-green for
the unrelated/concurrent failures already recorded above, so release qualification
is still open.

### Native application icon

`build-icon.py` reproducibly renders the exact three cubic paths from the web
`LogoMark` on the web brand color `#635bff`. The 1024 PNG was visually reviewed.
The packaged ICNS expands to eight macOS representations from 32 through 1024 pixels.
`CFBundleIconFile` resolves to `Resources/RealityLocal.icns`; deep strict ad-hoc
signature verification passed. The icon-bearing bundle passed native cookie/command
proof, stopped all children and removed its disposable installation. The verified
artifact is `apps/desktop/dist/Reality Local Demo Live Icon.app`.

### First-use window and Home refinement

Artifact: `apps/desktop/dist/Reality Local Home.app` (development, ad-hoc signed).
Native build, frontend production build, 29 navigation contracts, four disposable
copy tests and spec policy passed. `home-native-proof.txt` confirms hidden session
cookie and denied native commands with automatic cleanup. The real bundled browser
flow passed at 1440 × 960: first company → `/app?tenant=…` → visible primary sidebar
and Home summary controls. Screenshot `evidence/local-company-open.png` was reviewed:
Home and navigation are visible; the company settings/danger zone is not the landing
page. The native builder centers and limits startup size to the display work area.

Creation explicitly passes the Home destination option through both first-company
and subsequent-company forms. Restoration retains the existing default. The already
running user test was not replaced or stopped. The helper now defaults to this new
artifact. This milestone does not enable demo/live workers or AI credentials and
does not resolve the full-backend sweep failures recorded above.

### Demo default and missing-AI guidance

The shared setup browser contract now proves that selecting Try demo data checks live
simulation automatically, that the owner can clear it, and that selecting demo again
restores the checked default. The real packaged desktop acceptance passed with that
default and reached a running Demo Data source with retained payments. The optional
Anthropic field is a visible bordered password control with a provider-shaped hint.

The Copilot service regression proves that an arbitrary question without a company or
managed key returns explicit AI configuration guidance and never the legacy V0 text.
The read payload exposes only `ai_configured`; Chat renders the existing localized
not-configured status and links to the existing AI configuration view. Six focused
Chat tests, Ruff, the frontend production build and JavaScript syntax checks passed.
The verified artifact is `apps/desktop/dist/Reality Local Demo Ready.app`.

### No-scroll first use

At 1440 by 960 the real packaged browser acceptance now asserts that document scroll
height does not exceed the viewport and that Create company is visible. Responsive
spacing keeps all three choices, their descriptions, the optional Anthropic field and
the action on screen. The desktop-only temporary notice has an explicit 37 pixel box,
and onboarding subtracts that height instead of adding overflow. The complete live-demo
acceptance and cleanup passed. The artifact is
`apps/desktop/dist/Reality Local Demo Ready No Scroll.app`.
