# Verification checkpoint: reviewed large item files

Implemented item CSV capture and review only. Party/location profiles, coherent
file orders, stock corrections and general artifact-worker cutover remain pending.

Original bytes precede interpretation. The retained selection names every included
or excluded source row; the parent digest fixes mappings, defaults and membership.
Package approval uses canonical item creation and the shared batch worker. Reads
and replay do not interpret the file again or settle queue work.

Observed local PostgreSQL evidence:

- 5,000 new items: ten fixed packages, zero preparation effects, one real shared
  queue delivery, 5,000 accepted items and exact retained identities. Response-loss
  recovery returns the original prepared selection after execution.
- HTTP preparation and confirmation enqueue work without accepting items; repeated
  status reads remain read-only.
- Conflicting current SKU refuses the complete package; changed callback defaults
  refuse before item creation. Foreign artifact/source/job/batch references refuse.
- Final combined PostgreSQL admission/catalog/action/refusal rerun: 72 passed in
  53.41 seconds. The foreign package test initially exposed an unscoped supplied
  source object, then passed after source/job tenant resolution preceded parsing.
- Real authenticated browser proof passed with separate API, Web and worker
  processes: dropped preparation and approval responses, reopening, original-byte
  download, exact receipt links, foreign download refusal and all four languages.
  The first browser run exposed a queue-polling tool-name mismatch; fixed.
- Web build and all four language audits pass. Business annotation audit has no
  unresolved rules, missing roots or approved tests.

This proves correctness for the item profile, not the required repeated throughput
benchmark, all file profiles or global CI completion.

## Existing artifact profile implementation checkpoint

The additional artifact planners cover the existing item, party, location,
inventory snapshot, external-stock, bank-statement and sales-order targets. Raw
capture and preparation accept no business records. Larger selections retain an
exact whole-file manifest and use shared batch settlement; complete file orders
retain distinct source identities. Single coherent units keep synchronous review.
Bank statements require current financial-owner authority and never execute a
bank transfer or infer an invoice allocation.

Missing source order totals now remain null through migration 0140, accepted
Document storage, the register and inspector. Received zero and inconsistent
totals are preserved. The migration preserves populated values and refuses an
unsafe downgrade. This is a proven schema change for FR-008a, not a derived total.

Observed evidence before this checkpoint:

- Initial six profile tests failed because artifact admission was unsupported;
  their implemented preparation/application cases passed.
- The larger-file and separate-order identity proofs failed against the initial
  one-package implementation, then passed with shared fixed batch selection.
- 43 shared intake, bulk, artifact and migration tests passed in 50.49 seconds.
- 14 artifact and populated migration tests passed in 10.01 seconds, including
  501 accepted locations through two exact units and truthful root completion.
- The register/inspector unknown-total regression passed separately.
- Frontend build, four-language audit, Ruff, spec policy and annotation checks
  passed. Generated catalog documentation was refreshed.

The full backend regression suite is running. Automatic legacy file-adapter
cutover, renewed review, mandate-based agent decisions, cross-path coverage and
controlled performance measurements remain open in specs 356/360/361. This
checkpoint does not claim that the universal intake rollout is complete.
