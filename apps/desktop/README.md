# Reality Desktop

The app opens the real Reality company-creation form and then the existing product
workspace. It supports an empty company, an empty Sandbox or the live international
demo, plus an optional Anthropic API key.

Two builds come out of the same source and never share a data directory:

| Build | Identifier | On quit |
|---|---|---|
| Persistent (default) | `ai.runreality.local` | Keeps everything until an explicit erasure |
| Fresh-test harness (`--disposable`) | `ai.runreality.local.development` | Removes its database and secret |

Feature/design: [spec 239](../../specs/239-macos-local-app/spec.md) for the package,
[spec 240](../../specs/240-persistent-macos-distribution/spec.md) for persistence.
Actual results: [239 verification](../../specs/239-macos-local-app/verification.md),
[240 verification](../../specs/240-persistent-macos-distribution/verification.md).

Keychain custody, validated backup/restore, Developer ID signing, notarization and
signed updates remain unfinished. Until they exist the artifact may be handed to named
testers with the instructions below, never published as a public download.

## The persistent installation

Everything durable lives in one directory per installation:

```
~/Library/Application Support/ai.runreality.local/
  current                      # identifier of the active installation
  installations/<id>/
    installation.json          # identity, layout and last application version
    data/                      # PostgreSQL cluster
    artifacts/                 # artifact backend
    backups/                   # checkpoint written before a new version migrates
    secret                     # cluster password, 0600, until Keychain custody lands
```

The cluster listens on no TCP port. Its Unix socket is created fresh under
`/private/tmp` on each start, because macOS rejects socket paths beyond about 104 bytes
and an Application Support path plus an identifier exceeds that.

Moving the application to the Trash keeps the data, so reinstalling or updating never
costs a company. Erasure is a separate confirmed command inside the bundle:

```sh
'/Applications/Reality Local.app/Contents/Resources/uninstall.command'
```

Run the same file's underlying script without `--uninstall` to see where the data is,
how large it is and which version wrote it:

```sh
'/Applications/Reality Local.app/Contents/Resources/runtime/python/bin/python3.12' -I \
  '/Applications/Reality Local.app/Contents/Resources/probe/installation.py'
```

A second start of the same installation is refused rather than allowed to corrupt the
cluster. A forced quit leaves the data intact; the next start stops the orphaned
database process and continues.

## Hand the build to a tester

The package is ad-hoc signed, not notarized. On macOS 15 and newer the old
right-click-to-open route no longer works, so the instructions are:

1. Apple Silicon Mac, macOS 14 or newer. No Homebrew, Xcode or PostgreSQL required.
2. Move `Reality Local.app` to `/Applications`.
3. First launch is refused. Open System Settings → Privacy & Security and choose
   "Open Anyway", or run once:
   `xattr -dr com.apple.quarantine '/Applications/Reality Local.app'`.
4. Data lives in `~/Library/Application Support/ai.runreality.local` and stays there.
5. There is no update mechanism yet: a new version arrives as a new download. A version
   change writes a checkpoint into `backups/` before migrating, and the newest three are
   kept, but restoring one is still a manual `pg_restore` with the bundled tools.
6. Keep the existing system running in parallel. This build carries no availability or
   data-loss guarantee.

## Start a fresh interactive test

```sh
.venv/bin/python apps/desktop/scripts/test-preview.py
```

This helper accepts only a fresh-test build (`--disposable`); it copies and deletes the
application, which would be wrong for a persistent installation.

The default artifact is `dist/Reality Local Demo Ready No Scroll.app`. It carries the native
macOS version of the web LogoMark and opens at 1440 × 960
logical pixels (limited to the display work area), with company creation leading to Home.
The helper installs a fresh
app copy, starts a new database, and waits while you create a company or demo and use
the product. Quit the app to remove both test data and the temporary app copy. The
source build stays available for another run. No existing Reality installation or
external PostgreSQL database is touched.

For unattended native checks use `--verify --runs 2`. The interactive build initializes
its actual database at startup; it does not run the earlier detached database smoke.
The historical proof build can still be tested explicitly with `--app`.

For the real browser journey (requires the ignored build-only Playwright dependency):

```sh
node apps/desktop/tests/onboarding-browser.mjs
```

That test uses the packaged backend, creates a real company, verifies the workspace,
and checks that the temporary database directory is absent after shutdown. Browser
cookies are injected only by the test runner; the native app uses its private pipe.

## Prove that data survives

Against a built runtime, without the native shell:

```sh
.venv/bin/python apps/desktop/scripts/verify-persistence.py --runtime 'apps/desktop/build/relocated runtime core'
```

