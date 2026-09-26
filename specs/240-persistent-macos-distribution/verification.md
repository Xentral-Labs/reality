# Verification: Persistent macOS Distribution — Increment 1

**Date**: 2026-09-21
**Scope**: User Story 1 and the non-destructive half of User Story 3. Distribution
signing, notarization, updates, Keychain custody and the website contract are not
covered and are listed as unmet below.

| Check | Result | Evidence |
|---|---|---|
| Desktop Python suite | 47 passed | `.venv/bin/python -m pytest apps/desktop/tests -q` |
| Ruff on apps/desktop | All checks passed | `ruff check --no-cache apps/desktop` |
| Ruff format on changed files | Clean | `ruff format --check` on the nine touched files |
| Rust formatting | Passed | `cargo fmt --check` |
| Spec policy | Passed | `python3 scripts/check_spec_policy.py` |
| Native shell rebuild | Compiled, 48 s | Rust 1.98.1, Tauri 2.11.5, isolated toolchain |
| Lifecycle against the built runtime | Passed | evidence/persistence-run.json |
| Packaged application quit and reopen | Passed | evidence/application-cycle.json |
| Recovery from a forced quit | Passed | evidence/forced-quit.json |
| Release build with the current core | Passed, migration 0088 | evidence/release-build.json |
| Code signature after real use | Intact, no bytecode added | evidence/release-build.json |
| Core job-runner regression | 2 passed | tests/test_job_runner_process.py |
| Reporting-graph parent resolution | 8 passed, stable in 30 processes | tests/test_reporting_graph_coverage.py |
| Reopening straight after a quit | Passed | evidence/release-build.json |

## What the runs actually did

**Lifecycle (evidence/persistence-run.json)**: against a real Application Support base,
the first start created installation `605bfeb1…`, migrated to `0069_inventory_generations`
and created a company. The second start returned the same owner and the same company and
reported `identity_is_stable: true`. A second concurrent start was refused. Raising the
application version from 0.1.0 to 0.2.0 moved the checkpoint count from 0 to 1 before
migration. Erasure removed the installation, kept an unrelated file beside it and kept
the base directory. PostgreSQL never listened on TCP in any run.

**Packaged application (evidence/application-cycle.json)**: the ad-hoc signed
`Reality Local.app` was launched, a company was created through the real service against
the application's own running cluster, and the application was quit. The data directory
remained, no PostgreSQL process survived, and the next launch reused installation
`ba28dfc6…` with the same owner `usr_283f97acbb` and the same company
`ten_2b7cac8108` — "Company From The App". The bundled erasure command then removed it.

**Forced quit (evidence/forced-quit.json)**: the shell and every Python supervisor were
killed with SIGKILL. PostgreSQL was left genuinely orphaned with a live pid file. The
next launch stopped that process, started a new postmaster and read the company back.

**Release build (evidence/release-build.json)**: the artifact published for testers was
assembled from the current core wheel, the current web frontend and a release-profile
shell. Its cluster reaches `0088_tenant_scoped_keys`. The database was serving 1.2 s
after launch, a quit took 3.8 s and left no database process, and reopening took 0.6 s
and returned the same company.

Three defects surfaced while verifying that build and were fixed here.

Reopening immediately after a quit hit the installation lock while the previous process
was still stopping, so a start now waits up to 60 seconds for that shutdown instead of
refusing. The native shell turned any failed start into a non-unwinding Rust panic and a
macOS crash report; it now prints the reason and exits.

The application invalidated its own code signature on first use by writing bytecode into
its signed bundle. `python -I` ignores `PYTHONDONTWRITEBYTECODE`, so only the `-B` flag
prevents it, and every bundled interpreter call now passes it. The remaining writer was
`reality.jobs.runner`, which spawns one child per job through `sys.executable` without
the parent's flags; the child command now carries `-B` whenever the parent runs with it.
That matters beyond the desktop: any read-only or signed deployment would hit it. After
the fix, creating a company in the running application leaves the signature intact and
adds no file to the bundle.

## A pre-existing flake this branch had to fix

