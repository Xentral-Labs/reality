# Quickstart: Increment 2 Verification

Use disposable macOS test accounts and PostgreSQL roots only. Never run recovery tests
against a user's business installation.

1. Run focused core key-provider tests and desktop Keychain adapter tests. Prove create,
   reopen, denial, missing item, replacement refusal, legacy-file migration and exact
   erasure; scan process arguments, logs and output for seeded values.
2. Seed a prior-version fixture with tenant records, original source bytes, secrets and
   queued jobs. Upgrade it and compare IDs, payload bytes, relations and secret reads.
3. Inject corrupt dump, insufficient space, killed restore, failed migration and failed
   readiness. In every case assert the old generation remains selected and no product
   role served the staged database.
4. Kill immediately before and after pointer replacement, reopen, and verify the journal
   deterministically retains either the old validated generation or the new validated
   generation without duplicate business effects.
5. Run the complete desktop suite, affected PostgreSQL tests, Ruff, Rust formatting,
   migration checks and spec policy. Record exact commands and results in
   `verification.md`; do not mark T011/T013 complete while any required check is red.

## Unsigned tester beta verification

1. Build only with the explicit tester-beta packaging option and inspect the app metadata,
   channel marker, visible warning and bundled manual-open guide. Confirm the bundle ID
   remains `ai.runreality.local` and the artifact name is unmistakably a beta.
2. On a disposable clean macOS account, use Finder's Open flow, create a company and reopen
   ten times. Confirm the same installation and records remain and the warning stays visible.
3. Inspect the temporary custody record without printing its contents: require a regular,
   current-user-owned `0600` file. Seed malformed, missing, symlinked and permissive variants
   and require startup to fail before PostgreSQL, API, scheduler or worker begins.
4. Scan the app bundle, arguments, logs, browser storage, backup and default diagnostics for
   seeded generated and upstream secret values. Require zero matches outside the custody record.
5. Replace the beta with a simulated entitled successor. Exercise denial and termination around
   Keychain write/readback; require the original record and business data to remain. On success,
   require exact value equality in both Keychain entries and absence of the temporary record.
6. Prove CI uploads the beta only as a private workflow artifact and rejects tag, GitHub release,
   public website and auto-update publication paths. Record all evidence in `verification.md`.
