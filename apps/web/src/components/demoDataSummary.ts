// Feature 168: the order-to-cash observations of a Demo Data connection.
// Pure shaping for the integration panel; every value comes from the status read.

export type OrderToCash = {
  invoices_issued: number;
  payments_received: number;
  payments_allocated: number;
  invoices_settled: number;
  open_residuals: number;
  credit_created: string;
  unmatched_payments: number;
  failed: number;
  last_settlement: string | null;
  next_settlement: string | null;
};

export type OrderToCashRow = { key: keyof OrderToCash; label: string; value: string };

/** Counter rows in reading order; labels are English source strings for t(). */
export function orderToCashRows(block: OrderToCash | undefined): OrderToCashRow[] {
  if (!block) return [];
  const rows: [keyof OrderToCash, string][] = [
    ["invoices_issued", "Invoices issued"],
    ["payments_received", "Payments received"],
    ["payments_allocated", "Payments allocated"],
    ["invoices_settled", "Invoices settled"],
    ["open_residuals", "Open residuals"],
    ["credit_created", "Customer credit created"],
    ["unmatched_payments", "Unmatched payments"],
    ["failed", "Settlement failures"],
  ];
  return rows.map(([key, label]) => ({ key, label, value: String(block[key]) }));
}

/** Anything a person may want to look at: a difference, a credit or a failure. */
export function needsAttention(block: OrderToCash | undefined): boolean {
  if (!block) return false;
  return (
    block.open_residuals > 0 ||
    block.unmatched_payments > 0 ||
    block.failed > 0 ||
    Number(block.credit_created) > 0
  );
}

export type FinanceView = "payments" | "open-items" | "journal";

/** Deep links into the Finance page of the unified app, filtered to the synthetic source. */
export function financeLink(tenantId: string, view: FinanceView): string {
  const query = new URLSearchParams({ tenant: tenantId, finance_view: view, source: "demo_data" });
  return `/app/finance?${query.toString()}`;
}
