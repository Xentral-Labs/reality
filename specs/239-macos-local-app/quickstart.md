# Validation Guide: macOS Local App

**Status**: Runtime build/spike commands now exist; full native application and release
qualification commands remain planned. See verification.md for executed evidence.

## Available now

From repository root run `python3 scripts/check_spec_policy.py`. `make spec-check`
invokes the same validator; on the current machine make is blocked by the unaccepted
Xcode license. No license acceptance or developer-tool installation is part of planning.

## Implementation prerequisites

Architecture/security approval of the local identity column and contract; dedicated
macOS build environment; pinned dependency lock; physical clean Apple Silicon machine;
Developer ID/notarization credentials for the signed qualification stage. Tests use
isolated PostgreSQL databases and OS-user data roots, never the user's current business data.

## Planned commands (must be added by tasks before running)

```sh
python3 apps/desktop/scripts/build-runtime.py --target aarch64-apple-darwin
bash apps/desktop/scripts/package.sh --unsigned
.venv/bin/pytest packages/reality-core/tests/test_desktop_identity.py packages/reality-core/tests/test_desktop_setup.py packages/reality-core/tests/test_desktop_ai.py packages/reality-core/tests/test_desktop_secrets.py packages/reality-core/tests/test_desktop_http.py packages/reality-core/tests/test_desktop_maintenance.py
.venv/bin/pytest apps/desktop/tests
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml
node apps/web/scripts/desktop-onboarding-browser.mjs
bash apps/desktop/scripts/qualify.sh --artifact /path/to/Reality.dmg
```

`package.sh --unsigned` is for internal testing only; qualify rejects unsigned artifacts
for release evidence. The harness must support isolated data-root selection and retain
safe evidence under `specs/239-macos-local-app/evidence/` (never keys or business payloads).

## Required independent acceptance runs

1. US1: clean Mac, no Docker/Python/Node; install, Empty and Demo in separate data roots,
   AI skipped, interruption/retry, inspect first source-backed result. Repeat with live on.
2. US2: mocked deterministic provider outcomes plus explicit real-provider smoke with
   synthetic content; test removal/replacement, no internet, no inherited-key fallback,
   locked Keychain and no plaintext in logs/export. Never commit test credentials.
3. US3: actual occupied-port sentinels per FR-017, second launch, child kill, sleep/wake,
   close/Quit, stale endpoint report, invalid origin/Host/cookie and another OS account.
4. US4: database with sources/artifacts/secrets/pending jobs; encrypted backup to another
   Mac, wrong passphrase/corruption, low disk, interrupted update and failed migration.
   Compare IDs/source bytes/relations and verify no source auto-restarts after restore.
5. Four-language/both-theme keyboard walkthrough; inspect original product navigation.
6. Timed clean launch and 20 data-loaded runs on the declared minimum hardware; ten-person
   novice pilot for SC-001. Capture hardware/OS, sample definition, result and failures.

## Complete regression gates

Run `make lint`, `make test`, `make web-build`, `make spec-check`, then
`npm run i18n:audit` in apps/web. Use direct equivalents only when build tooling is
unavailable and record omissions. Run full migration upgrade/downgrade/rollback tests.
If command/tool/catalog/MCP schema changes occur, run `make docs-generate` and
`make docs-catalog-check`. A failing or unavailable required gate prevents release completion.

## Evidence record

Record build/revision, OS/hardware, signing/notarization verification, measured startup,
package/disk/memory sizes, test commands/results and recovery artifact hashes in
`verification.md`. Do not mark SC/FR/tasks done on the strength of this guide alone.

## Implemented isolated spike (2026-09-19)

```sh
DEVELOPER_DIR=/Library/Developer/CommandLineTools cargo test --offline --manifest-path apps/desktop/spike/Cargo.toml
.venv/bin/python -m pytest apps/desktop/tests -q
.venv/bin/ruff check apps/desktop
```

These tests need local loopback binding permission. They do not need PostgreSQL,
Docker, Tauri downloads or signing credentials. This validates the prototype only;
the earlier full-package commands remain planned until T003/T004 are complete.

## Implemented runtime pipeline

Use the exact cache/build/assembly commands in [apps/desktop/README.md](../../apps/desktop/README.md).
`build-runtime.py` also requires --cache and --output; these replace the earlier
placeholder standalone --target invocation. `assemble-runtime.py` takes a checked
wheelhouse and current core wheel, then `runtime-smoke.py` proves the migrated core
on a temporary private-socket database. No Tauri package.sh or release qualify.sh
exists yet; those commands above remain planned.
