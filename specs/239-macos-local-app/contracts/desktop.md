# Desktop Interface and Security Contract

## Native shell boundary

Two windows: bundled maintenance/setup shell and unprivileged loopback Product Web.
Product Web has no shell/file/Keychain/IPC capabilities. Native commands are individually
allowlisted for the bundled window: runtime status/start/quit, choose backup file,
backup/restore preview/confirm, update check/preview/confirm and diagnostic export.
No arbitrary command, URL-fetch proxy, SQL execution or arbitrary-path read/write.
Validate canonical user-selected paths, reject symlink traversal and archive traversal.
External navigation always leaves the WebView; new-window requests cannot inherit privileges.

Native supervisor owns an inherited control channel to the desktop Python entrypoint.
At launch send configuration and secret custody through pipes, not argv/environment
or temporary files. Protocol is framed, size-bounded and versioned. It carries no general
business command interface. Worker children use the same key-provider contract without
inheriting open database connections. Unknown message/role/version is a hard failure.

## Identity exchange

Native startup requests a cryptographically random single-use 256-bit capability,
valid at most 30 seconds and bound to this runtime generation. Exchange is native-only
on the inherited channel; only its hash is retained while pending. Consumption and
session issuance are serialized. Persist the existing hashed UserSession, return the
raw token only over the channel to native code, then set an HttpOnly, SameSite=Strict,
host-only cookie in the product WebView before navigation. Rotate on each launch;
revoke desktop-issued sessions on normal Quit. Crash-expired capabilities cannot replay.

The local origin is `http://127.0.0.1:<allocated-port>`; exact Host including port is
required. State-changing HTTP requests require that exact Origin; do not admit null,
localhost aliases or ambient development origins. Use session authentication on all
business reads as well. Health answers contain no company information. Local HTTP
cookies cannot use the production HTTPS Secure policy; hosted cookies retain it.
Native cookie installation and WebView-origin behavior are mandatory spike evidence.

Account bootstrap is a shared service restricted to trusted desktop context, never
an unauthenticated HTTP signup endpoint. It creates a non-admin local_os account;
central account policy adds the exact owner binding while tenant membership remains
mandatory. Disable public signup/login/email verification/invitation/admin entrypoints
in this adapter. Hosted deployment never accepts desktop capability or local_os identity.

## Setup and AI

Only public presentation/status data exists before owner bootstrap. UI setup stores
non-secret progress locally and submits a stable request ID through ordinary authenticated
company setup. Confirm name/environment/demo/live intent before mutation. Tenant ID comes
from the confirmed shared result, not a native default or frontend URL assumption.
LLM key remains transient in the password input; save only through the current owner-only
AI service after company creation. On interruption the user may need to re-enter an
unsaved key; do not persist a draft secret. Clear input buffers after submission.

Desktop no-AI is an explicit runtime policy for settings without a configured provider
key: do not interpret the existing `local` provider as an on-device model or hosted
fallback. Provider/model test uses fixed synthetic content, no tools, bounded tokens,
10-second timeout, no automatic retries, no redirects to a different credential host.
Return stable codes: ready, credentials_invalid, model_unavailable, rate_limited,
network_unavailable, provider_error. Never forward raw provider errors containing secrets.

## Operational contracts

Single runtime lock; occupied ports allocate another port safely. Closing window retains
menu presence, Quit stops children. Sleep/wake preserves existing queue semantics.
No REALITY_BOOTSTRAP_TENANT_NAME or platform-admin auto-bootstrap on desktop launch.
Migration is an explicit exclusive release step; API/job role startup checks schema only.

Backup requires writer quiescence across API, scheduler, worker and supported CLI access.
Export includes all tenants in this single-owner installation and says so in preview.
Restore validates encryption, paths, sizes, schema and artifact hashes into a new generation;
creates a checkpoint before replacing nonempty data; imports recovered master key into
Keychain only as part of the staged switch. Invalidate old sessions and issue a new local
session. Resume external-source schedules only after explicit restore review to avoid
replaying effects on the original and restored Mac; preserve unresolved outcomes.

Before updating show old/new release and maintenance impact. Reject different PostgreSQL
major, unsupported schema, bad signature or insufficient staging/checkpoint space before
changing active data. Migration failure restores matched checkpoint while writers remain
blocked. Never downgrade data silently after successful reopening. Uninstall retains data;
erase requires typed installation-name confirmation and leaves exported backups untouched.

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