CI failed on analytics tests with `node order_line: parent needs one unambiguous
foreign key`, and the same failure appeared once locally. It is not caused by this
feature. `graph_model._foreign_keys()` collected `column.foreign_keys`, an unordered
set, into a map keyed by column. Every business table is tenant-scoped, so `tenant_id`
belongs to each composite constraint and could claim whichever parent the set yielded
last. `document_line` then looked like it referenced `document` through both
`document_id` and `tenant_id`, and validation refused.

The order depends on object identity, so it varies per process and no hash seed
controls it. Measured before the fix: 3 of 30 processes saw the ambiguity; after it,
0 of 30. CI runs `pytest -n 2 --dist worksteal`, so each worker took that chance on
every run. Resolution now reads the foreign-key constraints and ignores the tenant
column, which names the referring column exactly once.

A second pre-existing flake surfaced in the same shard.
`test_demo_profile_history` selected "the" credit note by type, and the profile seeds
two: `CR-001`, which carries a billed-line link, and `COST-LATE-CREDIT`, which is
deliberately unlinked so a complete sale's fulfillment scope stays unambiguous. With no
ordering, which one came back was the database's choice; CI got the unlinked one. The
test now names `CR-001`.

## Boundary

The earlier runs used the core wheel built on 2026-09-19, which stops at migration
`0069_inventory_generations`. The release build above carries the current
`0088_tenant_scoped_keys`.

Twenty consecutive cycles under SC-001 were not run; three application launches and
three scripted lifecycle runs were. Everything below is not implemented:

- FR-006 Keychain custody. The cluster password is a `0600` file in the installation.
- FR-007 validated checkpoints. A `pg_dump` is written before a changed version
  migrates and the newest three are kept, but it is neither validated nor restored
  automatically, and a failed migration does not roll back.
- FR-008 backup and restore as a product surface.
- FR-010 Developer ID signing, Hardened Runtime, notarization, stapling. The package is
  ad-hoc signed and requires the reader to approve it in System Settings by hand.
  `.github/workflows/macos-release.yml` carries the steps and names the Apple secrets
  they need, and skips them while those secrets are absent. That workflow has never
  been executed; the published beta was built by hand with the same commands.
- FR-011 clean-machine qualification. Every run above happened on the development Mac.
- FR-012 signed updates. A new version is a new download.
- FR-013 diagnostics, FR-014 the website download contract, FR-016 release manifests.

No business schema, service, tool or web behavior was changed. No migration was added.

## Increment 2 implementation progress

The owner approved the Increment 2 architecture on 2026-09-26. The first test-first
slice introduced a shared process-local master-key provider. Four new tests first failed
because the provider did not exist, then passed after implementation. Focused provider
and tenant-scoped AI/secret regression: 7 passed, 1 skipped, 29 deselected.

Desktop mode now has a fail-closed process-key boundary: one valid Fernet key may be
bound to one installation per process and cannot be replaced or resolved for another
installation. Hosted environment and development-file resolution retain their existing
contract. `security/secrets.py` and the legacy AI-key migration now share this resolver.

T013 remains open. Native Security.framework custody, private stdin delivery, migration
of the transitional PostgreSQL password file, exact Keychain erasure and real native
acceptance have not yet been implemented. T011 also remains open; no data-generation
switch or recovery behavior is claimed by this slice.

The next T013 slice added the native Security.framework adapter without invoking the
`security` command. It uses exact installation-scoped service/account pairs, secure OS
randomness, read-after-write verification and a versioned private stdin handshake.
Existing installations offer their retained database password to native custody over
that pipe; the file is removed only after Keychain verification and successful database
startup. New installations use a temporary initdb password file and remove it
immediately. Product, scheduler and worker processes install the vault key once in
memory and enable fail-closed desktop resolution.

Verification: native unit suite 2 passed and one real login-Keychain round trip was
skipped because the execution account reported that no unlocked login Keychain was
available; 21 installation/package tests passed; focused core key/secret regression
again passed 7 with 1 skipped and 29 deselected. Ruff, Python formatting, Rust formatting,
Spec Policy and diff checks passed. T013 remains open until a signed packaged run proves
the real Keychain round trip and exact erasure removes both owned entries while retaining
unrelated entries. T011 remains untouched.

The first T011 slice now provides durable PostgreSQL generation state. Increment 1's
`data/` directory is adopted once with an atomic move, exact bytes unchanged, into an
opaque private generation. A private `current-data` pointer selects the active
generation. Paths must be canonical UUIDs with matching manifests; traversal or a
foreign/malformed generation fails closed.

