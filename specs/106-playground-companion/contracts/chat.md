# Companion API
POST /api/playground/runs/{run_id}/chat requires an eligible authenticated run owner.
Body: message (1–4000 characters), history (0–12 role/content entries).
Response: {answer: string}. Foreign runs are not found; provider failures explicit.
No submitted tenant or system messages accepted. No business or proposal writes.
