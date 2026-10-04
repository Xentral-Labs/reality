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