Upgrade staging records a value-free maintenance journal. Only a generation marked
validated may become active. Activation writes the new manifest, atomically replaces
the pointer and only then marks the previous generation retained. A failed stage removes
only its owned incomplete directory and leaves the previous pointer and bytes unchanged;
failure reasons are deliberately absent from the durable journal. The packaged runtime
now includes this recovery module and the persistent installation resolves its data
through it.

Verification: five new recovery tests first failed because the module was absent and
then passed; combined recovery/installation/package suite passed 26 tests. Ruff, format,
Spec Policy and diff checks passed. T011 remains open: the real `pg_dump`, archive and
space validation, restore, Alembic migration, product-readiness probe and injected
process-failure matrix are not connected to the staged generation yet.

Checkpoint admission now binds archive size and SHA-256 to installation ID, source
generation, application version and schema revision. `pg_restore --list` must recognize
the archive and include `alembic_version`; foreign, corrupt, empty, truncated or tampered
input is rejected before staging. A preflight reserves the larger of three archive sizes
or 256 MiB before work begins. Three additional tests first failed and then passed;
the combined recovery/installation/package suite now passes 29 tests.

A real temporary persistence run found and fixed one integration defect before database
initialization: PostgreSQL requires an empty data directory, so generation manifests now
live beside their private PostgreSQL directories rather than inside them. The rerun then
initialized and migrated the generation through the bundled runtime's head, but its
probe stopped because the locally retained runtime core predates `desktop_identity`
(it ends at migration 0067). This is a stale local build input, not passing end-to-end
evidence; rebuild/assembly with the current core is required before the real staged
upgrade proof can be claimed. T011 remains open.

The embedded dependency lock was regenerated from the current core contract and its
offline wheelhouse refreshed. Runtime assembly then passed its dependency audit, and
the rebuilt runtime smoke reached migration `0099_payment_term_prepayment`, loaded the
catalog and job roles, verified a readable dump, and confirmed that PostgreSQL did not
listen on TCP.

The next real persistence run completed the connected staged-upgrade path. A version
change now reads the source schema revision, writes and validates an installation- and
generation-bound checkpoint, performs the disk preflight, initializes a sibling
PostgreSQL generation, restores the archive, runs current Alembic migrations through a
private stdin configuration, reads back the resulting schema revision and only then
atomically activates the new generation. The final evidence run reported
`generation_changed_on_upgrade: true` and `previous_generation_retained: true`. The
same tenant `ten_09882645a0` and owner `usr_6851431abe` were present after activation at revision
`0099_payment_term_prepayment`; PostgreSQL remained socket-only. Focused recovery,
installation and package tests pass 30 tests, including failure both before and after
stage validation while the old active bytes remain unchanged. The complete desktop
suite passes 61 tests.

T011 remains partial rather than complete: the proof still uses current-schema data
with a simulated application-version transition, not retained prior-release fixtures,
and the process-kill matrix at each durable journal boundary has not yet been run.

Startup reconciliation now covers the durable activation boundaries. Before inspecting
the maintenance journal, startup stops any orphaned postmaster belonging to an owned
generation. A journal still pointing at the source generation removes only the
incomplete sibling and records failure. If the atomic pointer already selects the new
validated generation, startup marks the source retained and completes the journal.
Malformed, foreign or contradictory journal state fails closed.

Five reconciliation scenarios and two injected `activate()` interruptions pass: before
the pointer write the source remains active; immediately after the pointer write the
new generation remains active and the source becomes retained. The focused recovery,
installation and package suite now passes 37 tests. A subsequent real PostgreSQL
lifecycle again preserved tenant `ten_9cc95c065a` and owner `usr_78ca951714`, reported
both `generation_changed_on_upgrade: true` and `previous_generation_retained: true`,
and remained socket-only at schema `0099_payment_term_prepayment`. T011 remains partial
only because retained prior-release fixtures and an OS-level kill matrix across the
long-running dump, restore and migration phases are still outstanding.

