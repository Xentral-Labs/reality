# Feature Specification: Persistent macOS Distribution

**Feature Branch**: `240-persistent-macos-distribution`  
**Created**: 2026-09-19  
**Status**: Proposed  
**Language**: English  
**Input**: Turn the disposable Reality Local macOS proof into a persistent application that can be downloaded from the public website and retains all local data when the app closes.

## Context and Intent

### Problem

The current macOS development package intentionally creates a fresh PostgreSQL cluster
for each run and deletes the installation, company, credentials and test data on Quit.
That behavior is useful for acceptance testing but cannot be offered as the public
Reality Local product. A downloaded application must preserve business data across
normal closes, restarts and application upgrades, while still offering an explicit,
safe way to erase the complete local installation.

### Scope

Define the persistent installation identity and filesystem layout; PostgreSQL, API,
scheduler and worker lifecycle; Keychain custody; restart and crash recovery; backup,
restore and migration checkpoints; app-only removal versus confirmed full erasure;
signed/notarized universal packaging; signed updates; clean-Mac qualification; and the
public website download contract.

### Non-Goals

- Hosting customer business data in a Reality cloud service.
- Adding a second database engine or replacing PostgreSQL.
- Silently collecting diagnostics, credentials or business payloads.
- Automatically authorizing real external connections during installation.
- Replacing the existing company setup, Demo Data, job or AI settings services.

## User Scenarios & Testing

### User Story 1 — Close and continue later (Priority: P1)

A person installs Reality Local, creates a company, closes the application and later
reopens it with the same company, records, settings and source controls available.

**Independent Test**: Create a company and identifiable records, quit normally, verify
all child processes stop, reopen the installed app and prove the same tenant-scoped
records are returned from the same persistent PostgreSQL cluster.

### User Story 2 — Update without losing data (Priority: P1)

A person installs a signed newer version and continues with existing data after a
checked migration. An interrupted or failed migration restores the last valid state.

**Independent Test**: Upgrade a prior signed fixture through the supported version
matrix, inject interruption and low-disk failures, and verify either the upgraded data
or the original checkpoint is usable with no partial authority.

### User Story 3 — Remove the app or erase everything (Priority: P1)

A person can remove only the application while retaining local data, or deliberately
choose a separately confirmed full erasure that removes the database, settings,
artifacts and owned Keychain entries for exactly this installation.

**Independent Test**: App-only removal followed by reinstall restores the company;
confirmed full erasure removes only the selected installation and a reinstall starts
empty. Unrelated Keychain items and other installations remain unchanged.

### User Story 4 — Download a trusted macOS release (Priority: P1)

A visitor downloads Reality Local from the public website, installs it without a
Gatekeeper warning and can verify its version, system requirements and checksum.

**Independent Test**: On clean supported Macs, download the published HTTPS artifact,
verify checksum, Developer ID signature, Hardened Runtime, notarization and stapling,
install from DMG, finish first use and perform one signed update.

### User Story 5 — Recover or ask for support safely (Priority: P2)

A person can create an encrypted backup, restore it on a compatible Mac and export a
diagnostic bundle that excludes credentials and business contents by default.

**Independent Test**: Restore a backup with the correct Keychain/credential workflow;
reject corrupt, wrong-version and wrong-key backups; scan diagnostics for secrets and
business payloads.

## Requirements

### Functional Requirements

- **FR-001**: The release application MUST use a stable opaque installation identity
  and a versioned directory beneath the user's Application Support directory.
- **FR-002**: Normal window close and Quit MUST stop Reality processes cleanly without
  deleting PostgreSQL data, settings, artifacts, credentials or installation identity.
- **FR-003**: PostgreSQL MUST remain the only supported database and MUST use a private
  installation-scoped socket plus dynamically allocated internal ports where needed.
- **FR-004**: Startup MUST supervise PostgreSQL, API, scheduler and worker, detect stale
  processes and recover safely after forced termination, sleep and restart.
- **FR-005**: The existing trusted local identity and tenant boundaries MUST survive
  restarts without admitting request-provided identity or disabling product auth.
- **FR-006**: LLM and integration credentials MUST use installation-owned macOS
  Keychain entries; secret values MUST NOT appear in arguments, browser storage,
  logs, diagnostics or API reads.
- **FR-007**: Before an application upgrade changes data, Reality MUST create and
  validate a recoverable checkpoint and MUST restore it if migration cannot complete.
