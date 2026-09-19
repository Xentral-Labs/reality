# Reality Local for macOS — Product and Delivery Concept

**Date**: 2026-09-19
**Status**: Product scope accepted for planning on 2026-09-19; see plan.md for the selected technical design.
**Specification**: [239 — macOS Local App](spec.md)

## Recommendation

Ship a downloadable Reality.app in a signed, notarized disk image. It contains the
existing Product Web, Reality Core, private PostgreSQL runtime, scheduler and worker.
A small desktop shell owns their lifecycle and displays the existing product.
The user installs no Docker, Python, Node, database, terminal tooling or cloud account.

Start with one macOS user on one Apple Silicon Mac. Proposed qualification baseline:
macOS 14 or later, 8 GB memory, and 5 GB free space before business data grows. These
are release targets to validate on physical hardware, not measured compatibility claims.
Intel, Windows, Linux desktop packages and team hosting are later decisions.

“Local” describes storage and execution. A configured external LLM still receives
selected prompts, tool context and results. The product must say this before the first
request; provider usage is billed by that provider. No Reality-hosted LLM fallback,
cloud login, telemetry upload or business-data synchronization is enabled implicitly.

## First-run experience

1. Download, drag Reality to Applications and open it normally.
2. Choose **Try demo data** or **Start my company**. Empty company is the default;
   show an editable company name, with a useful suggestion for the demo choice.
3. Optionally enable **Live demo activity** on the demo path. It defaults off and
   means activity while Reality is running. No real integrations are connected.
4. Choose an LLM provider and enter its API key. Offer a recommended release-tested
   model and an advanced model selector. Explain data transmission and possible
   provider charges. **Set up AI later** is equally available.
5. Review the company, demo/live choice and AI destination, then click **Start Reality**.
   This confirms company creation and the selected demo source scope. An explicit
   connection test sends only synthetic content and is separately labeled.
6. Open the existing cockpit, with an obvious first question and full Inspector links.
   Without AI, the operational UI remains usable and Chat explains how to enable it.

Language and time zone come from macOS, remain editable, and are presentation only.
No email verification, password, SMTP server, database URL, port, model endpoint or
hosting domain is required in the normal setup. Setup failures retain non-secret
choices and resume the same company request rather than create a second company.

## Reuse and actual gaps

| Area | Existing evidence | Required addition |
|---|---|---|
| Business application | `apps/web`, `packages/reality-core`, `docs/ARCHITECTURE.md` | Package static product assets and shared runtime; no desktop business fork |
| Self-host operations | `installer/`, spec 187 | Reuse operational lessons; existing scripts require Docker and do not satisfy desktop setup |
| AI configuration | `agent/settings.py`, `security/secrets.py` | Guided provider validation; desktop master-key custody; explicit no-AI state |
| Identity | `web/auth.py`, `docs/WEB_SPEC.md` | Desktop-only owner bootstrap and trusted local session establishment |
| Company/demo setup | Spec 146 and `docs/features/company-setup-demo.md` | Invoke confirmed shared setup; preserve idempotency and durable live completion marker |
| Background jobs | `apps/scheduler`, `apps/worker`, specs 147/149/179 | Supervise existing roles and route private health checks |
| Distribution | Container-based deployments | Native dependency builds, signing, notarization, release qualification |
| Recovery | Installer database/artifact/config backup | Desktop backup UI, portable secret recovery and migration-safe updates |

Repository inspection shows existing provider presets and tenant-scoped encrypted
secrets. It does not establish that every configured model is available or tested.
The desktop release must qualify its advertised provider/model combinations instead
of treating all existing strings as compatibility evidence. The existing provider
value `local` maps to Reality-managed behavior; it is not proof of an on-device LLM.

## Proposed technical shape

```text
Reality.app — window, setup, lifecycle, Keychain bridge
    | authenticated local session
    v
Existing Product Web + Web/API adapter
    | shared tenant-scoped application services/tools
    +---- private PostgreSQL
    +---- local source-artifact directory
    +---- selected external LLM (explicit setup)

Existing scheduler -> existing PostgreSQL job queue -> existing worker
```

Use a thin Tauri shell as the leading candidate because it can package external
binaries and reuse the existing frontend. Compare it with a small Swift/WKWebView
shell in a bounded packaging spike before the technical plan fixes a framework.
Tauri documentation confirms sidecar packaging, not that our complete Python and
PostgreSQL dependency set already runs inside a signed app.

Bundle a pinned Python runtime and its dependencies, the matching PostgreSQL binaries,
migrations, static assets and application roles from one repository revision.
Do not download executable dependencies at first launch. A release manifest records
versions, checksums and licenses. Packaging must include native dependencies and
resource paths used by the core; the production app cannot depend on a source checkout.

Keep mutable data under the macOS user's Application Support directory, outside the
signed app bundle: database, source artifacts, non-secret configuration and bounded
logs. Keep the existing encrypted secret vault authoritative. Store its master key
in macOS Keychain and resolve it through a reviewed backend bridge; do not introduce
a second LLM credential store. Plaintext keys must not enter command-line arguments,
frontend persistence, logs or diagnostic bundles. Keychain denial leaves a recoverable
locked state and never silently generates a replacement key.

PostgreSQL uses a private user-owned socket or authenticated loopback endpoint, with
no LAN exposure. The local API binds only to loopback and still requires a session.
Use a single-use, short-lived native bootstrap capability to obtain the ordinary
owner session. Keep the capability out of URLs and logs; validate allowed Host and
Origin, reject cross-site requests and unauthenticated local clients. Loopback alone
is not authentication. Arbitrary web pages must not be able to initialize an owner,
read tenant data or confirm actions. Exact IPC/session mechanics require threat review.

