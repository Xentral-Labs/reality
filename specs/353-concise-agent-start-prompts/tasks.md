# Tasks

- [x] Review requirements and cadence against the user's accepted scope (FR-001–005).
- [x] Plan documentation verification before editing; constitution and analysis PASS.
- [x] Rewrite all prompts and align surrounding instructions in both locales (FR-001–005).
- [ ] Run documentation and specification gates; review length, timing and boundaries.
- [ ] Commit and prepare a reviewable pull request, reporting access limitations.

## Verification Evidence

Formatting, spec policy, docs build, prompt length/identifier audit and targeted
starting-path, home and relative-link tests pass. The full docs suite has 12 passing
files and one failing file: docs-contract reports spawnSync python3 EPERM in the
unrelated live MCP verifier. Direct execution reports 62 of 63 tests passing; the
verifier subprocess prints success and exits zero but Node receives EPERM. Full
suite completion remains unchecked due to this environment limitation.
