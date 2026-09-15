# Quickstart: Delete Empty Chat Sessions

## Automated proof

```bash
make spec-check
PYTHONPATH=packages/reality-core/src .venv/bin/pytest -q packages/reality-core/tests/test_master_data_api.py -k "copilot and (archive or empty)"
cd apps/web
npm run test:contracts
npm run i18n:audit
npm run build
```

Expected: every command passes; an empty session disappears permanently while a session with a
message remains in the archive and restores with its message.

## Manual acceptance

1. Start a new chat and send no message.
2. Open its options; verify the action says `Delete chat` and confirms permanent removal.
3. Confirm; verify the session appears in neither active nor archived chats.
4. Send a message in another chat, then remove it.
5. Verify its action says `Archive chat`, it appears under Archived chats, and restore retains the
   complete conversation.

## Recorded verification

- Backend API suite: 45 passed.
- Frontend contract suite: 188 passed.
- Translation audit: English, German, Dutch, and Spanish passed with no missing entries.
- Production Web build: passed.
- Schema/migration review: no schema, migration, backfill, source, evidence, or Reality change.