The durable-boundary matrix now also runs in real child processes. Four workers are
terminated with `SIGKILL` while the journal is preparing, after validation, immediately
before the active-pointer write and immediately after it. A fresh process reconciles
each installation using only its durable pointer, manifests and maintenance journal.
The first three cases retain the authoritative source and remove the incomplete sibling;
the post-pointer case retains the source and completes the new active generation. The
recovery module passes 20 focused tests. Remaining T011 evidence is narrowed to retained
prior-release database fixtures and hard termination during the external `pg_dump`,
`pg_restore` and Alembic subprocesses themselves.

Restore, migration and verification now write an allowlisted, value-free phase into the
same maintenance journal before each long-running operation. Unknown phases and phases
for a non-current staged generation fail closed. Checkpoint filenames also include an
opaque suffix, so a restart within the same second cannot collide with a partial archive.

The child-process `SIGKILL` matrix now includes `restore`, `migration` and `verification`
phase journals in addition to the four activation boundaries. All seven hard-exit cases
reconcile correctly, and the recovery suite passes 27 tests. A real PostgreSQL lifecycle
with the phase writes also passed at revision `0099_payment_term_prepayment`, preserving
tenant `ten_4f9e474b82` and owner `usr_864a749e9a` across a genuine staged restore and
activation. T011 still requires retained prior-release fixtures and termination of the
real external subprocesses while they are executing, rather than immediately at their
durable phase boundaries.

Checkpoint publication is now safe against termination inside `pg_dump`. The command
writes to a private `.checkpoint-<uuid>.partial` path; only successful completion causes
an atomic rename to the collision-free final `.dump` name followed by a directory
`fsync`. Startup removes only owned unpublished partials while leaving complete archives
untouched. Tests prove a failed dump cannot appear as a published checkpoint and that
cleanup is narrowly scoped. The focused recovery/installation/package suite passes 51
tests. A subsequent real PostgreSQL upgrade again produced exactly one complete
checkpoint and preserved tenant `ten_32b1b97471` and owner `usr_9eb1f57516` through
staged restore and activation at revision `0099_payment_term_prepayment`.

A separate real-runtime interruption harness now creates a tenant, launches staged
upgrades in independent OS processes and sends `SIGKILL` at the durable restore and
migration boundaries while each staged PostgreSQL cluster is running. Both workers
returned `-9`. On restart, Reality stopped the orphaned staged postmaster, reconciled the
pre-switch journal to the source generation, removed the incomplete sibling and reran
the upgrade successfully. Restore and migration cases both preserved tenant
`ten_f3a6d699dc`, reached `0099_payment_term_prepayment` and reported no TCP listener.

This closes the real-runtime interruption evidence for current-schema upgrades. T011
remains partial only because the acceptance matrix still needs retained database fixtures
created by actual older application releases, rather than a version transition over a
database already at the current schema.

The final T011 gate used the repository's `mac-v0.1.0` release tag rather than the
unreleased local 0069 build. Its core wheel and migrations were materialized in an
isolated temporary runtime directly from tag commit `193d3264`; no source in the working
tree or external package input was substituted. That runtime created tenant
`ten_dbd63f5ebe` at the tag's real head `0088_tenant_scoped_keys`. The current runtime
then wrote one validated checkpoint, restored a sibling generation, migrated it to
`0099_payment_term_prepayment` and switched the pointer atomically. The tenant survived,
the generation changed, the source generation remained available, and PostgreSQL stayed
socket-only. T011 is complete.

The first T012 slice defines the encrypted backup envelope. Six tests cover exact
round-trip bytes, encrypted manifest and payload, wrong key, ciphertext tampering,
truncation, foreign installation, unsupported schema and strict manifest fields. The
implementation streams AES-256-GCM, authenticates before trusting manifest authority,
and atomically publishes plaintext only after installation, schema, size and SHA-256
checks pass; every failure removes its private partial. The packaged application includes
the module. T012 remains open until backup creation and staged PostgreSQL restore are
connected to an explicit confirmed product operation and verified end to end.

The next T012 slice connects that envelope to the real database lifecycle. Backup first
runs socket-only `pg_dump`, verifies the custom archive, derives an installation-bound
backup key from the vault key through HKDF, encrypts the archive and always deletes the
temporary plaintext. Restore authenticates and decrypts to a private staging path,
checks `pg_restore --list`, restores a sibling PostgreSQL generation, runs current
migrations and schema verification, and uses the same validated atomic activation as
upgrades.

