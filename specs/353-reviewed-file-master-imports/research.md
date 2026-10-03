# Research: Reviewed file, master-data and stock imports

Read-only repository investigation on 2026-10-03. Findings describe the current
checkout; proposed behavior is not claimed as implemented.

## R01: Preserve single-package limits, add a distinct large-file path

- Decision: Preserve single-package limits, add a distinct large-file path.
- Rationale: item_imports MAX_ROWS=500/MAX_BYTES=2MiB is explicit existing behavior; applying that parser before packaging would reject 5,000 rows.
- Alternatives rejected: Simply labelling the current CSV path as supporting 5,000 rows.

## R02: Validate duplicates over the full file

- Decision: Validate duplicates over the full file.
- Rationale: Per-package validation cannot detect cross-package collisions before approval.
- Alternatives rejected: Ignoring duplicates until a later package fails at execution.

## R03: Keep external stock separate from book correction

- Decision: Keep external stock separate from book correction.
- Rationale: External stock is a received assertion; inventory_snapshot currently emits movements from a comparison with book stock.
- Alternatives rejected: Accepting an external assertion as authority to alter book stock.

## Compatibility review

Legacy tests that expect immediate accepted interpretation need deliberate updates
to prepare → review → approve assertions, preserving their existing domain refusal
checks. The roadmap is not evidence of current autonomous agent permission or
5,000-row support. No unresolved product clarification remains; engineering defaults
and limits are explicitly documented in spec/plan/contracts.