The run creates a company, stops, starts again and reads the same records back, refuses
a second concurrent start, writes a checkpoint for a changed application version and
then erases exactly one installation. It uses a temporary base directory unless `--base`
names another one; point it at a path under Application Support to exercise the real
location. Recorded results are in
[240 verification](../../specs/240-persistent-macos-distribution/verification.md).

## Run the isolated tests

From the repository root, with Rust and the repository Python test environment:

```sh
DEVELOPER_DIR=/Library/Developer/CommandLineTools cargo test --offline --manifest-path apps/desktop/spike/Cargo.toml
.venv/bin/python -m pytest apps/desktop/tests -q
```

The explicit developer directory selects installed Command Line Tools without changing
machine-wide Xcode settings. Omit it on hosts without that directory. Tests need local
loopback socket access; they never stop software already using a conventional port.
Cargo has no external dependencies. Python fixtures build the probe in a temporary folder.

`spike/Cargo.toml` compiles `src-tauri/src/supervisor.rs` without a Tauri dependency.
Each native child binds `127.0.0.1:0`, reports the actual origin over its parent pipe,
and serves synthetic `/healthz` responses using that same socket. The supervisor
registry rejects late endpoint reports from retired generations. No business data,
authentication, database or production API is exposed by the probe.

## Inspect runtime candidates

```sh
python3 apps/desktop/scripts/runtime_audit.py --wheel /path/to/core.whl
python3 apps/desktop/scripts/runtime_audit.py --tree /path/to/staged/runtime
python3 apps/desktop/scripts/runtime_audit.py --binary /path/to/python3.12 --binary /path/to/postgres
```

These checks reject missing core resources, archive escapes, external/broken/absolute
symlinks and non-system absolute Mach-O dependencies. Exit 1 means a detected defect;
exit 0 means only that these checks passed. Relative loader/rpath dependencies,
architecture, signatures and actual execution still require qualification. Candidate
executables are inspected with otool, never executed by the audit.

The installed Homebrew Python is not used as the shipped runtime. The pipeline below
bundles standalone CPython and PostgreSQL; Developer ID signing and clean-Mac
proof remain incomplete. No system-wide dependencies, signing keys or
machine configuration are installed or changed.

## Build the bundled runtime (development only)

Build inputs are pinned in `scripts/runtime-dependencies.lock`; download the exact
URLs there into `build/downloads/` using their declared archive names. The builder
checks SHA-256 before extraction. Resolve/download the Python wheelhouse only when
intentionally updating its committed hash lock, never at end-user startup.

```sh
.venv/bin/python -m pip download --only-binary=:all: --require-hashes -r apps/desktop/scripts/python-requirements.lock -d apps/desktop/build/wheelhouse
.venv/bin/python apps/desktop/scripts/build-runtime.py --cache apps/desktop/build/downloads --output apps/desktop/build/runtime-base --jobs 8
```

This consumes the pinned standalone Python distribution and builds PostgreSQL plus
`pg_trgm`, required by Reality's existing search migration. Build tools are needed
only on the development/build machine. Native load references, architecture, minimum
macOS version and symlink containment are checked. Modified binaries receive local
ad-hoc signatures; these are not Developer ID signatures or notarization.

Build the current core wheel with Hatchling from `packages/reality-core` into a chosen
build directory, then assemble and smoke-test using absolute paths where appropriate:

```sh
.venv/bin/python apps/desktop/scripts/assemble-runtime.py --runtime apps/desktop/build/runtime-base --wheelhouse apps/desktop/build/wheelhouse --core-wheel /path/to/business_reality-0.0.1-py3-none-any.whl --output 'apps/desktop/build/relocated runtime core'
.venv/bin/python apps/desktop/scripts/runtime-smoke.py --runtime 'apps/desktop/build/relocated runtime core'
```

Assembly is offline, checks all package hashes and runs `pip check`. Output paths
must not already exist. The smoke test launches a disposable PostgreSQL cluster with
a random password, SCRAM authentication and a private Unix socket (no TCP listener),
then runs the real packaged migrations from a temporary working directory. It checks
search extension availability and imports the real job-role entrypoints without
starting jobs. The test database and process are removed afterwards. The runtime
manifest records the dependency lock, core wheel hash and qualification boundary.

The runtime is still an internal development artifact: no app window, first-run
identity/setup or production lifecycle has been integrated yet.

### Native cookie preview

The Tauri 2.11.5 development shell packages the audited runtime and a deliberately
isolated loopback proof server. It does not create a company or offer AI setup yet.
The server binds `127.0.0.1:0`, passes its endpoint and random cookie over a private
pipe, and serves no business operations. Rust inserts the HttpOnly, SameSite=Strict
session cookie into an ephemeral WebView before navigating. Exact Host/Origin checks,
no capabilities, and navigation restricted to the issued origin bound this preview.
The cookie cannot be Secure on this HTTP-only loopback proof. Production session
isolation and same-host cross-port threats still require the planned security review.

