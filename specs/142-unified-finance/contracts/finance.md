# Finance presentation contract

`/app/finance` uses existing authenticated `/api/tenants/{tenant}/finance/{open-items,payments,journal}` GETs. Page defaults 1, size 50; returned pager governs bounds. Open items: q, flow receivable/payable, item_status outstanding/open/partial/paid/empty. Payments: q reference IDs, direction incoming/outgoing/empty. Journal: q reference IDs/account, exact account. Existing backend contracts unchanged.

URL fields: finance_view (open-items/payments/journal), flow, finance_status, direction, account, entry; q/page/tenant reused. Invalid enum values fall back to defaults. entry means document/payment/ledger_entry according to tab. Tab change clears entry/search/page; company change additionally clears filters/account. Account codes remain exact text; account links select the exact journal account.

Controls show complete filtered open-item or journal totals, one card per currency with named components. Payment totals response is ignored; no cross-currency arithmetic. No invented observed timestamp. Canonical reversal labels are preserved. Advanced operations remain links to supporting routes.