- **FR-008**: The product MUST expose backup and restore with version, integrity,
  installation and encryption checks before replacing active data.
- **FR-009**: Removing the `.app` MUST preserve local data. Full erasure MUST be a
  separate, explicit and confirmed action that identifies every owned item before
  deletion and never uses global Library or Keychain deletion.
- **FR-010**: The distributable app and DMG MUST be versioned, signed with Developer ID,
  use Hardened Runtime, be notarized and staple the notarization result.
- **FR-011**: The release MUST qualify each supported architecture and macOS version on
  a clean machine without Homebrew, developer tools or an existing PostgreSQL install.
- **FR-012**: Updates MUST be signed, verified before installation and recover safely
  from download, signature, disk-space, process-stop and migration failures.
- **FR-013**: Diagnostics MUST be opt-in, locally reviewable and exclude credentials and
  business payloads by default; any expanded export requires explicit scope selection.
- **FR-014**: The public website MUST publish an HTTPS download, version, release date,
  supported macOS/architecture list, checksum, release notes, install instructions,
  local-data statement, backup guidance and full-erasure instructions.
- **FR-015**: First use MUST retain the shared company/demo/live and optional Anthropic
  setup from spec 239; it MUST NOT introduce desktop-only business services.
- **FR-016**: Release CI MUST produce reproducible manifests for bundled PostgreSQL,
  Python, native extensions, frontend and app resources and fail on undeclared input.

## Edge Cases

- The app is killed while PostgreSQL is checkpointing or while an update is staged.
- The device has insufficient free space for a checkpoint, migration or backup.
- A stale socket, PID file or prior process belongs to another installation.
- Keychain access is denied, the original key is missing or restored data uses another key.
- The application bundle is replaced while background children are still stopping.
- Two copies of the same installation are started concurrently.
- The backup is corrupt, newer than the app, incomplete or belongs to another identity.
- The user removes the app, retains data and reinstalls a newer compatible version.

### Data and Architecture Requirements

- **DR-001**: No business schema expansion is authorized by this specification; any
  later schema need requires a separately proven use case.
- **DR-002**: Source → Evidence → Reality, tenant scope and shortest true links remain
  unchanged in persistent and restored data.
- **DR-003**: Scheduler and worker use the shared registry and services; neither runs
  migrations and no per-desktop browser timer becomes a job authority.
- **DR-004**: Installation metadata is operational packaging state, not business truth,
  and stays outside tenant business tables unless a later specification proves otherwise.

## Success Criteria

- **SC-001**: Twenty consecutive quit/reopen cycles preserve the same test company and
  records and leave no orphan Reality or PostgreSQL process.
- **SC-002**: Every supported prior-version fixture upgrades or restores its checkpoint
  under the clean-Mac matrix with zero lost or duplicated business records.
- **SC-003**: App-only uninstall/reinstall restores data; confirmed erasure leaves no
  owned data or credential and preserves unrelated items in 100% of qualification runs.
- **SC-004**: Gatekeeper accepts every published artifact offline after download, and
  signature, notarization, stapling and checksum checks pass.
- **SC-005**: Automated secret scanning finds no configured credential or sampled
  business payload in logs, arguments, browser storage or default diagnostics.

## Requirement Traceability

| Requirement | Scenario | Planned evidence |
|---|---|---|
| FR-001–006, DR-002–004 | US1 | Restart, crash, identity, tenant and process lifecycle tests |
| FR-007, FR-012 | US2 | Version-fixture migration, interruption and rollback matrix |
| FR-009 | US3 | App-only removal and installation-scoped full-erasure tests |
| FR-010, FR-011, FR-014, FR-016 | US4 | Clean-Mac download, signature, notarization, manifest and update checks |
| FR-008, FR-013 | US5 | Backup/restore integrity and diagnostic secret-scanning tests |
| FR-015 | US1, US4 | Shared company/demo/live/AI setup regression suite |

## Assumptions and Dependencies

- The owner supplies an active Apple Developer account, final product name, bundle ID,
  supported architecture decision and public HTTPS download location before release.
- Spec 239's disposable package remains the fresh-test harness and is never relabeled
  as the persistent release.
- The existing PostgreSQL, migration, job, company setup, Demo Data and AI settings
  contracts remain authoritative.
- Product planning must decide the signed update framework and Intel support during
  clarification before implementation planning begins.
