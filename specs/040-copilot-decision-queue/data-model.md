# Data Model: Copilot Decision Queue and Chat Archiving

## ChatSession

Add nullable `archived_at` UTC timestamp. `NULL` means active; a value means hidden from the
ordinary conversation list but retained and restorable. ChatMessage ownership is unchanged.

## ChangeProposal

No schema change. `status=proposed` feeds Pending approvals; terminal `executed` and `rejected`
rows feed Decision history. Existing rows have no reliable ChatSession provenance, so none is
invented.

## OperationalException

No persistence change. Exceptions remain derived and occupy a separate view.
