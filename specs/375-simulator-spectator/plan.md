# Implementation Plan: Simulator spectator

**Branch**: feat/company-reference-simulator | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

## Summary
Read-only local Python HTTP viewer and static browser assets under the simulator. Normalize existing explicit journal references into customer/supplier messages and related activity. New runs export atomic spectator snapshots after checkpoints and at termination, preserving old artifact compatibility.

## Technical Context
Python 3.12 standard library HTTP server and artifact reader; plain HTML/CSS/JavaScript; no added dependency. Run-local JSON/JSONL only, no database in viewer. pytest contract/security tests, actual simulator integration, Chromium/Playwright browser checks. Loopback Linux/macOS development use. Poll five seconds, one read-only selected-run request, at most the current bounded month journals. No business mutations or scheduling infrastructure.

## Constitution Check
| Principle | Result | Evidence |
| --- | --- | --- |
| Source → Evidence → Reality | PASS | Original source/message/receipt IDs exposed, no invented business evidence |
| Reality authority | PASS | Displays captured checkpoints, no stock/account calculations |
| Proven schema | PASS | No schema or migration |
| Tenant/services | PASS | Viewer only reads explicitly selected local run files, all business calls remain unchanged |
| Spec/test evidence | PASS | Accepted scope; tests before code; FR task map below |
| Explainable UI | PASS | Named events, optional original evidence; separate simulator UI |
| Simplicity | PASS | Standard-library server, static assets; no product deployment |
| Received values | PASS | Original message amounts and captured totals preserved |

Post-design gates remain PASS. No exception required.

## Project Structure
- scenarios/company_simulator/viewer/{__init__.py,__main__.py,reader.py,server.py,index.html,app.js,style.css} (relative to packages/reality-core)
- scenarios/company_simulator/complete.py: export spectator snapshot; no operator/business flow changes
- tests/scenarios/test_simulator_viewer.py; test_complete_company.py: test-first coverage
- specs/375-simulator-spectator/{research.md,data-model.md,contracts/viewer.md,quickstart.md,tasks.md,review.md}

## Design and risks
Match prepared/committed tool records by proposal/event IDs to resolve explicit source context and accepted order counterparties. Match party_create returned IDs to input records in order as existing bridge does. Fail unresolved mappings visibly. Prefer snapshot/report world events for business timeline; older unfinished runs fall back to accepted operations with separate operation counts, never claim case-family coverage. Original messages render as text. HTTP GET routes only, fixed assets and /api/runs[/RUN]; enforce realpath containment for run and artifact files; no arbitrary downloads. Loopback bind and local Host/Origin checks. Truncated tails and malformed files are surfaced as notices. Snapshot includes released view, refs, world events, goals and coverage, but no private future behavior. Atomic replace avoids partial snapshot publication.

## Verification and rollback
Test meaningful read security, identity, count/status distinction and partial-write recovery first. Browser checks cover selection, filtering, refresh, raw text, narrow viewport and inert hostile content. Verify complete and Shopify snapshot export with existing integration cases, then full backend suite; lint/spec/whitespace gates. No product web/catalog/schema change, so those gates are inapplicable. Remove viewer and snapshot emission to roll back; older artifacts remain readable.

## Correspondence presentation extension

Spec374 FR-009 adds explicit local correspondence journals. Keep existing party filtering and inert text rendering; add human-readable local-simulation/draft badges, simulation day and recorded reply-to subject. Browser proof covers supplier conversation, simulated-send boundary and reply context without changing product UI or backend business authority. Constitution gates remain PASS.

## Live/replay story extension

Approved scope: user's request to connect the existing playful prototype to growing journals. Add fixed story assets and a read-only story-data endpoint using ArtifactStore containment/loading; no database, mutations, scheduler or schema. Watch mode follows latest complete checkpoint, replay uses available recorded days. Existing spectator remains the fallback for unsupported profiles. Constitution gates PASS; no unresolved clarification or critical analysis finding. Verification: artifact endpoint regression, browser append/poll/replay/run-switch checks and existing viewer tests. Full business suite is not required for this isolated read-only adapter change.
