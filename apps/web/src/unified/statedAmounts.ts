/** Net and tax exactly as an invoice position states them (spec 284). */
export type StatedAmounts = { net?: string; tax?: string };

/**
 * The received detail a position sends: only the values the person typed, trimmed.
 * Nothing is derived: a missing net or tax stays missing, and gross is never filled
 * from them. The service compares the stated values and refuses a contradiction.
 */
export function statedDetail(value: StatedAmounts | undefined): StatedAmounts | undefined {
  const detail: StatedAmounts = {};
  const net = value?.net?.trim();
  const tax = value?.tax?.trim();
  if (net) detail.net = net;
  if (tax) detail.tax = tax;
  return net || tax ? detail : undefined;
}

/** A draft position with its stated detail cleaned, or without the key at all. */
export function withStatedDetail<T extends { reality_finance_v1?: StatedAmounts }>(position: T): T {
  const { reality_finance_v1, ...rest } = position;
  const detail = statedDetail(reality_finance_v1);
  return (detail ? { ...rest, reality_finance_v1: detail } : rest) as T;
}
