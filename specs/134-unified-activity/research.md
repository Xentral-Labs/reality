# Research
Existing api.timeline supports hours 0..720, default 24, query, attention filter and before_sequence. It returns at most 100 events by default and has_more from an extra row. Ordering is descending recording sequence; time-window filtering uses occurred_at. Activities group only the current page and must not be presented as complete processes. Summary/chart counts have different scopes and are not used.

Read-only research by order_research confirmed existing service tests for tenant/cursor/business context. Area classification differs between filters and returned events; omit area filters. status=completed is not business fulfillment; do not show it as success. Preserve structured business_context values and localize known action titles. Unknown title falls back to server wording.

Always inspect business_event. Subject links allow only document, document_line, source_record, business_event, fact, commitment, party, item, location, reservation, movement, payment, exception. Other subjects are available through exact technical values and event evidence.

No new service or schema is needed. Reject grouped timelines, total counters and unread polling as unnecessary scope.
