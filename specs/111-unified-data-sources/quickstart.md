# Validation guide

Baseline Spec110: 1491 backend tests plus 7 existing skips; 125 frontend contracts. Add source API and browser coverage before implementation. Run the full PostgreSQL suite with PYTHONPATH=src and two load-scope workers; make lint/spec-check, web formatting/contracts/i18n/build, all unified browser harnesses and docs formatting/tests/build. Review actual isolated local preview 5177/8007.

Built-in specification quality 8/8. Research resolved bounded metadata, exact version filtering and job-status semantics before implementation. No extension hooks configured. Technical completion does not authorize rollout or retirement.

## Technical review and focused proof

- New metadata and exact-evidence tests: **2 passed**. Source metadata queries
  were captured to prove they do not select source payload, job input or error.
  Counts and version paging are tenant-scoped, including unregistered origins
  and missing/unmapped jobs; reads leave authoritative record counts unchanged.
- Initial metadata API test failed before implementation. The first evidence
  fixture exposed the existing one-document-per-source-and-type constraint;
  the corrected fixture uses two distinct document types for valid paging proof.
- Exact source filter is additive inside shared document_page before count/page;
  existing clients retain defaults. It does not infer a source from a human number.
- Existing evidence reads and selected Inspector retain their payload-size
  characteristics. This increment only guarantees metadata column selection
  for the new systems and original-record lists, not a global payload byte cap.
- Built-in Source/Evidence domain vocabulary remains unchanged; the evidence
  tab uses the existing localized Documents label.

The real authenticated local preview passed system → two source versions →
original/reload → exact v2 evidence → document Inspector. Metadata excludes
payload. `/private/tmp/reality-111-live.log`. Synthetic examples were installed
through shared services only in the dedicated sample database and tenant.

Desktop received-record review confirms neutral job status, explicit provenance
and clear original/evidence actions. No connection-health claim or new import
execution path is introduced. Advanced source setup, imports and technical
Explorer remain supporting paths.

## Verified gates — 2026-09-07

- Full PostgreSQL suite: **1493 passed, 7 existing skips**, 207.51 seconds
  (`/private/tmp/reality-111-backend.log`).
- Frontend contracts **126 passed**; localization **1449/1449** in en/de/nl/es.
  Formatting and production build passed. Logs use
  `/private/tmp/reality-111-{contracts-final,i18n-final,format,web-final}.log`.
- Docs: formatting, **45 tests** and production build passed. Python lint,
  spec policy and diff whitespace checks passed.
- Final source browser passed system → source version → exact evidence,
  escaped original, Inspector focus/reload, paging/filter/retry/company reset
  and no mutation requests, with **48 localized screenshots**.
  `/private/tmp/reality-111-browser-final.log`.
- Foundation/delivery regression passed all case/launcher/Chat action entries,
  confirmation recovery, Inspector and its full visual matrix.
  `/private/tmp/reality-111-foundation.log`.

Final visual review included light desktop received records and dark mobile
documents. Long metadata wraps inside cells; the table has its own horizontal
scroll container. The selected payload remains unchanged original content.

Finance regression passed all three views and 48 screenshots; Analytics/master
data passed four-family review/recovery and 64 screenshots; warehouse/attention
passed exact-item traversal, resolved/error states and 64 screenshots. Logs:
`/private/tmp/reality-111-finance.log`, `reality-111-workspace.log` and
`reality-111-operations.log` in the same temporary directory.

All ten tasks are technically complete. Final review has no remaining critical
finding. The 5177/8007 local preview is ready for owner review. No deployment,
merge, legacy UI deletion or Playground retirement is claimed.
