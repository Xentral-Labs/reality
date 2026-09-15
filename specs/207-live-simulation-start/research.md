# Research

- Decision: use opt-in bounded offsets in the existing shared scheduling envelope. Research of materialize_due, controls and handler authorization confirms handlers must not own future eligibility. A separate timer/queue or handler-side timing was rejected.
- Decision: guarantee one initial order using produce; normal plan can emit zero. Scheduling alone cannot prove initial visible activity.
- Decision: use existing status reader and permissions. Bootstrap demo_data_state can become stale; inferring running state there was rejected.
- Decision: poll only visible eligible shell, cancel timed-out and old-company requests. Existing Home uses the same bounded read pattern.
- All unknowns resolved. No new dependency or schema.
