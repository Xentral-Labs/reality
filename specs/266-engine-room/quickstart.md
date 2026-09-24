# Quickstart: Engine Room

1. Start the local stack (API, MCP runtime, worker, scheduler, web) and sign in as a company owner.
2. Open **Inspector → Activities → Live**. Load a register page in a second browser as another member. It appears as channel Web under that member within 2 seconds.
3. With an MCP token, call a read tool and then propose a change. Approve it in the web. The Live tab shows one trace: MCP propose → web decide → business events. Each event opens the event Inspector.
4. Ask the chat a question that uses tools. Choose "Show in engine room" on the answer. The filter shows the chat request and its tool calls.
5. **Overhead (SC-003)**: on a quiet machine, time identical `GET /api/tenants/{t}/items` requests with `REALITY_INTERACTIONS=off` and `on`, in alternating blocks of 100 (2000 requests), with the background writer started as the app lifespan does. The p95 difference must be ≤ 5 ms.

   Measured 2026-09-24 on a shared, loaded laptop (load average 23, two other sessions' pytest runs, Docker Desktop at 200 % CPU). This is **not** a quiet-machine result:
   - First design (inline writes, `@app.middleware`): median +5.9 ms, p95 +10 ms.
   - Final design (queue, batch, ASGI): three runs gave medians −0.6, +3.9 and +3.7 ms, and p95s +1.3, +10.4 and −15.4 ms. The baseline itself moved between 18 and 28 ms median.
   - Verdict: SC-003 is not proven. Re-measure on a quiet machine before merge.
6. Sign in as a member and open `/app/inspector?inspector_view=live`. The page reports "not found".
7. Retention: reads never return rows older than 7 days, and the next recorded interaction of the company deletes up to 500 of them (at most every 10 minutes per process). Business events are untouched.

## Live browser check

`apps/web/scripts/engine-room-live-browser.mjs` runs against a real API (not fixtures). Seed a database with an owner `owner@example.test`, a member `member@example.test` (password `a-long-account-password`), one company and one MCP token. Run the API with `REALITY_AUTH_MODE=enabled`, Vite on `127.0.0.1:5266` proxying to it, then:

```bash
TENANT=<id> TOKEN=<mcp token id> SHOTS=/tmp/shots \
PLAYWRIGHT_MODULE=<path>/playwright/index.mjs \
ENGINE_ROOM_MCP_CALL='<command that calls one MCP read tool with that token>' \
node apps/web/scripts/engine-room-live-browser.mjs
```

Result on 2026-09-24: 24/24 checks passed, covering live arrival, member attribution, route template, written stage, MCP token and issuer, linked events, pause and resume, URL filter and reload, replay, owner-only access, the token entry point, 390 px width in dark mode and zero console errors.
