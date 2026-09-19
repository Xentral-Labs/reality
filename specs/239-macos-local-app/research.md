# Research: macOS Local App

**Date**: 2026-09-19. Repository inspection and primary documentation; native runtime proof is tracked
in verification.md and evidence/.

## D1 — Desktop shell

**Decision**: Plan Tauri 2 with Rust lifecycle code and the existing React product.
Use the system WebView, not a bundled browser. The first implementation milestone
must prove the signed complete dependency bundle before investing in onboarding.
**Rationale**: Reuses Product Web and supplies packaging/capability controls.
**Alternatives**: Swift/WKWebView is the fallback if the spike proves a concrete blocker;
Electron adds a browser runtime; Docker does not satisfy the accepted installation UX.
A framework switch requires updating plan/tasks before continuing, not parallel shells.

## D2 — Packaged runtime

**Decision**: Build relocatable CPython 3.12 and PostgreSQL 17 for arm64 in macOS CI,
with pinned patch releases and checked source checksums in a release dependency lock.
Build a complete wheelhouse, install the existing core, and include migrations,
alembic.ini, catalogs, storylines and static web assets. Sign nested Mach-O code before
the outer app. No production dependency resolution or downloads on first launch.
**Rationale**: Repository core is Python >=3.12; installer currently uses PostgreSQL 17.
Existing wheel force-includes resources but init_db still reads ROOT/alembic.ini, so
packaging must prove installed resource paths rather than assume wheel installation suffices.
**Alternatives**: A system Python/Homebrew dependency breaks clean-Mac setup. Freezing
Python adds import/resource/fork behavior risk; reconsider only after measured bundle issues.

## D3 — Explicit local identity

**Decision**: Add AppUser.authentication_method with values email/local_os and default
email. Desktop local owner has a reserved opaque .invalid email label, an unguessable
unused password hash, active status and NULL email_verified_at. Never claim that an
email was verified. Central account eligibility checks accept local_os only when the
trusted desktop runtime is bound to that exact persisted owner ID. Hosted policy rejects it.
**Rationale**: Existing company_setup calls require_playground_account; tenant_policy
also checks verified email in require_playground_run and practice_company_runs. A
NULL verified timestamp alone fails, while setting it would manufacture verification.
The typed field repeatedly controls authorization, so it meets the proven-schema rule.
**Alternatives**: Global auth bypass violates isolation; fake verified email misstates
identity; per-route exceptions drift. This narrow schema change requires architecture
review before implementation, not another user-facing setup question.

## D4 — Sessions and secrets

**Decision**: Extract session issuance into a shared account service, retaining hashed
session tokens and cookie transport. A native-only IPC request obtains a single-use
bootstrap capability and exchanges it for a session; native code installs the HttpOnly
cookie before showing the loopback product page. No token is exposed to frontend JS.
Use a Keychain-backed master-key resolver for the existing secret vault, supplied to
trusted Python roles through inherited anonymous pipes at process launch.
**Rationale**: Existing web/auth.py owns session issuance; security/secrets.py already
owns tenant-scoped envelope encryption. Desktop custody must fail closed, not use its
existing developer file fallback. Each worker child receives only the key access it needs.
**Alternatives**: Frontend localStorage, command arguments, plaintext .env and a second
provider-key store increase disclosure risk or duplicate authority.

## D5 — Access surface

**Decision**: Serve built product assets and existing API routes on one random loopback
origin inside the desktop adapter. Strict Host/Origin checks, ordinary session checks,
and no native permissions for the product page. Only the separate bundled native
maintenance window has narrowly enumerated native commands. External URLs open in
the default browser and never navigate a privileged WebView. Startup IPC is native-only.
**Rationale**: Same-origin reuse avoids a frontend API fork; loopback is not authentication.
**Alternatives**: Wide remote WebView permissions or trusting localhost are insufficient.

## D6 — Maintenance

**Decision**: User-requested update checks; signed whole releases; quiesced logical
PostgreSQL dump plus artifact/config snapshot; authenticated encrypted portable backup.
Use the existing cryptography dependency with Scrypt-derived archive key and AES-GCM;
version the format, cap KDF/header/resource sizes, authenticate manifest and chunks, and
validate paths/checksums before staging. Never invent a cipher. Include master-key
recovery material inside encryption. Automatic checkpoints use a random backup key
kept in Keychain; portable exports use the user's passphrase.
**Rationale**: The existing installer proves the required data set but exports .env
plaintext; that is not the proposed desktop portable-backup contract.
**Alternatives**: Live filesystem copy is not a consistent database backup. App-only
rollback cannot undo an incompatible schema. PostgreSQL major changes require a
separately qualified migration and are refused by v1's routine updater.

## Primary references

Consulted 2026-09-19. These support capabilities, not compatibility claims for Reality.

- [Tauri sidecars](https://v2.tauri.app/develop/sidecar/): architecture-specific binaries.
- [Tauri capabilities](https://v2.tauri.app/security/capabilities/): isolate native permissions.
- [Tauri signing](https://tauri.app/distribute/sign/macos/): signing and notarization workflow.
- [Apple Developer ID](https://developer.apple.com/developer-id/): direct distribution.
- [PostgreSQL upgrades](https://www.postgresql.org/docs/17/upgrading.html): major-version migration.

All design questions have selected approaches. Clean-machine viability, native cookie
injection, signed child execution and recovery drills remain explicit proof gates.

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

## D7 — Initial AI qualification boundary

Inspection of agent/settings.py::copilot_api_key shows company Anthropic credentials
or a managed ANTHROPIC_API_KEY fallback. The preset list alone is not multi-provider
Copilot support. The first qualified desktop release therefore advertises Anthropic
only, using a release-tested model from that adapter, plus Skip AI. Additional providers
are added only after shared Copilot adapter tests, not a desktop-only implementation.
Desktop removes inherited managed/provider environment fallback and rejects remote
provider use without that company's explicit credential. This is qualification of the
spec's supported-provider choice, not a promise that every existing preset works.

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

The real packaged migration smoke exposed a required contrib component: `pg_trgm`
for migration 0063/global search. The runtime build now compiles and installs this
extension, and layout validation rejects a bundle without its control file and
native module. This reuses the existing search schema; no desktop-specific search
implementation or new business migration is introduced.