The end-to-end run produced an 821,510-byte encrypted backup at revision
`0099_payment_term_prepayment`. It then added a second tenant after the backup and
restored the artifact: the backed-up tenant remained, the later tenant disappeared, the
active generation changed, the prior generation remained available, and PostgreSQL did
not listen on TCP. Seven envelope tests and the combined 58 focused backup/recovery/
installation/package tests pass. T012 remains open until this operation is exposed
through a confirmed native product flow and real wrong-key/corrupt restore attempts are
shown to leave the active generation unchanged.

The real-runtime restore harness now attempts both failure modes before the valid
restore. A different vault key and a bit-flipped encrypted archive were each rejected;
after each attempt the active pointer and exact set of data generations were unchanged.
The valid artifact remained restorable afterward, preserved the backed-up tenant and
removed only the tenant created after the backup. The run reported
`wrong_key_rejected_unchanged: true` and `corrupt_rejected_unchanged: true` at revision
`0099_payment_term_prepayment` with no TCP listener. T012 now remains open only for an
explicit confirmed native backup/restore product flow and its packaged acceptance run.

The native shell and private runtime now expose that maintenance flow. The shell accepts
exactly one of `--backup <path>` or `--restore <path> --confirm-restore`, rejects an
unconfirmed restore before Keychain or PostgreSQL access, and forwards no credential in
arguments. After the normal installation-scoped Keychain handshake, backup runs against
the exclusively held socket-only cluster; restore runs staged activation before any API,
scheduler, worker or WebView starts. Three Python argument-contract tests and two Rust
shell tests pass. T012 remains open only until these commands are exercised through a
newly packaged app with an unlocked login Keychain.

The fresh-package gate rebuilt the Rust shell, packaged the current runtime/frontend and
ad-hoc signed an isolated application. Native backup correctly stopped before PostgreSQL
when macOS rejected Data-Protection-Keychain creation with `A required entitlement is
not present`. No backup or Keychain value was created. This proves the remaining
acceptance depends on the Developer ID/entitlement work in T016; weakening custody or
falling back to a file is not acceptable.

That run also found a package identity defect: `local-runtime.py` looked one directory
above `Contents/Info.plist`, silently falling back to the production identifier. The
path now resolves the packaged plist exactly and has a regression test. The test-created
fallback installation contained no `PG_VERSION` or business data and was moved intact to
`/private/tmp/reality-t012-native.HPx3HG/removed-production-fallback-shell`; no existing
installation was deleted. T012 remains open on its signed-package Keychain gate.

The first T016 signing slice turns that external gate into an executable contract. A
release helper generates the exact `com.apple.application-identifier`, team identifier
and single private `keychain-access-groups` value from validated Team ID and bundle ID,
and rejects development-only `get-task-allow`. Post-sign qualification requires the
embedded Developer ID provisioning profile, reads the signed entitlements back with
`codesign`, compares every required value and runs deep strict signature verification.
Five tests pass. The release workflow now requires `APPLE_TEAM_ID` and
`APPLE_PROVISIONING_PROFILE`, embeds the profile, signs with the generated entitlements
and invokes the verifier. T016 remains open until real credentials exercise this path,
all nested components receive explicit signatures, and notarized DMG manifests are
generated and qualified.

The next T016 slice removes `codesign --deep` from the release signing action. A
magic-header inventory finds every Mach-O file without executing candidate code, orders
the leaves deterministically deepest-first and signs each with timestamp and Hardened
Runtime before the app root receives its entitlements. The release workflow now also
emits sorted, versioned SHA-256 manifests for the packaged app inputs and final DMG and
publishes both beside the checksum. Seven focused signing/manifest tests pass. Running
the generator over the freshly packaged acceptance app recorded 9,697 file or symlink
entries in stable order. T016 remains open for the credentialed signature, notarization,
stapling and second-build reproducibility comparison.

The package version is no longer hard-coded: the release version now populates both
`CFBundleShortVersionString` and `CFBundleVersion`, with a regression test. Manifest
comparison reports metadata or exact path-level differences and the release workflow
packages the app twice into independent directories before signing, generates both
complete manifests and requires them to match. The local double-package proof captured
9,697 entries in each app and the JSON manifests were byte-identical. T016 remains open
only for credentialed Developer ID signing, notarization, stapling and validation of the
signed DMG path on release infrastructure.

