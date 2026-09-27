# Quickstart: Service refusals speak the user's language

## Setup

Run an isolated stack (see `specs/282-cost-review-draft/quickstart.md` for the recipe) with a
business company and a delivered sales order line. Use two accounts, or switch the language
in the account settings: one in German, one in English.

## Checks

1. **US1:** in German, record an invoice for the order line with gross 60.00, net 50.00 and
   tax 9.50. The form refuses it with the German sentence for `invoice_net_tax_mismatch`, and
   nothing is recorded.
2. **US1 fallback:** in English, the same attempt shows "Net plus tax differs from the invoice
   gross." exactly as before.
3. **US2:** in Dutch, prepare an order whose line has no amount. The refusal names the line
   number in the Dutch sentence. In master data, a negative lead time is refused with the
   field name in Dutch.
4. **US3:** in Spanish, force a refused tool call in the chat. The panel shows the Spanish
   sentence, and the tool result in the interaction log carries the English sentence and the
   code.
5. **FR-008:** an MCP client calling the same tool receives the English `message`, and the
   refusal code in `code`.

## Evidence

| Check | Result | Date |
|---|---|---|
| Checks 1–5 (T904) | — | — |
