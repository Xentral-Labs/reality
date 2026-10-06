# Local correspondence contract (complete v2)

This is a finite rehearsal artifact contract, not production email transport.

Each `messages.jsonl` row records `day`, actual `recorded_at`, opaque `party_id` and
`source_record_id`, `direction`, `status`, and the exact immutable Source `payload`.
Payload contains sender/recipient, subject/body, synthetic marker,
`transport: local_simulation`, unique run-local `message_id`, `thread_id`, optional
`in_reply_to`, kind, and explicit existing business references. Order IDs are included
when already available; a source is never rewritten to attach a later-created order.

Incoming records have `direction: incoming`, `status: received`. Fixture-generated
outgoing responses have `direction: outgoing`, `status: simulated`. Custom responses
have `direction: outgoing`, `status: proposed`; none grants mail approval or reports
provider acceptance. Message evidence never fulfills a commitment or posts money.

The copied released operator view includes messages as recorded. Private future
notices remain absent until their release day. Custom complete-profile operators may
return this command through the existing callable interface:

```json
{"kind": "reply", "message_id": "RELEASED_INCOMING_ID", "subject": "Exact subject", "body": "Exact plain text"}
```

Subject/body must be nonempty strings and remain exact. The message ID must identify
an already released incoming message in this run. Recipient, party and thread are
inherited from that message, never invented from an address. This stores draft evidence
only and has no dispatch operation. An invalid command stops with retained uncertainty;
it is not automatically retried. A fresh explicit draft command creates a fresh message.

Supplier confirmations/delay notices release one day after an accepted purchase;
receipt notices require an accepted warehouse receipt. Customer cancellation/return
messages require their released events; status queries release one day before the
stated deadline. Prompt/delayed baseline replies follow released messages and accepted
business actions. Idle/custom operators receive no automatic outgoing responses.
