# Application Tool Contracts

Every mutation uses the existing proposal preview and explicit confirmation envelope.

## `finance_dunning_notice_record`

Input: invoice IDs, level, notice date, optional exact fee, reason and optional source identity. Preview returns party, currency, invoice residuals, fee accounts and resulting receivable. Confirmation returns notice/document/membership IDs, optional fee posting IDs and inspector links.

## `finance_dunning_notice_reverse`

Input: notice ID and reason. Confirmation records reversal and reverses the effective fee posting exactly once.

## Existing settlement-adjustment tool

Add customer-only `bad_debt`. Preview names the dedicated expense account. Confirmation and reversal envelopes remain unchanged.

## `finance_deposit_record`

Input: side, party, amount, currency, reference, effective time and source identity. Confirmation returns deposit document, source, posting group and control entry.

## `finance_deposit_clear`

Input: deposit document ID, final invoice ID and exact amount. Preview returns available/open before and after. Confirmation returns SettlementAllocation and inspector links.

## Existing commitment revision tool

Keep optional quantity and explain that increases and decreases are restatements. Shipment and receipt actions remain unchanged.
