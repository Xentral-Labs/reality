# Research

- Decision: reuse existing movement receipt validation and whole-reservation release. Rationale: services already define effects and tracking; partial release is not supported and is out of scope. Alternative rejected: new UI arithmetic or direct ORM mutation.
- Decision: resolve release reservation→commitment internally. Rationale: shortest true relationship; canonical tool accepts reservation_id only.
- Decision: dedicated release proof using exact action event and released reservation. Rationale: existing release events record commitment_id, not a quantity; no backfill or second authority.
- Decision: extend current state-bound review and unresolved pool protection to destination receipts and reservation IDs. Rationale: existing proposal claim/reconcile lifecycle avoids duplicate execution.
- Research source: read-only research agent plus local inspection of services/core.py, delivery_actions.py, delivery_reads.py, tools/application.py and Playground editors. No unresolved design question remains.
