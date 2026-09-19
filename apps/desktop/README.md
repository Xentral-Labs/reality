# Reality Desktop — interactive development build

The current development app opens the real Reality company-creation form and then
the existing product workspace. It supports a disposable empty company, empty Sandbox
or live international demo and an optional Anthropic API key. Quitting stops the API,
scheduler, worker and PostgreSQL, then removes that test's data and encrypted secret.
Persistent storage, Keychain custody and distribution signing remain unfinished.
Feature/design: [spec 239](../../specs/239-macos-local-app/spec.md).
Actual results: [verification](../../specs/239-macos-local-app/verification.md).

## Start a fresh interactive test

```sh
.venv/bin/python apps/desktop/scripts/test-preview.py
```

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
  --output 'apps/desktop/dist/Reality Local Development.app'
```

Choose a new output path when one already exists. The package includes
`local-runtime.py` (temporary PostgreSQL lifecycle), `local-product.py` (explicit
migration preparation followed by the authenticated API), and the product frontend.
No release-ready persistent installation or crash-recovery guarantee is implied.
