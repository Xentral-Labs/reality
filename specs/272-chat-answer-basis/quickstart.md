# Quickstart: Validate Compact Chat Answer Basis

## Automated proof

```bash
.venv/bin/pytest -q packages/reality-core/tests/test_storyline_trace.py packages/reality-core/tests/test_http_boundary.py
node --test apps/web/scripts/chat-answer-basis.test.mjs
cd apps/web && npm run i18n:audit && npm run build
```

Then run `make spec-check`, `make lint`, `make test`, and `make web-build`.

## Local walkthrough

1. Apply migrations and start the local API and Product Web using the repository's normal local commands.
2. Open Chat in an ordinary company with an open customer order.
3. Ask `Welche Kundenaufträge sind noch offen?`.
4. Expand `Grundlage dieser Antwort` below the assistant reply.
5. Verify at most four compact rows show the order reference, requested/reserved quantities, and a clearly derived blocked/uncovered observation.
6. Follow the order link and verify it opens the same tenant's existing detail/Inspector path.
7. Open an older reply or create a no-provider reply and verify no empty basis disclosure appears.
