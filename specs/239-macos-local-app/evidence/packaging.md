# Packaging Spike Evidence

**Date**: 2026-09-19
**Outcome**: Native port proof passes; complete signed runtime packaging is not qualified.

## Executed

- Rust 1.83.0, arm64 Darwin; standalone dependency-free native probe compiled using
  `DEVELOPER_DIR=/Library/Developer/CommandLineTools` and its macOS SDK. This does not
  accept or change the Xcode license. Cargo uses `--offline` and a temporary target directory.
- Six Rust tests: bounded address retries, immediate resource-exhaustion failure,
  retained listener ownership, stale-generation fencing, role/loopback validation,
  and partial-startup socket release. See spike-rust.txt.
- Twelve pytest cases: four native child-process port scenarios and eight runtime
  packaging checks. See spike-pytest.txt. Initial missing-implementation failures are
  recorded in ports-red.txt and package-red.txt; the later absolute-symlink case is
  additional edge-case coverage, not claimed as an observed failing-first case.
- Sentinel listeners occupy conventional ports where not already owned by real software;
  pre-existing listeners are left untouched. Three probe roles receive different
  OS-allocated ports; repeated requests use the original bound sockets. Two generations
  coexist on separate ports and a later process restarts successfully.
- Current core wheel built with Hatchling to a temporary directory. Resource/ZIP preflight
  passes: catalogs, migration environment/versions, storylines and example imports exist.
  This is not a core/database startup or clean-machine execution test.
- Installed Homebrew Python inspected with otool: absolute dependency on its Cellar
  Python framework is correctly rejected. See python-candidate-audit.json.
- `security find-identity -v -p codesigning` reports zero valid identities in this session.
  No PostgreSQL runtime/build tree is available under the inspected Homebrew paths.

## Limitations and gates

T003/T004 remain incomplete. Need pinned relocatable CPython and PostgreSQL builds,
full dependency closure/architecture/resource checks, actual packaged API/scheduler/worker,
Tauri/WebView cookie exchange, Developer ID signing/notarization and clean-Mac tests.
The Rust probe serves only synthetic health JSON; it has no business application,
identity, database, native UI, backup or provider integration. Runtime audit only detects
known preflight defects; relative library references still require loader/rpath validation.

Sandbox initially denied bind(), so the loopback tests were rerun with approved local
socket access. No public listeners, external network tests or production data were used.
No application/core behavior, schema, hosted deployment or machine-wide toolchain settings
were changed. Downstream integration remains gated by the full packaging result.

## Follow-up runtime proof

The earlier missing runtime-build prerequisites were resolved using pinned standalone
Python and a local PostgreSQL source build with existing Command Line Tools. See
../verification.md and runtime-smoke.json: actual core migrations, pg_trgm and dump
tooling now pass in the relocated runtime. The earlier limitations paragraph describes
the first spike; Tauri/native cookie, Developer ID and clean-machine qualification
remain open. No machine-wide packages or Xcode license settings were changed.
# Native preview evidence

Date: 2026-09-19. Host: current developer Apple Silicon Mac, not a clean machine.

- Rust 1.98.1, Tauri 2.11.5, tauri-build 2.6.3; Cargo.lock retained.
- Python and PostgreSQL are copied from the previously audited relocated runtime.
- `codesign --verify --deep --strict` passes on the ad-hoc preview bundle.
- Real WKWebView page reports `cookie_hidden=true, native_command_denied=true`.
- The latter attempts `plugin:app|version` and requires a policy-denial error.
- Initial object-absence probe failed: Tauri internals exist with empty capabilities.
- All 27 isolated desktop Python tests pass; no product setup claimed complete.
- CUA app selection failed despite recognizing the running app; visual QA is pending.
- Developer ID signing, notarization, minimum-OS and clean-Mac testing remain open.

No cookie value, local account credential or customer data is included in this evidence.

Final artifact: `apps/desktop/dist/Reality Local.app` (266 MiB locally).
`Contents/MacOS/reality-local --verify` returned exit 0; see native-webview-proof.txt.
A subsequent process check found no `native-probe.py` or preview executable remaining.
This verifies the preview child cleanup only, not future PostgreSQL/worker lifecycle.