T013 now also has an exact native Keychain erasure primitive. It preflights both the
database and vault entries for the selected installation before deleting either, deletes
only their exact service/account coordinates, and reads both back to require
`errSecItemNotFound`. The isolation test proves a sibling installation resolves to
different coordinates. Native Keychain tests pass three with two real login-Keychain
tests skipped because the execution account cannot supply the required entitled,
unlocked Keychain. T013 remains open until erasure is connected to a crash-safe confirmed
filesystem quarantine/commit flow and exercised by the credentialed package.

The filesystem half of confirmed erasure is now a crash-safe quarantine transaction.
Preparation writes a value-free journal, exclusively moves exactly one owned installation
to `erasing/<installation-id>`, removes its active pointer and blocks replacement starts.
Keychain failure can atomically roll the directory and pointer back; verified Keychain
success permits commit to remove only the quarantined directory. Crash reconciliation
distinguishes interruption before and after the atomic move without guessing from a live
process. Twenty-two installation tests and the combined 49 installation/recovery tests
pass. T013 remains open until the native erasure protocol connects Keychain deletion to
rollback/commit and the credentialed package runs it.

The native erasure protocol now closes that connection. The packaged uninstall command
invokes the signed app with the explicit `--erase --confirm-erasure` pair rather than
calling the Python filesystem remover directly. Python quarantines the selected owned
installation before requesting native deletion; Rust deletes only its two exact
installation-scoped Keychain records and reports the observed state. Both missing commits
the filesystem deletion, both present rolls it back, and a partial or unreadable state
fails closed with the filesystem still quarantined. A later launch inspects and resolves
the same journal, covering termination after either side of the Keychain operation without
creating a replacement installation. The full desktop suite passes 110 tests, the Rust
suite passes six with the two credential-dependent login-Keychain tests skipped, and Ruff,
Rust formatting, and whitespace validation pass. T013 remains open only for the signed,
entitled package acceptance run that exercises the real login Keychain.

The T016 workflow now treats publication as a signed-only operation. It requires the
complete certificate, identity, team, provisioning-profile and App Store Connect API-key
set before entering the signed path, and a tag or explicit publish request fails instead
of uploading an ad-hoc artifact when any credential is absent. After notarization and
stapling, a dedicated qualifier independently verifies the DMG signature, validates its
stapled ticket and asks Gatekeeper to assess the primary signature. Private temporary
certificate and API-key files are removed by exit traps even when a command fails. Nine
focused signing and manifest tests pass. T016 remains open for execution with repository
credentials, Apple notarization, and retained evidence from the resulting artifact.

FR-017 now has an explicit named-tester beta implementation through T021–T026. Packaging
requires `--unsigned-tester-beta`, retains the stable production bundle identifier for a
later in-place signed migration, and adds a distinct display name, release label, immutable
channel marker, Finder/manual-open guide and persistent in-product warning. Generated
database and vault values live in one atomic, current-user-owned `0600` operational record;
missing existing custody, symlinks, malformed content, identity mismatch and any other mode
fail closed. The runtime selects this provider only from packaged metadata, never arguments
or environment. A signed successor writes both exact values to installation-scoped Keychain
entries, reads them back and only then removes the unchanged beta record; interruption or
mismatch retains it. Release workflow policy rejects beta publication from tags, releases,
the website or update paths and uses a distinct private artifact name.

The focused beta/package/protocol suite passes 33 tests, the complete desktop suite passes
129 tests, the Rust suite passes six with two credentialed login-Keychain tests skipped,
the production frontend builds, and Ruff, Spec Policy and whitespace checks pass. A real
ad-hoc bundle was assembled at
`/private/tmp/reality-unsigned-beta.QhVI1z/Reality Local Unsigned Beta.app`; strict deep
code-signature verification succeeds and its packaged channel reads `unsigned-tester-beta`.
It was deliberately not launched because the current account's production Application
Support location is outside disposable test scope. T027 remains open for a disposable clean
macOS account, ten restart cycles, manual-open evidence and the real signed-successor test.
