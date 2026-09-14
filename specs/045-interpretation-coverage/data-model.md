# Data Model: Interpretation Coverage

## InterpretationOutcome

Immutable audit row with opaque ID, tenant/source/job FKs, attempt, classification, interpreter name/version, reason code, safe summary, and UTC completion time. `(tenant, job, attempt)` is unique. Attempt zero is for terminal intake classifications. Classifications: `interpreted`, `needs_review`, `unsupported`, `stale`, `conflict`, `failed`.

These classes are mutually exclusive. `needs_review` is an explicit, safe interpreter refusal caused by ambiguous business meaning; `failed` follows an exception and rollback. `pending` and `processing` are non-terminal ImportJob states and produce no outcome. `not_recorded` is a computed historical-coverage label, not a stored outcome.

## InterpretationRecordReference

Child row with opaque ID, tenant/outcome FKs, controlled record type, and opaque record ID. `(tenant, outcome, type, record ID)` is unique. Only interpreted outcomes may have references. Initial types: document, document_line, commitment.

## Coverage Row

Computed source metadata, current job state, ordered outcome summaries, current classification, and produced references. It excludes raw payload/input/error. No outcome means `not_recorded`.
