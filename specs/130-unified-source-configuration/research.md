# Research decisions
Read-only plan research by order_research inspected core.py:9985–10176 and web authorization.
- Existing member-authorized services suffice. No owner-only UI policy added.
- System code normalized and tenant-unique; duplicate POST can fail, including concurrent database uniqueness. No automatic retry.
- Flags are metadata only; they do not enforce common enqueue admission. UI cannot claim pause/disconnect/sync.
- Interpreter availability is code/source-type registration evidence only, not live transport.
- No rename, description update, receipt/idempotency token or optimistic concurrency API exists. Show current-state recovery, not exact action proof.
- Rejected alternative: migrate connector-shell wizard, which presents templates without live transport. Deferred alongside arbitrary capability creation.