Desktop identity is an explicit deployment policy, isolated from hosted signup and
admission. Create one local owner through an application service; continue ordinary
account, tenant membership and authorization checks afterwards. No fake verified email,
global auth-disable flag or browser-supplied tenant authority. The unlocked macOS
account is the v1 trust boundary; shared OS accounts and compromised same-user processes
are outside that isolation claim. More companies may use existing capabilities, but
only one company is created during first run.

Keep MCP, public site, invitation delivery, inbound webhooks and LAN listening disabled
in v1. Do not replace the current authenticated HTTP MCP with a new local transport.
Optional integrations that require public callbacks need later scoped design; outbound
operations can use existing supported paths after ordinary user configuration.

## Lifecycle and background behavior

Acquire a per-installation lock. A second launch focuses the existing window. Start
PostgreSQL, check schema compatibility, and run an explicit exclusive release/migration
step before starting API, scheduler and worker. These roles never run migrations at
startup. The app only reports ready when database, API and both background roles are
healthy; LLM availability has a separate state.

Closing the window keeps Reality running with an obvious menu-bar presence; Quit stops
new work, allows bounded in-flight completion, then shuts down application roles and
database. The first close explains this behavior. No login item or background daemon
is installed implicitly. Sleep and Quit pause execution; wake/relaunch use the existing
queue leases, recovery and coalescing rules. Do not promise activity while the Mac is
asleep or reconstruct every missed demo interval. Unexpected child failure enters a
visible recovering/degraded state with bounded retries, never an infinite restart loop.

## Updates, backups and removal

V1 offers user-initiated update checking and installation with version/release notes.
Verify publisher identity and artifact integrity before execution. Install only an
entire compatible release. Before migration: stop writers, check disk capacity, produce
and verify a recoverable checkpoint including database, source artifacts, configuration
and a protected recovery copy of the master key. Keep the prior compatible app.

A code-only rollback after a schema change is unsafe. Failed updates restore a matched
app/schema/data checkpoint before new writes are allowed. Successful updates reopen
for business; any later restore explicitly warns that post-checkpoint work is lost.
PostgreSQL major upgrades use an explicit qualified upgrade procedure, not replacement
of binaries against an old data directory. Interrupted updates must have a durable,
recoverable stage record.

Provide **Back up** and **Restore backup** in Settings. Portable backups are encrypted
with a user-provided recovery passphrase, include the protected vault recovery material,
and restore on another supported Mac without access to the original Keychain. Warn
that a forgotten passphrase cannot be recovered. Restore validates versions/checksums,
stages data before switching, asks before replacing a nonempty installation and retains
a pre-restore checkpoint. A same-disk checkpoint is recovery protection, not off-device
backup; the user chooses an export destination. Never copy live database files casually.

Deleting Reality.app keeps business data. A separate, explicit **Delete local data**
flow previews the affected installation and backups, offers export, and requires
confirmation. External exported backups are never silently removed.

## Delivery slices and feasibility gates

These are conceptual work packages, not implementation tasks or authorization to code.

1. **Packaging proof:** install a signed prototype on a clean Apple Silicon Mac; run
   bundled database/core and existing UI without developer tools. Measure launch time,
   idle memory, package size and disk use. Prove all child binaries can be notarized.
2. **Usable local product:** scoped owner bootstrap, resumable setup, existing demo,
   provider test and encrypted secrets; preserve tenant and Chat confirmation boundaries.
3. **Reliable daily use:** lifecycle, sleep/wake, health, disk-full handling, crash recovery,
   portable backup/restore and safe update/migration failure drills.
4. **Release qualification:** supported macOS matrix, keyboard/localization review,
   signed distribution tests on clean machines, licenses and documented recovery.

The first slice can establish feasibility, but a public download needs all four.
The largest uncertainties are bundled native dependencies, secure desktop identity,
Keychain recovery and update rollback. Estimate implementation effort after the first
spike; the existing web UI alone does not make this a one-day wrapper task.

## Alternatives considered

| Option | Benefit | Reason not selected for the proposed first release |
|---|---|---|
| Existing Docker installer | Lowest new engineering effort | Requires external runtime and operational setup |
| Launcher opening the default browser | Less window integration | Still needs packaging, local authentication and lifecycle; native window gives coherent setup |
| Electron shell | Mature desktop ecosystem | Adds a browser runtime; use only if packaging/WKWebView proof exposes a concrete blocker |
| SQLite edition | Smaller installation | Violates PostgreSQL-only contract and forks storage behavior |
| Fully on-device LLM | No provider key or prompt transfer | Adds model downloads, hardware sizing and capability qualification; separate scope |

## Evidence and review boundary

Consulted 2026-09-19:

- [Apple: Developer ID distribution](https://developer.apple.com/developer-id/)
  establishes signing/notarization as the normal direct-distribution path.
- [Apple: Packaging Mac software](https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution)
  describes distribution packaging and testing on a separate Mac.
- [Tauri: External binaries](https://v2.tauri.app/develop/sidecar/)
  documents architecture-specific sidecar packaging.
- [PostgreSQL: Cluster upgrades](https://www.postgresql.org/docs/17/upgrading.html)
  distinguishes major upgrades and logical migration from ordinary minor replacement.

Architecture choices above are proposals inferred from the existing repository and
these capabilities. No native build, security validation, performance qualification or
implementation has been performed. After product acceptance, run the plan,
Constitution Check, tasks and analysis workflow before implementing. Update long-lived
auth/setup/deployment contracts when the behavior is implemented; do not describe this
proposal as an already available product.