With the isolated Rust toolchain installed in `build/rustup`:

```sh
RUSTUP_HOME="$PWD/apps/desktop/build/rustup" \
CARGO_HOME="$PWD/apps/desktop/build/cargo" \
CARGO_TARGET_DIR="$PWD/apps/desktop/build/tauri-target" \
DEVELOPER_DIR=/Library/Developer/CommandLineTools \
MACOSX_DEPLOYMENT_TARGET=14.0 \
rustup run 1.98.1 cargo build --locked --manifest-path apps/desktop/src-tauri/Cargo.toml

.venv/bin/python apps/desktop/scripts/package-preview.py \
  --runtime 'apps/desktop/build/relocated runtime core' \
  --binary apps/desktop/build/tauri-target/debug/reality-local \
  --output 'apps/desktop/dist/Reality Local Preview.app'
```

An installed persistent application exposes maintenance through its native executable,
so database and vault credentials still come from the exact installation-scoped macOS
Keychain entries rather than shell arguments:

```sh
'/Applications/Reality Local.app/Contents/MacOS/reality-local' \
  --backup "$HOME/Desktop/company.reality-backup"

'/Applications/Reality Local.app/Contents/MacOS/reality-local' \
  --restore "$HOME/Desktop/company.reality-backup" --confirm-restore
```

Backup is read-only. Restore replaces the active logical database state and therefore
requires the explicit `--confirm-restore` flag; without it the native shell exits before
opening Keychain custody or PostgreSQL. Neither command places secret values in process
arguments.

The complete future Apple Developer ID certificate, provisioning-profile, App Store
Connect API-key, GitHub-secret and first signed-release procedure is recorded in
[`specs/240-persistent-macos-distribution/apple-release-setup.md`](../../specs/240-persistent-macos-distribution/apple-release-setup.md).

The output directory must not already exist. The package is ad-hoc signed and
verified locally; it is not notarized or ready for distribution. Startup is bounded
by a ten-second endpoint handshake. Closing the private parent pipe stops the proof
server; this is not the production database/job lifecycle supervisor.

The preview executable accepts `--verify`: it exits after the WebView reports cookie
secrecy and a policy-denied app-version command (exit 0 on both, 2 on failure).
Tauri's internal JS object is present; absence of granted capabilities, not absence
of this object, is the tested boundary. The private pipe logs boolean results only.

### Fresh install / PostgreSQL / uninstall test cycle

From the repository root, run:

```sh
.venv/bin/python apps/desktop/scripts/test-preview.py
```

This creates a unique disposable copy of the preview app, including its bundled
PostgreSQL and Python. Before opening the UI, it initializes a new private PostgreSQL
cluster, applies the real migrations, checks zero tenants and dump readability,
stops PostgreSQL and removes the cluster, artifacts and dump. Quit the preview to
remove its temporary app copy. The original build remains available for the next run.
The database smoke and stateless UI are separate checks; the preview has no company
or API-key setup and is not connected to that disposable database.

For two unattended cycles (also usable by the coding agent):

```sh
.venv/bin/python apps/desktop/scripts/test-preview.py --verify --runs 2
```

Each run uses a different private directory under `/private/tmp`. The helper removes
only directories it created, including on ordinary errors. A machine crash or force
kill can leave a temporary directory; this is not a production uninstaller. It does
not erase macOS-managed logs/caches, unrelated PostgreSQL installations, or any real
Reality data. Future persistent company data and Keychain test identities require
the isolation/uninstall implementation described by FR-018 before this command can
claim to reset the complete product. Ordinary app removal remains data-preserving;
full product erasure will be a distinct, explicit action.


## Package the interactive build

Build the current core wheel and frontend, assemble a new runtime with that wheel,
then use the native binary built from `src-tauri`:

```sh
.venv/bin/python apps/desktop/scripts/package-preview.py \
  --runtime apps/desktop/build/onboarding-runtime \
  --binary apps/desktop/build/tauri-target/debug/reality-local \
  --frontend apps/web/dist \
  --output 'apps/desktop/dist/Reality Local.app'
```

Choose a new output path when one already exists. The package includes
`installation.py` and `cluster.py` (durable installation and PostgreSQL lifecycle),
`local-runtime.py` (process supervision), `local-product.py` (explicit migration
preparation followed by the authenticated API), the erasure command and the product
frontend.

Add `--disposable` for the fresh-test harness. That build carries the development
identifier, marks itself with `probe/disposable`, titles its window "Test Installation"
and ships no erasure command, because quitting already removes its data.

The signature is ad-hoc. Developer ID signing, notarization, stapling, signed updates
and clean-machine qualification are not performed here, so no public download is implied.
