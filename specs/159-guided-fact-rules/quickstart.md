# Validation guide

Run make spec-check, make lint, make test and make web-build from the active integration
worktree. Run guided-rules-browser.mjs against a dedicated Vite preview with BASE_URL,
PLAYWRIGHT_MODULE and PLAYWRIGHT_EXECUTABLE. Synthetic API fixtures prove no unconfirmed
writes. Open Inspector → Rules → Fact rules; inspect source/example, nested condition,
simulation and replay workflows at desktop and 390px in English and German.

All final gates passed; see `verification.md` for counts and production-browser evidence.
