# Quickstart: Engine Room

1. Start the local stack (API, MCP runtime, worker, scheduler, web) and sign in as a company owner.
2. Open **Inspector → Activities → Live**. Load a register page in a second browser as another member. It appears as channel Web under that member within 2 seconds.
3. With an MCP token, call a read tool and then propose a change. Approve it in the web. The Live tab shows one trace: MCP propose → web decide → business events. Each event opens the event Inspector.
4. Ask the chat a question that uses tools. Choose "Show in engine room" on the answer. The filter shows the chat request and its tool calls.
5. **Overhead (SC-003)**: on a quiet machine, time 500 identical `GET /api/tenants/{t}/inventory` requests, once with `REALITY_INTERACTIONS=off` and once with it on, back to back. The p95 difference must be ≤ 5 ms.
6. Sign in as a member and open `/app/inspector?inspector_view=live`. The page reports "not found".
7. Run `interactions.retention` with a clock 8 days ahead. Rows older than 7 days are gone, and business events are untouched.
