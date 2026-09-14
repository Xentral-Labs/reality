# Interface Contracts

- Ordinary `/api/auth/signup` accepts explicit `playground` boolean (default false for compatibility). Invitation signup does not register Playground intent. UI submits true with clear creation consent.
- `GET /api/company-setup/playground` reads applicability, receipt state, archive state and availability only. Authenticated account scope, no creation.
- `POST /api/company-setup/playground` accepts `{ "confirmed": true }`; requires active verified consent and calls canonical setup using the fixed request key. Returns existing company result. Disabled/archived cases remain explicit errors; retry uses the same POST.
- Copilot read payload adds nullable `allowance`: limit, used, remaining, resets_at. Null means existing provider/company behavior applies. Rejection before managed dispatch uses existing InvalidOperation error transport, with useful reset text. UI refreshes authoritative allowance after every send attempt.
- Operational starter task routing is read-only. A matching successful rendered result signals completion; clicks, loading, errors and uninitialized observations cannot signal success.
- GitHub uses an ordinary voluntary external link to `https://github.com/Xentral-Labs/reality`; click/dismiss suppresses the prompt for the account in this browser.

Public copy says “Try for free”; the owner explicitly chose no initial expiry and no permanent-free promise.
