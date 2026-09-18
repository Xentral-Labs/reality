# Research and decisions
Read-only agents balances_232/history_232 confirmed canonical service boundaries.
party_balances is paginated (100); extract its unpaged Decimal/date rows. Numeric
settlements retain LedgerEntry.effective_at, SettlementAllocation.allocated_at and
LedgerReversal.reversed_at. All must share one exclusive cutoff. aging_register(as_of)
is only an aging reference date and is not historical balance support.
Movement.occurred_at plus appended compensation/replacement legs supports effective
physical stock. Reservation.status is overwritten; payment terms are mutable; neither
can prove past state. Universal recorded-at history is missing. OpeningScope.cutover_date
and opening-stock movements constrain backward coverage. No event-log replay or schema
expansion is justified for this slice.
